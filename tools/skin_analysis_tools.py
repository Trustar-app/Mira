# YouCam肤质分析API封装
def skin_analysis(image_path):
    """
    调用 YouCam API 进行肤质分析。
    :param image_path: 本地图片路径
    :return: 原始分析结果（data 字段），异常时抛出异常或返回 None
    """
    import os
    import requests
    import json
    from config import YOUCAM_API_KEY, YOUCAM_SECRET_KEY
    # 1. 获取 access_token（如无则获取）
    access_token = os.environ.get("YOUCAM_ACCESS_TOKEN")
    if not access_token:
        url = "https://yce-api-01.perfectcorp.com/oauth2/v1/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": YOUCAM_API_KEY,
            "client_secret": YOUCAM_SECRET_KEY
        }
        resp = requests.post(url, data=data)
        if resp.status_code != 200:
            raise RuntimeError(f"YouCam平台认证失败：{resp.text}")
        access_token = resp.json()["access_token"]
        os.environ["YOUCAM_ACCESS_TOKEN"] = access_token
    # 2. 上传图片
    if not image_path or not os.path.exists(image_path):
        raise FileNotFoundError("未找到图片文件")
    headers = {"Authorization": f"Bearer {access_token}"}
    with open(image_path, "rb") as f:
        files = {"file": f}
        resp = requests.post(
            "https://yce-api-01.perfectcorp.com/s2s/v1.0/file",
            headers=headers,
            files=files
        )
    if resp.status_code != 200:
        raise RuntimeError(f"图片上传失败：{resp.text}")
    src_id = resp.json()["result"]["src_id"]
    # 3. 发起 Skin Analysis 任务
    payload = {
        "file_sets": {
            "src_ids": [src_id]
        },
        "mode": "std"  # 标清分析
    }
    resp = requests.post(
        "https://yce-api-01.perfectcorp.com/s2s/v1.0/task/skin-analysis",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(payload)
    )
    if resp.status_code != 200:
        raise RuntimeError(f"AI分析任务发起失败：{resp.text}")
    task_id = resp.json()["result"]["task_id"]
    # 4. 轮询任务状态
    while True:
        resp = requests.get(
            f"https://yce-api-01.perfectcorp.com/s2s/v1.0/task/skin-analysis?task_id={task_id}",
            headers=headers
        )
        result = resp.json()["result"]
        if result["status"] == "success":
            break
        elif result["status"] == "error":
            raise RuntimeError(f"AI分析失败：{result.get('error_message', '未知错误')}")
        import time
        time.sleep(result.get("polling_interval", 1) / 1000.0)
    # 5. 返回原始分析结果
    data = result["results"][0]["data"][0]
    return data 

# AI肤质分析结果反馈生成

def skin_feedback(data):
    """
    用大模型生成肤质分析反馈。
    :param data: 肤质分析原始结果（dict）
    :return: 反馈文本（str）
    """
    from config import OPENAI_API_KEY, OPENAI_API_BASE
    from langchain_openai import ChatOpenAI
    from langchain.schema import SystemMessage, HumanMessage
    SYSTEM_PROMPT = (
        "你是一个专业的皮肤健康顾问，请根据用户的肤质检测结果，生成如下内容：\n"
        "1. 检测完成提示（如：已完成肤质检测，具体信息可以查看肤质检测结果）\n"
        "2. 肤质分析说明（如：你的黑眼圈为轻度，请继续保持早睡早起的好习惯）\n"
        "3. 情感反馈（如：别担心，坚持护肤会越来越好！）\n"
        "4. 下一步建议（如：和Mira说说你最关心的肤质问题是什么吧）\n"
        "请用简洁、温暖的中文输出。\n"
        "用户肤质检测原始数据如下：\n"
        f"{data}"
    )
    llm = ChatOpenAI(model_name="qwen-plus", temperature=0, openai_api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="请生成反馈")
    ]
    feedback = llm.invoke(messages).content.strip()
    return feedback 