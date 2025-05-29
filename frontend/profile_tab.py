import gradio as gr
from state import UserProfile

def render_profile_tab(app_state):
    profile = app_state.value['profile'] if hasattr(app_state, 'value') else app_state['profile']
    with gr.Column():
        with gr.Accordion("📝 个人档案帮助 Mira 更了解你", open=False):
            gr.Markdown("""
            * 可以在聊天时说"帮我建档案"来更新信息，说"帮我检测肤质"来更新肤质评分
            * 也可以在这里直接调整
                        
            💡 修改后记得点击"保存"并重新开始对话哦~
            """, elem_classes="compact-markdown")
        # 基本信息
        gr.Markdown("### 👤 基本信息")
        with gr.Row():
            name = gr.Textbox(label="姓名", value=profile.get('name', ''))
            gender = gr.Textbox(label="性别", value=profile.get('gender', ''))
            age = gr.Textbox(label="年龄", value=profile.get('age', ''))
        # 面部与肤质特征
        gr.Markdown("### 💆 面部与肤质特征")
        gr.Markdown("#### 面部特征")
        with gr.Row():
            face_shape = gr.Textbox(label="脸型", value=profile.get('face_features', {}).get('face_shape', ''))
            eyes = gr.Textbox(label="眼睛", value=profile.get('face_features', {}).get('eyes', ''))
            nose = gr.Textbox(label="鼻子", value=profile.get('face_features', {}).get('nose', ''))
            mouth = gr.Textbox(label="嘴巴", value=profile.get('face_features', {}).get('mouth', ''))
            eyebrows = gr.Textbox(label="眉毛", value=profile.get('face_features', {}).get('eyebrows', ''))

        gr.Markdown("#### 肤质特征")
        with gr.Row():
            skin_color = gr.Textbox(label="肤色", value=profile.get('skin_color', ''))
            skin_type = gr.Textbox(label="肤质类型 (油性/干性/中性/混合性)", value=profile.get('skin_type', ''))
            
        gr.Markdown("#### 肤质评分")
        with gr.Row():
            with gr.Column():
                spot = gr.Slider(label="斑点 (spot)", minimum=0, maximum=10, step=1, value=profile.get('skin_quality', {}).get('spot', 0) or 0)
                wrinkle = gr.Slider(label="皱纹 (wrinkle)", minimum=0, maximum=10, step=1, value=profile.get('skin_quality', {}).get('wrinkle', 0) or 0)
                pore = gr.Slider(label="毛孔 (pore)", minimum=0, maximum=10, step=1, value=profile.get('skin_quality', {}).get('pore', 0) or 0)
                redness = gr.Slider(label="发红 (redness)", minimum=0, maximum=10, step=1, value=profile.get('skin_quality', {}).get('redness', 0) or 0)
                oiliness = gr.Slider(label="出油 (oiliness)", minimum=0, maximum=10, step=1, value=profile.get('skin_quality', {}).get('oiliness', 0) or 0)
            with gr.Column():
                acne = gr.Slider(label="痘痘 (acne)", minimum=0, maximum=10, step=1, value=profile.get('skin_quality', {}).get('acne', 0) or 0)
                dark_circle = gr.Slider(label="黑眼圈 (dark_circle)", minimum=0, maximum=10, step=1, value=profile.get('skin_quality', {}).get('dark_circle', 0) or 0)
                eye_bag = gr.Slider(label="眼袋 (eye_bag)", minimum=0, maximum=10, step=1, value=profile.get('skin_quality', {}).get('eye_bag', 0) or 0)
                tear_trough = gr.Slider(label="泪沟 (tear_trough)", minimum=0, maximum=10, step=1, value=profile.get('skin_quality', {}).get('tear_trough', 0) or 0)
                firmness = gr.Slider(label="皮肤紧致度 (firmness)", minimum=0, maximum=10, step=1, value=profile.get('skin_quality', {}).get('firmness', 0) or 0)
            
        # 能力与偏好
        gr.Markdown("### 💫 能力与偏好")
        with gr.Row():
            makeup_skill_level = gr.Slider(label="化妆能力等级", minimum=0, maximum=10, step=1, value=profile.get('makeup_skill_level', 0) or 0)
            skincare_skill_level = gr.Slider(label="护肤能力等级", minimum=0, maximum=10, step=1, value=profile.get('skincare_skill_level', 0) or 0)
        user_preferences = gr.Textbox(label="个人诉求与偏好", lines=2, value=profile.get('user_preferences', ''))
        save_btn = gr.Button("保存", elem_id="profile-save-btn")

        def save_profile(name, gender, age, face_shape, eyes, nose, mouth, eyebrows, skin_color, skin_type,
                         spot, wrinkle, pore, redness, oiliness, acne, dark_circle, eye_bag, tear_trough, firmness,
                         makeup_skill_level, skincare_skill_level, user_preferences, state):
            state['profile'] = {
                'name': name,
                'gender': gender,
                'age': age,
                'skin_color': skin_color,
                'skin_type': skin_type,
                'face_features': {
                    'face_shape': face_shape,
                    'eyes': eyes,
                    'nose': nose,
                    'mouth': mouth,
                    'eyebrows': eyebrows,
                },
                'skin_quality': {
                    'spot': spot,
                    'wrinkle': wrinkle,
                    'pore': pore,
                    'redness': redness,
                    'oiliness': oiliness,
                    'acne': acne,
                    'dark_circle': dark_circle,
                    'eye_bag': eye_bag,
                    'tear_trough': tear_trough,
                    'firmness': firmness,
                },
                'makeup_skill_level': makeup_skill_level,
                'skincare_skill_level': skincare_skill_level,
                'user_preferences': user_preferences
            }
            return state, gr.Info('个人档案已保存！')

        save_btn.click(
            save_profile,
            inputs=[name, gender, age, face_shape, eyes, nose, mouth, eyebrows, skin_color, skin_type,
                    spot, wrinkle, pore, redness, oiliness, acne, dark_circle, eye_bag, tear_trough, firmness,
                    makeup_skill_level, skincare_skill_level, user_preferences, app_state],
            outputs=[app_state, gr.Markdown(visible=False)]
        )

        # 返回所有控件对象
    return [
        name, gender, age, face_shape, eyes, nose, mouth, eyebrows,
        skin_color, skin_type, spot, wrinkle, pore, redness, oiliness,
        acne, dark_circle, eye_bag, tear_trough, firmness,
        makeup_skill_level, skincare_skill_level, user_preferences
    ]
