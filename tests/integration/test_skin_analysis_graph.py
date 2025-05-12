
@pytest.fixture
def skincare_graph():
    # 构建并返回肤质检测子图实例
    return build_skincare_graph()

def test_flow_no_video_input(skincare_graph):
    """
    测试：无视频输入时，流程应在 wait_for_video_node 节点中断并提示用户干预。
    """
    state = SkincareState(user_video=None)
    result = skincare_graph.invoke(state)
    assert result.progress or result.error  # 应有提示
    assert not result.best_face_image

def test_flow_invalid_video(skincare_graph, monkeypatch):
    """
    测试：视频输入但无法检测到人脸，流程应在 video_analysis_node 节点中断。
    """
    state = SkincareState(user_video="invalid_video.mp4")
    # mock extract_best_face_frame 返回 None
    monkeypatch.setattr("mira.tools.media_utils.extract_best_face_frame", lambda x: None)
    result = skincare_graph.invoke(state)
    assert result.progress or result.error
    assert not result.best_face_image

def test_flow_valid_video_and_analysis(skincare_graph, monkeypatch):
    """
    测试：视频输入有效，能检测到人脸并完成肤质分析，流程顺利结束。
    """
    state = SkincareState(user_video="valid_video.mp4")
    # mock extract_best_face_frame 返回图片路径
    monkeypatch.setattr("mira.tools.media_utils.extract_best_face_frame", lambda x: "face.jpg")
    # mock 肤质分析模型
    monkeypatch.setattr("mira.agents.skincare.SkincareAgent.analyze_skin", lambda self, x: {"moisture": 80})
    result = skincare_graph.invoke(state)
    assert result.best_face_image == "face.jpg"
    assert result.skin_analysis_result is not None
    assert result.analysis_report

def test_flow_analysis_failure(skincare_graph, monkeypatch):
    """
    测试：视频和图片都有效，但肤质分析模型失败，流程应在 node_skin_analysis 节点中断。
    """
    state = SkincareState(user_video="valid_video.mp4")
    monkeypatch.setattr("mira.tools.media_utils.extract_best_face_frame", lambda x: "face.jpg")
    monkeypatch.setattr("mira.agents.skincare.SkincareAgent.analyze_skin", lambda self, x: None)
    result = skincare_graph.invoke(state)
    assert result.best_face_image == "face.jpg"
    assert not result.skin_analysis_result
    assert result.progress or result.error