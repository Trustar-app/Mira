# app.py
from graphs.mira_graph import mira_graph
from tools.common.formatters import (
    format_messages, structure_to_frontend_outputs
)
from tools.common.utils import audio_to_text, video_to_text
import gradio as gr
from langgraph.types import Command
from utils.loggers import MiraLog
import uuid

def process_user_input(video, audio, text, chat=None, thread_id=None, resume=None):
    """
    支持多轮对话记忆，thread_id用于区分不同会话。
    兼容mira_graph.stream自定义输出结构{"type": , "content": ...}
    """
    markdown = ""
    image = None
    gallery = []
    profile = ""
    products = []

    if chat is None:
        chat = []
    # 用户输入加入chat
    if text:
        chat.append({"role": "user", "content": text})
    if audio:
        chat.append({"role": "user", "content": gr.Audio(audio)})
    if video:
        chat.append({"role": "user", "content": gr.Video(video)})
    yield chat, markdown, image, gallery, profile, products, None, None, "", thread_id, resume

    # 多模态信息处理
    multimodal_text = ""
    if text:
        multimodal_text += text
    if audio:
        progress_message = "正在处理语音输入..."
        if chat and chat[-1].get("role") == "assistant":
            chat[-1]["content"] = progress_message
        else:
            chat.append({"role": "assistant", "content": progress_message})
        yield chat, markdown, image, gallery, profile, products, progress_message, None, "", thread_id, resume
        multimodal_text += audio_to_text(audio)
    if video:
        progress_message = "正在处理视频输入..."
        if chat and chat[-1].get("role") == "assistant":
            chat[-1]["content"] = progress_message
        else:
            chat.append({"role": "assistant", "content": progress_message})
        yield chat, markdown, image, gallery, profile, products, progress_message, None, "", thread_id, resume
        multimodal_text += video_to_text(video)
    
    config = {"configurable": {"thread_id": thread_id}}
    if resume:
        inputs = Command(resume={
            "text": text,
            "audio": audio,
            "video": video,
            "multimodal_text": multimodal_text,
            "messages": format_messages(video, audio, text, multimodal_text)
        })
    else:
        inputs = {
            "current_text": text,
            "current_audio": audio,
            "current_video": video,
            "multimodal_text": multimodal_text,
            "messages": format_messages(video, audio, text, multimodal_text)
        }
    for step in mira_graph.stream(inputs, config, stream_mode="custom"):
        # 兼容自定义输出结构
        msg_type = step.get("type")
        content = step.get("content")
        MiraLog("app", f"msg_type: {msg_type}")
        
        if msg_type == "progress":
            # 进度信息，chat区只保留一条最新assistant进度
            if chat and chat[-1].get("role") == "assistant":
                chat[-1]["content"] = content
            else:
                chat.append({"role": "assistant", "content": content})
            markdown, image, gallery, profile, products = "", None, [], "", []
            yield chat, markdown, image, gallery, profile, products, None, None, "", thread_id, None
        elif msg_type == "interrupt":
            # 中断信息，chat区只保留一条最新assistant进度
            if chat and chat[-1].get("role") == "assistant":
                chat[-1]["content"] = content
            else:
                chat.append({"role": "assistant", "content": content})
            yield chat, markdown, image, gallery, profile, products, None, None, "", thread_id, "interrupt"
        elif msg_type == "chat":
            # 流式chat输出，上一条是assistant则替换，否则append
            if chat and chat[-1].get("role") == "assistant":
                chat[-1]["content"] = content
            else:
                chat.append({"role": "assistant", "content": content})
            markdown, image, gallery, profile, products = "", None, [], "", []
            yield chat, markdown, image, gallery, profile, products, None, None, "", thread_id, None
        elif msg_type == "structure":
            chat, markdown, image, gallery, profile, products, a, b, c = structure_to_frontend_outputs(content)
            MiraLog("app", f"chat: {chat}")
            MiraLog("app", f"markdown: {markdown}")
            MiraLog("app", f"image: {image}")
            MiraLog("app", f"gallery: {gallery}")
            MiraLog("app", f"profile: {profile}")
            MiraLog("app", f"products: {products}")
            yield chat, markdown, image, gallery, profile, products, None, None, "", thread_id, None
        else:
            yield chat, markdown, image, gallery, profile, products, None, None, "", thread_id, None

def build_demo():
    with gr.Blocks(theme=gr.themes.Soft(), css=".gradio-container {background: #f8f9fa;} .title {font-size:2.2em;font-weight:bold;color:#d63384;margin-bottom:0.2em;} .subtitle{color:#868e96;}") as demo:
        gr.Markdown("<div class='title'>🎀 Mira 智能化妆镜</div><div class='subtitle'>AI赋能你的美丽日常</div>", elem_id="main-title")
        thread_id_state = gr.State(str(uuid.uuid4()))  # 用于存储当前对话的thread_id
        resume_state = gr.State(None)  # 用于存储中断信息
        with gr.Row():
            # 第一行：左-输入区，右-反馈区
            with gr.Column(scale=1):
                gr.Markdown("#### 📥 用户输入区")
                video_in = gr.Video(sources=["webcam"], include_audio=True, label="录制视频（含音频）")
                audio_in = gr.Audio(sources=["microphone"], label="语音输入")
                text_in = gr.Textbox(label="文本输入", lines=2, placeholder="请输入你的问题或需求…")
                submit_btn = gr.Button("提交", elem_id="submit-btn")
                new_chat_btn = gr.Button("新建对话", elem_id="new-chat-btn")
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
            inputs=[video_in, audio_in, text_in, chat_out, thread_id_state, resume_state],
            outputs=[chat_out, markdown_out, image_out, gallery_out, profile_out, products_out, video_in, audio_in, text_in, thread_id_state, resume_state]
        )
        # 新建对话按钮：重置所有输入输出，并生成新thread_id
        def new_chat():
            return [], "", None, [], "", [], None, None, "", str(uuid.uuid4()), None
        new_chat_btn.click(
            new_chat,
            inputs=[],
            outputs=[chat_out, markdown_out, image_out, gallery_out, profile_out, products_out, video_in, audio_in, text_in, thread_id_state, resume_state]
        )
    return demo

demo = build_demo()

if __name__ == "__main__":
    demo.launch() 