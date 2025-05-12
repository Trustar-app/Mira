import os
from config import OPENAI_API_KEY, OPENAI_API_BASE
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from moviepy.video.io.VideoFileClip import VideoFileClip
import tempfile
import speech_recognition as sr
import os

def multimodal_chat_agent() -> str:
    """
    多模态聊天 Agent，输入为（含文本、音频、视频），输出为回复文本。
    """
    # 可拼接多模态内容，调用 LLM/MLLM

def recognize_intent(text: str) -> str:
    """
    用 LLM 对文本进行意图识别，返回意图类别
    """
    # prompt 设计：请判断用户意图属于以下哪一类...

    SYSTEM_PROMPT = (
    "你是一个智能意图识别助手。请根据用户输入内容和对话上下文，判断其意图，并只输出以下六个标签之一：\n"
    "build_profile（建档/档案/profile）、skin_check（肤质/skin）、makeup_guidance（化妆/妆容/makeup）、"
    "product_query（产品/推荐/product）、emotion_chat（闲聊/打招呼/鼓励/你好/hi/hello/聊）、resume_last_step（恢复/继续/上次）。"
    "如果无法判断，输出 emotion_chat。只输出标签本身，不要输出其他内容。"
)


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