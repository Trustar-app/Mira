# run_omni.py (修改版)
import asyncio
import os
import sys
import time
import signal
from pathlib import Path
import uuid
import argparse

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入IPC模块
from comm.IPC import SharedMemoryIPC, IPCMessage, base64_to_file, file_to_base64

import app.agent as ag
from app.llm import LLM
from app.logger import logger

# 历史消息存储
history_cache = {}
# 临时文件目录
TEMP_DIR = Path("./tmp")
TEMP_DIR.mkdir(exist_ok=True)

# 退出信号标记
running = True

# 全局IPC对象
req_ipc = None
resp_ipc = None

def signal_handler(sig, frame):
    """处理退出信号"""
    global running
    logger.info("接收到退出信号，准备关闭后端服务...")
    running = False

# 解析命令行参数获取共享内存名称
def parse_args():
    parser = argparse.ArgumentParser(description="后端Agent服务")
    parser.add_argument("--ipc-name", type=str, default="mira_ipc",
                        help="共享内存基础名称")
    return parser.parse_args()


# 注册信号处理
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def connect_ipc(ipc_name):
    """连接到IPC共享内存"""
    req_name = f"{ipc_name}_req"
    resp_name = f"{ipc_name}_resp"
    max_retries = 10
    retries = 0
    global req_ipc, resp_ipc
    
    while retries < max_retries:
        try:
            # 连接到请求通道
            req_ipc = SharedMemoryIPC(name=req_name, create=False)
            req_ipc.connect()
            
            # 连接到响应通道
            resp_ipc = SharedMemoryIPC(name=resp_name, create=False)
            resp_ipc.connect()
            
            logger.info(f"成功连接到IPC共享内存: {req_name}和{resp_name}")
            return req_ipc, resp_ipc
        except Exception as e:
            retries += 1
            logger.error(f"连接IPC失败 (尝试 {retries}/{max_retries}): {e}")
            if retries >= max_retries:
                logger.error("已达到最大重试次数，无法连接到共享内存")
                raise e
            # 等待前端创建完成
            time.sleep(1)

async def process_message(message: IPCMessage, agent = None):
    """处理接收到的IPC消息"""
    global req_ipc, resp_ipc
    
    if not message:
        return
        
    logger.info(f"处理消息: {message.message_type}, ID: {message.message_id}")
    
    try:
        # 更新消息状态为处理中
        # resp_ipc.send_message(IPCMessage(
        #     message_type=message.message_type,
        #     message_id=message.message_id,
        #     status="processing"
        # ))
        
        if message.message_type == "请求agent服务":
            if agent is None:
                # 创建Agent
                agent = ag.QwenOmniAgent(llm=LLM(config_name="omni"))
            
            # 准备请求参数，仅包含agent支持的4个参数
            kwargs = {}
            
            # 文本请求
            if message.text_data:
                kwargs["text_request"] = message.text_data
            else:
                kwargs["text_request"] = "解释一下这个视频/图像/音频"
            
            # 处理图像
            if message.image_data:
                image_path = str(TEMP_DIR / f"{uuid.uuid4()}.png")
                if base64_to_file(message.image_data, image_path):
                    kwargs["image_request"] = file_to_base64(image_path)
            
            # 处理视频
            if message.video_data:
                video_path = str(TEMP_DIR / f"{uuid.uuid4()}.mp4")
                if base64_to_file(message.video_data, video_path):
                    kwargs["video_request"] = file_to_base64(video_path)
            
            # 处理音频
            if message.audio_data:
                audio_path = str(TEMP_DIR / f"{uuid.uuid4()}.wav")
                if base64_to_file(message.audio_data, audio_path):
                    # 将音频数据转换为base64并作为audio_request参数
                    kwargs["audio_request"] = file_to_base64(audio_path)
            
            logger.info(f"调用agent.run，参数: {list(kwargs.keys())}")
            
            # 异步调用agent
            try:
                result = await agent.run(**kwargs)

                # 解析文本
                response_text = result["text"]
                
                # 如果返回的是音频数据的路径，转换为base64
                response_audio = ""
                if "audio_path" in result:
                    audio_path = result["audio_path"]
                    if os.path.exists(audio_path):
                        response_audio = file_to_base64(audio_path)
                elif "audio" in result:  # 如果直接返回的是base64编码的音频
                    response_audio = result["audio"]
                
                # 创建完成响应消息
                response_message = IPCMessage(
                    message_type=message.message_type,
                    message_id=message.message_id,
                    status="completed",
                    response_text=response_text
                )
                
                if response_audio:
                    response_message.response_audio = response_audio
                
                # 发送完成响应
                resp_ipc.send_message(response_message)
                logger.info("agent发送响应完成")
                
            except Exception as err:
                logger.error(f"Agent执行失败: {err}")
                error_message = IPCMessage(
                    message_type=message.message_type,
                    message_id=message.message_id,
                    status="error",
                    error_message=f"处理请求时出错: {str(err)}"
                )
                resp_ipc.send_message(error_message)
            
        elif message.message_type == "清空历史消息":
            # 清空历史消息缓存
            history_cache.clear()
            # 更新消息状态为完成
            resp_ipc.send_message(IPCMessage(
                message_type=message.message_type,
                message_id=message.message_id,
                status="completed"
            ))
            
        elif message.message_type == "挂起后端服务":
            # 更新消息状态为完成
            resp_ipc.send_message(IPCMessage(
                message_type=message.message_type,
                message_id=message.message_id,
                status="completed"
            ))
            # 触发退出
            global running
            running = False
            
        else:
            # 未知消息类型
            logger.warning(f"未知消息类型: {message.message_type}")
            error_message = IPCMessage(
                message_type=message.message_type,
                message_id=message.message_id,
                status="error",
                error_message=f"未知消息类型: {message.message_type}"
            )
            resp_ipc.send_message(error_message)
    
    except Exception as e:
        logger.error(f"处理消息时出错: {e}")
        try:
            error_message = IPCMessage(
                message_type=message.message_type if message else "unknown",
                message_id=message.message_id if message else str(uuid.uuid4()),
                status="error",
                error_message=f"处理消息时出错: {str(e)}"
            )
            resp_ipc.send_message(error_message)
        except Exception as send_err:
            logger.error(f"发送错误消息失败: {send_err}")

