"""
新用户建档子流程 Graph，节点实现如下。
"""
import logging
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt
from state import UserProfileEditState
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage

# 明确 user_profile 结构
USER_PROFILE_FIELDS = [
    "name", "gender", "age", "create_time",
    "face_features", "skin_color", "skin_quality", "last_skin_check",
    "makeup_skill_level", "skincare_skill_level", "user_preferences"
]

llm = ChatOpenAI(model="qwen2.5-vl-72b-instruct", streaming=True)

# 1. 性别选择节点
def gender_selection_node(state: UserProfileEditState, stream_writer=None):
    logging.info("[gender_selection_node] called")
    gender = state.user_profile.get("gender") if state.user_profile else None
    if not gender:
        msg = "请选择你的性别（男/女/其他）。"
        return interrupt(msg)
    # 写入 state
    state.user_profile = dict(state.user_profile or {})
    state.user_profile["gender"] = gender
    return state

# 2. 年龄输入节点
def age_input_node(state: UserProfileEditState, stream_writer=None):
    logging.info("[age_input_node] called")
    age = state.user_profile.get("age") if state.user_profile else None
    if not age:
        msg = "请输入你的年龄。"
        return interrupt(msg)
    state.user_profile = dict(state.user_profile or {})
    state.user_profile["age"] = age
    return state

# 3. 面部特征采集与分析节点（用 LLM 分析视频）
def face_feature_analysis_node(state: UserProfileEditState, stream_writer=None):
    logging.info("[face_feature_analysis_node] called")
    video_path = state.user_profile.get("face_video") if state.user_profile else None
    if not video_path:
        msg = "请上传面部视频以采集五官特征、肤色和肤质。"
        return interrupt(msg)
    # 用 LLM 分析视频（假设视频已转为 base64 或路径可直接用）
    prompt = f"请分析用户上传的面部视频，提取五官特征、肤色、肤质，输出JSON，字段包括face_features, skin_color, skin_quality。视频路径：{video_path}"
    messages = [HumanMessage(content=prompt)]
    result = ""
    if stream_writer:
        stream_writer({"progress": "正在分析面部特征..."})
    for chunk in llm.stream(messages):
        if hasattr(chunk, 'content') and chunk.content:
            result += chunk.content
            if stream_writer:
                stream_writer({"messages": chunk.content})
    # 简单解析（实际应用中应做更严格的JSON解析）
    import json
    try:
        features = json.loads(result)
    except Exception:
        msg = "面部分析失败，请重新上传视频。"
        return interrupt(msg)
    state.user_profile = dict(state.user_profile or {})
    state.user_profile["face_features"] = features.get("face_features")
    state.user_profile["skin_color"] = features.get("skin_color")
    state.user_profile["skin_quality"] = features.get("skin_quality")
    return state

# 4. 化妆专业度打分节点
def makeup_skill_node(state: UserProfileEditState, stream_writer=None):
    logging.info("[makeup_skill_node] called")
    makeup_skill = state.user_profile.get("makeup_skill_level") if state.user_profile else None
    if makeup_skill is None:
        msg = "请给你的化妆专业度打分（0-10分）。"
        return interrupt(msg)
    state.user_profile = dict(state.user_profile or {})
    state.user_profile["makeup_skill_level"] = makeup_skill
    return state

# 5. 护肤专业度打分节点
def skincare_skill_node(state: UserProfileEditState, stream_writer=None):
    logging.info("[skincare_skill_node] called")
    skincare_skill = state.user_profile.get("skincare_skill_level") if state.user_profile else None
    if skincare_skill is None:
        msg = "请给你的护肤专业度打分（0-10分）。"
        return interrupt(msg)
    state.user_profile = dict(state.user_profile or {})
    state.user_profile["skincare_skill_level"] = skincare_skill
    return state

# 6. 个人诉求与偏好收集节点
def user_preferences_node(state: UserProfileEditState, stream_writer=None):
    logging.info("[user_preferences_node] called")
    preferences = state.user_profile.get("user_preferences") if state.user_profile else None
    if not preferences:
        msg = "请分享你在护肤和化妆中的诉求或偏好。"
        return interrupt(msg)
    state.user_profile = dict(state.user_profile or {})
    state.user_profile["user_preferences"] = preferences
    return state

# 7. 用户名采集节点
def name_input_node(state: UserProfileEditState, stream_writer=None):
    logging.info("[name_input_node] called")
    name = state.user_profile.get("name") if state.user_profile else None
    if not name:
        msg = "请告诉我你的名字。"
        return interrupt(msg)
    state.user_profile = dict(state.user_profile or {})
    state.user_profile["name"] = name
    return state

# 8. 档案生成与保存节点
def profile_generate_node(state: UserProfileEditState, stream_writer=None):
    logging.info("[profile_generate_node] called")
    # 汇总所有信息，生成档案
    msg = f"用户档案已生成：{state.user_profile}"
    if stream_writer:
        stream_writer({"progress": msg})
    return state

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