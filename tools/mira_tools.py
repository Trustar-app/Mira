from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

# 意图类别列表
INTENT_CATEGORIES = [
    "聊天互动",  # 默认闲聊、问候等
    "肤质检测",  # 皮肤状态分析、面部检测等
    "创建用户档案",  # 用户信息收集、档案创建等
    "产品分析",  # 产品推荐、识别、分析等
    "化妆或护肤引导"  # 化妆教学、护肤指导等
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
def recognize_intent(content: list, config) -> str:
    """
    用 LLM 对文本进行意图识别，返回意图类别
    """
    text = [item["text"] for item in content if item["type"] == "text"]
    prompt = f"""你是一个智能美妆助手的意图识别模块。请判断用户输入的意图属于下列哪一类，只需返回类别本身：

{INTENT_CATEGORIES}

判断规则：
1. 产品分析类：
   - 包含产品推荐请求，如"推荐适合我的粉底液"、"有什么好用的面霜推荐"
   - 包含产品识别请求，如"这个产品是什么"、"帮我看看这个护肤品"
   - 包含产品成分分析请求，如"分析一下这个产品的成分"、"这个产品适合我吗"

2. 化妆或护肤引导类：
   - 包含化妆教学请求，如"教我画眼线"、"想学习画眉毛"、"我想画一个妆"

3. 肤质检测类：
   - 明确要求进行肤质分析，如"帮我检测下皮肤"、"看看我的皮肤状况"
   - 询问具体肤质问题，如"我的皮肤是什么类型"、"帮我看看脸上的问题"

4. 创建用户档案类：
   - 明确表示要创建或修改个人信息，如"我要创建档案"、"更新我的信息"

5. 聊天互动类（默认类别）：
   - 日常问候，如"你好"、"早上好"
   - 模糊或间接的美妆相关问题，如"你觉得我适合什么妆容"
   - 情感或闲聊内容，如"今天心情不好"、"我昨天买了新口红"
   - 其他不属于上述类别的内容

要求：
- 优先匹配具体的功能类别（产品分析、化妆引导、肤质检测、创建档案）
- 只有当完全无法确定具体意图时，才返回"聊天互动"
- 如果一句话包含多个意图，选择最主要、最明确的一个

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

def recognize_intent_with_current_flow(content: list, current_flow: str, previous_dialog: str, config) -> str:
    """
    用 LLM 根据当前用户输入文本和历史意图，判断是否需要继续当前意图，还是需要切换到其他意图。
    """
    text = [item["text"] for item in content if item["type"] == "text"]
    prompt = f"""你是一个智能美妆助手的意图管理模块。请根据当前用户输入和当前执行的流程，判断是否需要切换到新的意图。可选的意图类别如下：

{INTENT_CATEGORIES}

上一轮对话：{previous_dialog}
当前用户输入：{text}
当前执行的流程：{current_flow}

判断规则：
1. 强制切换场景（需要切换到新意图）：
   - 用户明确表达了对其他功能的需求，如在护肤流程中说"帮我检测下皮肤"
   - 用户表达了对当前流程的否定或终止，如"不用了"、"先不做这个"
   - 用户提出了与当前流程完全无关的新需求

2. 保持当前流程场景（返回"继续"）：
   - 用户在回答当前流程的问题
   - 用户在询问当前流程的相关细节
   - 用户表达了继续当前流程的意愿
   - 用户的输入是对当前流程的补充信息

3. 特殊处理：
   - 在产品分析流程中，允许连续分析多个产品
   - 在化妆引导流程中，允许连续学习多个妆容技巧
   - 在肤质检测流程中，新的检测请求应该开启新流程

请根据以上规则，判断是否需要切换意图。
- 如果需要切换，直接返回新的意图类别
- 如果应该继续当前流程，直接返回"继续"
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



