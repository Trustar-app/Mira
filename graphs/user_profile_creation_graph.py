"""
新用户建档子流程 Graph，节点实现如下。
"""

def build_user_profile_graph():
    """
    构建新用户建档子流程 Graph，注册所有节点与分支。
    :return: LangGraph Subgraph 实例
    """

def gender_selection_node(state):
    """
    性别选择节点：引导用户选择性别，校验输入。通过 interrupt 请求用户干预
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 若未选择，返回 progress/error，要求用户输入
    # 若已选择，更新 gender 字段，进入下一节点

def age_input_node(state):
    """
    年龄输入节点：引导用户输入年龄，校验输入。通过 interrupt 请求用户干预
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 若未输入，返回 progress/error
    # 若已输入，更新 age 字段，进入下一节点

def face_feature_analysis_node(state):
    """
    面部特征采集与分析节点：引导用户上传视频，分析五官、肤色、肤质。通过 interrupt 请求用户干预
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """
    # 检查视频输入，若无则 progress/error
    # 有视频则调用人脸特征分析Agent

def makeup_skill_node(state):
    """
    化妆专业度打分节点：引导用户打分，校验输入。通过 interrupt 请求用户干预
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """

def skincare_skill_node(state):
    """
    护肤专业度打分节点：引导用户打分，校验输入。通过 interrupt 请求用户干预
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """

def user_preferences_node(state):
    """
    个人诉求与偏好收集节点：引导用户输入文本/语音，抽取关键信息。通过 interrupt 请求用户干预
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """

def name_input_node(state):
    """
    用户名采集节点：引导用户输入姓名，校验输入。通过 interrupt 请求用户干预
    :param state: 当前 State
    :return: (新 State, 进度消息)
    """

def profile_generate_node(state):
    """
    档案生成与保存节点：汇总所有信息，生成用户档案，推送到前端。
    :param state: 当前 State
    :return: (新 State, 反馈消息)
    """