from state import MiraState, UserProfile, Product
import base64
import mimetypes
from langchain_core.messages import HumanMessage
from utils.loggers import MiraLog
import os
from PIL import Image
from typing import Union, List, Dict, Any

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

def dict_to_markdown(d, indent=0):
    """
    将结构化 dict 转为 markdown 格式字符串
    支持特殊类型：护肤/化妆计划、产品检索结果、肤质分析结果等
    """
    markdown = ""
    prefix = "  " * indent  # 两个空格缩进

    # 特殊类型处理
    if "type" in d and "steps" in d:  # 护肤/化妆计划
        markdown += f"{prefix}### {d['type']}计划\n\n"
        for i, step in enumerate(d["steps"], 1):
            markdown += f"{prefix}#### 步骤 {i}: {step['step_name']}\n\n"
            markdown += f"{prefix}- **使用产品**: {step['product_type']}\n"
            markdown += f"{prefix}- **操作说明**: {step['instructions']}\n"
            if step.get('notes'):
                markdown += f"{prefix}- **注意事项**: {step['notes']}\n"
            markdown += "\n"
        return markdown

    if "query" in d and "results" in d:  # 产品检索结果
        markdown += f"{prefix}### 检索结果\n\n"
        markdown += f"{prefix}**搜索词**: {d['query']}\n\n"
        for i, result in enumerate(d["results"], 1):
            markdown += f"{prefix}#### {i}. {result['title']}\n\n"
            markdown += f"{prefix}{result['content'][:200]}...\n\n"  # 限制内容长度
            markdown += f"{prefix}[查看详情]({result['url']})\n\n"
        if d.get("images"):
            markdown += f"{prefix}### 相关图片\n\n"
            for img_url in d["images"][:3]:  # 限制图片数量
                markdown += f"{prefix}![产品图片]({img_url})\n"
        return markdown

    if "skin_quality" in d:  # 肤质分析结果
        markdown += f"{prefix}### 肤质检测结果\n\n"
        
        # 显示检测图片
        if d.get("image"):
            markdown += f"{prefix}#### 检测图片\n\n"
            # 确保 base64 字符串格式正确
            image_base64 = d["image"]
            if "base64," not in image_base64:
                image_base64 = f"data:image/jpeg;base64,{image_base64}"
            markdown += f"{prefix}![检测图片]({image_base64})\n\n"
        
        # 分组展示评分
        markdown += f"{prefix}#### 评分详情\n\n"
        scores = d["skin_quality"]
        groups = {
            "基础肤质": ["spot", "wrinkle", "pore", "redness", "oiliness", "acne"],
            "眼部状况": ["dark_circle", "eye_bag", "tear_trough"],
            "整体状态": ["firmness"]
        }
        
        for group_name, metrics in groups.items():
            markdown += f"{prefix}##### {group_name}\n\n"
            for metric in metrics:
                if metric in scores:
                    score = scores[metric]
                    score_bar = "▓" * int(score) + "░" * (10 - int(score))
                    markdown += f"{prefix}- **{en_to_cn(metric)}**: {score_bar} ({score}/10)\n"
            markdown += "\n"
        return markdown

    # 通用字典处理
    for key, value in d.items():
        if key == "image":  # 跳过图片字段,因为已经在特殊处理中展示
            continue
            
        key = en_to_cn(key)
        if isinstance(value, dict):
            markdown += f"{prefix}### {key}\n\n"
            markdown += dict_to_markdown(value, indent + 1)
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                markdown += f"{prefix}### {key}\n\n"
                for item in value:
                    markdown += dict_to_markdown(item, indent + 1)
            else:
                items = ", ".join(str(item) for item in value)
                markdown += f"{prefix}- **{key}**: {items}\n\n"
        else:
            markdown += f"{prefix}- **{key}**: {value}\n\n"
    
    return markdown

# 英文key转中文
def en_to_cn(key):
    en_to_cn_dict = {
        "name": "姓名",
        "gender": "性别",
        "age": "年龄",
        "skin_color": "肤色",
        "skin_type": "肤质类型",

        "face_features": "面部特征",
        "face_shape": "脸型",
        "eyes": "眼睛",
        "nose": "鼻子",
        "mouth": "嘴巴",
        "eyebrows": "眉毛",
        "skin_quality": "肤质评分",
        "spot": "斑点评分",
        "wrinkle": "皱纹评分",
        "pore": "毛孔评分",
        "redness": "发红评分",
        "oiliness": "出油评分",
        "acne": "痘痘评分",
        "dark_circle": "黑眼圈评分",
        "eye_bag": "眼袋评分",
        "tear_trough": "泪沟评分",
        "firmness": "皮肤紧致度评分",

        "makeup_skill_level": "化妆能力",
        "skincare_skill_level": "护肤能力",
        "user_preferences": "个人诉求与偏好",

        "image_url": "产品图片",
        "product_name": "产品名称",
        "category": "产品分类",
        "brand": "产品品牌",
        "ingredients": "成分",
        "effects": "功效",
        "description": "备注",
    }
    return en_to_cn_dict.get(key, key)

def format_user_info(user_profile: Union[UserProfile, Dict[str, Any]], products_directory: List[Product] = None) -> str:
    """
    将用户信息和产品目录格式化为易读的markdown格式
    
    Args:
        user_profile: 用户档案信息
        products_directory: 用户的产品目录
        
    Returns:
        str: 格式化后的markdown文本
    """
    markdown = "【用户档案】\n"
    
    # 处理用户基本信息
    basic_info = {
        "name": user_profile.get("name"),
        "gender": user_profile.get("gender"),
        "age": user_profile.get("age")
    }
    basic_info = {k: v for k, v in basic_info.items() if v}  # 移除空值
    if basic_info:
        markdown += dict_to_markdown(basic_info)
    
    # 处理肤质信息
    skin_info = {
        "skin_color": user_profile.get("skin_color"),
        "skin_type": user_profile.get("skin_type")
    }
    skin_info = {k: v for k, v in skin_info.items() if v}  # 移除空值
    if skin_info:
        markdown += "【肤质信息】\n" + dict_to_markdown(skin_info)
    
    # 处理面部特征
    if face_features := user_profile.get("face_features"):
        face_features = {k: v for k, v in face_features.items() if v}  # 移除空值
        if face_features:
            markdown += "【面部特征】\n" + dict_to_markdown(face_features)
    
    # 处理肤质评分
    if skin_quality := user_profile.get("skin_quality"):
        skin_quality = {k: v for k, v in skin_quality.items() if v is not None}  # 移除空值
        if skin_quality:
            markdown += "【肤质评分】\n" + dict_to_markdown(skin_quality)
    
    # 处理技能和偏好
    skill_info = {
        "makeup_skill_level": user_profile.get("makeup_skill_level"),
        "skincare_skill_level": user_profile.get("skincare_skill_level"),
        "user_preferences": user_profile.get("user_preferences")
    }
    skill_info = {k: v for k, v in skill_info.items() if v}  # 移除空值
    if skill_info:
        markdown += "【技能和偏好】\n" + dict_to_markdown(skill_info)
    
    # 处理产品目录
    if products_directory:
        markdown += "\n【用户产品目录】\n"
        for product in products_directory:
            product_info = {k: v for k, v in product.items() if v and k != "image_url"}  # 移除空值和图片URL
            if product_info:
                markdown += dict_to_markdown(product_info)
    
    return markdown