from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.config import get_stream_writer
from state import MiraState
from tools.mira_tools import recognize_intent, multimodal_chat_agent
from graphs.user_profile_creation_graph import user_profile_creation_graph
from graphs.user_profile_edit_graph import user_profile_edit_graph
from graphs.skin_analysis_graph import skin_analysis_graph
from graphs.product_recognition_graph import product_recognition_graph
from graphs.product_recommend_graph import product_recommend_graph
from graphs.care_makeup_guide_graph import care_makeup_guide_graph

# 1. 多模态意图识别与流程调度节点
def mira(state: MiraState):
    """
    多模态意图识别与流程调度节点。
    """
    writer = get_stream_writer()
    writer({"type": "progress", "content": "正在识别意图..."})
    intent = recognize_intent(state["multimodal_text"])
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
        response = multimodal_chat_agent(state["messages"], streaming=True)
        buffer = ""
        for chunk in response:
            buffer += chunk
            writer({"type": "chat", "content": buffer})
        return {"messages": [AIMessage(content=buffer)]}


# 4. 构建主流程 Graph
def build_main_graph():
    graph = StateGraph(MiraState)
    graph.add_node("mira", mira)
    graph.add_node("user_profile_creation_subgraph", user_profile_creation_graph)
    graph.add_node("user_profile_edit_subgraph", user_profile_edit_graph)
    graph.add_node("skin_analysis_subgraph", skin_analysis_graph)
    graph.add_node("product_recognition_subgraph", product_recognition_graph)
    graph.add_node("product_recommend_subgraph", product_recommend_graph)
    graph.add_node("care_makeup_guide_subgraph", care_makeup_guide_graph)

    graph.add_edge(START, "mira")
    for subgraph_name in [
        "user_profile_creation_subgraph",
        "user_profile_edit_subgraph",
        "skin_analysis_subgraph",
        "product_recognition_subgraph",
        "product_recommend_subgraph",
        "care_makeup_guide_subgraph"
    ]:
        graph.add_edge(subgraph_name, "mira")
    graph.add_edge("mira", END)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)

mira_graph = build_main_graph()