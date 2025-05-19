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
    messages = []
    
    # 处理文本
    if text:
        messages.append({"type": "text", "text": text})
    
    # 处理视频
    if video and isinstance(video, str) and os.path.exists(video):
        try:
            # 读取视频文件并转换为base64
            with open(video, "rb") as video_file:
                video_base64 = base64.b64encode(video_file.read()).decode("utf-8")
            
            # 构建符合API要求的消息格式
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "video_url",
                            "video_url": {
                                "url": f"data:video/mp4;base64,{video_base64}"
                            }
                        }
                    ]
                }
            ]
            
            # 如果有文本内容，添加到content列表中
            if multimodal_text:
                messages[0]["content"].append({
                    "type": "text",
                    "text": multimodal_text
                })
            
        except Exception as e:
            MiraLog("formatters", f"处理视频数据时出错: {e}", "ERROR")
            if multimodal_text:
                messages = [{
                    "role": "user",
                    "content": [{"type": "text", "text": multimodal_text}]
                }]
    
    # 如果没有视频，只有文本
    elif multimodal_text:
        messages = [{
            "role": "user",
            "content": [{"type": "text", "text": multimodal_text}]
        }]
    
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
        try:
            import base64
            from PIL import Image
            import io
            
            # 处理base64前缀
            if "base64," in image:
                image = image.split("base64,")[1]
            
            # 处理填充
            missing_padding = len(image) % 4
            if missing_padding:
                image += "=" * (4 - missing_padding)
            
            # 解码并转换为PIL Image
            image_data = base64.b64decode(image)
            pil_image = Image.open(io.BytesIO(image_data))
            
            # 保存为PIL图像对象
            skin_result_dict["image"] = pil_image
        except Exception as e:
            MiraLog('app', f"将base64转换为PIL图像时出错: {e}")
            skin_result_dict["image"] = None

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

