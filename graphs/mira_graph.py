from langgraph.graph import StateGraph, START, END, Command
from state import MiraState
from tools.mira_tools import aggregate_multimodal_text, recognize_intent, multimodal_chat_agent

def mira(state: MiraState):
    """
    多模态意图识别与流程调度节点。
    """
    multimodal_text = aggregate_multimodal_text(state.user_text, state.user_audio, state.user_video)
    intent = recognize_intent(multimodal_text)
    if intent == "profile":
        return Command(goto="user_profile_subgraph")
    elif intent == "skincare":
        return Command(goto="skincare_subgraph")
    elif intent == "product_recommend":
        return Command(goto="product_recommend_subgraph")
    elif intent == "product_recognition":
        return Command(goto="product_recognition_subgraph")
    elif intent == "care_makeup_guide":
        return Command(goto="care_makeup_guide_subgraph")
    else:
        # 默认进入多模态聊天
        reply = multimodal_chat_agent(state)
        new_message = {"role": "assistant", "content": reply}
        return {"messages": (state.messages or []) + [new_message]}

def build_main_graph():
    graph = StateGraph(MiraState)
    graph.add_node("mira", mira)
    graph.add_node("user_profile_subgraph", user_profile_subgraph)
    graph.add_node("skincare_subgraph", skincare_subgraph)
    graph.add_node("product_recommend_subgraph", product_recommend_subgraph)
    graph.add_node("product_recognition_subgraph", product_recognition_subgraph)
    graph.add_node("care_makeup_guide_subgraph", care_makeup_guide_subgraph)

    graph.add_edge(START, "supervisor")
    for subgraph_name in [
        "user_profile_subgraph",
        "skincare_subgraph",
        "product_recommend_subgraph",
        "product_recognition_subgraph",
        "care_makeup_guide_subgraph"
    ]:
        graph.add_edge(subgraph_name, "supervisor")
    graph.add_edge("supervisor", END)
    return graph.compile()

mira_graph = build_main_graph()