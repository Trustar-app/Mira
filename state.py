"""
State 结构、reducer、schema 定义，支持主流程与各子流程状态管理。
"""
from typing import Optional, Dict, Any, List, TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
class MiraState(TypedDict, total=False):
    # 全局信息
    user_profile: Optional[Dict[str, Any]]      # 用户档案
    products_directory: Optional[Dict[str, Any]]  # 用户自有产品目录
    messages: Annotated[List[AnyMessage], add_messages]    # 全局消息历史

    current_text: Optional[str]
    current_audio: Optional[str]
    current_video: Optional[str]
    multimodal_text: Optional[str]


class SkinAnalysisState(TypedDict, total=False):
    user_profile: Optional[Dict[str, Any]]
    products_directory: Optional[Dict[str, Any]]
    messages: Annotated[List[AnyMessage], add_messages]

    current_text: Optional[str]
    current_audio: Optional[str]
    current_video: Optional[str]
    multimodal_text: Optional[str]

    # 中间产物
    best_face_image: Optional[str]   # 最佳脸部图片路径
    face_detected: Optional[bool]    # 是否检测到人脸


class UserProfileEditState(TypedDict, total=False):
    user_profile: Optional[Dict[str, Any]]
    products_directory: Optional[Dict[str, Any]]
    messages: Annotated[List[AnyMessage], add_messages]

    current_text: Optional[str]
    current_audio: Optional[str]
    current_video: Optional[str]
    multimodal_text: Optional[str]


class CareMakeupGuideState(TypedDict, total=False):
    user_profile: Optional[Dict[str, Any]]
    products_directory: Optional[Dict[str, Any]]
    messages: Annotated[List[AnyMessage], add_messages]

    current_text: Optional[str]
    current_audio: Optional[str]
    current_video: Optional[str]
    multimodal_text: Optional[str]

    scenario: Optional[str]
    recommended_steps: Optional[List[Dict[str, Any]]]  # 推荐/确认后的步骤列表
    current_step_index: Optional[int]
    current_step_feedback: Optional[str]


class ProductRecognitionState(TypedDict, total=False):
    user_profile: Optional[Dict[str, Any]]
    products_directory: Optional[Dict[str, Any]]
    messages: Annotated[List[AnyMessage], add_messages]

    current_text: Optional[str]
    current_audio: Optional[str]
    current_video: Optional[str]
    multimodal_text: Optional[str]

    # 中间产物
    product_raw_info: Optional[Dict[str, Any]]   # AI识别出的原始产品信息（如品牌、品名、条码等）
    product_structured_info: Optional[Dict[str, Any]]  # 网络检索到的结构化产品信息


class ProductRecommendationState(TypedDict, total=False):
    user_profile: Optional[Dict[str, Any]]
    products_directory: Optional[Dict[str, Any]]
    messages: Annotated[List[AnyMessage], add_messages]

    current_text: Optional[str]
    current_audio: Optional[str]
    current_video: Optional[str]
    multimodal_text: Optional[str]

    # 推荐需求
    recommend_category: Optional[str]       # 推荐的产品类别（如“粉底液”）
    recommend_preferences: Optional[str]    # 用户特殊诉求/偏好

    # 推荐结果
    recommended_products: Optional[List[Dict[str, Any]]]  # 推荐产品列表
    personalized_reasons: Optional[List[str]]             # 个性化推荐理由
