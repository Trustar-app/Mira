def test_main_graph_chat(monkeypatch):
    """
    测试：多模态输入为普通对话，流程应停留在 supervisor 并返回聊天回复。
    """

def test_main_graph_enter_skincare(monkeypatch):
    """
    测试：多模态输入为肤质检测请求，流程应跳转到 skincare_subgraph。
    """

def test_main_graph_enter_profile(monkeypatch):
    """
    测试：多模态输入为建档请求，流程应跳转到 user_profile_subgraph。
    """

def test_main_graph_switch_flow(monkeypatch):
    """
    测试：流程中用户随时切换意图，能正确跳转到对应子图。
    """