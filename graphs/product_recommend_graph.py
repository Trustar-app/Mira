"""
产品推荐子流程 Graph，节点实现如下。
"""
import logging
from langgraph.graph import StateGraph, END, START
from state import ProductRecommendationState
from langgraph.config import get_stream_writer
from langgraph.types import interrupt

# 1. 推荐需求采集节点
def recommend_intent_node(state: ProductRecommendationState):
    """
    推荐需求采集节点：判断用户是否明确表达推荐需求，未表达则 interrupt 请求输入。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 若无 recommend_category，interrupt 请求用户补充需求
    # 若有，进入下一节点
    logging.info("[recommend_intent_node] called")
    if not state.get("recommend_category"):
        response = interrupt({"type": "interrupt", "content": "请说明你想要推荐哪类产品？"})
        state["recommend_category"] = response
    return state

# 2. 产品检索与智能筛选节点
def product_search_node(state: ProductRecommendationState):
    """
    产品检索与智能筛选节点：基于用户档案、需求、偏好，检索最匹配的产品列表。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 调用 search_recommended_products 工具函数
    # 若检索失败，interrupt 请求用户补充信息
    # 若成功，进入下一节点
    logging.info("[product_search_node] called")
    writer = get_stream_writer()
    # mock: 实际应调用 search_recommended_products 工具
    state["recommended_products"] = [
        {"name": "粉底液A", "brand": "品牌A"},
        {"name": "粉底液B", "brand": "品牌B"}
    ]
    writer({"type": "progress", "content": f"为你找到以下产品：{state['recommended_products']}"})
    return state

# 3. 个性化推荐理由生成节点
def personalized_reason_node(state: ProductRecommendationState):
    """
    个性化推荐理由生成节点：AI基于用户信息和产品特性，生成每个推荐产品的个性化推荐理由。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 调用 generate_personalized_reasons 工具函数
    # 推送推荐结果和理由到前端
    logging.info("[personalized_reason_node] called")
    writer = get_stream_writer()
    # mock: 实际应调用 generate_personalized_reasons 工具
    state["personalized_reasons"] = [
        "粉底液A适合你的肤质，遮瑕力强。",
        "粉底液B轻薄自然，适合日常妆容。"
    ]
    writer({"type": "structure", "content": {"products": state["recommended_products"], "reasons": state["personalized_reasons"]}})
    return state

def build_product_recommend_graph():
    graph = StateGraph(ProductRecommendationState)
    graph.add_node("recommend_intent", recommend_intent_node)
    graph.add_node("product_search", product_search_node)
    graph.add_node("personalized_reason", personalized_reason_node)
    graph.add_edge(START, "recommend_intent")
    graph.add_edge("recommend_intent", "product_search")
    graph.add_edge("product_search", "personalized_reason")
    graph.add_edge("personalized_reason", END)
    return graph.compile()

product_recommend_graph = build_product_recommend_graph()