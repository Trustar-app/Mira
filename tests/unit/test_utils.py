import os
from tools.common.utils import video_to_audio, audio_to_text, video_to_text
from tools.common.logger import get_logger

logger = get_logger("", log_file="logs/test_utils.log")

ASSETS_DIR = os.path.join(os.path.dirname(__file__), '../assets')
VIDEO_PATH = os.path.abspath(os.path.join(ASSETS_DIR, 'skin_analysis_query.mp4'))
AUDIO_PATH = os.path.abspath(os.path.join(ASSETS_DIR, 'hello.wav'))

# 1. video_to_audio 测试
def test_video_to_audio():
    audio_path = video_to_audio(VIDEO_PATH)
    logger.info(f"video_to_audio 输出音频路径: {audio_path}")
    assert os.path.exists(audio_path)
    assert audio_path.endswith('.wav')
    # 清理临时文件
    os.remove(audio_path)

# 2. audio_to_text 测试
# 预期文本："你好，今天天气怎么样？"
def test_audio_to_text():
    text = audio_to_text(AUDIO_PATH)
    logger.info(f"audio_to_text 输出文本: {text}")
    assert isinstance(text, str)
    assert '你好' in text

# 3. video_to_text 测试
# 预期文本："请帮我做一个肤质检测"
def test_video_to_text():
    text = video_to_text(VIDEO_PATH)
    logger.info(f"video_to_text 输出文本: {text}")
    assert isinstance(text, str)
    assert '肤质' in text or '检测' in text