import os
import pytest
import base64
from tools.mira_tools import video_to_audio, audio_to_text, video_to_text, recognize_intent, multimodal_chat_agent
from tools.common.logger import get_logger
import mimetypes

logger = get_logger("", log_file="logs/test_mira_tools.log")

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

# 4. recognize_intent 测试
@pytest.mark.parametrize('query,expected_intent', [
    ("你好，今天天气怎么样？", "聊天互动"),
    ("请帮我做一个肤质检测", "肤质检测"),
    ("我想创建个人档案", "创建用户档案"),
    ("推荐适合我的粉底液", "产品推荐"),
    ("请识别这个产品，并保存到我的信息库中", "产品识别"),
    ("我想要日常淡妆", "化妆引导"),
    ("今天皮肤有点干，想补水", "护肤引导"),
    ("我要修改我的个人信息", "档案编辑"),
])
def test_recognize_intent(query, expected_intent):
    intent = recognize_intent(query)
    logger.info(f"recognize_intent 输入: {query}，输出: {intent}")
    assert isinstance(intent, str)
    assert intent == expected_intent

# 5. multimodal_chat_agent 测试
# 用 OpenAI 官方多模态格式，视频 base64
def test_multimodal_chat_agent():
    # 读取视频并编码为 base64
    with open(VIDEO_PATH, "rb") as f:
        video_bytes = f.read()
    video_b64 = base64.b64encode(video_bytes).decode("utf-8")
    mime_type, _ = mimetypes.guess_type(VIDEO_PATH)
    if not mime_type:
        mime_type = "video/mp4"
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "请帮我做一个肤质检测"},
                {"type": "video_url", "video_url": {"url": f"data:{mime_type};base64,{video_b64}"}}
            ]
        }
    ]
    result = multimodal_chat_agent(messages)
    logger.info(f"multimodal_chat_agent 输入: {messages}\n输出: {result}")
    assert isinstance(result, str)
