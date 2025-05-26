"""
护肤/化妆引导子流程 Graph，节点实现如下。
"""
from langgraph.graph import StateGraph, END, START
from state import CareMakeupGuideState, ConfigState
from langgraph.config import get_stream_writer
from langgraph.types import interrupt
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.prebuilt import InjectedState, ToolNode
from typing import Annotated
from langgraph.types import Command
from pydantic import BaseModel, Field

@tool("generate_plan", return_direct=True, response_format="content_and_artifact")
def generate_plan(state: Annotated[dict, InjectedState], config: RunnableConfig):
    """
    生成护肤/化妆计划
    """
    system_prompt = (
        "你是一位专业的护肤与化妆计划生成助手。\n\n"
        "请根据用户信息、产品收藏夹和用户历史对话，生成一份个性化的护肤或化妆方案。\n"
        "返回的计划应包含以下字段，并以 **JSON 格式** 输出：\n"
        "{{\n"
        '  "type": "护肤" 或 "化妆",\n'
        '  "steps": [\n'
        "    {{\n"
        '      "step_name": "步骤名称",\n'
        '      "product_type": "产品种类，如洁面、爽肤水、粉底液等",\n'
        '      "instructions": "操作说明",\n'
        '      "notes": "注意事项"\n'
        "    }},\n"
        "    ... // 其他步骤\n"
        "  ]\n"
        "}}\n"
        "```\n\n"
        "【用户信息】：{user_profile}\n"
        "【产品收藏夹】：{products_directory}\n"
        "{plan_section}"
    ).format(
        user_profile=state.get("user_profile", "无"),
        products_directory=state.get("products_directory", "无"),
        plan_section=f"【当前计划】：{state['plan']}\n" if state.get("plan") else ""
    )
    llm = ChatOpenAI(
        model=config.chat_model_name,
        openai_api_base=config.chat_api_base,
        openai_api_key=config.chat_api_key,
        streaming=False
    ).with_structured_output(method="json_mode")
    msg = "完成计划生成，请向用户简要说明当前计划内容，并请求确认" if not state.get("plan") else "生成新计划，请向用户简要说明计划内容，并请求确认"
    response = llm.invoke([SystemMessage(content=system_prompt)] + state.get("messages", []))
    
    return msg, {"plan": response}

class InputCollectionInput(BaseModel):
    query: str = Field(description="你对用户的请求或询问")

@tool("request_user_input", args_schema=InputCollectionInput, return_direct=True)
def request_user_input(query: str):
    """
    请求用户输入
    """
    response = interrupt({"type": "interrupt", "content": query})
    content = []
    if response.get("text"):
        content.append({"type": "text", "text": response.get("text")})
    if response.get("video"):
        content.append({"type": "video_url", "video_url": response.get("video")})
    return content

tool_node = ToolNode(
    tools=[generate_plan, request_user_input],
    handle_tool_errors=False
)

# 节点实现
def chatbot(state: CareMakeupGuideState, config: RunnableConfig):
    stream_writer = get_stream_writer()
    # 构建系统 prompt
    system_prompt = (
        "你是一位专业的护肤与化妆指导助手，负责根据用户的具体需求和个人信息提供个性化方案。\n\n"
        "请遵循以下流程完成你的任务：\n"
        "1. 如果用户尚未提出明确需求，请调用 request_user_input 工具引导其简要说明当前需求（如：约会妆容、日常护肤、特殊场合等）。\n"
        "2. 一旦获取到简要的需求，就请调用 generate_plan 工具为其制定一套完整的护肤或化妆方案，不要多轮询问用户需求，请直接生成方案。\n"
        "3. 列出完整方案后，请调用 request_user_input 工具征询用户是否确认：\n"
        "   - 若确认，则进入逐步引导流程；\n"
        "   - 若不确认，请根据用户反馈重新调用 generate_plan 工具制定方案。\n"
        "4. 在逐步引导过程中：\n"
        "   - 每一步都需提示用户上传视频；\n"
        "   - 针对上传内容给予专业反馈，并继续下一步。\n"
        "5. 全部步骤完成后，请对整个体验进行总结，并给予积极鼓励。\n\n"
        "每次只能调用一个工具。"
        "以下是当前计划(如果还未生成计划，请忽略)：\n"
        "{plan}\n"
    ).format(
        plan=state.get("plan", "无")
    )
    messages = [SystemMessage(content=system_prompt), *state.get("messages", [])]
    stream_writer({"type": "progress", "content": "正在分析用户输入..."})
    content_buffer = ""
    first_chunk = True
    llm = ChatOpenAI(
        model="qwen3-235b-a22b",
        openai_api_base=config.chat_api_base,
        openai_api_key=config.chat_api_key,
        streaming=True
    )
    llm_with_tools = llm.bind_tools([generate_plan, request_user_input])
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

def post_tool_node(state: CareMakeupGuideState):
    writer = get_stream_writer()
    tool_message = state.get("messages", [])[-1]
    if hasattr(tool_message, "artifact") and tool_message.artifact:
        writer({"type": "final", "content": {"markdown": tool_message.artifact}})
        return {**tool_message.artifact}


def chatbot_condition(state: CareMakeupGuideState):
    writer = get_stream_writer()
    messages = state.get("messages", [])
    if not messages:
        return END
    last_msg = messages[-1]
    # 判断是否有 tool_call
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        tool_name = last_msg.tool_calls[0]['name']
        if tool_name == "generate_plan":
            writer({"type": "progress", "content": "正在生成计划..."})
        return "tool_node"
    return END  # 或下一个节点

def build_care_makeup_guide_graph():
    graph = StateGraph(CareMakeupGuideState, config_schema=ConfigState)
    graph.add_node("chatbot", chatbot)
    graph.add_node("tool_node", tool_node)
    graph.add_node("post_tool_node", post_tool_node)

    graph.add_edge(START, "chatbot")
    graph.add_conditional_edges("chatbot", chatbot_condition, {
        "tool_node": "tool_node",
        END: END
    })
    graph.add_edge("tool_node", "post_tool_node")
    graph.add_edge("post_tool_node", "chatbot")
    return graph.compile()

care_makeup_guide_graph = build_care_makeup_guide_graph()