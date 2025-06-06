"""
肤质检测子流程 Graph，节点实现如下。
"""
import os
import base64
from pathlib import Path
from langgraph.graph import StateGraph, END, START
from state import SkinAnalysisState, ConfigState
from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from utils.loggers import MiraLog
from tools.skin_analysis_tools import extract_best_face_frame, skin_analysis, skin_feedback, skin_analysis_by_QwenYi, get_image_base64
from langchain_core.runnables import RunnableConfig

# 1. 输入采集节点
def wait_for_video_node(state: SkinAnalysisState):
    """
    输入采集节点：判断并引导用户上传/录制视频。如果没有视频，通过 interrupt 请求用户干预
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    MiraLog("skin_analysis", f"进入肤质检测子图")

    # 将video转成base64
    if state["messages"][-1].content[0]["type"] != "video_url":
        while True:
            MiraLog("skin_analysis", f"肤质检测的视频输入不存在")
            response = interrupt({"type": "interrupt", "content": "请上传面部视频以进行肤质检测。"})
            video = response.get("video")
            if video and os.path.exists(video):
                break
        try:
            with open(video, "rb") as video_file:
                video_bytes = video_file.read()
                video_base64 = base64.b64encode(video_bytes).decode('utf-8')
                state["current_video_base64"] = video_base64
                MiraLog("skin_analysis", f"视频转换为base64成功，路径: {video}, 转换后长度: {len(video_base64)}")
        except Exception as e:
            MiraLog("skin_analysis", f"视频转换为base64失败: {e}", "ERROR")
    else:
        video_url = state["messages"][-1].content[0]["video_url"]["url"]
        state["current_video_base64"] = video_url
    return state

# 2. 视频分析节点
def video_analysis_node(state: SkinAnalysisState):
    """
    视频有效性分析节点：提取最佳帧并做人脸检测，返回最佳图片。如果提取不到合适的人脸图片，要求重新输入视频。通过 interrupt 请求用户干预。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 调用 extract_best_face_frame，更新 best_face_image/face_detected
    MiraLog("skin_analysis", "进入视频分析节点")
    writer = get_stream_writer()

    while True:
        writer({"type": "progress", "content": "正在提取最佳人脸图片..."})
        best_face_path = extract_best_face_frame(state["current_video_base64"])
        if not best_face_path:
            while True:
                response = interrupt({"type": "interrupt", "content": "未检测到人脸，请重新输入视频。"})
                video = response.get("video")
                if video and os.path.exists(video):
                    break
            try:
                with open(video, "rb") as video_file:
                    video_bytes = video_file.read()
                    video_base64 = base64.b64encode(video_bytes).decode('utf-8')
                    state["current_video_base64"] = video_base64
                    MiraLog("skin_analysis", f"视频转换为base64成功，路径: {video}, 转换后长度: {len(video_base64)}")
            except Exception as e:
                MiraLog("skin_analysis", f"视频转换为base64失败: {e}", "ERROR")
        else:
            break

    state["best_face_path"] = best_face_path
    state["face_detected"] = True
    
    # 转换为base64用于前端展示
    best_face_base64 = get_image_base64(best_face_path)
    if best_face_base64:
        state["best_face_image"] = best_face_base64
    
    return state

# 3. 肤质AI检测节点
def node_skin_analysis(state: SkinAnalysisState, config: RunnableConfig):
    """
    肤质AI检测节点：对图片做肤质分析。
    :param state: 当前 State
    :return: (新 State, 分析报告)
    """
    # 调用肤质分析模型，更新 skin_analysis_result/analysis_report
    MiraLog("skin_analysis", "进入肤质AI检测节点")
    writer = get_stream_writer()
    best_face_path = state["best_face_path"]

    writer({"type": "progress", "content": "正在进行肤质AI检测..."})
    if config["configurable"].get("use_youcam"):
        skin_analysis_result = skin_analysis(best_face_path, config)
    else:
        skin_analysis_result = skin_analysis_by_QwenYi(best_face_path, config)
    state["user_profile"]["skin_quality"] = skin_analysis_result.get("skin_quality")
    state["skin_analysis_result"] = skin_analysis_result
   
    return state

# 4. 结果反馈节点
def node_result_feedback(state: SkinAnalysisState, config: RunnableConfig):
    """
    结果反馈节点：基于分析报告，AI 生成个性化解读。
    :param state: 当前 State
    :param analysis_report: 肤质分析报告
    :return: (新 State, 反馈消息)
    """
    # 生成个性化解读，更新 analysis_report/progress
    MiraLog("skin_analysis", "进入结果反馈节点")
    writer = get_stream_writer()
    writer({"type": "progress", "content": "正在分析检测结果..."})
    response = skin_feedback(state["skin_analysis_result"], config)
    analysis_report = ""
    for chunk in response:
        analysis_report += chunk
        writer({"type": "progress", "content": analysis_report})
    state["analysis_report"] = analysis_report
    
    # 清理临时文件
    if state.get("best_face_path") and os.path.exists(state["best_face_path"]):
        try:
            os.unlink(state["best_face_path"])
        except:
            pass
    
    writer({"type": "final", "content": {
        "response": analysis_report, 
        "markdown": {**state["skin_analysis_result"], "image": state.get("best_face_image")}, 
        "profile": state["user_profile"],
    }})
    return state

def build_skincare_graph():
    graph = StateGraph(SkinAnalysisState, config_schema=ConfigState)
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