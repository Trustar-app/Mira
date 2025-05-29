"""
产品识别子流程 Graph，节点实现如下。
"""
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END, START
from langgraph.types import interrupt
from langgraph.prebuilt import ToolNode, InjectedState
from langgraph.config import get_stream_writer
from state import ProductAnalysisState, ConfigState
from utils.loggers import MiraLog
from tools.product_analysis_tools import extract_structured_info_from_search
from tools.common.formatters import format_user_info
from langchain_core.tools import tool, InjectedToolCallId
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from typing_extensions import Annotated


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
def add_product_to_directory_tool(state: Annotated[dict, InjectedState], config: RunnableConfig, tool_call_id: Annotated[str, InjectedToolCallId]) -> dict:
    """
    将产品信息放入目录。
    """
    stream_writer = get_stream_writer()
    stream_writer({"type": "progress", "content": "正在抽取产品信息..."})
    structured_info = extract_structured_info_from_search(state["messages"][-6:], config)
    stream_writer({"type": "final", "content": {"product": structured_info}})
    return Command(
        update={
            "messages": [ToolMessage(content="产品已加入目录", tool_call_id=tool_call_id)],
            "product_structured_info": structured_info
        }
    )


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
    tools=[tool_search, add_product_to_directory_tool],
    handle_tool_errors=True
)


def chatbot(state: ProductAnalysisState, config: RunnableConfig):
    MiraLog("product_analysis", "进入产品分析聊天机器人")
    stream_writer = get_stream_writer()
    
    # 获取角色设定
    character_setting = config["configurable"].get("character_setting", {})
    
    # 格式化用户信息和产品目录
    formatted_info = format_user_info(state.get("user_profile", {}), state.get("products_directory", []))
    
    system_message = (
        f"你是 {character_setting['name']}，一个专业的美妆顾问和心理陪伴师。\n\n"
        f"【角色设定】\n"
        f"性格特点：{character_setting['personality']}\n"
        f"语气特点：{character_setting['tone']}\n"
        f"专业领域：{character_setting['expertise']}\n"
        f"互动风格：{character_setting['interaction_style']}\n\n"
        "【任务说明】\n"
        "你现在是一位全能的产品分析专家，需要根据用户的不同需求提供相应的分析和建议：\n\n"
        "1. 产品推荐场景\n"
        "- 理解用户的具体需求（如肤质、使用场景等）\n"
        "- 基于需求推荐合适的产品，并解释推荐理由\n\n"
        "2. 产品识别场景\n"
        "- 识别用户提到的产品信息\n"
        "- 提供产品的基本信息（品牌、功效、特点等）\n\n"
        "3. 成分分析场景\n"
        "- 分析产品成分表\n"
        "- 评估产品是否适合用户\n"
        "- 提醒潜在的使用注意事项\n\n"
        "【执行步骤】\n"
        "1. 如果用户没有提供足够信息，请询问用户的需求或需要识别的产品的信息。\n"
        "2. 获取用户输入后，调用 tavily_search 工具，检索产品的图片、名称、分类、品牌、成分、功效等信息。\n"
        "3. 在检索到足够的产品信息后，作为语音助手，用温柔的语气向用户简要讲述产品与用户的适配度分析，并询问用户是否需要将该产品加入个人产品目录。\n"
        "4. 如果用户确认加入，则调用 add_product_to_directory 工具，将产品信息放入目录。\n"
        "5. 无论用户是否加入，完成后直接结束对话。\n\n"
        "【回复要求】\n"
        "1. 所有回复必须简短、口语化，适合语音播报\n"
        "2. 不要使用分点列举的形式回答\n"
        "3. 不要在回复中包含图片URL或其他非自然语言的内容\n"
        "4. 每次回复控制在100字以内\n"
        "5. 使用自然的语气助词和语气词，让对话更生动\n\n"
        f"{formatted_info}"
    )

    llm = ChatOpenAI(
        model=config["configurable"].get("chat_model_name"),
        openai_api_base=config["configurable"].get("chat_api_base"),
        openai_api_key=config["configurable"].get("chat_api_key"),
        streaming=True
    )
    llm_with_tools = llm.bind_tools([tool_search, add_product_to_directory_tool])
    messages = [
        SystemMessage(content=system_message),
        *state["messages"]
    ]
    stream_writer({"type": "progress", "content": "正在分析..."})
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

def tool_post_node(state: ProductAnalysisState):
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

    # 调用 tavily_search 工具后，展示检索结果
    if tool_name == "tavily_search":
        import json
        content = json.loads(last_msg.content)
        stream_writer = get_stream_writer()
        stream_writer({"type": "final", "content": {"markdown": content}})

    return state

def build_product_graph():
    graph = StateGraph(ProductAnalysisState, config_schema=ConfigState)
    # 主要节点
    graph.add_node("chatbot", chatbot)    
    graph.add_node("tools", tool_node)
    graph.add_node("tool_post", tool_post_node)

    graph.add_conditional_edges(
        "chatbot",
        tool_condition,
        {
            "tools": "tools",
            END: END
        }
    )

    graph.add_edge(START, "chatbot")
    graph.add_edge("tools", "tool_post")
    graph.add_edge("tool_post", "chatbot")
    return graph.compile()

product_analysis_graph = build_product_graph()