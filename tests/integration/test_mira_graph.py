import pytest
from graphs.mira_graph import mira_graph
from langchain_core.messages import HumanMessage, AIMessage

def test_main_graph_chat(monkeypatch):
    """
    测试：多模态输入为普通对话，流程应停留在mira节点并返回聊天回复。
    """
    # 构造输入
    state = {
        "multimodal_text": "你好，今天天气怎么样？",
        "messages": [HumanMessage(content="你好，今天天气怎么样？")]
    }
    # 执行主流程
    result = None
    for step in mira_graph.stream(state, {"configurable": {"thread_id": "test1"}}, stream_mode="values"):
        result = step
    # 验证输出有AIMessage
    assert isinstance(result["messages"][-1], AIMessage)


def test_main_graph_enter_profile_creation(monkeypatch):
    """
    测试：多模态输入为建档请求，流程应跳转到 user_profile_creation_subgraph。
    """
    monkeypatch.setattr("tools.mira_tools.recognize_intent", lambda x: "创建用户档案")
    mira_graph._nodes["user_profile_creation_subgraph"] = lambda state, *a, **kw: {"user_profile": {"name": "mock_user"}}
    state = {
        "multimodal_text": "我想创建个人档案",
        "messages": [HumanMessage(content="我想创建个人档案")]
    }
    result = None
    for step in mira_graph.stream(state, {"configurable": {"thread_id": "test2"}}, stream_mode="values"):
        result = step
    assert "user_profile" in result
    assert result["user_profile"]["name"] == "mock_user"


def test_main_graph_enter_profile_edit(monkeypatch):
    """
    测试：多模态输入为档案编辑请求，流程应跳转到 user_profile_edit_subgraph。
    """
    monkeypatch.setattr("tools.mira_tools.recognize_intent", lambda x: "档案编辑")
    mira_graph._nodes["user_profile_edit_subgraph"] = lambda state, *a, **kw: {"user_profile": {"name": "edit_user"}}
    state = {
        "multimodal_text": "我要修改个人档案",
        "messages": [HumanMessage(content="我要修改个人档案")]
    }
    result = None
    for step in mira_graph.stream(state, {"configurable": {"thread_id": "test3"}}, stream_mode="values"):
        result = step
    assert "user_profile" in result
    assert result["user_profile"]["name"] == "edit_user"


def test_main_graph_enter_skin_analysis(monkeypatch):
    """
    测试：多模态输入为肤质检测请求，流程应跳转到 skin_analysis_subgraph。
    """
    monkeypatch.setattr("tools.mira_tools.recognize_intent", lambda x: "肤质检测")
    mira_graph._nodes["skin_analysis_subgraph"] = lambda state, *a, **kw: {"skin_analysis_result": {"mock": 1}}
    state = {
        "multimodal_text": "请帮我做一个肤质检测",
        "messages": [HumanMessage(content="请帮我做一个肤质检测")]
    }
    result = None
    for step in mira_graph.stream(state, {"configurable": {"thread_id": "test4"}}, stream_mode="values"):
        result = step
    assert "skin_analysis_result" in result
    assert result["skin_analysis_result"]["mock"] == 1


def test_main_graph_enter_product_recognition(monkeypatch):
    """
    测试：多模态输入为产品识别请求，流程应跳转到 product_recognition_subgraph。
    """
    monkeypatch.setattr("tools.mira_tools.recognize_intent", lambda x: "产品识别")
    mira_graph._nodes["product_recognition_subgraph"] = lambda state, *a, **kw: {"product_structured_info": {"brand": "欧莱雅"}}
    state = {
        "multimodal_text": "请识别这个产品",
        "messages": [HumanMessage(content="请识别这个产品")]
    }
    result = None
    for step in mira_graph.stream(state, {"configurable": {"thread_id": "test5"}}, stream_mode="values"):
        result = step
    assert "product_structured_info" in result
    assert result["product_structured_info"]["brand"] == "欧莱雅"


def test_main_graph_enter_product_recommend(monkeypatch):
    """
    测试：多模态输入为产品推荐请求，流程应跳转到 product_recommend_subgraph。
    """
    monkeypatch.setattr("tools.mira_tools.recognize_intent", lambda x: "产品推荐")
    mira_graph._nodes["product_recommend_subgraph"] = lambda state, *a, **kw: {"recommended_products": [{"name": "粉底液"}]}
    state = {
        "multimodal_text": "推荐适合我的粉底液",
        "messages": [HumanMessage(content="推荐适合我的粉底液")]
    }
    result = None
    for step in mira_graph.stream(state, {"configurable": {"thread_id": "test6"}}, stream_mode="values"):
        result = step
    assert "recommended_products" in result
    assert result["recommended_products"][0]["name"] == "粉底液"


def test_main_graph_enter_care_makeup_guide(monkeypatch):
    """
    测试：多模态输入为护肤/化妆引导请求，流程应跳转到 care_makeup_guide_subgraph。
    """
    monkeypatch.setattr("tools.mira_tools.recognize_intent", lambda x: "护肤引导")
    mira_graph._nodes["care_makeup_guide_subgraph"] = lambda state, *a, **kw: {"recommended_steps": [{"step": "洁面"}]}
    state = {
        "multimodal_text": "请给我一个护肤流程",
        "messages": [HumanMessage(content="请给我一个护肤流程")]
    }
    result = None
    for step in mira_graph.stream(state, {"configurable": {"thread_id": "test7"}}, stream_mode="values"):
        result = step
    assert "recommended_steps" in result
    assert result["recommended_steps"][0]["step"] == "洁面"

