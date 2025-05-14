import base64
import mimetypes
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from config import OPENAI_API_BASE, OPENAI_API_KEY
import json

def video_to_base64(video_path: str):
    """
    将视频文件转为base64字符串及mime类型
    """
    with open(video_path, "rb") as video_file:
        video_data = video_file.read()
        base64_video = base64.b64encode(video_data).decode('utf-8')
        mime_type, _ = mimetypes.guess_type(video_path)
    return base64_video, mime_type or "video/mp4"


def analyze_face_features_with_llm(video_path: str) -> dict:
    """
    用LLM分析面部视频，提取五官特征、肤色、肤质等结构化信息。
    输入: 视频文件路径
    输出: dict，包含face_features, skin_color, skin_quality等字段
    """
    base64_video, mime_type = video_to_base64(video_path)
    prompt = f"请分析用户上传的面部视频，提取五官特征、肤色、肤质，输出JSON，字段包括face_features, skin_color, skin_quality。视频路径：{video_path}"
    messages = [HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "video_url", "video_url": {"url": f"data:{mime_type};base64,{base64_video}"}}
    ])]
    llm = ChatOpenAI(
        model="qwen2.5-vl-72b-instruct",
        openai_api_base=OPENAI_API_BASE,
        openai_api_key=OPENAI_API_KEY,
        streaming=False
    )
    response = llm.invoke(messages)
    try:
        features = json.loads(response.content)
    except Exception:
        features = {}
    return features
