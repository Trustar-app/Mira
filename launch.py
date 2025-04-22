# mira_process.py (修改版)
import gradio as gr
from http import HTTPStatus
import uuid
from gradio_client import utils as client_utils
import gradio.processing_utils as processing_utils
import base64
import soundfile as sf
import numpy as np
import io
import os
from dotenv import load_dotenv
import modelscope_studio.components.base as ms
import modelscope_studio.components.antd as antd
import shutil
import multiprocessing
import subprocess
import sys
import time
import json
from pathlib import Path

# 创建comm目录（如果不存在）
os.makedirs("comm", exist_ok=True)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入IPC模块
from comm.IPC import SharedMemoryIPC, IPCMessage, file_to_base64

# 加载环境变量
load_dotenv()

# Voice settings
VOICE_LIST = ['Cherry', 'Ethan', 'Serena', 'Chelsie']
DEFAULT_VOICE = 'Cherry'

# 本地文件存储路径
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

default_system_prompt = 'You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech.'

is_modelscope_studio = os.getenv('MODELSCOPE_ENVIRONMENT') == 'studio'

# 创建IPC连接
req_ipc = None  # 用于发送请求到后端
resp_ipc = None  # 用于接收后端的响应
MESSAGE_CHECK_INTERVAL = 0.1  # 100ms

def init_ipc():
    global req_ipc, resp_ipc


    try:
        # 初始化请求IPC通道
        req_ipc = SharedMemoryIPC(name="mira_ipc_req", size=1024*1024*200)  # 200MB共享内存
        # 初始化响应IPC通道
        resp_ipc = SharedMemoryIPC(name="mira_ipc_resp", size=1024*1024*200)  # 200MB共享内存
        print("IPC通道初始化成功")
    except Exception is FileNotFoundError:
        try:
            from multiprocessing import shared_memory
            shm = shared_memory.SharedMemory(name="mira_ipc_req")
            shm.close()
            shm.unlink()
            shm = shared_memory.SharedMemory(name="mira_ipc_resp")
            shm.close()
            shm.unlink()
        except Exception as e:
            print(f"IPC初始化失败: {e}")
            raise e

def get_text(text: str, cn_text: str):
    if is_modelscope_studio:
        return cn_text
    return text

def save_uploaded_file(file_path: str) -> str:
    """保存上传的文件到本地目录"""
    if file_path.startswith("http"):
        return file_path
    
    # 生成唯一的文件名
    ext = os.path.splitext(file_path)[1]
    new_filename = f"{uuid.uuid4()}{ext}"
    new_file_path = os.path.join(UPLOAD_DIR, new_filename)
    
    # 复制文件到上传目录
    shutil.copy2(file_path, new_file_path)
    return new_file_path

