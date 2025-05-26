"""
产品识别子流程 Graph，节点实现如下。
"""
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt
from langgraph.prebuilt import ToolNode, InjectedState
from langgraph.config import get_stream_writer
from state import ProductAnalysisState, ConfigState
from utils.loggers import MiraLog
from tools.product_analysis_tools import extract_structured_info_from_search
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Annotated
from langchain_core.runnables import RunnableConfig

system_message = (
    "你是一位私人产品适配度分析专家，你的任务是基于用户提到的产品，完成如下步骤：\n"
    "1. 如果用户没有提供产品信息，请调用 query_user_input 工具，采集用户输入的产品名称或描述。\n"
    "2. 获取用户输入后，调用 tavily_search 工具，检索产品的图片、名称、分类、品牌、成分、功效等信息。\n"
    "3. 在检索到足够的产品信息后，作为语音助手，用温柔的语气向用户简要讲述该产品与用户的适配度分析。\n"
    "4. 分析完成后，调用 add_product_to_directory 工具，询问用户是否将该产品加入个人产品目录。\n"
    "5. 无论用户是否加入，完成后直接结束对话。\n"
    "用户信息如下：\n{user_profile}\n"
)

# 工具模型实例
# llm = ChatOpenAI(
#     model="gpt-4o-2024-11-20",
#     openai_api_base="https://api.ai-gaochao.cn/v1",
#     openai_api_key="sk-OYhuRkOKEQu5YXp107140dC2E1F14dA1AaFe934b9294A10b",
#     streaming=True
# )


class InputCollectionInput(BaseModel):
    query: str = Field(description="你的询问")

@tool("query_user_input", args_schema=InputCollectionInput, return_direct=True)
def input_collection_tool(query: str) -> dict:
    """
    采集用户输入（文本/视频）
    """
    response = interrupt({"type": "interrupt", "content": query})
    content = []
    if response.get("text"):
        content.append({"type": "text", "text": response.get("text")})
    if response.get("video"):
        content.append({"type": "video_url", "video_url": response.get("video")})

    return content

@tool("add_product_to_directory", return_direct=True)
def add_product_to_directory_tool() -> dict:
    """
    用户确认后将产品信息放入目录。
    """
    confirm = interrupt({"type": "interrupt", "content": ""})
    if "是" in confirm.get("text", "").lower():
        return "产品已加入目录"
    else:
        return "产品未加入目录"

def extract_structured_info_node(state: ProductAnalysisState):
    stream_writer = get_stream_writer()
    stream_writer({"type": "progress", "content": "正在抽取产品信息..."})
    structured_info = extract_structured_info_from_search(state["messages"])
    state["product_structured_info"] = structured_info
    stream_writer({"type": "final", "content": {"product": structured_info}})
    return state

class TavilySearchWithConfig(TavilySearch):
    def _run(
        self,
        query: str,
        config: RunnableConfig = None,
        **kwargs
    ):
        # 如果有新的 key，动态替换
        if config and hasattr(config, "tavily_api_key"):
            self.api_wrapper.tavily_api_key = config.tavily_api_key
        # 调用父类 _run
        return super()._run(query, **kwargs)

tool_search = TavilySearchWithConfig(
    max_results=5
)

tool_node = ToolNode(
    tools=[tool_search, input_collection_tool, add_product_to_directory_tool],
    handle_tool_errors=True
)


def chatbot(state: ProductAnalysisState, config: RunnableConfig):
    MiraLog("product_analysis", "进入产品分析聊天机器人")
    stream_writer = get_stream_writer()

    llm = ChatOpenAI(
        model=config.chat_model_name,
        openai_api_base=config.chat_api_base,
        openai_api_key=config.chat_api_key,
        streaming=True
    )
    llm_with_tools = llm.bind_tools([tool_search, input_collection_tool, add_product_to_directory_tool])
    messages = [
        SystemMessage(content=system_message.format(user_profile=state["user_profile"])),
        *state["messages"]
    ]
    stream_writer({"type": "progress", "content": "正在理解产品需求..."})
    content_buffer = ""
    first_chunk = True
    for chunk in llm_with_tools.stream(messages):
        if hasattr(chunk, "content") and chunk.content:
            content_buffer += chunk.content
            stream_writer({"type": "progress", "content": content_buffer})
        if first_chunk:
            buffer = chunk
            first_chunk = False
        else:
            buffer = buffer + chunk 

    if content_buffer:
        stream_writer({"type": "final", "content": {"response": content_buffer}})
    return {"messages": buffer}

    
# 构建子流程 Graph
def tool_condition(state: ProductAnalysisState):
    if messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError("没有找到 AI 消息")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        # 如果是 tavily_search 工具调用，则用 writer 输出进度
        if ai_message.tool_calls[0]['name'] == "tavily_search":
            stream_writer = get_stream_writer()
            stream_writer({"type": "progress", "content": "正在检索产品信息..."})
        return "tools"
    return END

def tool_post_condition(state: ProductAnalysisState):
    # 获取最近一条 ToolMessage
    messages = state.get("messages", [])
    if not messages:
        return "chatbot"
    last_msg = messages[-1]
    # 判断是否是 add_product_to_directory_tool 的 ToolMessage
    tool_name = None
    tool_content = None
    if hasattr(last_msg, "name"):
        tool_name = last_msg.name
    elif isinstance(last_msg, dict) and "name" in last_msg:
        tool_name = last_msg["name"]
    if hasattr(last_msg, "content"):
        tool_content = last_msg.content
    elif isinstance(last_msg, dict) and "content" in last_msg:
        tool_content = last_msg["content"]
    if tool_name == "add_product_to_directory" and tool_content == "产品已加入目录":
        return "extract_structured_info_node"
    return "chatbot"

def build_product_graph():
    graph = StateGraph(ProductAnalysisState, config_schema=ConfigState)
    # 主要节点
    graph.add_node("chatbot", chatbot)    
    graph.add_node("tools", tool_node)
    graph.add_node("extract_structured_info_node", extract_structured_info_node)

    graph.add_conditional_edges(
        "chatbot",
        tool_condition,
        {
            "tools": "tools",
            END: END
        }
    )
    graph.add_conditional_edges(
        "tools",
        tool_post_condition,
        {
            "extract_structured_info_node": "extract_structured_info_node",
            "chatbot": "chatbot"
        }
    )
    graph.add_edge("extract_structured_info_node", "chatbot")
    graph.add_edge(START, "chatbot")
    return graph.compile()

product_analysis_graph = build_product_graph()