import gradio as gr
from http import HTTPStatus
import uuid
from gradio_client import utils as client_utils
import gradio.processing_utils as processing_utils
import base64
from openai import OpenAI
import soundfile as sf
import numpy as np
import io
import os
from dotenv import load_dotenv
import modelscope_studio.components.base as ms
import modelscope_studio.components.antd as antd
import shutil

# 加载环境变量
load_dotenv()

# Voice settings
VOICE_LIST = ['Cherry', 'Ethan', 'Serena', 'Chelsie']
DEFAULT_VOICE = 'Cherry'

# 本地文件存储路径
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

default_system_prompt = 'You are Qwen, a virtual human developed by the Qwen Team, Alibaba Group, capable of perceiving auditory and visual inputs, as well as generating text and speech.'

API_KEY = os.environ['API_KEY']

client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

is_modelscope_studio = os.getenv('MODELSCOPE_ENVIRONMENT') == 'studio'


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

# 这里将历史聊天记录转换为 API 请求消息
def format_history(history: list, system_prompt: str, file_cache):
    messages = []
    # 1. 添加系统prompt
    messages.append({"role": "system", "content": system_prompt})
    # 2. 遍历历史聊天记录
    for item in history:
        # 2.1 处理纯文本的消息
        if isinstance(item["content"], str):
            messages.append({"role": item['role'], "content": item['content']})
        # 2.2 处理多模态的消息
        elif item["role"] == "user" and (isinstance(item["content"], list) or
                                         isinstance(item["content"], tuple)):
            file_path = item["content"][0]

            # 检查缓存中是否已有该文件的本地路径
            local_path = file_cache.get(file_path, save_uploaded_file(file_path))
            file_cache[file_path] = local_path
            print(f"[DEBUG][format_history] local_path: {local_path}")

            mime_type = client_utils.get_mimetype(local_path)
            ext = os.path.splitext(local_path)[1][1:]  # 移除点号
            print(f"[DEBUG][format_history] mime_type: {mime_type}")
            print(f"[DEBUG][format_history] ext: {ext}")

            # 将文件转换为 base64
            with open(local_path, "rb") as f:
                file_data = base64.b64encode(f.read()).decode("utf-8")
                file_url = f"data:{mime_type};base64,{file_data}"
                print(f"[DEBUG][format_history] file_url: {file_url}")

            if mime_type.startswith("image"):
                messages.append({
                    "role": item['role'],
                    "content": [{
                        "type": "image_url",
                        "image_url": {
                            "url": file_url
                        }
                    }]
                })
            elif mime_type.startswith("video"):
                messages.append({
                    "role": item['role'],
                    "content": [{
                        "type": "video_url",
                        "video_url": {
                            "url": file_url
                        }
                    }]
                })
            elif mime_type.startswith("audio"):
                messages.append({
                    "role": item['role'],
                    "content": [{
                        "type": "input_audio",
                        "input_audio": {
                            "data": file_url,
                            "format": ext
                        }
                    }]
                })
    return messages


# 核心处理API响应的函数
def predict(messages, voice=DEFAULT_VOICE):
    try:
        # print('predict history: ', messages)
        # 1. 调用 OpenAI API 生成响应
        completion = client.chat.completions.create(
            model="qwen-omni-turbo",
            messages=messages,
            modalities=["text", "audio"],
            audio={
                "voice": voice,
                "format": "wav"
            },
            stream=True,
            stream_options={"include_usage": True})

        # 2. 处理API响应
        response_text = ""
        audio_str = ""
        for chunk in completion:
            if chunk.choices:
                delta = chunk.choices[0].delta
                if hasattr(
                        delta,
                        'audio') and delta.audio and delta.audio.get("transcript"):
                    response_text += delta.audio.get("transcript")
                if hasattr(delta,
                        'audio') and delta.audio and delta.audio.get("data"):
                    audio_str += delta.audio.get("data")
                yield {"type": "text", "data": response_text}
        
        # 3. 处理音频响应
        pcm_bytes = base64.b64decode(audio_str)
        audio_np = np.frombuffer(pcm_bytes, dtype=np.int16)
        wav_io = io.BytesIO()
        sf.write(wav_io, audio_np, samplerate=24000, format="WAV")
        wav_io.seek(0)
        wav_bytes = wav_io.getvalue()
        audio_path = processing_utils.save_bytes_to_cache(
            wav_bytes, "audio.wav", cache_dir=demo.GRADIO_CACHE)
        
        # 4. 返回音频响应
        yield {"type": "audio", "data": audio_path}

    # 5. 处理异常
    except Exception as e:
        error_message = f"{str(e)}"
        raise gr.Error(error_message, duration=8)



