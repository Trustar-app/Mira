import os
from config import OPENAI_API_KEY, OPENAI_API_BASE
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from moviepy.video.io.VideoFileClip import VideoFileClip
import tempfile
import speech_recognition as sr
import os

# 意图类别列表
INTENT_CATEGORIES = [
    "聊天互动",
    "肤质检测",
    "创建用户档案",
    "产品推荐",
    "产品识别",
    "化妆引导",
    "护肤引导",
    "档案编辑"
]

# 1. 多模态聊天 Agent
# 输入: OpenAI 格式 messages（支持文本和视频）
def multimodal_chat_agent(messages, streaming=False):
    """
    多模态聊天 Agent，输入为（含文本、音频、视频），输出为回复文本。
    若streaming=True，则返回生成器，每次yield一个chunk，便于流式对接前端。
    """
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        model="qwen2.5-vl-72b-instruct",
        streaming=streaming
    )
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
def recognize_intent(text: str) -> str:
    """
    用 LLM 对文本进行意图识别，返回意图类别
    """
    prompt = f"""
你是一个智能助手，请判断用户输入的意图属于下列哪一类，只需返回类别本身，不要返回其他内容：
{INTENT_CATEGORIES}
要求：
- 只有当用户输入内容非常明确、直接地表达了某个具体意图（如“请帮我做肤质检测”、“我要创建个人档案”等），才返回该意图类别。
- 如果用户输入模糊、带有疑问、犹豫、否定、复合、闲聊、无关、或无法确定意图，请直接返回“聊天互动”。
- 例如“你觉得我适合什么妆容？”、“我昨天买了个新口红”等都应判定为“聊天互动”。
用户输入：{text}
请直接输出最匹配的类别。
"""
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        model="qwen2.5-14b-instruct"
    )
    result = llm.invoke([HumanMessage(content=prompt)])
    # 只返回类别本身
    intent = result.content.strip()
    # 容错：如模型输出带标点或解释，做简单清洗
    for cat in INTENT_CATEGORIES:
        if cat in intent:
            return cat
    return "聊天互动"

