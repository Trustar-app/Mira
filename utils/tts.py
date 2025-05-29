import os
import requests
import dashscope
from pathlib import Path
import time
import shutil
from datetime import datetime, timedelta

from utils.loggers import MiraLog

# 缓存配置
AUDIO_CACHE_DIR = "audio_cache"
MAX_CACHE_SIZE_MB = 100  # 最大缓存大小（MB）
MAX_CACHE_AGE_HOURS = 1 # 最大缓存时间（小时）
CLEANUP_INTERVAL_HOURS = 1  # 清理间隔（小时）

def _get_cache_size_mb():
    """获取缓存目录大小（MB）"""
    total_size = 0
    for dirpath, _, filenames in os.walk(AUDIO_CACHE_DIR):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)  # 转换为MB

def _cleanup_cache():
    """清理音频缓存"""
    MiraLog("tts", "开始清理音频缓存")
    try:
        if not os.path.exists(AUDIO_CACHE_DIR):
            return

        current_time = time.time()
        files_to_delete = []
        total_size = 0
        need_cleanup = False

        # 遍历所有文件
        for filename in os.listdir(AUDIO_CACHE_DIR):
            if not filename.endswith('.wav'):
                continue
                
            file_path = os.path.join(AUDIO_CACHE_DIR, filename)
            file_stat = os.stat(file_path)
            file_age = current_time - file_stat.st_mtime
            file_size = file_stat.st_size / (1024 * 1024)  # MB
            
            # 检查文件是否过期
            if file_age > MAX_CACHE_AGE_HOURS * 3600:
                files_to_delete.append(file_path)
                need_cleanup = True
            else:
                total_size += file_size

        # 检查是否需要基于大小清理
        MiraLog("tts", f"当前缓存大小：{total_size}MB")
        MiraLog("tts", f"最大缓存大小：{MAX_CACHE_SIZE_MB}MB")
        if total_size > MAX_CACHE_SIZE_MB:
            need_cleanup = True
            # 按修改时间排序所有文件
            all_files = [(os.path.join(AUDIO_CACHE_DIR, f), os.path.getmtime(os.path.join(AUDIO_CACHE_DIR, f)))
                        for f in os.listdir(AUDIO_CACHE_DIR) if f.endswith('.wav')]
            all_files.sort(key=lambda x: x[1])  # 按修改时间排序
            
            # 删除最旧的文件直到总大小低于限制
            for file_path, _ in all_files:
                if total_size <= MAX_CACHE_SIZE_MB:
                    break
                if file_path not in files_to_delete:  # 避免重复添加
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    files_to_delete.append(file_path)
                    total_size -= file_size

        # 只有在需要清理时才执行删除操作
        if need_cleanup:
            MiraLog("tts", f"需要清理的文件数量：{len(files_to_delete)}")
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    MiraLog("tts", f"已删除缓存文件：{file_path}")
                except Exception as e:
                    MiraLog("tts", f"删除文件失败 {file_path}: {str(e)}")
        else:
            MiraLog("tts", "无需清理缓存")

    except Exception as e:
        MiraLog("tts", f"清理缓存时出错：{str(e)}")

def _ensure_cache_cleanup():
    """确保缓存清理机制运行"""
    cleanup_file = os.path.join(AUDIO_CACHE_DIR, ".last_cleanup")
    current_time = time.time()
    
    try:
        # 检查当前缓存大小
        current_size = _get_cache_size_mb()
        MiraLog("tts", f"检查缓存状态 - 当前大小：{current_size}MB，最大限制：{MAX_CACHE_SIZE_MB}MB")
        
        # 检查是否需要基于时间间隔清理
        time_based_cleanup = False
        if os.path.exists(cleanup_file):
            last_cleanup = os.path.getmtime(cleanup_file)
            time_based_cleanup = current_time - last_cleanup >= CLEANUP_INTERVAL_HOURS * 3600
            if time_based_cleanup:
                MiraLog("tts", f"达到清理时间间隔：{CLEANUP_INTERVAL_HOURS}小时")
        else:
            time_based_cleanup = True
            MiraLog("tts", "清理记录文件不存在，需要清理")
        
        # 检查是否需要基于大小清理
        size_based_cleanup = current_size > MAX_CACHE_SIZE_MB
        if size_based_cleanup:
            MiraLog("tts", "缓存大小超过限制，需要清理")
        
        # 如果任一条件满足，执行清理
        if time_based_cleanup or size_based_cleanup:
            _cleanup_cache()
            # 更新最后清理时间
            with open(cleanup_file, 'w') as f:
                f.write(str(current_time))
        else:
            MiraLog("tts", "无需清理缓存")
            
    except Exception as e:
        MiraLog("tts", f"检查缓存状态时出错：{str(e)}")

def text_to_speech(text: str, voice: str = "Cherry", save_dir: str = AUDIO_CACHE_DIR, api_key: str = None) -> str:
    """
    将文本转换为语音并保存为音频文件
    
    Args:
        text: 要转换的文本
        voice: 语音类型，默认使用 "Cherry"
        save_dir: 音频文件保存目录，默认为 AUDIO_CACHE_DIR
        api_key: API key，如果不提供则使用环境变量中的 TTS_API_KEY
    
    Returns:
        str: 保存的音频文件路径，如果失败则返回 None
    """
    try:
        # 确保缓存目录存在
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        
        # 检查并清理缓存
        _ensure_cache_cleanup()
        
        # 生成唯一的文件名
        import hashlib
        filename = f"{hashlib.md5(f'{text}_{time.time()}'.encode()).hexdigest()}.wav"
        save_path = os.path.join(save_dir, filename)
        
        # 调用 TTS API
        response = dashscope.audio.qwen_tts.SpeechSynthesizer.call(
            model="qwen-tts",
            api_key=api_key,
            text=text,
            voice=voice,
        )
        
        if not response or not response.output or not response.output.audio:
            MiraLog("tts", "TTS API 返回结果异常", "ERROR")
            return None
            
        audio_url = response.output.audio["url"]
        
        # 下载音频文件
        response = requests.get(audio_url)
        response.raise_for_status()
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
            
        MiraLog("tts", f"音频文件已保存至：{save_path}")
        return save_path
        
    except Exception as e:
        MiraLog("tts", f"TTS 转换失败：{str(e)}", "ERROR")
        return None

def init_audio_cache():
    """初始化音频缓存目录"""
    try:
        # 创建缓存目录
        Path(AUDIO_CACHE_DIR).mkdir(parents=True, exist_ok=True)
        # 清理旧缓存
        _cleanup_cache()
    except Exception as e:
        print(f"初始化音频缓存失败：{str(e)}")

# 测试代码
if __name__ == "__main__":
    init_audio_cache()
    test_text = "那我来给大家推荐一款T恤，这款呢真的是超级好看，这个颜色呢很显气质，而且呢也是搭配的绝佳单品，大家可以闭眼入，真的是非常好看，对身材的包容性也很好，不管啥身材的宝宝呢，穿上去都是很好看的。推荐宝宝们下单哦。"
    result = text_to_speech(test_text)
    print(f"转换结果：{result}")