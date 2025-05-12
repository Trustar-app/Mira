def test_extract_best_face_frame_valid():
    """
    测试：输入有效视频，能正确提取最佳人脸帧。
    """
    result = media_utils.extract_best_face_frame("valid_video.mp4")
    assert result == "face.jpg"  # 需 mock 实现

def test_extract_best_face_frame_no_face():
    """
    测试：输入视频无有效人脸，返回 None。
    """
    result = media_utils.extract_best_face_frame("no_face_video.mp4")
    assert result is None