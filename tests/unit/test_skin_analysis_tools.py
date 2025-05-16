import os
import pytest
# 添加项目根目录到Python路径
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
import tools.skin_analysis_tools as skin_tools
from utils.loggers import MiraLog
import json

# 肤质检测的视频在 mockdata/肤质检测.mp4
VALID_VIDEO = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mockdata/肤质检测.mp4'))
VALID_IMAGE = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../mockdata/肤质检测.png'))

# 测试结果放在 tests/results/skin_analysis_tools/
RESULT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../results/skin_analysis_tools/'))

# 1. extract_best_face_frame 测试
def test_extract_best_face_frame_valid():
    """
    测试：输入有效视频的base64编码，能正确提取最佳人脸帧并返回base64图片。
    """
    import base64
    import os
    
    # 将测试视频文件转换为base64格式
    with open(VALID_VIDEO, 'rb') as video_file:
        video_base64 = base64.b64encode(video_file.read()).decode('utf-8')
    
    # 调用函数获取base64格式的最佳帧
    result_base64 = skin_tools.extract_best_face_frame(video_base64)
    
    # 验证返回结果
    assert result_base64 is not None
    assert isinstance(result_base64, str)
    assert len(result_base64) > 0
    
    # 确保结果目录存在
    os.makedirs(RESULT_DIR, exist_ok=True)
    
    # 将base64转换回图片并保存到结果目录
    result_file = os.path.join(RESULT_DIR, 'best_face_frame.jpg')
    with open(result_file, 'wb') as img_file:
        img_file.write(base64.b64decode(result_base64))
    
    # 验证生成的图片文件
    assert os.path.exists(result_file)
    assert os.path.getsize(result_file) > 0
    
    MiraLog("test", f"已保存最佳帧图片到: {result_file}")
    
    # 不删除结果文件，保留供检查
    # 如果需要删除，取消下面的注释：
    # os.remove(result_file)

# def test_extract_best_face_frame_no_face():
#     """
#     测试：输入无人脸视频的base64编码，应返回None。
#     """
#     import base64
    
#     # 检查INVALID_VIDEO是否存在
#     if not os.path.exists(INVALID_VIDEO):
#         MiraLog("test", f"无效测试视频不存在: {INVALID_VIDEO}", "WARNING")
#         pytest.skip("无效测试视频不存在")
    
#     # 将测试视频文件转换为base64格式
#     with open(INVALID_VIDEO, 'rb') as video_file:
#         video_base64 = base64.b64encode(video_file.read()).decode('utf-8')
    
#     # 调用函数
#     result = skin_tools.extract_best_face_frame(video_base64)
#     assert result is None

# 2. skin_analysis 测试
def test_skin_analysis_success():
    """
    测试：skin_analysis接收base64图像数据并正常返回分析结果。
    """
    import base64
    
    # 使用 VALID_IMAGE 作为测试数据
    with open(VALID_IMAGE, 'rb') as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    
    # 使用base64数据调用skin_analysis
    data = skin_tools.skin_analysis(image_base64)
    
    # 验证返回结果
    assert data is not None
    assert isinstance(data, dict) or isinstance(data, list)
    
    MiraLog("test", "皮肤分析测试完成，成功返回分析结果")
    
    # 可选：保存结果以供查看
    result_file = os.path.join(RESULT_DIR, 'skin_analysis_result.json')
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    MiraLog("test", f"分析结果已保存到: {result_file}")
    
    return data  # 返回结果供下一个测试使用

# 3. skin_feedback 测试
def test_skin_feedback():
    """
    测试：skin_feedback 能生成反馈文本
    """
    # 先用 best_face.jpg 得到分析结果
    data = {"pore": {"raw_score": 99.9246597290039, "ui_score": 99, "output_mask_name": "pore_output.png"}}
    result = skin_tools.skin_feedback(data)
    MiraLog("skin_analysis", f"肤质分析反馈: {result}")
    assert isinstance(result, str)
    assert len(result) > 0

if __name__ == "__main__":
    test_extract_best_face_frame_valid()
    # test_skin_analysis_success()
    test_skin_feedback()
