from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage


def messages_to_text(messages):
    lines = []
    for msg in messages:
        role = getattr(msg, "role", "unknown")
        content = getattr(msg, "content", "")
        # content 可能为 list（如多模态），需处理
        if isinstance(content, list):
            # 处理多模态内容列表
            content_parts = []
            for c in content:
                # 跳过视频URL类型
                if isinstance(c, dict) and c.get("type") == "video_url":
                    continue
                    
                if isinstance(c, dict):
                    # 获取内容类型,默认为text
                    content_type = c.get("type", "text")
                    # 获取文本内容,优先使用text字段,否则使用content字段
                    text = c.get("text") or c.get("content", "")
                    content_parts.append(f"[{content_type}] {text}")
                else:
                    # 非字典类型直接转为字符串
                    content_parts.append(str(c))
                    
            content = "\n".join(content_parts)
        lines.append(f"{role}: {content}")
    return "\n".join(lines)

def extract_structured_info_from_search(messages: list) -> dict:

    # 1. 转为字符串
    history_text = messages_to_text(messages)
    # 2. 设计 prompt
    prompt = (
        "请根据以下用户与AI的对话内容，提取产品的结构化信息，输出标准 JSON，字段内容为中文。\n"
        "需要提取的字段如下：\n"
        "  - 产品图片（image_url）\n"
        "  - 产品名称（name）\n"
        "  - 产品分类（category）\n"
        "  - 产品品牌（brand）\n"
        "  - 产品成分（ingredients）\n"
        "  - 产品功效（effects）\n"
        "请严格按照如下 JSON 格式输出：\n"
        "{\n"
        '  "image_url": "",\n'
        '  "name": "",\n'
        '  "category": "",\n'
        '  "brand": "",\n'
        '  "ingredients": "",\n'
        '  "effects": ""\n'
        "}\n"
        "对话内容如下：\n"
        f"{history_text}"
    )
    messages = [HumanMessage(content=prompt)]
    llm = ChatOpenAI(
        model="qwen2.5-vl-72b-instruct",
        openai_api_base=OPENAI_API_BASE,
        openai_api_key=OPENAI_API_KEY,
        streaming=False
    ).with_structured_output(method="json_mode")
    response = llm.invoke(messages)
    return response