def media_predict(audio, video, history, system_prompt, state_value, voice_choice):
    """处理媒体输入并通过IPC发送到后端"""
    message_id = str(uuid.uuid4())
    
    # 构造IPC消息
    ipc_message = IPCMessage(
        message_type="请求agent服务",
        message_id=message_id,
        text_data="",  # 媒体模式下没有文本输入
        system_prompt=system_prompt,
        voice=voice_choice
    )
    
    # 处理音频
    if audio:
        audio_path = save_uploaded_file(audio)
        ipc_message.audio_data = file_to_base64(audio_path)
        history.append({"role": "user", "content": (audio, )})
        
    # 处理视频
    if video:
        video_path = save_uploaded_file(video)
        ipc_message.video_data = file_to_base64(video_path)
        history.append({"role": "user", "content": (video, )})
    
    # 第一次返回，更新UI状态
    yield (
        None,  # microphone
        None,  # webcam
        history,  # media_chatbot
        gr.update(visible=False),  # submit_btn
        gr.update(visible=True),  # stop_btn
        state_value  # state
    )
    
    # 发送消息到后端
    if req_ipc:
        req_ipc.send_message(ipc_message)
        print("发送了消息到后端")
        
        # 添加空白回复占位符
        history.append({"role": "assistant", "content": ""})
        
        # 等待并处理后端响应
        while True:
            # 检查消息更新
            message = resp_ipc.peek_message()
            if message and message.message_id == message_id and message.status != "pending":
                print(f"从agent读取信息：\n{message}")
                # 如果消息处理完成或出错
                if message.status == "completed":
                    # 更新文本回复
                    if message.response_text:
                        history[-1]["content"] = message.response_text
                        yield (
                            None,  # microphone
                            None,  # webcam
                            history,  # media_chatbot
                            gr.update(visible=False),  # submit_btn
                            gr.update(visible=True),  # stop_btn
                            state_value  # state
                        )
                    
                    # 处理音频回复
                    if message.response_audio:
                        # 将base64音频转换为文件
                        audio_data = base64.b64decode(message.response_audio)
                        audio_np = np.frombuffer(audio_data, dtype=np.int16)
                        wav_io = io.BytesIO()
                        sf.write(wav_io, audio_np, samplerate=24000, format="WAV")
                        wav_io.seek(0)
                        wav_bytes = wav_io.getvalue()
                        audio_path = processing_utils.save_bytes_to_cache(
                            wav_bytes, "audio.wav", cache_dir=demo.GRADIO_CACHE)
                        
                        history.append({
                            "role": "assistant",
                            "content": gr.Audio(audio_path)
                        })
                    
                    # 从队列中移除已处理的消息
                    resp_ipc.receive_message()
                    break
                elif message.status == "error":
                    # 处理错误情况
                    history[-1]["content"] = f"错误: {message.error_message}"
                    # 从队列中移除已处理的消息
                    resp_ipc.receive_message()
                    break
                elif message.status == "processing":
                    # 处理中，更新UI显示部分完成的响应
                    if message.response_text and message.response_text != history[-1]["content"]:
                        history[-1]["content"] = message.response_text
                        yield (
                            None,  # microphone
                            None,  # webcam
                            history,  # media_chatbot
                            gr.update(visible=False),  # submit_btn
                            gr.update(visible=True),  # stop_btn
                            state_value  # state
                        )
            
            # 短暂等待后继续检查
            time.sleep(MESSAGE_CHECK_INTERVAL)
    
    # 最终返回，更新UI状态
    yield (
        None,  # microphone
        None,  # webcam
        history,  # media_chatbot
        gr.update(visible=True),  # submit_btn
        gr.update(visible=False),  # stop_btn
        state_value  # state
    )

def chat_predict(text, audio, image, video, history, system_prompt, state_value, voice_choice):
    """处理文本和媒体输入并通过IPC发送到后端"""
    message_id = str(uuid.uuid4())
    
    # 构造IPC消息
    ipc_message = IPCMessage(
        message_type="请求agent服务",
        message_id=message_id,
        text_data=text or "",
        system_prompt=system_prompt,
        voice=voice_choice
    )
    
    # 处理文本输入
    if text:
        history.append({"role": "user", "content": text})
    
    # 处理音频输入
    if audio:
        audio_path = save_uploaded_file(audio)
        ipc_message.audio_data = file_to_base64(audio_path)
        history.append({"role": "user", "content": (audio, )})
    
    # 处理图像输入
    if image:
        image_path = save_uploaded_file(image)
        ipc_message.image_data = file_to_base64(image_path)
        history.append({"role": "user", "content": (image, )})
    
    # 处理视频输入
    if video:
        video_path = save_uploaded_file(video)
        ipc_message.video_data = file_to_base64(video_path)
        history.append({"role": "user", "content": (video, )})
    
    # 第一次返回，更新UI状态
    yield None, None, None, None, history, state_value
    
    # 发送消息到后端
    if req_ipc:
        req_ipc.send_message(ipc_message)
        
        # 添加空白回复占位符
        history.append({"role": "assistant", "content": ""})
        
        # 等待并处理后端响应
        while True:
            # 检查消息更新
            message = resp_ipc.peek_message()
            if message and message.message_id == message_id and message.status != "pending":
                # 如果消息处理完成或出错
                if message.status == "completed":
                    # 更新文本回复
                    if message.response_text:
                        history[-1]["content"] = message.response_text
                        yield gr.skip(), gr.skip(), gr.skip(), gr.skip(), history, state_value
                    
                    # 处理音频回复
                    if message.response_audio:
                        # 将base64音频转换为文件
                        audio_data = base64.b64decode(message.response_audio)
                        audio_np = np.frombuffer(audio_data, dtype=np.int16)
                        wav_io = io.BytesIO()
                        sf.write(wav_io, audio_np, samplerate=24000, format="WAV")
                        wav_io.seek(0)
                        wav_bytes = wav_io.getvalue()
                        audio_path = processing_utils.save_bytes_to_cache(
                            wav_bytes, "audio.wav", cache_dir=demo.GRADIO_CACHE)
                        
                        history.append({
                            "role": "assistant",
                            "content": gr.Audio(audio_path)
                        })
                    
                    # 从队列中移除已处理的消息
                    resp_ipc.receive_message()
                    break
                elif message.status == "error":
                    # 处理错误情况
                    history[-1]["content"] = f"错误: {message.error_message}"
                    # 从队列中移除已处理的消息
                    resp_ipc.receive_message()
                    break
                elif message.status == "processing":
                    # 处理中，更新UI显示部分完成的响应
                    if message.response_text and message.response_text != history[-1]["content"]:
                        history[-1]["content"] = message.response_text
                        yield gr.skip(), gr.skip(), gr.skip(), gr.skip(), history, state_value
            
            # 短暂等待后继续检查
            time.sleep(MESSAGE_CHECK_INTERVAL)
    
    yield gr.skip(), gr.skip(), gr.skip(), gr.skip(), history, state_value

