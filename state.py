"""
State 结构、reducer、schema 定义，支持主流程与各子流程状态管理。
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class MiraState(BaseModel):
    # 全局信息
    user_profile: Optional[Dict[str, Any]] = None      # 用户档案
    messages: Optional[List[Dict[str, Any]]] = None    # 全局消息历史
    current_flow: Optional[str] = None                 # 当前主流程名
    progress: Optional[str] = None
    error: Optional[str] = None

    # 子流程输入/输出通道
    skincare_input: Optional[Dict[str, Any]] = None
    skincare_result: Optional[Dict[str, Any]] = None

    profile_input: Optional[Dict[str, Any]] = None
    profile_result: Optional[Dict[str, Any]] = None

    guide_input: Optional[Dict[str, Any]] = None
    guide_result: Optional[Dict[str, Any]] = None

    product_recognition_input: Optional[Dict[str, Any]] = None
    product_recognition_result: Optional[Dict[str, Any]] = None

    product_recommend_input: Optional[Dict[str, Any]] = None
    product_recommend_result: Optional[Dict[str, Any]] = None


class SkincareState(BaseModel):
    # 用户输入
    user_profile: Optional[Dict[str, Any]] = None  # 共享字段
    user_text: Optional[str] = None         # 用户文本输入
    user_audio: Optional[str] = None        # 用户音频文件路径
    user_video: Optional[str] = None        # 用户视频文件路径

    # 中间产物
    best_face_image: Optional[str] = None   # 最佳脸部图片路径
    face_detected: Optional[bool] = None    # 是否检测到人脸

    # 分析结果
    skin_analysis_result: Optional[Dict[str, Any]] = None  # 肤质分析结构化结果
    analysis_report: Optional[str] = None   # AI 生成的分析报告文本

    # 进度与消息
    progress: Optional[str] = None          # 当前进度消息
    error: Optional[str] = None             # 错误信息

def skincare_reducer(state: SkincareState, update: dict) -> SkincareState:
    """
    合并节点输出到当前 State，返回新 State。
    :param state: 当前 SkincareState
    :param update: 节点返回的 dict（只包含需要更新的字段）
    :return: 新 SkincareState
    """
    # Pydantic BaseModel 支持 .copy(update=...) 语法
    return state.model_copy(update=update)


class UserProfileEditState(BaseModel):
    user_profile: Optional[Dict[str, Any]] = None  # 共享字段
    edit_field: Optional[str] = None
    edit_value: Optional[Any] = None

    progress: Optional[str] = None
    error: Optional[str] = None

def user_profile_reducer(state: UserProfileEditState, update: dict) -> UserProfileEditState:
    """
    合并节点输出到当前 State，返回新 State。
    :param state: 当前 UserProfileEditState
    :param update: 节点返回的 dict
    :return: 新 UserProfileEditState
    """
    return state.model_copy(update=update)


class CareMakeupGuideState(BaseModel):
    user_profile: Optional[Dict[str, Any]] = None  # 共享字段
    user_intent: Optional[str] = None
    guide_type: Optional[str] = None
    scenario: Optional[str] = None

    recommended_steps: Optional[List[Dict[str, Any]]] = None  # 推荐/确认后的步骤列表
    current_step_index: Optional[int] = 0
    current_step_feedback: Optional[str] = None

    user_video: Optional[str] = None
    user_feedback: Optional[str] = None  # 用户对推荐方案或步骤的反馈/修改建议

    progress: Optional[str] = None
    error: Optional[str] = None
    internal: Optional[Dict[str, Any]] = None

def makeup_reducer(state, action):
    """
    化妆子流程的状态 reducer。
    :param state: 当前 State
    :param action: 节点输出的 action
    :return: 新 State
    """

class ProductRecognitionState(BaseModel):
    # 用户输入
    user_profile: Optional[Dict[str, Any]] = None  # 共享字段
    user_video: Optional[str] = None         # 用户上传的视频路径
    user_text: Optional[str] = None          # 用户输入的产品名称/条码等文本

    # 中间产物
    product_raw_info: Optional[Dict[str, Any]] = None   # AI识别出的原始产品信息（如品牌、品名、条码等）
    product_structured_info: Optional[Dict[str, Any]] = None  # 网络检索到的结构化产品信息
    product_analysis: Optional[str] = None              # AI生成的适配性分析/个性化解读

    # 进度与消息
    progress: Optional[str] = None
    error: Optional[str] = None
    internal: Optional[Dict[str, Any]] = None           # 私有状态

def product_recognition_reducer(state: ProductRecognitionState, update: dict) -> ProductRecognitionState:
    """
    合并节点输出到当前 State，返回新 State。
    :param state: 当前 ProductRecognitionState
    :param update: 节点返回的 dict
    :return: 新 ProductRecognitionState
    """
    return state.copy(update=update)

class ProductRecommendationState(BaseModel):
    # 用户输入
    user_profile: Optional[Dict[str, Any]] = None  # 共享字段
    user_text: Optional[str] = None                # 用户输入的推荐需求文本
    user_audio: Optional[str] = None               # 用户输入的语音（可选）
    user_image: Optional[str] = None               # 用户上传的图片（可选）

    # 推荐需求
    recommend_category: Optional[str] = None       # 推荐的产品类别（如“粉底液”）
    recommend_preferences: Optional[str] = None    # 用户特殊诉求/偏好

    # 推荐结果
    recommended_products: Optional[List[Dict[str, Any]]] = None  # 推荐产品列表
    personalized_reasons: Optional[List[str]] = None             # 个性化推荐理由

    # 进度与消息
    progress: Optional[str] = None
    error: Optional[str] = None
    internal: Optional[Dict[str, Any]] = None

def product_recommendation_reducer(state: ProductRecommendationState, update: dict) -> ProductRecommendationState:
    """
    合并节点输出到当前 State，返回新 State。
    :param state: 当前 ProductRecommendationState
    :param update: 节点返回的 dict
    :return: 新 ProductRecommendationState
    """
    return state.copy(update=update)


# 主图与子图 State 映射示例
def call_skincare_subgraph(state: MiraState):
    skincare_input = {
        "user_profile": state.user_profile,
        "user_video": state.skincare_input.get("user_video") if state.skincare_input else None,
        "user_text": state.skincare_input.get("user_text") if state.skincare_input else None,
        "user_audio": state.skincare_input.get("user_audio") if state.skincare_input else None,
    }
    skincare_output = skincare_subgraph.invoke(skincare_input)
    return {"skincare_result": skincare_output}

def handle_skincare_result(state: MiraState):
    if state.skincare_result and "skin_analysis_result" in state.skincare_result:
        user_profile = state.user_profile or {}
        user_profile["skin_quality"] = state.skincare_result["skin_analysis_result"]
        return {"user_profile": user_profile}
    return {}