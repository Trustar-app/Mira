import base64
import mimetypes
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

def video_to_base64(video_path: str):
    """
    将视频文件转为base64字符串及mime类型
    """
    with open(video_path, "rb") as video_file:
        video_data = video_file.read()
        base64_video = base64.b64encode(video_data).decode('utf-8')
        mime_type, _ = mimetypes.guess_type(video_path)
    return base64_video, mime_type or "video/mp4"


def analyze_face_features_with_llm(video_path, config) -> dict:
    """
    用LLM分析面部视频，提取五官特征、肤色、肤质等结构化信息。
    输入: 视频文件路径
    输出: dict，包含face_features, skin_color, skin_quality等字段
    """
    base64_video, mime_type = video_to_base64(video_path)
    prompt = (
        "请分析用户上传的面部视频，精准识别并打标以下面部特征，输出 JSON，字段内容为中文。\n\n"
        "【需要提取的面部特征及标签】\n"
        "1. face_features（五官特征）：\n"
        "    - 脸型（face_shape）：方脸、圆脸、瓜子脸、方圆脸、鹅蛋脸、高颧骨\n"
        "    - 眼睛（eyes）：单眼皮、双眼皮、大眼睛、小眼睛\n"
        "    - 鼻子（nose）：大鼻子、小鼻子、高鼻梁、低鼻梁\n"
        "    - 嘴巴（mouth）：大嘴、小嘴\n"
        "    - 眉毛（eyebrows）：浓眉、淡眉\n"
        "2. 肤色（skin_color）：黄1白、黄2白、黑皮、白皮\n"
        "3. 肤质标签（skin_type）：痘肌、黑眼圈、敏感肌、黑头、毛孔粗大、干皮、油皮、混干皮、混油皮、色斑、皮肤暗沉\n"
        "\n"
        "请严格按照上述标签进行面部特征识别和 AI 打标，并输出如下 JSON 格式：\n"
        "{\n"
        '  "face_features": {\n'
        '    "face_shape": "",\n'
        '    "eyes": "",\n'
        '    "nose": "",\n'
        '    "mouth": "",\n'
        '    "eyebrows": ""\n'
        "  },\n"
        '  "skin_color": "",\n'
        '  "skin_type": []\n'
        "}\n"
        "其中 skin_type 字段为数组，可多选。\n"
        "分析时请确保每个字段都给出最符合实际的视频特征标签。"
        f"\n视频内容：{video_path}"
    )
    messages = [HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "video_url", "video_url": {"url": f"data:{mime_type};base64,{base64_video}"}}
    ])]
    llm = ChatOpenAI(
        model=config['configurable'].get("chat_model_name"),
        openai_api_base=config['configurable'].get("chat_api_base"),
        openai_api_key=config['configurable'].get("chat_api_key"),
        streaming=False
    ).with_structured_output(method="json_mode")
    response = llm.invoke(messages)
    return response
