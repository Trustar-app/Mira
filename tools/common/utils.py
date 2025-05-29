from moviepy.video.io.VideoFileClip import VideoFileClip
import tempfile
import speech_recognition as sr
import os

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

def fill_config_with_env(config: dict) -> dict:
    key_env_map = {
        "chat_api_key": "CHAT_API_KEY",
        "tavily_api_key": "TAVILY_API_KEY",
    }
    new_config = config.copy()
    for key, env_name in key_env_map.items():
        if new_config.get(key, "") == "default":
            new_config[key] = os.getenv(env_name, "")
    return new_config