# 封装API请求和处理API响应
def media_predict(audio, video, history, system_prompt, state_value,
                  voice_choice):
    # 1. 处理本次的音频和视频输入
    # TODO 这里实际上是可以支持text输入的，但这里只处理音频和视频
    files = [audio, video]
    for f in files:
        if f:
            history.append({"role": "user", "content": (f, )})

    # 2. 将历史聊天记录转换为 API 请求消息
    formatted_history = format_history(history=history,
                                       system_prompt=system_prompt,
                                       file_cache=state_value["file_cache"])

    # 3. 首次返回
    yield (
        None,  # microphone 麦克风
        None,  # webcam 摄像头
        history,  # media_chatbot 历史聊天记录
        gr.update(visible=False),  # submit_btn 提交按钮
        gr.update(visible=True),  # stop_btn 停止按钮
        state_value  # state 状态
    )
    
    # 4. 预备接受API响应
    history.append({"role": "assistant", "content": ""})

    # 5. 处理API响应
    for chunk in predict(formatted_history, voice_choice):
        if chunk["type"] == "text":
            history[-1]["content"] = chunk["data"]
            yield (
                None,  # microphone
                None,  # webcam
                history,  # media_chatbot
                gr.update(visible=False),  # submit_btn
                gr.update(visible=True),  # stop_btn
                state_value  # state
            )
        if chunk["type"] == "audio":
            history.append({
                "role": "assistant",
                "content": gr.Audio(chunk["data"])
            })

    # 6. 最终返回
    yield (
        None,  # microphone
        None,  # webcam
        history,  # media_chatbot
        gr.update(visible=True),  # submit_btn
        gr.update(visible=False),  # stop_btn
        state_value  # state
    )


def chat_predict(text, audio, image, video, history, system_prompt,
                 state_value, voice_choice):
    # Process text input
    if text:
        history.append({"role": "user", "content": text})

    # Process audio input
    if audio:
        history.append({"role": "user", "content": (audio, )})

    # Process image input
    if image:
        history.append({"role": "user", "content": (image, )})

    # Process video input
    if video:
        history.append({"role": "user", "content": (video, )})

    formatted_history = format_history(history=history,
                                       system_prompt=system_prompt,
                                       file_cache=state_value["file_cache"])

    yield None, None, None, None, history, state_value

    history.append({"role": "assistant", "content": ""})
    for chunk in predict(formatted_history, voice_choice):
        if chunk["type"] == "text":
            history[-1]["content"] = chunk["data"]
            yield gr.skip(), gr.skip(), gr.skip(), gr.skip(
            ), history, state_value
        if chunk["type"] == "audio":
            history.append({
                "role": "assistant",
                "content": gr.Audio(chunk["data"])
            })
    yield gr.skip(), gr.skip(), gr.skip(), gr.skip(), history, state_value


with gr.Blocks() as demo, ms.Application(), antd.ConfigProvider():
    state = gr.State({"file_cache": {}})
    
    # 1. 侧边栏
    with gr.Sidebar(open=False):
        system_prompt_textbox = gr.Textbox(label="System Prompt",
                                           value=default_system_prompt)
        voice_choice = gr.Dropdown(label="Voice Choice",
                                   choices=VOICE_LIST,
                                   value=DEFAULT_VOICE)
    # 2. 头部
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
    # 3. TabView
    with gr.Tabs():
        # 3.1 在线模式
        with gr.Tab("Online"):
            with gr.Row():
                with gr.Column(scale=1):
                    """ 
                     五个组件 一个音频输入，一个摄像头，
                     一个提交按钮，一个停止按钮，一个清除历史按钮
                    """
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

demo.queue(default_concurrency_limit=100, max_size=100).launch(max_threads=100,
                                                               ssr_mode=False)
