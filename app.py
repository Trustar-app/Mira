# app.py
from graphs.mira_graph import mira_graph
from tools.common.formatters import (
    frontend_inputs_to_state, state_to_frontend_outputs
)
import gradio as gr
import logging
import os

# 日志目录
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    filename="logs/face_detect.log",
    filemode="a",
    encoding="utf-8"
)
# 控制台同步输出
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)


def process_user_input(video, audio, text, chat=None):
    markdown = ""
    image = None
    gallery = []
    profile = ""
    products = []

    if chat is None:
        chat = []
    if text:
        chat.append({"role": "user", "content": text})
    if audio:
        chat.append({"role": "user", "content": gr.Audio(audio)})
    if video:
        chat.append({"role": "user", "content": gr.Video(video)})
    yield chat, markdown, image, gallery, profile, products, None, None, ""
    
    for step in mira_graph(frontend_inputs_to_state(video, audio, text, chat)):
        # 基于不同结果，分别处理 chat、markdown、image、gallery、profile、products 信息,并yield，有的是中间的进度信息，有的是结果
        yield state_to_frontend_outputs(step)
        
                

def build_demo():
    with gr.Blocks(theme=gr.themes.Soft(), css=".gradio-container {background: #f8f9fa;} .title {font-size:2.2em;font-weight:bold;color:#d63384;margin-bottom:0.2em;} .subtitle{color:#868e96;}") as demo:
        gr.Markdown("<div class='title'>🎀 Mira 智能化妆镜</div><div class='subtitle'>AI赋能你的美丽日常</div>", elem_id="main-title")
        with gr.Row():
            # 第一行：左-输入区，右-反馈区
            with gr.Column(scale=1):
                gr.Markdown("#### 📥 用户输入区")
                video_in = gr.Video(sources=["webcam"], include_audio=True, label="录制视频（含音频）")
                audio_in = gr.Audio(sources=["microphone"], label="语音输入")
                text_in = gr.Textbox(label="文本输入", lines=2, placeholder="请输入你的问题或需求…")
                submit_btn = gr.Button("提交", elem_id="submit-btn")
            with gr.Column(scale=2):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 🤖 AI对话区")
                        chat_out = gr.Chatbot(label="AI对话", value=[], type="messages")
                    with gr.Column():
                        gr.Markdown("#### 🧾 结构化反馈区")
                        markdown_out = gr.Markdown(label="结构化分析结果")
                        image_out = gr.Image(label="分析图片")
                        gallery_out = gr.Gallery(label="反馈图片集", columns=4)
        with gr.Row():
            # 第二行：左-用户档案，右-产品卡片集
            with gr.Column():
                gr.Markdown("#### 📦 用户档案")
                profile_out = gr.Markdown("")
            with gr.Column():
                gr.Markdown("#### 💄 产品卡片集")
                products_out = gr.Gallery(label="产品卡片集", value=[], columns=2, height=220)
        # 事件绑定
        submit_btn.click(
            process_user_input,
            inputs=[video_in, audio_in, text_in, chat_out],
            outputs=[chat_out, markdown_out, image_out, gallery_out, profile_out, products_out, video_in, audio_in, text_in]
        )
    return demo

demo = build_demo()

if __name__ == "__main__":
    demo.launch() 