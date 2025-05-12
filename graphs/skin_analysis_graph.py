"""
肤质检测子流程 Graph，节点实现见下。
"""
def build_skincare_graph():
    """
    构建肤质检测子流程 Graph，注册所有节点与分支。
    :return: LangGraph Subgraph 实例
    """

def wait_for_video_node(state):
    """
    输入采集节点：判断并引导用户上传/录制视频。如果没有视频，通过 interrupt 请求用户干预
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 检查 user_video，若无则返回 progress/error
    # 若有则返回 {"progress": "收到视频，准备分析", ...}

def video_analysis_node(state):
    """
    视频有效性分析节点：提取最佳帧并做人脸检测，返回最佳图片。如果提取不到合适的人脸图片，要求重新输入视频。通过 interrupt 请求用户干预。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 调用 extract_best_face_frame，更新 best_face_image/face_detected

def node_skin_analysis(state):
    """
    肤质AI检测节点：对图片做肤质分析。
    :param state: 当前 State
    :return: (新 State, 分析报告)
    """
    # 调用肤质分析模型，更新 skin_analysis_result/analysis_report


def node_result_feedback(state):
    """
    结果反馈节点：基于分析报告，AI 生成个性化解读。
    :param state: 当前 State
    :param analysis_report: 肤质分析报告
    :return: (新 State, 反馈消息)
    """
    # 生成个性化解读，更新 analysis_report/progress
