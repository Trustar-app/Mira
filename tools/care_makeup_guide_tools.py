def agent_generate_steps(user_intent: str, guide_type: str, scenario: Optional[str], user_feedback: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    调用 LLM/Agent，根据用户需求和修改建议，生成产品种类列表和分步流程（每步含产品和动作）。
    :param user_intent: 用户需求
    :param guide_type: "skincare" or "makeup"
    :param scenario: 场景/妆容需求
    :param user_feedback: 用户对推荐方案的修改建议
    :return: 推荐步骤列表
    """

def analyze_step_video(video_path: str, step_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析用户上传的视频，判断是否完成本步骤，返回分析结果和建议。
    :param video_path: 视频路径
    :param step_info: 当前步骤信息
    :return: 分析结果（如{"completed": True, "feedback": "手法标准"}）
    """