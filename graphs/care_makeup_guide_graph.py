"""
护肤/化妆引导子流程 Graph，节点实现如下。
"""
import logging
from langgraph.graph import StateGraph, END, START
from state import CareMakeupGuideState
from langgraph.config import get_stream_writer
from langgraph.types import interrupt

# 1. 用户需求采集节点
def user_intent_node(state: CareMakeupGuideState):
    """
    用户需求采集节点：判断用户是否明确表达需求，未表达则 interrupt 请求输入。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 若无 user_intent，则 interrupt
    # 若有，解析 guide_type/scenario，进入下一节点
    logging.info("[user_intent_node] called")
    if not state.get("scenario"):
        response = interrupt({"type": "interrupt", "content": "请描述你本次护肤/化妆的需求或场景。"})
        state["scenario"] = response
    return state

# 2. 推荐与确认节点
def recommend_and_confirm_steps_node(state: CareMakeupGuideState):
    """
    1. 调用 Agent，根据 user_intent/guide_type/scenario 生成推荐产品种类列表和分步流程（每步含产品和动作）。
    2. 若用户有修改建议（user_feedback），Agent 结合建议重新生成推荐。
    3. 推送推荐方案到前端，interrupt 等待用户“确认”或“修改建议”。
    4. 若用户确认，进入分步引导；若有修改建议，循环本节点。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 伪代码逻辑：
    # if not state.recommended_steps or state.user_feedback:
    #     调用 Agent 生成/更新推荐步骤
    #     state.recommended_steps = agent_generate_steps(state.user_intent, state.guide_type, state.scenario, state.user_feedback)
    # interrupt 推送推荐方案，等待用户输入
    # if 用户输入“确认”，进入 step_guide_node
    # if 用户输入“修改建议”，state.user_feedback = 用户输入，循环本节点
    logging.info("[recommend_and_confirm_steps_node] called")
    writer = get_stream_writer()
    # mock: 实际应调用 agent_generate_steps 工具
    if not state.get("recommended_steps"):
        state["recommended_steps"] = [
            {"step": "洁面", "desc": "用温水洁面"},
            {"step": "爽肤水", "desc": "轻拍爽肤水"}
        ]
    writer({"type": "progress", "content": f"推荐流程：{state['recommended_steps']}"})
    # interrupt 等待用户确认
    response = interrupt({"type": "interrupt", "content": "请确认推荐流程，或提出修改建议。"})
    # mock: 只要有响应就进入下一步
    return state

# 3. 分步骤引导节点
def step_guide_and_feedback_node(state: CareMakeupGuideState):
    """
    1. 取当前步骤 recommended_steps[current_step_index]，Mira文本引导用户操作，interrupt 等待用户上传视频。
    2. 分析用户视频，给出反馈，interrupt 等待用户“完成/遇到问题/补充说明”。
    3. 若用户完成，current_step_index+1，循环本节点；否则可人工干预或补充说明。
    4. 所有步骤完成后，进入 summary_node。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 伪代码逻辑：
    # if state.current_step_index < len(state.recommended_steps):
    #     step = state.recommended_steps[state.current_step_index]
    #     interrupt 引导用户操作，等待视频
    #     分析视频，给反馈
    #     interrupt 等待用户反馈
    #     if 用户反馈“完成”:
    #         state.current_step_index += 1
    #         循环本节点
    #     else:
    #         可人工干预或补充说明
    # else:
    #     进入 summary_node
    logging.info("[step_guide_and_feedback_node] called")
    writer = get_stream_writer()
    idx = state.get("current_step_index", 0)
    steps = state.get("recommended_steps", [])
    if idx < len(steps):
        step = steps[idx]
        writer({"type": "progress", "content": f"第{idx+1}步：{step['step']} - {step['desc']}"})
        # interrupt 等待用户上传视频
        response = interrupt({"type": "interrupt", "content": f"请上传你完成{step['step']}的操作视频。"})
        # mock: 实际应调用 analyze_user_video 工具
        feedback = "动作标准，很棒！"
        state["current_step_feedback"] = feedback
        writer({"type": "progress", "content": feedback})
        # interrupt 等待用户反馈
        response2 = interrupt({"type": "interrupt", "content": "本步骤已完成？如遇问题请补充说明。"})
        # mock: 只要有响应就进入下一步
        state["current_step_index"] = idx + 1
        return state
    else:
        return state

# 4. 总结节点
def summary_node(state: CareMakeupGuideState):
    """
    结束节点：Mira总结本次体验，鼓励用户。
    :param state: 当前 State
    :return: (新 State, 反馈消息)
    """
    logging.info("[summary_node] called")
    writer = get_stream_writer()
    writer({"type": "progress", "content": "护肤/化妆流程已完成，Mira为你点赞！"})
    return state

def build_care_makeup_guide_graph():
    graph = StateGraph(CareMakeupGuideState)
    graph.add_node("user_intent", user_intent_node)
    graph.add_node("recommend_and_confirm_steps", recommend_and_confirm_steps_node)
    graph.add_node("step_guide_and_feedback", step_guide_and_feedback_node)
    graph.add_node("summary", summary_node)
    graph.add_edge(START, "user_intent")
    graph.add_edge("user_intent", "recommend_and_confirm_steps")
    graph.add_edge("recommend_and_confirm_steps", "step_guide_and_feedback")
    graph.add_edge("step_guide_and_feedback", "summary")
    graph.add_edge("summary", END)
    return graph.compile()

care_makeup_guide_graph = build_care_makeup_guide_graph()