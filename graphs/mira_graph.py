from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from state import MiraState
from tools.mira_tools import recognize_intent, multimodal_chat_agent, video_to_text
from graphs.user_profile_creation_graph import user_profile_creation_graph
from graphs.user_profile_edit_graph import user_profile_edit_graph
from graphs.skin_analysis_graph import skin_analysis_graph
from graphs.product_recognition_graph import product_recognition_graph
from graphs.product_recommend_graph import product_recommend_graph
from graphs.care_makeup_guide_graph import care_makeup_guide_graph

# 1. 多模态意图识别与流程调度节点
def mira_router(state: MiraState):
    """
    多模态意图识别与流程调度节点。
    """
    multimodal_text = video_to_text(
        state.profile_input.get("user_text") if state.profile_input else None,
        state.profile_input.get("user_audio") if state.profile_input else None,
        state.profile_input.get("user_video") if state.profile_input else None
    )
    intent = recognize_intent(multimodal_text)
    if intent == "创建用户档案":
        return Command(goto="user_profile_creation_subgraph")
    elif intent == "档案编辑":
        return Command(goto="user_profile_edit_subgraph")
    elif intent == "肤质检测":
        return Command(goto="skin_analysis_subgraph")
    elif intent == "产品推荐":
        return Command(goto="product_recommend_subgraph")
    elif intent == "产品识别":
        return Command(goto="product_recognition_subgraph")
    elif intent in ["化妆引导", "护肤引导"]:
        return Command(goto="care_makeup_guide_subgraph")
    else:
        # 默认进入多模态聊天
        reply = multimodal_chat_agent(multimodal_text)
        new_message = {"role": "assistant", "content": reply}
        return {"messages": (state.messages or []) + [new_message]}

# 2. supervisor 节点，负责多模态聊天和消息追加
def supervisor(state: MiraState):
    multimodal_text = video_to_text(
        state.profile_input.get("user_text") if state.profile_input else None,
        state.profile_input.get("user_audio") if state.profile_input else None,
        state.profile_input.get("user_video") if state.profile_input else None
    )
    reply = multimodal_chat_agent(multimodal_text)
    new_message = {"role": "assistant", "content": reply}
    return {"messages": (state.messages or []) + [new_message]}

# 3. 子流程调用节点（invoke 子图，输入输出严格按 state.py 设计）
def call_user_profile_creation(state: MiraState):
    result = user_profile_creation_graph.invoke(state.profile_input or {})
    return {"profile_result": result, "user_profile": result.get("user_profile")}

def call_user_profile_edit(state: MiraState):
    result = user_profile_edit_graph.invoke(state.profile_input or {})
    return {"profile_result": result, "user_profile": result.get("user_profile")}

def call_skin_analysis(state: MiraState):
    result = skin_analysis_graph.invoke(state.skincare_input or {})
    return {"skincare_result": result, "user_profile": result.get("user_profile")}

def call_product_recognition(state: MiraState):
    result = product_recognition_graph.invoke(state.product_recognition_input or {})
    return {"product_recognition_result": result}

def call_product_recommend(state: MiraState):
    result = product_recommend_graph.invoke(state.product_recommend_input or {})
    return {"product_recommend_result": result}

def call_care_makeup_guide(state: MiraState):
    result = care_makeup_guide_graph.invoke(state.guide_input or {})
    return {"guide_result": result}

# 4. 构建主流程 Graph
def build_main_graph():
    graph = StateGraph(MiraState)
    graph.add_node("mira_router", mira_router)
    graph.add_node("supervisor", supervisor)
    graph.add_node("user_profile_creation_subgraph", call_user_profile_creation)
    graph.add_node("user_profile_edit_subgraph", call_user_profile_edit)
    graph.add_node("skin_analysis_subgraph", call_skin_analysis)
    graph.add_node("product_recognition_subgraph", call_product_recognition)
    graph.add_node("product_recommend_subgraph", call_product_recommend)
    graph.add_node("care_makeup_guide_subgraph", call_care_makeup_guide)

    graph.add_edge(START, "mira_router")
    graph.add_edge("mira_router", "supervisor")
    for subgraph_name in [
        "user_profile_creation_subgraph",
        "user_profile_edit_subgraph",
        "skin_analysis_subgraph",
        "product_recognition_subgraph",
        "product_recommend_subgraph",
        "care_makeup_guide_subgraph"
    ]:
        graph.add_edge(subgraph_name, "supervisor")
    graph.add_edge("supervisor", END)
    return graph.compile()

mira_graph = build_main_graph()