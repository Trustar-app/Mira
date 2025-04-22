# ./comm/IPC.py
import multiprocessing as mp
from multiprocessing import shared_memory
import numpy as np
import json
import os
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Union
import base64

@dataclass
class IPCMessage:
    """进程间通信的消息格式"""
    message_type: str  # 消息类型："请求agent服务"，"清空历史消息"，"挂起后端服务"等
    text_data: str = ""  # 文本数据
    image_data: str = ""  # 图像数据（base64编码）
    audio_data: str = ""  # 音频数据（base64编码）
    video_data: str = ""  # 视频数据（base64编码）
    response_text: str = ""  # 回复的文本
    response_audio: str = ""  # 回复的音频（base64编码）
    message_id: str = ""  # 消息ID
    status: str = "pending"  # 状态：pending, processing, completed, error
    error_message: str = ""  # 错误信息
    timestamp: float = field(default_factory=time.time)  # 时间戳
    system_prompt: str = ""  # 系统提示语
    voice: str = ""  # 语音选择
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IPCMessage':
        """从字典创建实例"""
        return cls(**data)

class SharedMemoryIPC:
    """基于共享内存的进程间通信实现"""
    
    def __init__(self, name: str, create: bool = True, size: int = 1024*1024*600):  # 默认200MB共享内存
        """
        初始化共享内存IPC
        :param name: 共享内存名称
        :param size: 共享内存大小（字节）
        """
        self.name = name
        self.size = size
        self.shm = shared_memory.SharedMemory(
            name=name, create=create, size=size
        )
        # 创建锁用于同步访问
        self.lock = mp.Lock()
        # 初始化共享内存
        self._init_memory()
    
    def _init_memory(self):
        """初始化共享内存区域"""
        with self.lock:
            # 存储格式: [message_count(4字节), 消息1长度(4字节), 消息1数据, 消息2长度(4字节), 消息2数据, ...]
            buffer = memoryview(self.shm.buf)
            # 初始化消息计数为0
            np.frombuffer(buffer[:4], dtype=np.int32)[0] = 0
    
    def connect(self):
        """连接到已存在的共享内存"""
        self.shm = shared_memory.SharedMemory(name=self.name)
        
    def close(self):
        """关闭共享内存连接"""
        self.shm.close()
    
    def unlink(self):
        """释放共享内存资源"""
        self.shm.unlink()
    
    def send_message(self, message: IPCMessage) -> bool:
        """
        发送消息到共享内存
        :param message: 要发送的消息
        :return: 是否发送成功
        """
        try:
            with self.lock:
                buffer = memoryview(self.shm.buf)
                # 获取当前消息数量
                msg_count = np.frombuffer(buffer[:4], dtype=np.int32)[0]
                
                # 计算新消息的位置
                pos = 4  # 跳过消息计数器
                for _ in range(msg_count):
                    msg_len = np.frombuffer(buffer[pos:pos+4], dtype=np.int32)[0]
                    pos += 4 + msg_len  # 跳过长度字段和消息内容
                
                # 序列化消息
                msg_data = json.dumps(message.to_dict()).encode('utf-8')
                msg_len = len(msg_data)
                
                # 检查剩余空间是否足够
                if pos + 4 + msg_len > self.size:
                    return False
                
                # 写入消息长度
                np.frombuffer(buffer[pos:pos+4], dtype=np.int32)[0] = msg_len
                # 写入消息内容
                buffer[pos+4:pos+4+msg_len] = msg_data
                # 更新消息计数
                np.frombuffer(buffer[:4], dtype=np.int32)[0] = msg_count + 1
                
                return True
        except Exception as e:
            print(f"发送消息失败: {e}")
            return False
    
    def receive_message(self) -> Optional[IPCMessage]:
        """
        从共享内存接收一条消息（并从队列中移除）
        :return: 消息对象，如果没有消息则返回None
        """
        try:
            with self.lock:
                buffer = memoryview(self.shm.buf)
                # 获取当前消息数量
                msg_count = np.frombuffer(buffer[:4], dtype=np.int32)[0]
                
                if msg_count == 0:
                    return None
                
                # 读取第一条消息
                pos = 4  # 跳过消息计数器
                msg_len = np.frombuffer(buffer[pos:pos+4], dtype=np.int32)[0]
                msg_data = buffer[pos+4:pos+4+msg_len].tobytes()
                
                # 解析消息
                message = IPCMessage.from_dict(json.loads(msg_data.decode('utf-8')))
                
                # 移除该消息并整理共享内存
                new_pos = pos + 4 + msg_len
                
                # 安全地移动后续数据
                if msg_count > 1:  # 如果有多条消息
                    # 计算后续数据的长度
                    next_pos = new_pos
                    for _ in range(msg_count - 1):
                        next_msg_len = np.frombuffer(buffer[next_pos:next_pos+4], dtype=np.int32)[0]
                        next_pos += 4 + next_msg_len
                    
                    # 计算需要移动的字节数
                    move_size = next_pos - new_pos
                    
                    # 逐字节移动数据而不是整块赋值，避免结构不匹配问题
                    for i in range(move_size):
                        buffer[pos + i] = buffer[new_pos + i]
                
                # 更新消息计数
                np.frombuffer(buffer[:4], dtype=np.int32)[0] = msg_count - 1
                
                return message
        except Exception as e:
            print(f"接收消息失败: {e}")
            return None
    
    def peek_message(self) -> Optional[IPCMessage]:
        """
        查看第一条消息但不从队列中移除
        :return: 消息对象，如果没有消息则返回None
        """
        try:
            with self.lock:
                buffer = memoryview(self.shm.buf)
                # 获取当前消息数量
                msg_count = np.frombuffer(buffer[:4], dtype=np.int32)[0]
                
                if msg_count == 0:
                    return None
                
                # 读取第一条消息
                pos = 4  # 跳过消息计数器
                msg_len = np.frombuffer(buffer[pos:pos+4], dtype=np.int32)[0]
                msg_data = buffer[pos+4:pos+4+msg_len].tobytes()
                
                # 解析消息
                message = IPCMessage.from_dict(json.loads(msg_data.decode('utf-8')))
                return message
        except Exception as e:
            print(f"查看消息失败: {e}")
            return None
    
    def update_message(self, message_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新指定ID的消息
        :param message_id: 要更新的消息ID
        :param updates: 要更新的字段
        :return: 是否更新成功
        """
        try:
            with self.lock:
                buffer = memoryview(self.shm.buf)
                # 获取当前消息数量
                msg_count = np.frombuffer(buffer[:4], dtype=np.int32)[0]
                
                pos = 4  # 跳过消息计数器
                for _ in range(msg_count):
                    msg_pos = pos
                    msg_len = np.frombuffer(buffer[pos:pos+4], dtype=np.int32)[0]
                    msg_data = buffer[pos+4:pos+4+msg_len].tobytes()
                    pos += 4 + msg_len
                    
                    # 解析消息
                    msg_dict = json.loads(msg_data.decode('utf-8'))
                    if msg_dict.get('message_id') == message_id:
                        # 更新消息
                        for key, value in updates.items():
                            msg_dict[key] = value
                        
                        # 重新序列化
                        new_msg_data = json.dumps(msg_dict).encode('utf-8')
                        new_msg_len = len(new_msg_data)
                        
                        if new_msg_len <= msg_len:
                            # 如果新消息不比旧消息长，直接覆盖
                            np.frombuffer(buffer[msg_pos:msg_pos+4], dtype=np.int32)[0] = new_msg_len
                            buffer[msg_pos+4:msg_pos+4+new_msg_len] = new_msg_data
                            return True
                        else:
                            # 如果新消息更长，需要移动后续数据
                            shift = new_msg_len - msg_len
                            if pos + shift > self.size:
                                return False  # 空间不足
                            
                            # 移动后续数据
                            buffer[pos+shift:self.size] = buffer[pos:self.size-shift]
                            # 更新消息长度
                            np.frombuffer(buffer[msg_pos:msg_pos+4], dtype=np.int32)[0] = new_msg_len
                            # 写入新消息
                            buffer[msg_pos+4:msg_pos+4+new_msg_len] = new_msg_data
                            return True
                
                return False  # 未找到指定ID的消息
        except Exception as e:
            print(f"更新消息失败: {e}")
            return False

# 辅助函数
def file_to_base64(file_path: str) -> str:
    """将文件转换为base64字符串"""
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')

def base64_to_file(base64_str: str, file_path: str) -> bool:
    """将base64字符串保存为文件"""
    try:
        with open(file_path, "wb") as f:
            f.write(base64.b64decode(base64_str))
        return True
    except Exception as e:
        print(f"保存文件失败: {e}")
        return False