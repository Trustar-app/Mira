"""
用户档案编辑子流程 Graph，节点实现如下。
"""
import logging
from langgraph.graph import StateGraph, END, START
from state import UserProfileEditState
from langgraph.config import get_stream_writer
from langgraph.types import interrupt

# 1. 编辑意图识别节点
def edit_intent_node(state: UserProfileEditState):
    """
    编辑意图识别节点：识别用户想要编辑的字段，未明确则 interrupt 请求用户说明要修改什么。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 若无 edit_field，interrupt 请求用户输入
    # 若有，进入字段输入节点
    logging.info("[edit_intent_node] called")
    if not state.get("edit_field"):
        response = interrupt({"type": "interrupt", "content": "请说明你要修改的档案字段（如年龄、昵称等）。"})
        state["edit_field"] = response
    return state

# 2. 字段输入节点
def field_input_node(state: UserProfileEditState):
    """
    字段输入节点：根据 edit_field，动态生成输入提示，等待用户输入新值。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 若无 edit_value，interrupt 请求用户输入
    # 若有，进入确认保存节点
    logging.info("[field_input_node] called")
    if not state.get("edit_value"):
        response = interrupt({"type": "interrupt", "content": f"请输入新的{state.get('edit_field', '信息')}。"})
        state["edit_value"] = response
    return state

# 3. 确认保存节点
def confirm_save_node(state: UserProfileEditState):
    """
    确认保存节点：展示修改前后内容，询问用户是否确认保存。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 若无 internal["confirm"]，interrupt 请求用户确认
    # 若确认，进入保存节点；否则回到 edit_intent_node
    logging.info("[confirm_save_node] called")
    writer = get_stream_writer()
    # 展示修改前后内容
    before = state.get("user_profile", {}).get(state["edit_field"], "未设置")
    after = state["edit_value"]
    writer({"type": "progress", "content": f"你将把{state['edit_field']}从{before}修改为{after}，是否确认？"})
    response = interrupt({"type": "interrupt", "content": "请确认是否保存更改（是/否）。"})
    # mock: 只要有响应就进入保存
    state["confirm"] = response
    return state

# 4. 保存节点
def save_node(state: UserProfileEditState):
    """
    保存节点：将 edit_value 写入对应字段，更新档案。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # setattr(state, state.edit_field, state.edit_value)
    logging.info("[save_node] called")
    writer = get_stream_writer()
    # mock: 实际应将 edit_value 写入 user_profile
    state["user_profile"] = dict(state.get("user_profile") or {})
    state["user_profile"][state["edit_field"]] = state["edit_value"]
    writer({"type": "structure", "content": state["user_profile"]})
    return state

def build_user_profile_edit_graph():
    graph = StateGraph(UserProfileEditState)
    graph.add_node("edit_intent", edit_intent_node)
    graph.add_node("field_input", field_input_node)
    graph.add_node("confirm_save", confirm_save_node)
    graph.add_node("save", save_node)
    graph.add_edge(START, "edit_intent")
    graph.add_edge("edit_intent", "field_input")
    graph.add_edge("field_input", "confirm_save")
    graph.add_edge("confirm_save", "save")
    graph.add_edge("save", END)
    return graph.compile()

user_profile_edit_graph = build_user_profile_edit_graph()