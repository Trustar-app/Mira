# app.py
from datetime import datetime
from graphs.mira_graph import mira_graph
from tools.common.formatters import format_messages, dict_to_markdown
from tools.common.utils import video_to_text, fill_config_with_env
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
from config import MIRA_GREETING_PROMPT
from utils.tts import text_to_speech, init_audio_cache

load_dotenv()

def get_current_time_and_season():
    now = datetime.now()
    
    season_map = {
        (12, 1, 2): "冬季",
        (3, 4, 5): "春季",
        (6, 7, 8): "夏季",
        (9, 10, 11): "秋季"
    }
    
    current_season = next(season for months, season in season_map.items() if now.month in months)
    current_time = now.strftime("%H:%M")
    
    return current_time, current_season

def generate_greeting_prompt(app_state):
    # current_time, season = get_current_time_and_season()
    user_profile = app_state['profile']
    products_directory = app_state['products']
    greeting_prompt = MIRA_GREETING_PROMPT.format(
        # current_time=current_time,
        # season=season,
        user_profile=user_profile,
        products_directory=products_directory
    )
    return greeting_prompt

def combine_msg(chat, msg):
    # 如果最后一条消息是进度信息，则可以覆盖
    if chat and chat[-1].get("type") == "progress":
        chat[-1]["content"] = msg["content"]
        chat[-1]["type"] = msg["type"]
    else:
        chat.append({"role": "assistant", "content": msg["content"], "type": msg["type"]})
    return chat

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
    choices = [(p['product_name'], i) for i, p in enumerate(products)]
    return [
        render_products_collection(products),
        gr.update(choices=choices, value=None)
    ]

def extract_config_values(config):
    return [
        config.get('chat_api_key', ''),
        config.get('chat_api_base', ''),
        config.get('chat_model_name', ''),
        config.get('audio_model_name', ''),
        config.get('character_setting', {}).get('name', ''),
        config.get('character_setting', {}).get('personality', ''),
        config.get('character_setting', {}).get('background', ''),
        config.get('character_setting', {}).get('tone', ''),
        config.get('character_setting', {}).get('expertise', ''),
        config.get('character_setting', {}).get('interaction_style', ''),
        config.get('tavily_api_key', ''),
        config.get('use_youcam', False),
        config.get('youcam_api_key', ''),
        config.get('youcam_secret_key', '')
    ]

def process_user_input(video, text, chat, markdown, state):
    if text:
        chat.append({"role": "user", "content": text, "type": "final"})
    if video:
        chat.append({"role": "user", "content": gr.Video(video), "type": "final"})
    yield chat, "", state, None, "", None, *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])

    if video:
        progress_message = "正在处理视频输入..."
        chat = combine_msg(chat, {"content": progress_message, "type": "progress"})
        yield chat, "", state, None, "", None, *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])
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
            yield chat, markdown, state, None, "", None, *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])
            break
        msg_type = step.get("type")
        content = step.get("content")
        MiraLog("app", f"msg_type: {msg_type}")
        if msg_type == "progress":
            chat = combine_msg(chat, {"content": content, "type": "progress"})
            yield chat, markdown, state, None, "", None, *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])

        elif msg_type == "final":
            markdown = dict_to_markdown(content['markdown']) if content.get('markdown') else markdown
            state['profile'].update(content['profile']) if content.get('profile') else None
            state['products'].append(content['product']) if content.get('product') else None
            response = content.get("response", "")
            chat = combine_msg(chat, {"content": response, "type": "final"}) if response else chat
            
            # 对 final 消息进行 TTS 处理
            audio_path = None
            if response:
                audio_path = text_to_speech(
                    response,
                    voice=config_for_graph['audio_model_name'],
                    save_dir="audio_cache",
                    api_key=config_for_graph['chat_api_key']
                )
            
            yield chat, markdown, state, None, "", audio_path, *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])

        else:
            yield chat, markdown, state, None, "", None, *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])

def new_chat(state):
    state['config']['thread_id'] = str(uuid.uuid4())
    state['resume'] = False
    greeting_prompt = generate_greeting_prompt(state)
    state['config']['greeting_prompt'] = greeting_prompt
    greeting_response = mira_graph.invoke({"messages": format_messages(None, greeting_prompt)}, {"configurable": fill_config_with_env(state['config'])}, stream_mode=["custom"])
    chat = []
    response = ""
    first_chunk = True  
    for mode, chunk in greeting_response:
        if mode == "custom" and chunk['type'] == "progress":
            if first_chunk:
                first_chunk = False
                continue
            else:
                response = chunk['content']
            yield combine_msg(chat, {"content": response, "type": "progress"}), "", state, None, "", None, *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])
        elif mode == "custom" and chunk['type'] == "final":
            response = chunk['content']['response']
            chat = combine_msg(chat, {"content": response, "type": "final"})
            # 对欢迎语进行 TTS 处理
            audio_path = text_to_speech(
                response,
                voice=fill_config_with_env(state['config'])['audio_model_name'],
                save_dir="audio_cache",
                api_key=fill_config_with_env(state['config'])['chat_api_key']
            ) if response else None
            yield chat, "", state, None, "", audio_path, *extract_profile_values(state['profile']), *extract_products_values(state['products']), *extract_config_values(state['config'])

