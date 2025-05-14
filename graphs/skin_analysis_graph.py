"""
肤质检测子流程 Graph，节点实现如下。
"""
import logging
from langgraph.graph import StateGraph, END, START
from state import SkinAnalysisState
from langgraph.config import get_stream_writer
from langgraph.types import interrupt

# 1. 输入采集节点
def wait_for_video_node(state: SkinAnalysisState):
    """
    输入采集节点：判断并引导用户上传/录制视频。如果没有视频，通过 interrupt 请求用户干预
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 检查 user_video，若无则返回 progress/error
    # 若有则返回 {"progress": "收到视频，准备分析", ...}
    logging.info("[wait_for_video_node] called")
    if not state.get("current_video"):
        response = interrupt({"type": "interrupt", "content": "请上传面部视频以进行肤质检测。"})
        state["current_video"] = response
    return state

# 2. 视频分析节点
def video_analysis_node(state: SkinAnalysisState):
    """
    视频有效性分析节点：提取最佳帧并做人脸检测，返回最佳图片。如果提取不到合适的人脸图片，要求重新输入视频。通过 interrupt 请求用户干预。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 调用 extract_best_face_frame，更新 best_face_image/face_detected
    logging.info("[video_analysis_node] called")
    writer = get_stream_writer()
    # mock: 实际应调用 extract_best_face_frame 工具
    state["best_face_image"] = "mock_face_image.jpg"
    state["face_detected"] = True
    writer({"type": "progress", "content": "已提取最佳人脸图片，准备分析肤质..."})
    return state

# 3. 肤质AI检测节点
def node_skin_analysis(state: SkinAnalysisState):
    """
    肤质AI检测节点：对图片做肤质分析。
    :param state: 当前 State
    :return: (新 State, 分析报告)
    """
    # 调用肤质分析模型，更新 skin_analysis_result/analysis_report
    logging.info("[node_skin_analysis] called")
    writer = get_stream_writer()
    # mock: 实际应调用 skin_quality_analysis 工具
    state["skin_analysis_result"] = {"moisture": 80, "oiliness": 30, "wrinkle": 10}
    writer({"type": "progress", "content": f"肤质分析结果：{state['skin_analysis_result']}"})
    return state

# 4. 结果反馈节点
def node_result_feedback(state: SkinAnalysisState):
    """
    结果反馈节点：基于分析报告，AI 生成个性化解读。
    :param state: 当前 State
    :param analysis_report: 肤质分析报告
    :return: (新 State, 反馈消息)
    """
    # 生成个性化解读，更新 analysis_report/progress
    logging.info("[node_result_feedback] called")
    writer = get_stream_writer()
    # mock: 实际应调用 generate_skin_analysis_report 工具
    state["analysis_report"] = "你的皮肤水润，油脂分泌适中，细纹较少。"
    writer({"type": "structure", "content": state["analysis_report"]})
    return state

def build_skincare_graph():
    graph = StateGraph(SkinAnalysisState)
    graph.add_node("wait_for_video", wait_for_video_node)
    graph.add_node("video_analysis", video_analysis_node)
    graph.add_node("skin_analysis", node_skin_analysis)
    graph.add_node("result_feedback", node_result_feedback)
    graph.add_edge(START, "wait_for_video")
    graph.add_edge("wait_for_video", "video_analysis")
    graph.add_edge("video_analysis", "skin_analysis")
    graph.add_edge("skin_analysis", "result_feedback")
    graph.add_edge("result_feedback", END)
    return graph.compile()

skin_analysis_graph = build_skincare_graph()