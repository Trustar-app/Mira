from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# 意图类别列表
INTENT_CATEGORIES = [
    "聊天互动",
    "肤质检测",
    "创建用户档案",
    "产品分析",
    "化妆或护肤引导"
]

def generate_system_prompt(character_setting: dict) -> str:
    """
    根据角色设定生成系统提示词
    """
    return f"""你是 {character_setting['name']}，一个专业的美妆顾问和心理陪伴师。

性格特点：{character_setting['personality']}

背景故事：{character_setting['background']}

语气特点：{character_setting['tone']}

专业领域：{character_setting['expertise']}

互动风格：{character_setting['interaction_style']}

你的主要任务是：
1. 根据用户的需求提供专业的美妆和护肤建议
2. 进行肤质分析和产品推荐
3. 提供情感支持和心理陪伴
4. 帮助用户建立和维护个人美妆档案

回复要求：
1. 所有回复必须简短、口语化，适合语音播报
2. 不要使用分点列举的形式回答
3. 不要在回复中包含图片URL或其他非自然语言的内容
4. 每次回复控制在100字以内
5. 使用自然的语气助词和语气词，让对话更生动

请始终保持你的角色特点，用温暖专业的方式与用户互动。"""

# 1. 多模态聊天 Agent
# 输入: OpenAI 格式 messages（支持文本和视频）
def multimodal_chat_agent(messages, config, streaming=False):
    """
    多模态聊天 Agent，输入为（含文本、音频、视频），输出为回复文本。
    若streaming=True，则返回生成器，每次yield一个chunk，便于流式对接前端。
    """
    # 获取角色设定
    character_setting = config.get("character_setting", {})
    # 如果是第一次对话，添加系统提示词
    system_prompt = SystemMessage(content=generate_system_prompt(character_setting))
    llm = ChatOpenAI(
        openai_api_key=config.get("chat_api_key"),
        openai_api_base=config.get("chat_api_base"),
        model=config.get("chat_model_name"),
        streaming=streaming
    )
    messages = [system_prompt] + messages
    if streaming:
        # 返回生成器，流式输出
        def stream_gen():
            for chunk in llm.stream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
        return stream_gen()
    else:
        result = llm.invoke(messages)
        return result.content.strip()

# 2. 意图识别
# 输入: 用户文本，输出: 意图类别
# 使用 Qwen2.5-14B-Instruct
def recognize_intent(content: list, config) -> str:
    """
    用 LLM 对文本进行意图识别，返回意图类别
    """
    text = [item["text"] for item in content if item  == "text"]
    prompt = f"""
你是一个智能助手，请判断用户输入的意图属于下列哪一类，只需返回类别本身，不要返回其他内容：
{INTENT_CATEGORIES}
要求：
- 只有当用户输入内容非常明确、直接地表达了某个具体意图（如“请帮我做肤质检测”、“我要创建个人档案”、“帮我分析这个产品”等），才返回该意图类别。
- 如果用户输入模糊、带有疑问、犹豫、否定、复合、闲聊、无关、或无法确定意图，请直接返回“聊天互动”。
- 例如“你觉得我适合什么妆容？”、“我昨天买了个新口红”等都应判定为“聊天互动”。
用户输入：{text}
请直接输出最匹配的类别。
"""
    llm = ChatOpenAI(
        openai_api_key=config['configurable'].get("chat_api_key"),
        openai_api_base=config['configurable'].get("chat_api_base"),
        model=config['configurable'].get("chat_model_name")
    )
    result = llm.invoke([HumanMessage(content=prompt)])
    # 只返回类别本身
    intent = result.content.strip()
    # 容错：如模型输出带标点或解释，做简单清洗
    for cat in INTENT_CATEGORIES:
        if cat in intent:
            return cat
    return "聊天互动"

def recognize_intent_with_current_flow(content: list, current_flow: str, config) -> str:
    """
    用 LLM 根据当前用户输入文本和历史意图，判断是否需要继续当前意图，还是需要切换到其他意图。
    """
    text = [item["text"] for item in content if item["type"] == "text"]
    prompt = f"""
    你是一个智能助手，请根据当前用户输入文本和历史意图，判断是否需要继续当前意图，还是需要切换到其他意图，意图类别如下：
    {INTENT_CATEGORIES}
    要求：
    - 只有当用户输入内容非常明确、直接地表达了某个具体意图（如“请帮我做肤质检测”、“我要创建个人档案”等），才切换到其他意图类别。
    - 如果用户输入模糊、带有疑问、犹豫、否定、复合、闲聊、无关、或无法确定意图，请直接返回“继续”，不要切换到其他意图类别。
    当前用户输入文本：{text}
    当前意图：{current_flow}
    请直接输出“继续”或其他意图类别。
    """
    llm = ChatOpenAI(
        openai_api_key=config['configurable'].get("chat_api_key"),
        openai_api_base=config['configurable'].get("chat_api_base"),
        model=config['configurable'].get("chat_model_name")
    )
    result = llm.invoke([HumanMessage(content=prompt)])
    intent = result.content.strip()
    if intent in INTENT_CATEGORIES:
        return intent
    else:
        return current_flow



