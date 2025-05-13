import os
import pytest
import tools.skin_analysis_tools as skin_tools
from tools.common.logger import get_logger

logger = get_logger("", log_file="logs/test_skin_analysis_tools.log")

ASSETS_DIR = os.path.join(os.path.dirname(__file__), '../assets')
VALID_VIDEO = os.path.abspath(os.path.join(ASSETS_DIR, 'real_face_video.mp4'))
INVALID_VIDEO = os.path.abspath(os.path.join(ASSETS_DIR, 'invalid_video.mp4'))
BEST_FACE_IMG = os.path.abspath(os.path.join(ASSETS_DIR, 'best_face.jpg'))

# 1. extract_best_face_frame 测试
def test_extract_best_face_frame_valid():
    """
    测试：输入有效视频，能正确提取最佳人脸帧。
    """
    result = skin_tools.extract_best_face_frame(VALID_VIDEO)
    assert result is not None
    assert result.endswith('.jpg')
    assert os.path.exists(result)
    # 清理临时文件
    os.remove(result)

def test_extract_best_face_frame_no_face():
    """
    测试：输入视频无有效人脸，返回 None。
    """
    result = skin_tools.extract_best_face_frame(INVALID_VIDEO)
    assert result is None

# # 2. skin_analysis 测试（需配置好 API KEY）
# def test_skin_analysis_success():
#     """
#     测试：skin_analysis 正常返回数据
#     """
#     data = skin_tools.skin_analysis(BEST_FACE_IMG)
#     assert isinstance(data, dict) or isinstance(data, list)

# 3. skin_feedback 测试
# def test_skin_feedback():
#     """
#     测试：skin_feedback 能生成反馈文本
#     """
#     # 先用 best_face.jpg 得到分析结果
#     data = skin_tools.skin_analysis(BEST_FACE_IMG)
#     result = skin_tools.skin_feedback(data)
#     assert isinstance(result, str)
#     assert len(result) > 0
