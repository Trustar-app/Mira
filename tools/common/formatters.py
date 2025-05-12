from state import MiraState

def frontend_inputs_to_state(video, audio, text, chat=None):
    """
    将前端输入(video, audio, text, chat)转换为 MiraState
    """
    
    # 解析 chat 历史
    messages = chat if chat else []
    if text:
        messages.append({"role": "user", "content": text})
    if audio:
        messages.append({"role": "user", "content": audio})
    if video:
        messages.append({"role": "user", "content": video})

    # 构造 MiraState
    state = MiraState(
        user_text=text,
        user_audio=audio,
        user_video=video,
        messages=messages
        # 其他字段可按需补充
    )
    return state


def state_to_frontend_outputs(state):
    """
    将任意 State 转换为前端所需的 (chat, markdown, image, gallery, profile, products, ...)
    """
    # 1. 聊天历史
    chat = getattr(state, "messages", None) or []
    # 2. 结构化 markdown
    markdown = None
    image = None
    gallery = []
    profile = ""
    products = []

    # 针对不同 State 类型做分派
    if hasattr(state, "skin_analysis_result"):
        # 肤质检测流程
        skin_result = getattr(state, "skin_analysis_result", None) or {}
        formatted = format_skin_check(skin_result)
        markdown = formatted["markdown"]
        image = formatted["image"]
        gallery = formatted["gallery"]
        chat += formatted["chat"]
        profile = format_profile(getattr(state, "user_profile", {}))
    elif hasattr(state, "recommended_products"):
        # 产品推荐流程
        products = getattr(state, "recommended_products", [])
        markdown = format_product_recommendation(products)
    elif hasattr(state, "recommended_steps"):
        # 化妆/护肤引导流程
        steps = getattr(state, "recommended_steps", [])
        markdown = format_makeup_steps(steps)
    # ...其他流程...

    return chat, markdown, image, gallery, profile, products, None, None, ""