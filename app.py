# app.py
from graphs.mira_graph import mira_graph
from tools.common.formatters import format_messages, dict_to_markdown
from tools.common.utils import video_to_text
import gradio as gr
from langgraph.types import Command
from utils.loggers import MiraLog
import uuid
from state import default_app_state
from frontend.config_tab import render_config_tab
from frontend.profile_tab import render_profile_tab
from frontend.products_tab import render_products_tab, custom_css

def append_assistant_chat(chat, msg):
    if chat and chat[-1].get("type") == "progress":
        chat[-1]["content"] = msg["content"]
        chat[-1]["type"] = msg["type"]
    else:
        chat.append({"role": "assistant", "content": msg["content"], "type": msg["type"]})
    return chat

def process_user_input(video, text, chat, state):
    if text:
        chat.append({"role": "user", "content": text, "type": "final"})
    if video:
        chat.append({"role": "user", "content": gr.Video(video), "type": "final"})
    yield chat, "", state

    if video:
        progress_message = "正在处理视频输入..."
        chat = append_assistant_chat(chat, {"content": progress_message, "type": "progress"})
        yield chat, "", state
        text += "\n<视频中说话内容>\n" + video_to_text(video) + "\n</视频中说话内容>"
    config = {"configurable": state['config']}
    if state.get('resume'):
        inputs = Command(
            resume={
                "text": text,
                "video": video,
            }
        )
        state['resume'] = False
    else:
        inputs = {
            "messages": format_messages(video, text),
            "user_profile": state['profile'],
            "products_directory": state['products'],
        }
    for mode, step in mira_graph.stream(inputs, config, stream_mode=["custom", "updates"]):
        if mode == "updates" and not "__interrupt__" in step:
            continue
        if "__interrupt__" in step:
            content = step.get("__interrupt__")[0].value.get("content")
            chat = append_assistant_chat(chat, {"content": content, "type": "final"})
            state['resume'] = True
            yield chat, "", state
            break
        msg_type = step.get("type")
        content = step.get("content")
        MiraLog("app", f"msg_type: {msg_type}")
        if msg_type == "progress":
            chat = append_assistant_chat(chat, {"content": content, "type": "progress"})
            yield chat, "", state            
        elif msg_type == "final":
            markdown = dict_to_markdown(content['markdown'])
            state['profile'].update(content['profile'])
            state['products']['products'].append(content['product'])
            chat = append_assistant_chat(chat, {"content": content["response"], "type": "final"})
            yield chat, markdown, state
        else:
            yield chat, "", state

def build_demo():
    with gr.Blocks(theme=gr.themes.Soft(), css="""
    .gradio-container {background: #f8f9fa;}
    .title {font-size:2.2em;font-weight:bold;color:#d63384;margin-bottom:0.2em;}
    .subtitle{color:#868e96;}
    #feedback-md {
        height: 400px;
        max-height: 400px;
        min-height: 250px;
        width: 100%;
        overflow: auto;
        background: #fff;
        border: 1px solid #eee;
        border-radius: 8px;
        padding: 12px;
        box-sizing: border-box;
    }
    """ + custom_css) as demo:
        gr.Markdown("<div class='title'>🎀 Mira 智能化妆镜</div><div class='subtitle'>AI赋能你的美丽日常</div>", elem_id="main-title")
        app_state = gr.State(default_app_state())
        with gr.Tab("💬 聊天"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 📥 用户输入区")
                    video_in = gr.Video(sources=["webcam"], include_audio=True, label="录制视频（含音频）")
                    text_in = gr.Textbox(label="文本输入", lines=2, placeholder="请输入你的问题或需求…")
                    submit_btn = gr.Button("提交", elem_id="submit-btn")
                    new_chat_btn = gr.Button("新建对话", elem_id="new-chat-btn")
                with gr.Column(scale=3):
                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.Markdown("#### 🤖 AI对话区")
                            chat_out = gr.Chatbot(label="AI对话", value=[], type="messages")
                        with gr.Column(scale=1):
                            gr.Markdown("#### 🧾 结构化反馈区")
                            markdown_out = gr.Markdown(label="结构化分析结果", elem_id="feedback-md")
                submit_btn.click(
                    process_user_input,
                    inputs=[video_in, text_in, chat_out, app_state],
                    outputs=[chat_out, markdown_out, app_state]
                )
                def new_chat(state):
                    state['config']['thread_id'] = str(uuid.uuid4())
                    state['resume'] = False
                    return [], "", state
                new_chat_btn.click(
                    new_chat,
                    inputs=[app_state],
                    outputs=[chat_out, markdown_out, app_state]
                )
        with gr.Tab("👤 用户档案"):
            render_profile_tab(app_state)
        with gr.Tab("💄 产品卡片集"):
            render_products_tab(app_state)
        with gr.Tab("🎛 配置"):
            render_config_tab(app_state)
    return demo

demo = build_demo()

if __name__ == "__main__":
    demo.launch() 