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
from frontend.products_tab import render_products_tab
from frontend.custom_css import custom_css
from dotenv import load_dotenv
import os

load_dotenv()

def combine_msg(chat, msg):
    # 如果最后一条消息是进度信息，则可以覆盖
    if chat and chat[-1].get("type") == "progress":
        chat[-1]["content"] = msg["content"]
        chat[-1]["type"] = msg["type"]
    else:
        chat.append({"role": "assistant", "content": msg["content"], "type": msg["type"]})
    return chat

def fill_config_with_env(config: dict) -> dict:
    key_env_map = {
        "chat_api_key": "CHAT_API_KEY",
        "tavily_api_key": "TAVILY_API_KEY",
    }
    new_config = config.copy()
    for key, env_name in key_env_map.items():
        if new_config.get(key, "") == "default":
            new_config[key] = os.getenv(env_name, "")
    return new_config

def extract_profile_values(profile):
    return [
        profile.get('name', ''),
        profile.get('gender', ''),
        profile.get('age', ''),
        profile.get('face_features', {}).get('face_shape', ''),
        profile.get('face_features', {}).get('eyes', ''),
        profile.get('face_features', {}).get('nose', ''),
        profile.get('face_features', {}).get('mouth', ''),
        profile.get('face_features', {}).get('eyebrows', ''),
        profile.get('skin_color', ''),
        profile.get('skin_type', ''),
        profile.get('skin_quality', {}).get('spot', 0) or 0,
        profile.get('skin_quality', {}).get('wrinkle', 0) or 0,
        profile.get('skin_quality', {}).get('pore', 0) or 0,
        profile.get('skin_quality', {}).get('redness', 0) or 0,
        profile.get('skin_quality', {}).get('oiliness', 0) or 0,
        profile.get('skin_quality', {}).get('acne', 0) or 0,
        profile.get('skin_quality', {}).get('dark_circle', 0) or 0,
        profile.get('skin_quality', {}).get('eye_bag', 0) or 0,
        profile.get('skin_quality', {}).get('tear_trough', 0) or 0,
        profile.get('skin_quality', {}).get('firmness', 0) or 0,
        profile.get('makeup_skill_level', 0) or 0,
        profile.get('skincare_skill_level', 0) or 0,
        profile.get('user_preferences', ''),
    ]

def extract_products_values(products):
    from frontend.products_tab import render_products_collection
    choices = [(p['name'], i) for i, p in enumerate(products)]
    return [
        render_products_collection(products),
        gr.update(choices=choices, value=None)
    ]

def extract_config_values(config):
    return [
        config.get('chat_api_key', ''),
        config.get('chat_api_base', ''),
        config.get('chat_model_name', ''),
        config.get('chat_style', '温柔治愈') or '温柔治愈',
        config.get('tavily_api_key', ''),
        config.get('use_youcam', False),
        config.get('youcam_api_key', ''),
        config.get('youcam_secret_key', '')
    ]

def process_user_input(video, text, chat, state):
    if text:
        chat.append({"role": "user", "content": text, "type": "final"})
    if video:
        chat.append({"role": "user", "content": gr.Video(video), "type": "final"})
    yield chat, "", state, None, "", *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])

    if video:
        progress_message = "正在处理视频输入..."
        chat = combine_msg(chat, {"content": progress_message, "type": "progress"})
        yield chat, "", state, None, "", *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])
        text += "\n<视频中说话内容>\n" + video_to_text(video) + "\n</视频中说话内容>"
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
    
    config_for_graph = fill_config_with_env(state['config'])
    for mode, step in mira_graph.stream(inputs, {"configurable": config_for_graph}, stream_mode=["custom", "updates"]):
        if mode == "updates" and not "__interrupt__" in step:
            continue
        if "__interrupt__" in step:
            content = step.get("__interrupt__")[0].value.get("content")
            chat = combine_msg(chat, {"content": content, "type": "final"})
            state['resume'] = True
            yield chat, "", state, None, "", *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])
            break
        msg_type = step.get("type")
        content = step.get("content")
        MiraLog("app", f"msg_type: {msg_type}")
        if msg_type == "progress":
            chat = combine_msg(chat, {"content": content, "type": "progress"})
            yield chat, "", state, None, "", *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])
        elif msg_type == "final":
            markdown = dict_to_markdown(content['markdown']) if content.get('markdown') else ""
            state['profile'].update(content['profile']) if content.get('profile') else None
            state['products'].append(content['product']) if content.get('product') else None
            chat = combine_msg(chat, {"content": content["response"], "type": "final"}) if content.get("response") else chat
            yield chat, markdown, state, None, "", *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])
        else:
            yield chat, "", state, None, "", *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])

def build_demo():
    with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
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
                # 下面收集所有 tab 的控件
        with gr.Tab("👤 用户档案"):
            profile_widgets = render_profile_tab(app_state)
        with gr.Tab("💄 产品卡片集"):
            products_widgets = render_products_tab(app_state)
        with gr.Tab("🎛 配置"):
            config_widgets = render_config_tab(app_state)
        # 主回调 outputs 绑定所有控件
        submit_btn.click(
            process_user_input,
            inputs=[video_in, text_in, chat_out, app_state],
            outputs=[chat_out, markdown_out, app_state, video_in, text_in] + profile_widgets + products_widgets + config_widgets
        )
        def new_chat(state):
            state['config']['thread_id'] = str(uuid.uuid4())
            state['resume'] = False
            return [], "", state, None, "", *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])
        new_chat_btn.click(
            new_chat,
            inputs=[app_state],
            outputs=[chat_out, markdown_out, app_state, video_in, text_in] + profile_widgets + products_widgets + config_widgets
        )
    return demo

demo = build_demo()

if __name__ == "__main__":
    demo.launch() 