import gradio as gr
from tools.character_generation_tools import generate_character_setting

def render_config_tab(app_state):
    config = app_state.value['config'] if hasattr(app_state, 'value') else app_state['config']
    with gr.Column():
        with gr.Accordion("⚙️ 这里可以自定义 Mira 的设置：", open=False):
            gr.Markdown("""
            * 如果 API 异常可以更换密钥
            * 可以调整 Mira 的性格和说话风格
            * 开启或关闭额外的分析功能
                        
            💡 修改后记得点击"保存"并重新开始对话哦~
            """, elem_classes="compact-markdown")
        
        # 模型设置
        gr.Markdown("### 🤖 模型设置")
        gr.Markdown("[如果默认 API 失效，请前往<a href='https://bailian.console.aliyun.com/' target='_blank'>阿里百炼</a> 获取新 API Key，API不会上传]", elem_classes="compact-markdown")
        with gr.Row():
            chat_api_key = gr.Textbox(label="聊天模型的 API Key",value=config.get('chat_api_key', ''))
            chat_api_base = gr.Textbox(label="聊天模型的 Base URL", value=config.get('chat_api_base', ''))
        with gr.Row():
            chat_model_name = gr.Textbox(label="聊天模型的模型名称", value=config.get('chat_model_name', ''))
            voice_model_name = gr.Dropdown(
                label="语音模型的音色名称",
                choices=["longwan", "longcheng", "longhua", "longxiaochun"],
                value=config.get('voice_model_name', 'longwan'),
                info="CosyVoice 模型支持的音色选项"
            )
        
        # 角色设定
        gr.Markdown("### 👤 角色设定")
        with gr.Row():
            chat_style = gr.Textbox(label="聊天风格描述", value="", lines=1)
            with gr.Column():
                generate_btn = gr.Button("生成角色", variant="primary")
                gr.Markdown("""
                ✨ 描述你期望的聊天风格，点击生成角色即可
                * 建议生成后重新开始对话
                """, elem_classes="compact-markdown")
        with gr.Row():
            character_name = gr.Textbox(
                label="角色名称",
                value=config.get('character_setting', {}).get('name', 'Mira'),
                interactive=True
            )
            character_personality = gr.Textbox(
                label="性格特点",
                value=config.get('character_setting', {}).get('personality', ''),
                lines=2
            )
        with gr.Row():
            character_background = gr.Textbox(
                label="背景故事",
                value=config.get('character_setting', {}).get('background', ''),
                lines=3
            )
            character_tone = gr.Textbox(
                label="语气特点",
                value=config.get('character_setting', {}).get('tone', ''),
                lines=2
            )
        with gr.Row():
            character_expertise = gr.Textbox(
                label="专业领域",
                value=config.get('character_setting', {}).get('expertise', ''),
                lines=2
            )
            character_interaction = gr.Textbox(
                label="互动风格",
                value=config.get('character_setting', {}).get('interaction_style', ''),
                lines=2
            )

        # 工具设置
        gr.Markdown("### 🛠️ 工具设置")
        # Tavily 搜索工具
        gr.Markdown("Tavily搜索工具（如果默认 API 失效，请前往<a href='https://app.tavily.com/' target='_blank'>Tavily官网</a> 获取新 API Key，API 不会上传）")
        tavily_api_key = gr.Textbox(label="Tavily API Key", value=config.get('tavily_api_key', ''))
        # YouCam 工具
        gr.Markdown("YouCam 肤质分析工具（<a href='https://yce.perfectcorp.com/account/apikey' target='_blank'>YouCam官网</a> 获取 API Key 和 Secret Key）")
        with gr.Row():
            use_youcam = gr.Checkbox(label="使用 YouCam 做肤质分析（否则直接用大模型分析）", value=config.get('use_youcam', False))
            youcam_api_key = gr.Textbox(label="YouCam API Key", value=config.get('youcam_api_key', ''))
            youcam_secret_key = gr.Textbox(label="YouCam Secret Key", value=config.get('youcam_secret_key', ''))

        save_btn = gr.Button("保存", elem_id="config-save-btn")

        def generate_character(chat_style, state):
            model_config = {
                "chat_api_key": state['config']['chat_api_key'],
                "chat_api_base": state['config']['chat_api_base'],
                "chat_model_name": state['config']['chat_model_name']
            }
            character = generate_character_setting(chat_style, model_config)
            
            # 自动保存角色设定
            state['config']['character_setting'] = character
            
            return (
                character.get('name', ''),
                character.get('personality', ''),
                character.get('background', ''),
                character.get('tone', ''),
                character.get('expertise', ''),
                character.get('interaction_style', ''),
                state,
                ''
            )

        def save_config(chat_api_key, chat_api_base, chat_model_name, chat_style, 
                       character_name, character_personality, character_background,
                       character_tone, character_expertise, character_interaction,
                       tavily_api_key, use_youcam, youcam_api_key, youcam_secret_key, state):
            state['config']['chat_api_key'] = chat_api_key
            state['config']['chat_api_base'] = chat_api_base
            state['config']['chat_model_name'] = chat_model_name
            state['config']['chat_style'] = chat_style
            state['config']['character_setting'] = {
                'name': character_name,
                'personality': character_personality,
                'background': character_background,
                'tone': character_tone,
                'expertise': character_expertise,
                'interaction_style': character_interaction
            }
            state['config']['tavily_api_key'] = tavily_api_key
            state['config']['use_youcam'] = use_youcam
            state['config']['youcam_api_key'] = youcam_api_key
            state['config']['youcam_secret_key'] = youcam_secret_key
            return state, gr.Info('配置已保存！')

        # 生成角色设定按钮事件
        generate_btn.click(
            generate_character,
            inputs=[chat_style, app_state],
            outputs=[character_name, character_personality, character_background,
                    character_tone, character_expertise, character_interaction,
                    app_state, chat_style]
        )

        # 保存配置按钮事件
        save_btn.click(
            save_config,
            inputs=[
                chat_api_key, chat_api_base, chat_model_name, voice_model_name,
                character_name, character_personality, character_background,
                character_tone, character_expertise, character_interaction,
                tavily_api_key, use_youcam, youcam_api_key, youcam_secret_key,
                app_state
            ],
            outputs=[app_state, gr.Markdown(visible=False)]
        )

    # 返回所有配置控件对象
    return [
        chat_api_key, chat_api_base, chat_model_name, voice_model_name,
        character_name, character_personality, character_background,
        character_tone, character_expertise, character_interaction,
        tavily_api_key, use_youcam, youcam_api_key, youcam_secret_key
    ]


        
