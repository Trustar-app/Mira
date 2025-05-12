def test_flow_no_intent_interrupt():
    """
    测试：无推荐需求时，流程应在 recommend_intent_node interrupt。
    """

def test_flow_search_fail_interrupt(monkeypatch):
    """
    测试：检索失败，流程应 interrupt 请求补充信息。
    """

def test_flow_full_success(monkeypatch):
    """
    测试：完整流程，用户输入有效，能顺利推荐产品并生成推荐理由。
    """