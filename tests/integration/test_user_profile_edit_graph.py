def test_flow_no_edit_intent_interrupt():
    """
    测试：无编辑意图时，流程应在 edit_intent_node interrupt。
    """

def test_flow_invalid_edit_value_interrupt():
    """
    测试：输入新值不合法，流程应在 field_input_node interrupt。
    """

def test_flow_confirm_cancel():
    """
    测试：用户取消保存，流程应回到 edit_intent_node。
    """

def test_flow_full_success():
    """
    测试：完整流程，用户输入编辑意图、新值、确认保存，能正确更新档案并支持多轮编辑。
    """