async def clean_temp_files():
    """清理临时文件"""
    try:
        for file in TEMP_DIR.glob("*"):
            # 检查文件是否超过30分钟未被修改
            if time.time() - file.stat().st_mtime > 30 * 60:
                try:
                    file.unlink()
                    logger.info(f"已删除临时文件: {file}")
                except Exception as err:
                    logger.warning(f"删除临时文件失败: {file}, 错误: {err}")
    except Exception as err:
        logger.error(f"清理临时文件时出错: {err}")

async def main():
    # 解析命令行参数获取共享内存名称
    args = parse_args()
    ipc_name = args.ipc_name
    logger.info(f"启动后端服务，将连接到共享内存: {ipc_name}")
    
    # 连接IPC
    global req_ipc, resp_ipc
    req_ipc, resp_ipc = connect_ipc(ipc_name)
    
    # 创建Agent实例（可以重用）
    agent = ag.QwenOmniAgent(llm=LLM(config_name="omni"))
    
    # 主循环
    try:
        while running:
            try:
                # 获取一条消息
                message = req_ipc.peek_message()
                
                if message:
                    # 处理消息
                    await process_message(message, agent)
                    # 从请求队列中移除消息（使用安全模式，避免出错）
                    try:
                        req_ipc.receive_message()
                    except Exception as err:
                        logger.error(f"移除消息时出错: {err}")
                else:
                    # 无消息时休眠一段时间
                    await asyncio.sleep(0.2)  # 200ms
                
                # 每10秒清理一次临时文件
                if int(time.time()) % 10 == 0:
                    await clean_temp_files()
            except Exception as loop_err:
                logger.error(f"主循环单次迭代异常: {loop_err}")
                await asyncio.sleep(1)  # 出错后休息一秒
                
    except Exception as err:
        logger.error(f"主循环异常: {err}")
    
    finally:
        # 关闭IPC连接，但不要unlink（由前端负责）
        try:
            if req_ipc:
                req_ipc.close()
            if resp_ipc:
                resp_ipc.close()
            logger.info("已关闭IPC连接")
        except Exception as e:
            logger.error(f"关闭IPC连接失败: {e}")
        
        logger.info("后端服务已停止")

if __name__ == '__main__':
    try: # 运行主函数
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("接收到键盘中断，退出程序")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
    finally:
        logger.info("程序已结束")