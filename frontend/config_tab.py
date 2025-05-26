import gradio as gr

def render_config_tab(app_state):
    config = app_state.value['config'] if hasattr(app_state, 'value') else app_state['config']
    with gr.Column():
        # 模型设置
        gr.Markdown("### 🤖 模型设置")
        gr.Markdown("<a href='https://bailian.console.aliyun.com/' target='_blank'>阿里百炼</a> 获取 API Key、Base URL、模型名称。")
        with gr.Row():
            chat_api_key = gr.Textbox(label="聊天模型的 API Key", type="password", value=config.get('chat_api_key', ''))
            chat_api_base = gr.Textbox(label="聊天模型的 Base URL", value=config.get('chat_api_base', ''))
        with gr.Row():
            chat_model_name = gr.Textbox(label="聊天模型的模型名称", value=config.get('chat_model_name', ''))
            chat_style = gr.Dropdown(
                label="聊天风格",
                choices=["诚实朋友", "温柔治愈", "毒舌幽默"],
                value=config.get('chat_style', '温柔治愈') or "温柔治愈"
            )
        # 工具设置
        gr.Markdown("### 🛠️ 工具设置")
        # Tavily 搜索工具
        gr.Markdown("Tavily搜索工具（<a href='https://app.tavily.com/home' target='_blank'>Tavily官网</a> 获取 API Key）")
        tavily_api_key = gr.Textbox(label="Tavily API Key", type="password", value=config.get('tavily_api_key', ''))
        # YouCam 工具
        gr.Markdown("YouCam 肤质分析工具（<a href='https://yce.perfectcorp.com/account/apikey' target='_blank'>YouCam官网</a> 获取 API Key 和 Secret Key）")
        with gr.Row():
            use_youcam = gr.Checkbox(label="使用 YouCam 做肤质分析（否则直接用大模型分析）", value=config.get('use_youcam', False))
            youcam_api_key = gr.Textbox(label="YouCam API Key", type="password", value=config.get('youcam_api_key', ''))
            youcam_secret_key = gr.Textbox(label="YouCam Secret Key", type="password", value=config.get('youcam_secret_key', ''))

        save_btn = gr.Button("保存", elem_id="config-save-btn")

        def save_config(chat_api_key, chat_api_base, chat_model_name, chat_style, tavily_api_key, use_youcam, youcam_api_key, youcam_secret_key, state):
            state['config']['chat_api_key'] = chat_api_key
            state['config']['chat_api_base'] = chat_api_base
            state['config']['chat_model_name'] = chat_model_name
            state['config']['chat_style'] = chat_style
            state['config']['tavily_api_key'] = tavily_api_key
            state['config']['use_youcam'] = use_youcam
            state['config']['youcam_api_key'] = youcam_api_key
            state['config']['youcam_secret_key'] = youcam_secret_key
            return state

        save_btn.click(
            save_config,
            inputs=[chat_api_key, chat_api_base, chat_model_name, chat_style, tavily_api_key, use_youcam, youcam_api_key, youcam_secret_key, app_state],
            outputs=[app_state]
        )


        
