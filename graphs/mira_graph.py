from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.config import get_stream_writer
from state import MiraState
from tools.mira_tools import recognize_intent_with_current_flow, multimodal_chat_agent, recognize_intent
from graphs.user_profile_creation_graph import user_profile_creation_graph
from graphs.user_profile_edit_graph import user_profile_edit_graph
from graphs.skin_analysis_graph import skin_analysis_graph
from graphs.product_recognition_graph import product_recognition_graph
from graphs.product_recommend_graph import product_recommend_graph
from graphs.care_makeup_guide_graph import care_makeup_guide_graph
from utils.loggers import MiraLog
from typing_extensions import Literal

current_flow = None

intent_to_subgraph = {
    "创建用户档案": "user_profile_creation_subgraph",
    "档案编辑": "user_profile_edit_subgraph",
    "肤质检测": "skin_analysis_subgraph",
    "产品推荐": "product_recommend_subgraph",
    "产品识别": "product_recognition_subgraph",
    "化妆引导": "care_makeup_guide_subgraph",
    "护肤引导": "care_makeup_guide_subgraph",
}

# 多模态意图识别与流程调度节点
def mira(state: MiraState) -> Command[Literal["user_profile_creation_subgraph", "user_profile_edit_subgraph", "skin_analysis_subgraph", "product_recommend_subgraph", "product_recognition_subgraph", "care_makeup_guide_subgraph"]]:
    """
    多模态意图识别与流程调度节点。
    """
    writer = get_stream_writer()
    writer({"type": "progress", "content": "正在识别意图..."})
    intent = recognize_intent(state["multimodal_text"])
    MiraLog("mira_graph", f"意图识别结果: {intent}")
    
    if intent in intent_to_subgraph:
        return Command(goto=intent_to_subgraph[intent], update={"current_flow": intent})
    else:
        response = multimodal_chat_agent(state["messages"], streaming=True)
        buffer = ""
        for chunk in response:
            buffer += chunk
            writer({"type": "progress", "content": buffer})
        writer({"type": "final", "content": {"response": buffer}})
        return {"messages": [AIMessage(content=buffer)]}


# 构建主流程 Graph
def build_main_graph():
    graph = StateGraph(MiraState)
    graph.add_node("mira", mira)
    graph.add_node("user_profile_creation_subgraph", call_user_profile_creation_subgraph)
    graph.add_node("user_profile_edit_subgraph", call_user_profile_edit_subgraph)
    graph.add_node("skin_analysis_subgraph", call_skin_analysis_subgraph)
    graph.add_node("product_recognition_subgraph", call_product_recognition_subgraph)
    graph.add_node("product_recommend_subgraph", call_product_recommend_subgraph)
    graph.add_node("care_makeup_guide_subgraph", call_care_makeup_guide_subgraph)

    graph.add_edge(START, "mira")
    for subgraph_name in [
        "user_profile_creation_subgraph",
        "user_profile_edit_subgraph",
        "skin_analysis_subgraph",
        "product_recognition_subgraph",
        "product_recommend_subgraph",
        "care_makeup_guide_subgraph"
    ]:
        graph.add_edge(subgraph_name, END)
    graph.add_edge("mira", END)

    memory = MemorySaver()
    return graph.compile(checkpointer=memory)

def call_skin_analysis_subgraph(state: MiraState):
    if state.get("resume", False):
        intent = recognize_intent_with_current_flow(state["multimodal_text"], state.get("current_flow"))
        if intent != state.get("current_flow"):
            return Command(goto=intent_to_subgraph[intent], update={"current_flow": intent, "resume": False})

    subgraph_input = {
        "user_profile": state.get("user_profile"),
        "products_directory": state.get("products_directory"),
        "messages": state.get("messages", []),
        "current_text": state.get("current_text"),
        "current_audio": state.get("current_audio"),
        "current_video": state.get("current_video"),
        "multimodal_text": state.get("multimodal_text"),
    }
    subgraph_output = skin_analysis_graph.invoke(subgraph_input)
    return {
        "user_profile": subgraph_output.get("user_profile"),
        "products_directory": subgraph_output.get("products_directory"),
        "messages": subgraph_output.get("messages"),
        "current_text": subgraph_output.get("current_text"),
        "current_audio": subgraph_output.get("current_audio"),
        "current_video": subgraph_output.get("current_video"),
        "multimodal_text": subgraph_output.get("multimodal_text"),
        # "skin_analysis_result": subgraph_output.get("skin_analysis_result"),
        # "analysis_report": subgraph_output.get("analysis_report"),
    }

def call_user_profile_edit_subgraph(state: MiraState):
    if state.get("resume", False):
        intent = recognize_intent_with_current_flow(state["multimodal_text"], state.get("current_flow"))
        if intent != state.get("current_flow"):
            return Command(goto=intent_to_subgraph[intent], update={"current_flow": intent, "resume": False})
        
    subgraph_input = {
        "user_profile": state.get("user_profile"),
        "products_directory": state.get("products_directory"),
        "messages": state.get("messages", []),
        "current_text": state.get("current_text"),
        "current_audio": state.get("current_audio"),
        "current_video": state.get("current_video"),
        "multimodal_text": state.get("multimodal_text"),
    }
    subgraph_output = user_profile_edit_graph.invoke(subgraph_input)
    return {
        "user_profile": subgraph_output.get("user_profile"),
        "products_directory": subgraph_output.get("products_directory"),
        "messages": subgraph_output.get("messages"),
        "current_text": subgraph_output.get("current_text"),
        "current_audio": subgraph_output.get("current_audio"),
        "current_video": subgraph_output.get("current_video"),
        "multimodal_text": subgraph_output.get("multimodal_text"),
    }

