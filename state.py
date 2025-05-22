"""
State 结构、reducer、schema 定义，支持主流程与各子流程状态管理。
"""
from typing import Optional, Dict, Any, List, TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

def dict_merge_reducer(old, new):
    if old is None:
        old = {}
    if new is None:
        new = {}
    merged = {**old, **new}
    return merged


class MiraState(TypedDict, total=False):
    # 全局信息
    user_profile: Annotated[Dict[str, Any], dict_merge_reducer]      # 用户档案
    products_directory: Annotated[Dict[str, Any], dict_merge_reducer]  # 用户自有产品目录
    messages: Annotated[List[AnyMessage], add_messages]    # 全局消息历史
    resume: Optional[bool]    # 是否是中断后的回复

    current_text: Optional[str]
    current_audio: Optional[str]
    current_video: Optional[str]
    multimodal_text: Optional[str]

    current_flow: Optional[str]


class SkinAnalysisState(TypedDict, total=False):
    user_profile: Annotated[Dict[str, Any], dict_merge_reducer]
    products_directory: Annotated[Dict[str, Any], dict_merge_reducer]
    messages: Annotated[List[AnyMessage], add_messages]

    current_text: Optional[str]
    current_audio: Optional[str]
    current_video: Optional[str]
    multimodal_text: Optional[str]
    current_video_base64: Optional[str]

    # 中间产物
    best_face_image: Optional[str]   # 最佳脸部图片路径
    face_detected: Optional[bool]    # 是否检测到人脸
    skin_analysis_result: Optional[str]   # JSON字符串形式的肤质分析结果
    analysis_report: Optional[str]        # AI生成的个性化解读

    current_flow: Optional[str]


class UserProfileEditState(TypedDict, total=False):
    user_profile: Annotated[Dict[str, Any], dict_merge_reducer]
    products_directory: Annotated[Dict[str, Any], dict_merge_reducer]
    messages: Annotated[List[AnyMessage], add_messages]

    current_text: Optional[str]
    current_audio: Optional[str]
    current_video: Optional[str]
    multimodal_text: Optional[str]

    basic_info: Annotated[Dict[str, Any], dict_merge_reducer]
    current_flow: Optional[str]


class CareMakeupGuideState(TypedDict, total=False):
    user_profile: Annotated[Dict[str, Any], dict_merge_reducer]
    products_directory: Annotated[Dict[str, Any], dict_merge_reducer]
    messages: Annotated[List[AnyMessage], add_messages]

    current_text: Optional[str]
    current_audio: Optional[str]
    current_video: Optional[str]
    multimodal_text: Optional[str]

    scenario: Optional[str]
    recommended_steps: Optional[List[Dict[str, Any]]]  # 推荐/确认后的步骤列表
    current_step_index: Optional[int]
    current_step_feedback: Optional[str]

    current_flow: Optional[str]


class ProductAnalysisState(TypedDict, total=False):
    user_profile: Annotated[Dict[str, Any], dict_merge_reducer]
    products_directory: Annotated[Dict[str, Any], dict_merge_reducer]
    messages: Annotated[List[AnyMessage], add_messages]

    current_text: Optional[str]
    current_audio: Optional[str]
    current_video: Optional[str]
    multimodal_text: Optional[str]

    # 中间产物
    product_structured_info: Optional[Dict[str, Any]]  # 网络检索到的结构化产品信息

    current_flow: Optional[str]


class ProductRecommendationState(TypedDict, total=False):
    user_profile: Annotated[Dict[str, Any], dict_merge_reducer]
    products_directory: Annotated[Dict[str, Any], dict_merge_reducer]
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

    current_flow: Optional[str]
