"""
用户档案编辑子流程 Graph，节点实现如下。
"""

def build_user_profile_edit_graph():
    """
    构建老用户档案编辑子流程 Graph，注册所有节点与分支。
    :return: LangGraph Subgraph 实例
    """

def edit_intent_node(state):
    """
    编辑意图识别节点：识别用户想要编辑的字段，未明确则 interrupt 请求用户说明要修改什么。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 若无 edit_field，interrupt 请求用户输入
    # 若有，进入字段输入节点

def field_input_node(state):
    """
    字段输入节点：根据 edit_field，动态生成输入提示，等待用户输入新值。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 若无 edit_value，interrupt 请求用户输入
    # 若有，进入确认保存节点

def confirm_save_node(state):
    """
    确认保存节点：展示修改前后内容，询问用户是否确认保存。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 若无 internal["confirm"]，interrupt 请求用户确认
    # 若确认，进入保存节点；否则回到 edit_intent_node

def save_node(state):
    """
    保存节点：将 edit_value 写入对应字段，更新档案。
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # setattr(state, state.edit_field, state.edit_value)

user_profile_edit_graph = build_user_profile_edit_graph()