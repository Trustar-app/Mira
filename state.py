"""
State 结构、reducer、schema 定义，支持主流程与各子流程状态管理。
"""
from typing import Optional, Dict, Any, List
from typing_extensions import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from dotenv import load_dotenv
import os
import uuid

load_dotenv()

def dict_merge_reducer(old, new):
    if old is None:
        old = {}
    if new is None:
        new = {}
    merged = {**old, **new}
    return merged

# 前端 State 定义
class FaceFeature(TypedDict, total=False):
    face_shape: str  # 脸型 （方脸、圆脸、瓜子脸、方圆脸、鹅蛋脸、高颧骨）
    eyes: str  # 眼睛（单眼皮、双眼皮、大眼睛、小眼睛）
    nose: str  # 鼻子（大鼻子、小鼻子、高鼻梁、低鼻梁）
    mouth: str  # 嘴巴（大嘴巴、小嘴巴、厚嘴唇、薄嘴唇）
    eyebrows: str  # 眉毛（浓眉、细眉、弯眉、直眉）

class SkinQuality(TypedDict, total=False):
    spot: int  # 斑点评分 0-10
    wrinkle: int  # 皱纹评分 0-10
    pore: int  # 毛孔评分 0-10
    redness: int  # 发红评分 0-10
    oiliness: int  # 出油评分 0-10
    acne: int  # 痘痘评分 0-10
    dark_circle: int  # 黑眼圈评分 0-10
    eye_bag: int  # 眼袋评分 0-10
    tear_trough: int  # 泪沟评分 0-10
    firmness: int  # 皮肤紧致度评分 0-10

class UserProfile(TypedDict, total=False):
    # 基本信息
    name: str  # 姓名
    gender: str  # 性别
    age: int  # 年龄

    # 面部与肤质特征
    skin_color: str  # 肤色
    skin_type: str  # 肤质类型：油性、干性、中性、混合性
    face_features: FaceFeature
    skin_quality: SkinQuality

    # 能力与偏好
    makeup_skill_level: int  # 化妆能力等级 0-10
    skincare_skill_level: int  # 护肤能力等级 0-10
    user_preferences: str  # 个人诉求与偏好


def default_user_profile():
    return {
        "name": "",
        "gender": "",
        "age": None,
        
        "skin_color": "",
        "skin_type": "",
        "face_features": {
            "face_shape": "",
            "eyes": "",
            "nose": "",
            "mouth": "",
            "eyebrows": ""
        },
        "skin_quality": {
            "spot": None,
            "wrinkle": None,
            "pore": None,
            "redness": None,
            "oiliness": None,
            "acne": None,
            "dark_circle": None,
            "eye_bag": None,
            "tear_trough": None,
            "firmness": None
        },

        "makeup_skill_level": "",
        "skincare_skill_level": "",
        "user_preferences": ""
    }

class Product(TypedDict, total=False):
    image_url: str  # 产品图片
    name: str  # 产品名称
    category: str  # 产品分类
    brand: str  # 产品品牌
    ingredients: str  # 成分
    effects: str  # 功效
    description: str  # 备注

def default_products():
    return []

def default_config_state():
    return {
        "thread_id": str(uuid.uuid4()),
        "chat_api_key": os.getenv("CHAT_API_KEY", ""),
        "chat_api_base": os.getenv("CHAT_API_BASE", ""),
        "chat_model_name": os.getenv("CHAT_MODEL_NAME", ""),
        "audio_model_name": os.getenv("AUDIO_MODEL_NAME", ""),
        "chat_style": os.getenv("CHAT_STYLE", ""), 
        "tavily_api_key": os.getenv("TAVILY_API_KEY", ""),
        "use_youcam": os.getenv("USE_YOUCAM_API", "False") == "True",
        "youcam_api_key": os.getenv("YOUCAM_API_KEY", ""),
        "youcam_secret_key": os.getenv("YOUCAM_SECRET_KEY", "")
    }

class ConfigState(TypedDict, total=False):
    thread_id: str
    # 模型设置
    chat_api_key: str
    chat_api_base: str
    chat_model_name: str
    audio_model_name: str
    chat_style: str  # 聊天风格：诚实朋友、温柔治愈、毒舌幽默

    # 工具
    tavily_api_key: str
    use_youcam: bool
    youcam_api_key: str
    youcam_secret_key: str


def default_app_state():
    return {
        "config": default_config_state(),
        "profile": default_user_profile(),
        "products": default_products()
    }

class AppState(TypedDict, total=False):
    config: ConfigState
    profile: UserProfile
    products: list[Product]

    resume: bool = False  # 是否刚刚中断对话，需要恢复对话


# 后端 LangGraph State 
class MiraState(TypedDict, total=False):
    user_profile: Annotated[UserProfile, dict_merge_reducer]
    products_directory: Annotated[list[Product], dict_merge_reducer]
    messages: Annotated[List[AnyMessage], add_messages]
    current_flow: Optional[str]

class SkinAnalysisState(TypedDict, total=False):
    user_profile: Annotated[UserProfile, dict_merge_reducer]
    products_directory: Annotated[list[Product], dict_merge_reducer]
    messages: Annotated[List[AnyMessage], add_messages]

    # 中间产物
    current_video_base64: Optional[str]
    best_face_image: Optional[str]   # 最佳脸部图片路径
    face_detected: Optional[bool]    # 是否检测到人脸
    skin_analysis_result: Optional[str]   # JSON字符串形式的肤质分析结果
    analysis_report: Optional[str]        # AI生成的个性化解读


class UserProfileEditState(TypedDict, total=False):
    user_profile: Annotated[UserProfile, dict_merge_reducer]
    products_directory: Annotated[list[Product], dict_merge_reducer]
    messages: Annotated[List[AnyMessage], add_messages]

    basic_info: Annotated[Dict[str, Any], dict_merge_reducer]


class CareMakeupGuideState(TypedDict, total=False):
    user_profile: Annotated[UserProfile, dict_merge_reducer]
    products_directory: Annotated[list[Product], dict_merge_reducer]
    messages: Annotated[List[AnyMessage], add_messages]

    plan: Optional[str] # 护肤/化妆计划


class ProductAnalysisState(TypedDict, total=False):
    user_profile: Annotated[UserProfile, dict_merge_reducer]
    products_directory: Annotated[list[Product], dict_merge_reducer]
    messages: Annotated[List[AnyMessage], add_messages]

    # 中间产物
    product_structured_info: Optional[Dict[str, Any]]  # 网络检索到的结构化产品信息

