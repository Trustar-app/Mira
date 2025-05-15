from state import MiraState
import base64
import mimetypes
from langchain_core.messages import HumanMessage
from utils.loggers import MiraLog
import os
from PIL import Image

def format_messages(video, audio, text, multimodal_text):
    """
    将前端输入(video, audio, text)转换为 OpenAI 格式 messages
    """
    """messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请帮我做一个肤质检测"},
                {"type": "video_url", "video_url": {"url": f"data:{mime_type};base64,{video_b64}"}}
            ]
        }
    ]"""

    if video:
        with open(video, "rb") as f:
            video_bytes = f.read()
        video_b64 = base64.b64encode(video_bytes).decode("utf-8")
        mime_type, _ = mimetypes.guess_type(video)
        messages = [
            HumanMessage(
                content=[
                    {"type": "text", "text": multimodal_text},
                    {"type": "video_url", "video_url": {"url": f"data:{mime_type};base64,{video_b64}"}}
                ]
            )
        ]
    else:
        messages = [
            HumanMessage(
                content=[{"type": "text", "text": multimodal_text}]
            )
        ]
    return messages

def structure_to_frontend_outputs(state):
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
    if state["analysis_report"] is not None:
        # 肤质检测流程
        formatted = format_skin_check(state)
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

def format_skin_check(skin_state):
    """
    格式化肤质检测结果
    """
    skin_result_dict = {}
    # 修改这一行
    skin_result_dict["chat"] = [{"role": "assistant", "content": skin_state["analysis_report"]}]
    skin_result_dict["markdown"] = skin_state["skin_analysis_result"]
    image = skin_state["best_face_image"]
    if image.startswith("mockdata/"):
        # 模拟数据，从项目根目录读取图片
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        image_path = os.path.join(project_root, image)
        
        # 确认文件存在
        if os.path.exists(image_path):
            # 读取图片数据
            img = Image.open(image_path)
            skin_result_dict["image"] = img
        else:
            MiraLog('app', f"模拟图片文件不存在: {image_path}")
    else:  
        skin_result_dict["image"] = image

    skin_result_dict["gallery"] = []
    skin_result_dict["profile"] = ""
    skin_result_dict["products"] = []

    return skin_result_dict



def format_product_recommendation(products):
    """
    格式化产品推荐结果
    """
    pass

def format_makeup_steps(steps):
    """
    格式化化妆/护肤引导步骤
    """
    pass

def format_product_recognition(product_info):
    """
    格式化产品识别结果
    """
    pass

def format_profile(profile):
    """
    格式化用户档案
    """
    pass

def format_care_makeup_guide(steps):
    """
    格式化化妆/护肤引导步骤
    """
    pass

