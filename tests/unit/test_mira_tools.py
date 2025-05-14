import os
import pytest
import base64
from tools.mira_tools import recognize_intent, multimodal_chat_agent
from tools.common.logger import get_logger
import mimetypes
from langchain_core.messages import HumanMessage
logger = get_logger("", log_file="logs/test_mira_tools.log")

ASSETS_DIR = os.path.join(os.path.dirname(__file__), '../assets')
VIDEO_PATH = os.path.abspath(os.path.join(ASSETS_DIR, 'skin_analysis_query.mp4'))
AUDIO_PATH = os.path.abspath(os.path.join(ASSETS_DIR, 'hello.wav'))


# recognize_intent 测试
@pytest.mark.parametrize('query,expected_intent', [
    ("你好，今天天气怎么样？", "聊天互动"),
    ("请帮我做一个肤质检测", "肤质检测"),
    ("我想创建个人档案", "创建用户档案"),
    ("推荐适合我的粉底液", "产品推荐"),
    ("请识别这个产品，并保存到我的信息库中", "产品识别"),
    ("我想要日常淡妆", "化妆引导"),
    ("今天皮肤有点干，想补水", "护肤引导"),
    ("我要修改我的个人信息", "档案编辑"),
    # 边缘/模糊/无关/歧义/否定/复合/反问
    ("你觉得我适合什么妆容？", "聊天互动"),
    ("你是谁？", "聊天互动"),
    ("我不需要任何推荐", "聊天互动"),
    ("帮我推荐或者检测都可以", "聊天互动"),
    ("随便聊聊吧", "聊天互动"),
    ("你能做什么？", "聊天互动"),
    ("我昨天买了个新口红", "聊天互动"),
    ("我是陈小明", "聊天互动"),
    ("你能帮我吗？", "聊天互动"),
    ("我想要美丽", "聊天互动"),
    ("我想要一个建议", "聊天互动"),
    ("请问你能做哪些服务？", "聊天互动"),
])
def test_recognize_intent(query, expected_intent):
    intent = recognize_intent(query)
    logger.info(f"recognize_intent 输入: {query}，输出: {intent}")
    assert isinstance(intent, str)
    assert intent == expected_intent

# multimodal_chat_agent 测试
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
        HumanMessage(
            content=[
                {"type": "text", "text": "请帮我做一个肤质检测"},
                {"type": "video_url", "video_url": {"url": f"data:{mime_type};base64,{video_b64}"}}
            ]
        )
    ]
    result = multimodal_chat_agent(messages)
    logger.info(f"multimodal_chat_agent 输入: {messages}\n输出: {result}")
    assert isinstance(result, str)