def call_care_makeup_guide_subgraph(state: MiraState):
    if state.get("resume", False):
        intent = recognize_intent_with_current_flow(state["multimodal_text"], state.get("current_flow"))
        if intent != state.get("current_flow"):
            return Command(goto=intent_to_subgraph[intent], update={"current_flow": intent, "resume": False})
        
    subgraph_input = {
        "user_profile": state.get("user_profile"),
        "products_directory": state.get("products_directory"),
        "messages": state.get("messages", []),
        "current_text": state.get("current_text"),
        "current_audio": state.get("current_audio"),
        "current_video": state.get("current_video"),
        "multimodal_text": state.get("multimodal_text"),
    }
    subgraph_output = care_makeup_guide_graph.invoke(subgraph_input)
    return {
        "user_profile": subgraph_output.get("user_profile"),
        "products_directory": subgraph_output.get("products_directory"),
        "messages": subgraph_output.get("messages"),
        "current_text": subgraph_output.get("current_text"),
        "current_audio": subgraph_output.get("current_audio"),
        "current_video": subgraph_output.get("current_video"),
        "multimodal_text": subgraph_output.get("multimodal_text"),
    }

def call_product_recognition_subgraph(state: MiraState):
    if state.get("resume", False):
        intent = recognize_intent_with_current_flow(state["multimodal_text"], state.get("current_flow"))
        if intent != state.get("current_flow"):
            return Command(goto=intent_to_subgraph[intent], update={"current_flow": intent, "resume": False})
        
    subgraph_input = {
        "user_profile": state.get("user_profile"),
        "products_directory": state.get("products_directory"),
        "messages": state.get("messages", []),
        "current_text": state.get("current_text"),
        "current_audio": state.get("current_audio"),
        "current_video": state.get("current_video"),
        "multimodal_text": state.get("multimodal_text"),
    }
    subgraph_output = product_recognition_graph.invoke(subgraph_input)
    return {
        "user_profile": subgraph_output.get("user_profile"),
        "products_directory": subgraph_output.get("products_directory"),
        "messages": subgraph_output.get("messages"),
        "current_text": subgraph_output.get("current_text"),
        "current_audio": subgraph_output.get("current_audio"),
        "current_video": subgraph_output.get("current_video"),
        "multimodal_text": subgraph_output.get("multimodal_text"),
    }
    
def call_product_recommend_subgraph(state: MiraState):
    if state.get("resume", False):
        intent = recognize_intent_with_current_flow(state["multimodal_text"], state.get("current_flow"))
        if intent != state.get("current_flow"):
            return Command(goto=intent_to_subgraph[intent], update={"current_flow": intent, "resume": False})
        
    subgraph_input = {
        "user_profile": state.get("user_profile"),
        "products_directory": state.get("products_directory"),
        "messages": state.get("messages", []),
        "current_text": state.get("current_text"),
        "current_audio": state.get("current_audio"),
        "current_video": state.get("current_video"),
        "multimodal_text": state.get("multimodal_text"),
    }
    subgraph_output = product_recommend_graph.invoke(subgraph_input)
    return {
        "user_profile": subgraph_output.get("user_profile"),
        "products_directory": subgraph_output.get("products_directory"),
        "messages": subgraph_output.get("messages"),
        "current_text": subgraph_output.get("current_text"),
        "current_audio": subgraph_output.get("current_audio"),
        "current_video": subgraph_output.get("current_video"),
        "multimodal_text": subgraph_output.get("multimodal_text"),
    }

def call_user_profile_creation_subgraph(state: MiraState):
    if state.get("resume", False):
        intent = recognize_intent_with_current_flow(state["multimodal_text"], state.get("current_flow"))
        if intent != state.get("current_flow"):
            return Command(goto=intent_to_subgraph[intent], update={"current_flow": intent, "resume": False})
        
    subgraph_input = {
        "user_profile": state.get("user_profile"),
        "products_directory": state.get("products_directory"),
        "messages": state.get("messages", []),
        "current_text": state.get("current_text"),
        "current_audio": state.get("current_audio"),
        "current_video": state.get("current_video"),
        "multimodal_text": state.get("multimodal_text"),
    }
    subgraph_output = user_profile_creation_graph.invoke(subgraph_input)
    return {
        "user_profile": subgraph_output.get("user_profile"),
        "products_directory": subgraph_output.get("products_directory"),
        "messages": subgraph_output.get("messages"),
        "current_text": subgraph_output.get("current_text"),
        "current_audio": subgraph_output.get("current_audio"),
        "current_video": subgraph_output.get("current_video"),
        "multimodal_text": subgraph_output.get("multimodal_text"),
    }

mira_graph = build_main_graph()