def clear_history_ipc():
    """发送清空历史消息的请求"""
    if req_ipc:
        ipc_message = IPCMessage(
            message_type="清空历史消息",
            message_id=str(uuid.uuid4())
        )
        req_ipc.send_message(ipc_message)

with gr.Blocks() as demo, ms.Application(), antd.ConfigProvider():
    state = gr.State({"file_cache": {}})

    with gr.Sidebar(open=False):
        system_prompt_textbox = gr.Textbox(label="System Prompt",
                                           value=default_system_prompt)
        voice_choice = gr.Dropdown(label="Voice Choice",
                                   choices=VOICE_LIST,
                                   value=DEFAULT_VOICE)
    with antd.Flex(gap="small", justify="center", align="center"):
        antd.Image('./logo-1.png', preview=False, width=67, height=67)
        with antd.Flex(vertical=True, gap="small", align="center"):
            antd.Typography.Title("Mira",
                                  level=1,
                                  elem_style=dict(margin=0, fontSize=28))
            with antd.Flex(vertical=True, gap="small"):
                antd.Typography.Text(get_text("🎯 Instructions for use:",
                                              "🎯 使用说明："),
                                     strong=True)
                antd.Typography.Text(
                    get_text(
                        "1️⃣ Click the Audio Record button or the Camera Record button.",
                        "1️⃣ 点击音频录制按钮，或摄像头-录制按钮"))
                antd.Typography.Text(
                    get_text("2️⃣ Input audio or video.", "2️⃣ 输入音频或者视频"))
                antd.Typography.Text(
                    get_text(
                        "3️⃣ Click the submit button and wait for the model's response.",
                        "3️⃣ 点击提交并等待模型的回答"))
        antd.Image('./logo-2.png',
                   preview=False,
                   width=80,
                   height=80,
                   elem_style=dict(marginTop=5))
    with gr.Tabs():
        with gr.Tab("Online"):
            with gr.Row():
                with gr.Column(scale=1):
                    microphone = gr.Audio(sources=['microphone'],
                                          format="wav",
                                          type="filepath")
                    webcam = gr.Video(sources=['webcam'],
                                      format="mp4",
                                      height=400,
                                      include_audio=True)
                    submit_btn = gr.Button(get_text("Submit", "提交"),
                                           variant="primary")
                    stop_btn = gr.Button(get_text("Stop", "停止"), visible=False)
                    clear_btn = gr.Button(get_text("Clear History", "清除历史"))
                with gr.Column(scale=2):
                    media_chatbot = gr.Chatbot(height=650, type="messages")

                def clear_history():
                    clear_history_ipc()
                    return [], gr.update(value=None), gr.update(value=None)

                submit_event = submit_btn.click(fn=media_predict,
                                                inputs=[
                                                    microphone, webcam,
                                                    media_chatbot,
                                                    system_prompt_textbox,
                                                    state, voice_choice
                                                ],
                                                outputs=[
                                                    microphone, webcam,
                                                    media_chatbot, submit_btn,
                                                    stop_btn, state
                                                ])
                stop_btn.click(
                    fn=lambda:
                    (gr.update(visible=True), gr.update(visible=False)),
                    inputs=None,
                    outputs=[submit_btn, stop_btn],
                    cancels=[submit_event],
                    queue=False)
                clear_btn.click(fn=clear_history,
                                inputs=None,
                                outputs=[media_chatbot, microphone, webcam])

        with gr.Tab("Offline"):
            chatbot = gr.Chatbot(type="messages", height=650)

            # Media upload section in one row
            with gr.Row(equal_height=True):
                audio_input = gr.Audio(sources=["upload"],
                                       type="filepath",
                                       label="Upload Audio",
                                       elem_classes="media-upload",
                                       scale=1)
                image_input = gr.Image(sources=["upload"],
                                       type="filepath",
                                       label="Upload Image",
                                       elem_classes="media-upload",
                                       scale=1)
                video_input = gr.Video(sources=["upload"],
                                       label="Upload Video",
                                       elem_classes="media-upload",
                                       scale=1)

            # Text input section
            text_input = gr.Textbox(show_label=False,
                                    placeholder="Enter text here...")

            # Control buttons
            with gr.Row():
                submit_btn = gr.Button(get_text("Submit", "提交"),
                                       variant="primary",
                                       size="lg")
                stop_btn = gr.Button(get_text("Stop", "停止"),
                                     visible=False,
                                     size="lg")
                clear_btn = gr.Button(get_text("Clear History", "清除历史"),
                                      size="lg")

            def clear_chat_history():
                clear_history_ipc()
                return [], gr.update(value=None), gr.update(
                    value=None), gr.update(value=None), gr.update(value=None)

            submit_event = gr.on(
                triggers=[submit_btn.click, text_input.submit],
                fn=chat_predict,
                inputs=[
                    text_input, audio_input, image_input, video_input, chatbot,
                    system_prompt_textbox, state, voice_choice
                ],
                outputs=[
                    text_input, audio_input, image_input, video_input, chatbot,
                    state
                ])

            stop_btn.click(fn=lambda:
                           (gr.update(visible=True), gr.update(visible=False)),
                           inputs=None,
                           outputs=[submit_btn, stop_btn],
                           cancels=[submit_event],
                           queue=False)

            clear_btn.click(fn=clear_chat_history,
                            inputs=None,
                            outputs=[
                                chatbot, text_input, audio_input, image_input,
                                video_input
                            ])

            # Add some custom CSS to improve the layout
            gr.HTML("""
                <style>
                    .media-upload {
                        margin: 10px;
                        min-height: 160px;
                    }
                    .media-upload > .wrap {
                        border: 2px dashed #ccc;
                        border-radius: 8px;
                        padding: 10px;
                        height: 100%;
                    }
                    .media-upload:hover > .wrap {
                        border-color: #666;
                    }
                    /* Make upload areas equal width */
                    .media-upload {
                        flex: 1;
                        min-width: 0;
                    }
                </style>
            """)