def build_demo():
    with gr.Blocks(theme=gr.themes.Soft(), css=custom_css) as demo:
        gr.Markdown("<div class='title'>🎀 Mira 智能化妆镜</div><div class='subtitle'>AI赋能你的美丽日常</div>", elem_id="main-title")
        with gr.Accordion("👋 欢迎来到 Mira！我是一面智能镜子，也是你的私人美妆助理和美丽顾问。", open=False):
            gr.Markdown("""
            我可以：
            * 📝 **个人档案** - "我想创建我的档案" 或 "更新我的档案"
            * 💄 **肤质检测** - "帮我检测下皮肤状况" 或 "我的皮肤有什么问题"
            * 🔍 **产品分析** - "欧莱雅男士淡纹霜怎么样" 或 "推荐适合我的粉底液"
            * 👩‍🏫 **美妆指导** - "教我画一个约会妆" 或 "教我护肤"
            
            这个demo旨在模拟你与智能镜子的互动体验~
            """, elem_classes="compact-markdown")
        app_state = gr.State(default_app_state())
        with gr.Tab("💬 聊天"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 📥 用户输入区")
                    with gr.Accordion("💡 与 Mira 对话就像和朋友视频聊天一样：", open=False):
                        gr.Markdown("""
                        * 可以通过视频录制来展示和询问
                        * 也可以直接输入文字交流
                        """, elem_classes="compact-markdown")
                    gr.Markdown("⚠️ **注意**：视频对话需要较强的 CPU 处理能力，响应时间较长，建议优先使用文字对话。", elem_classes="compact-markdown")
                    video_in = gr.Video(sources=["webcam"], include_audio=True, label="视频对话（含音频）")
                    text_in = gr.Textbox(label="文字对话", lines=2, placeholder="请输入你的问题或需求…")
                    submit_btn = gr.Button("提交", elem_id="submit-btn")
                    new_chat_btn = gr.Button("新建对话", elem_id="new-chat-btn")
                with gr.Column(scale=2):
                    gr.Markdown("#### 🤖 AI对话区")
                    with gr.Accordion("💡 这里会显示 Mira 的回应，就像你在镜子前听到的对话一样：", open=False):
                        gr.Markdown("""
                        Mira 会：
                        * 🎯 理解你的需求
                        * 💝 给出个性化建议
                        * 📝 记录重要信息
                        """, elem_classes="compact-markdown")
                    greeting_prompt = generate_greeting_prompt(app_state.value)
                    app_state.value['config']['greeting_prompt'] = greeting_prompt
                    greeting_response = mira_graph.invoke({"messages": format_messages(None, greeting_prompt)}, {"configurable": fill_config_with_env(app_state.value['config'])}, stream_mode=["custom"])
                    print("重新生成欢迎语")
                    response = ""
                    for mode, chunk in greeting_response:
                        if mode == "custom" and chunk['type'] == "final":
                            response = chunk['content']['response']
                    audio_path = text_to_speech(response, voice=fill_config_with_env(app_state.value['config'])['audio_model_name'], save_dir="audio_cache", api_key=fill_config_with_env(app_state.value['config'])['chat_api_key'])
                    chat_out = gr.Chatbot(label="AI对话", value=[{"role": "assistant", "content": response, "type": "final"}], elem_id="chat-out", type="messages")
                    audio_out = gr.Audio(label="AI语音", elem_id="audio-out", value=audio_path, autoplay=True)
                with gr.Column(scale=1):
                    gr.Markdown("#### 🔍 分析结果")
                    with gr.Accordion("💡 这里会显示更详细的分析结果：", open=False):
                        gr.Markdown("""
                        * 🔬 皮肤检测结果
                        * 🔎 产品分析结果
                        * 💄 化妆或护肤指导计划
                        """, elem_classes="compact-markdown")
                    markdown_out = gr.Markdown(label="分析结果", elem_id="feedback-md")
                    clear_btn = gr.Button("清空", elem_id="clear-btn")
        with gr.Tab("👤 个人档案"):
            profile_widgets = render_profile_tab(app_state)
        with gr.Tab("💄 产品卡片集"):
            products_widgets = render_products_tab(app_state)
        with gr.Tab("🎛 配置"):
            config_widgets = render_config_tab(app_state)


        submit_btn.click(
            process_user_input,
            inputs=[video_in, text_in, chat_out, markdown_out, app_state],
            outputs=[chat_out, markdown_out, app_state, video_in, text_in, audio_out] + profile_widgets + products_widgets + config_widgets
        )

        new_chat_btn.click(
            new_chat,
            inputs=[app_state],
            outputs=[chat_out, markdown_out, app_state, video_in, text_in, audio_out] + profile_widgets + products_widgets + config_widgets
        )

        clear_btn.click(
            lambda markdown: "",
            inputs=[markdown_out],
            outputs=[markdown_out]
        )
    return demo

demo = build_demo()
# 初始化音频缓存
init_audio_cache()
demo.queue()
demo.launch(show_error=True, max_threads=10)