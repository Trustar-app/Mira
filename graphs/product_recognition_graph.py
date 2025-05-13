"""
产品识别子流程 Graph，节点实现如下。
"""
import logging
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt
from state import ProductRecognitionState

# 工具模型实例
llm_tool = ChatOpenAI(
    model="qwen2.5-vl-72b-instruct",
    streaming=True
)

# 1. 输入采集节点（支持 human-in-the-loop）
def input_collection_node(state: ProductRecognitionState, stream_writer=None):
    """
    判断输入是否包含有效产品视频/文本，若无则 human-in-the-loop。
    """
    logging.info("[input_collection_node] called")
    if not (state.user_video or state.user_text):
        msg = "请上传产品视频，或输入产品名称/条码。"
        if stream_writer:
            stream_writer({"progress": msg})
        return interrupt(msg)
    if stream_writer:
        stream_writer({"progress": "已收到产品输入，正在处理..."})
    return state

# 2. 产品信息提取与识别节点（human-in-the-loop + 工具调用 + stream）
def product_info_extraction_node(state: ProductRecognitionState, stream_writer=None):
    """
    AI识别视频/文本，提取产品关键信息。
    """
    logging.info("[product_info_extraction_node] called")
    prompt = "请从以下用户输入中提取产品关键信息（如品牌、品名、型号、条码等），以JSON格式输出：\n"
    if state.user_text:
        prompt += f"文本：{state.user_text}\n"
    if state.user_video:
        prompt += f"视频已上传。\n"
    messages = [HumanMessage(content=prompt)]
    product_info = ""
    if stream_writer:
        stream_writer({"progress": "正在识别产品信息..."})
    for chunk in llm_tool.stream(messages):
        if hasattr(chunk, 'content') and chunk.content:
            product_info += chunk.content
            if stream_writer:
                stream_writer({"messages": chunk.content})
    # 简单判断是否识别成功
    if not product_info or "未识别" in product_info or len(product_info.strip()) < 5:
        msg = "未能识别该产品，请重新上传或输入更清晰的信息。"
        if stream_writer:
            stream_writer({"progress": msg})
        return interrupt(msg)
    state.product_raw_info = product_info
    return state

# 3. 产品信息搜索节点（工具调用，stream）
def product_info_search_node(state: ProductRecognitionState, stream_writer=None):
    """
    基于提取出的产品信息，通过网络搜索，获取结构化信息。
    """
    logging.info("[product_info_search_node] called")
    prompt = f"请根据以下产品关键信息，检索并补全产品结构化信息（如品牌、品名、图片、条码等），以JSON格式输出：\n{state.product_raw_info}"
    messages = [HumanMessage(content=prompt)]
    search_result = ""
    if stream_writer:
        stream_writer({"progress": "正在检索产品结构化信息..."})
    for chunk in llm_tool.stream(messages):
        if hasattr(chunk, 'content') and chunk.content:
            search_result += chunk.content
            if stream_writer:
                stream_writer({"messages": chunk.content})
    state.product_structured_info = search_result
    return state

# 4. 结果反馈与收藏节点（参考 skin_feedback，stream）
def product_analysis_node(state: ProductRecognitionState, stream_writer=None):
    """
    AI分析产品适配性，生成个性化解读。
    """
    logging.info("[product_analysis_node] called")
    prompt = (
        "你是一个专业的美妆顾问，请根据用户档案和产品信息，生成如下内容：\n"
        "1. 产品适配性分析（如：该产品适合你的肤质/需求...）\n"
        "2. 个性化推荐理由和使用建议\n"
        "3. 情感鼓励和互动引导\n"
        "请用简洁、温暖的中文输出。\n"
        f"用户档案：{state.user_profile}\n产品信息：{state.product_structured_info}"
    )
    messages = [SystemMessage(content=prompt), HumanMessage(content="请生成反馈")]
    feedback = ""
    if stream_writer:
        stream_writer({"progress": "正在生成产品分析反馈..."})
    for chunk in llm_tool.stream(messages):
        if hasattr(chunk, 'content') and chunk.content:
            feedback += chunk.content
            if stream_writer:
                stream_writer({"messages": chunk.content})
    state.product_analysis = feedback
    return state

# 5. 构建子流程 Graph

def build_product_graph():
    """
    构建产品识别子流程 Graph，注册所有节点与分支。
    :return: LangGraph Subgraph 实例
    """
    graph = StateGraph(ProductRecognitionState)
    graph.add_node("input_collection", input_collection_node)
    graph.add_node("product_info_extraction", product_info_extraction_node)
    graph.add_node("product_info_search", product_info_search_node)
    graph.add_node("product_analysis", product_analysis_node)
    # 边：input->info_extraction->info_search->analysis->END
    graph.add_edge("input_collection", "product_info_extraction")
    graph.add_edge("product_info_extraction", "product_info_search")
    graph.add_edge("product_info_search", "product_analysis")
    graph.add_edge("product_analysis", END)
    graph.add_edge(START, "input_collection")
    return graph.compile()

product_recognition_graph = build_product_graph()