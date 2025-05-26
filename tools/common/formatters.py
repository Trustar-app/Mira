from state import MiraState
import base64
import mimetypes
from langchain_core.messages import HumanMessage
from utils.loggers import MiraLog
import os
from PIL import Image

def format_messages(video, text):
    """
    将前端输入(video, text)转换为 OpenAI 格式 messages
    """
    messages = []

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
            if text:
                messages[0]["content"].append({
                    "type": "text",
                    "text": text
                })
            
        except Exception as e:
            MiraLog("formatters", f"处理视频数据时出错: {e}", "ERROR")
            if text:
                messages = [{
                    "role": "user",
                    "content": [{"type": "text", "text": text}]
                }]
    
    # 如果没有视频，只有文本
    elif text:
        messages = [{
            "role": "user",
            "content": [{"type": "text", "text": text}]
        }]
    
    return messages

def structure_to_frontend_outputs(content):
    """
    将任意 State 转换为前端结构化展示区所需的 (markdown, image, gallery, profile, products, ...)
    """
    response = ""
    markdown = None
    image = None
    gallery = []
    profile = ""
    product = ""
    if content.get("response"):
        response = content["response"]
    if content.get("markdown"): # 对 dict 类型做优美的格式化处理
        markdown = dict_to_markdown(content["markdown"])
    if content.get("image"):
        image = content["image"]
    if content.get("gallery"):
        gallery = content["gallery"]
    if content.get("profile"):
        profile = dict_to_markdown(content["profile"])
    if content.get("product"):
        product = format_product(content["product"])

    return response, markdown, image, gallery, profile, product

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

def dict_to_markdown(d, indent=0):
    """将结构化 dict 转为 markdown 格式字符串，主项之间用两个换行隔开"""
    markdown = ""
    prefix = "  " * indent  # 两个空格缩进
    for key, value in d.items():
        if isinstance(value, dict):
            markdown += f"{prefix}- **{key}**:\n\n"
            markdown += dict_to_markdown(value, indent + 1)
        elif isinstance(value, list):
            markdown += f"{prefix}- **{key}**:\n\n"
            for item in value:
                if isinstance(item, dict):
                    markdown += dict_to_markdown(item, indent + 1)
                else:
                    markdown += f"{prefix}  - {item}\n\n"
        else:
            markdown += f"{prefix}- **{key}**: {value}\n\n"
    return markdown

