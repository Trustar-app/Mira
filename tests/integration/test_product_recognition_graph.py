# product 识别的集成测试
def test_flow_no_input_interrupt():
    """
    测试：无输入时，流程应在 input_collection_node interrupt。
    """

def test_flow_extraction_fail_interrupt(monkeypatch):
    """
    测试：输入无效，提取失败，流程应 interrupt 请求重新输入。
    """

def test_flow_search_fail_interrupt(monkeypatch):
    """
    测试：提取成功但检索失败，流程应该继续，只提供识别信息给后一节点，没有检索信息
    """

def test_flow_full_success(monkeypatch):
    """
    测试：完整流程，用户输入有效，能顺利识别、检索、分析并推送结果。
    """