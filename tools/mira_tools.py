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
def multimodal_chat_agent(messages, streaming=False) -> str:
    """
    多模态聊天 Agent，输入为（含文本、音频、视频），输出为回复文本。
    """
    # Qwen2.5-VL-72B-Instruct 支持多模态输入，OpenAI API 兼容
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        model="qwen2.5-vl-72b-instruct",
        streaming=streaming
    )
    # 直接传递 messages，LangChain 会自动处理 OpenAI 格式
    if streaming:
        response = ""
        for chunk in llm.stream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                response += chunk.content
        return response
    else:
        result = llm(messages)
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
用户输入：{text}
请直接输出最匹配的类别。
"""
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        openai_api_base=OPENAI_API_BASE,
        model="qwen2.5-14b-instruct"
    )
    result = llm([HumanMessage(content=prompt)])
    # 只返回类别本身
    intent = result.content.strip()
    # 容错：如模型输出带标点或解释，做简单清洗
    for cat in INTENT_CATEGORIES:
        if cat in intent:
            return cat
    return intent


def video_to_audio(video_path):
    # 用临时文件保存音频
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_audio:
        audio_path = tmp_audio.name
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path, logger=None)
    return audio_path

def audio_to_text(audio_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio, language="zh-CN")
    except Exception:
        text = ""
    return text

def video_to_text(video_path):
    audio_path = video_to_audio(video_path)
    try:
        text = audio_to_text(audio_path)
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)
    return text