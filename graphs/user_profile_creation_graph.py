"""
新用户建档子流程 Graph，节点实现如下。
"""
import logging
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt
from state import UserProfileEditState
from langgraph.config import get_stream_writer
from tools.user_profile_creation_tools import analyze_face_features_with_llm
from langchain_core.messages import AIMessage, HumanMessage
from tools.common.formatters import format_messages
from utils.loggers import MiraLog

# 1. 性别选择节点
def gender_selection_node(state: UserProfileEditState):
    MiraLog("user_profile_creation", "进入创建用户档案子图")
    MiraLog("user_profile_creation", f"节点：性别选择")
    response = interrupt({"type": "interrupt", "content": "请输入你的性别"})
    # 更新 State
    return {
        "user_profile": {"gender": response}, 
        "messages": [
                AIMessage(content={"type": "text", "text": "请输入你的性别"}),
                HumanMessage(content={"type": "text", "text": response})
            ]
    }

# 2. 年龄输入节点
def age_input_node(state: UserProfileEditState):
    MiraLog("user_profile_creation", f"节点：年龄输入")
    response = interrupt({"type": "interrupt", "content": "请输入你的年龄"})
    # 更新 State
    return {
        "user_profile": {"age": response}, 
        "messages": [
            AIMessage(content={"type": "text", "text": "请输入你的年龄"}),
            HumanMessage(content={"type": "text", "text": response})
        ]
    }

# 3. 面部特征采集与分析节点（用 VLM 分析视频）
def face_feature_analysis_node(state: UserProfileEditState):
    MiraLog("user_profile_creation", f"节点：面部特征采集与分析")
    while True:
        response = interrupt({"type": "interrupt", "content": "请上传面部视频以采集五官特征、肤色、肤质"})
        if "video" in response:
            break
        else:
            response = interrupt({"type": "interrupt", "content": "请上传面部视频以采集五官特征、肤色、肤质"})
    video_path = response['video']
    # 工具调用：分析面部特征
    features = analyze_face_features_with_llm(video_path)

    # 更新 State
    return {
        "user_profile": {
            "face_features": features.get("face_features"),
            "skin_color": features.get("skin_color"),
            "skin_quality": features.get("skin_quality")
        },
        "messages": [
            AIMessage(content={"type": "text", "text": "请上传面部视频以采集五官特征、肤色、肤质"}),
            HumanMessage(content={"type": "text", "text": response})
        ]
    }

# 4. 化妆专业度打分节点
def makeup_skill_node(state: UserProfileEditState):
    logging.info("[makeup_skill_node] called")
    response = interrupt({"type": "interrupt", "content": "请给你的化妆专业度打分（0-10分）"})
    return {
        "user_profile": {"makeup_skill_level": response},
        "messages": [
            AIMessage(content={"type": "text", "text": "请给你的化妆专业度打分（0-10分）"}),
            HumanMessage(content={"type": "text", "text": response})
        ]
    }

# 5. 护肤专业度打分节点
def skincare_skill_node(state: UserProfileEditState):
    logging.info("[skincare_skill_node] called")
    response = interrupt({"type": "interrupt", "content": "请给你的护肤专业度打分（0-10分）"})
    return {
        "user_profile": {"skincare_skill_level": response},
        "messages": [
            AIMessage(content={"type": "text", "text": "请给你的护肤专业度打分（0-10分）"}),
            HumanMessage(content={"type": "text", "text": response})
        ]
    }

# 6. 个人诉求与偏好收集节点
def user_preferences_node(state: UserProfileEditState):
    logging.info("[user_preferences_node] called")
    response = interrupt({"type": "interrupt", "content": "请分享你在护肤和化妆中的诉求或偏好"})
    return {
        "user_profile": {"user_preferences": response},
        "messages": [
            AIMessage(content={"type": "text", "text": "请分享你在护肤和化妆中的诉求或偏好"}),
            HumanMessage(content={"type": "text", "text": response})
        ]
    }

# 7. 用户名采集节点
def name_input_node(state: UserProfileEditState):
    logging.info("[name_input_node] called")
    response = interrupt({"type": "interrupt", "content": "请告诉我你的名字"})
    return {
        "user_profile": {"name": response},
        "messages": [
            AIMessage(content={"type": "text", "text": "请告诉我你的名字"}),
            HumanMessage(content={"type": "text", "text": response})
        ]
    }

# 8. 档案生成与保存节点
def profile_generate_node(state: UserProfileEditState):
    logging.info("[profile_generate_node] called")
    writer = get_stream_writer()
    # 汇总所有信息，生成档案
    msg = f"用户档案已生成：{state['user_profile']}"
    writer({"type": "progress", "content": msg})
    writer({"type": "structure", "content": state["user_profile"]})
    return {
        "user_profile": state["user_profile"],
        "messages": [
            AIMessage(content={"type": "text", "text": "用户档案已生成：" + str(state["user_profile"])}),
        ]
    }

# 构建子流程 Graph
def build_user_profile_graph():
    graph = StateGraph(UserProfileEditState)
    graph.add_node("gender_selection", gender_selection_node)
    graph.add_node("age_input", age_input_node)
    graph.add_node("face_feature_analysis", face_feature_analysis_node)
    graph.add_node("makeup_skill", makeup_skill_node)
    graph.add_node("skincare_skill", skincare_skill_node)
    graph.add_node("user_preferences", user_preferences_node)
    graph.add_node("name_input", name_input_node)
    graph.add_node("profile_generate", profile_generate_node)
    # 串联所有节点
    graph.add_edge("gender_selection", "age_input")
    graph.add_edge("age_input", "face_feature_analysis")
    graph.add_edge("face_feature_analysis", "makeup_skill")
    graph.add_edge("makeup_skill", "skincare_skill")
    graph.add_edge("skincare_skill", "user_preferences")
    graph.add_edge("user_preferences", "name_input")
    graph.add_edge("name_input", "profile_generate")
    graph.add_edge("profile_generate", END)
    graph.add_edge(START, "gender_selection")
    return graph.compile()

user_profile_creation_graph = build_user_profile_graph()