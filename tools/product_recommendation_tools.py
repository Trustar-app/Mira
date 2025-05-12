def parse_recommend_intent(user_text: Optional[str], user_audio: Optional[str], user_image: Optional[str]) -> Dict[str, str]:
    """
    解析用户输入，提取推荐类别和偏好。
    :param user_text: 用户文本
    :param user_audio: 用户语音
    :param user_image: 用户图片
    :return: {"recommend_category": ..., "recommend_preferences": ...}
    """

def search_recommended_products(user_profile: Dict[str, Any], recommend_category: str, recommend_preferences: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
    """
    检索最匹配的产品列表。
    :param user_profile: 用户档案
    :param recommend_category: 推荐类别
    :param recommend_preferences: 用户偏好
    :return: 推荐产品列表，失败返回 None
    """

def generate_personalized_reasons(user_profile: Dict[str, Any], products: List[Dict[str, Any]]) -> List[str]:
    """
    生成每个推荐产品的个性化推荐理由。
    :param user_profile: 用户档案
    :param products: 推荐产品列表
    :return: 推荐理由列表
    """