# 启动run_omni.py作为后端进程
def start_backend_process():
    # 获取当前目录，用于确定run_omni.py的位置
    current_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(current_dir, "run_qwen_omni.py")
    
    # 传递共享内存基础名称作为参数给后端进程
    # 后端将使用{ipc_name}_req和{ipc_name}_resp作为两个通道的名称
    process = subprocess.Popen([sys.executable, main_script, "--ipc-name=mira_ipc"])
    return process

# 添加清理函数确保正确释放共享内存
def cleanup_ipc():
    global req_ipc, resp_ipc
    if req_ipc and hasattr(req_ipc, 'shm'):
        try:
            req_ipc.close()
            # 只在前端进程中unlink共享内存
            req_ipc.unlink()
            print("请求通道共享内存资源已清理")
        except Exception as e:
            print(f"清理请求通道共享内存资源失败: {e}")
    
    if resp_ipc and hasattr(resp_ipc, 'shm'):
        try:
            resp_ipc.close()
            # 只在前端进程中unlink共享内存
            resp_ipc.unlink()
            print("响应通道共享内存资源已清理")
        except Exception as e:
            print(f"清理响应通道共享内存资源失败: {e}")

if __name__ == "__main__":
    # 添加freeze_support()解决多进程问题
    multiprocessing.freeze_support()
    
    # 初始化IPC
    init_ipc()
    
    # 使用多进程启动后端
    backend_process = multiprocessing.Process(target=start_backend_process)
    backend_process.daemon = True  # 设置为守护进程，这样当主进程结束时，后端进程也会结束
    backend_process.start()
    
    # 启动Gradio界面
    demo.queue(default_concurrency_limit=100, max_size=100).launch(max_threads=100,
                                                                   ssr_mode=False)
    
    # 注册清理函数在程序退出时执行
    import atexit
    atexit.register(cleanup_ipc)