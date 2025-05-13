import logging
import av
import insightface
import numpy as np
import tempfile
import cv2
import os
import requests
import json
from config import YOUCAM_API_KEY, YOUCAM_SECRET_KEY

# YouCam肤质分析API封装
def skin_analysis(image_path):
    """
    调用 YouCam API 进行肤质分析。
    :param image_path: 本地图片路径
    :return: 原始分析结果（data 字段），异常时抛出异常或返回 None
    """
    

    logging.info(f"[skin_analysis] 开始分析图片: {image_path}")
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
            logging.error(f"YouCam平台认证失败：{resp.text}")
            raise RuntimeError(f"YouCam平台认证失败：{resp.text}")
        access_token = resp.json()["access_token"]
        os.environ["YOUCAM_ACCESS_TOKEN"] = access_token
    # 2. 上传图片
    if not image_path or not os.path.exists(image_path):
        logging.error("未找到图片文件")
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
        logging.error(f"图片上传失败：{resp.text}")
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
        logging.error(f"AI分析任务发起失败：{resp.text}")
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
            logging.error(f"AI分析失败：{result.get('error_message', '未知错误')}")
            raise RuntimeError(f"AI分析失败：{result.get('error_message', '未知错误')}")
        import time
        time.sleep(result.get("polling_interval", 1) / 1000.0)
    # 5. 返回原始分析结果
    data = result["results"][0]["data"][0]
    logging.info(f"[skin_analysis] 分析完成: {data}")
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

    logging.info(f"[skin_feedback] 生成反馈，输入数据: {data}")
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
    llm = ChatOpenAI(model_name="qwen2.5-vl-72b-instruct", temperature=0, openai_api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="请生成反馈")
    ]
    feedback = llm.invoke(messages).content.strip()
    logging.info(f"[skin_feedback] 反馈内容: {feedback}")
    return feedback 

def extract_best_face_frame(video_path):
    """
    从视频中采样关键帧，做人脸检测，选取最佳帧，保存为临时图片，返回图片路径。
    :param video_path: 视频文件路径
    :return: 最佳帧图片路径（str），无有效帧时返回 None
    """


    logging.info(f"[extract_best_face_frame] 输入视频路径: {video_path}")
    if not video_path or not os.path.exists(video_path):
        logging.warning(f"[extract_best_face_frame] 视频路径无效或文件不存在: {video_path}")
        return None
    # 采样关键帧（I帧）
    max_frames = 100
    keyframes = []
    try:
        container = av.open(video_path)
        for frame in container.decode(video=0):
            if frame.key_frame:
                img = frame.to_ndarray(format='bgr24')
                keyframes.append(img)
                if len(keyframes) >= max_frames:
                    break
        logging.info(f"[extract_best_face_frame] 采样到关键帧数: {len(keyframes)}")
    except Exception as e:
        logging.error(f"[extract_best_face_frame] 视频解码异常: {e}")
        return None
    if not keyframes:
        logging.warning(f"[extract_best_face_frame] 未采样到任何关键帧")
        return None
    # 人脸检测与关键点提取
    model = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
    model.prepare(ctx_id=0)
    best_score = -1
    best_kps_count = 0
    best_frame = None
    for idx, frame in enumerate(keyframes):
        faces = model.get(frame)
        logging.info(f"[extract_best_face_frame] 第{idx+1}帧检测到人脸数: {len(faces) if faces else 0}")
        if not faces:
            continue
        face = faces[0]
        kps = face.kps
        kps_count = kps.shape[0]
        score = face.det_score
        logging.info(f"[extract_best_face_frame] 第{idx+1}帧关键点数: {kps_count}, 置信度: {score}")
        if kps_count < 5:
            continue
        if kps_count > best_kps_count or (kps_count == best_kps_count and score > best_score):
            best_kps_count = kps_count
            best_score = score
            best_frame = frame
    if best_frame is None or best_kps_count < 4:
        logging.warning(f"[extract_best_face_frame] 未找到关键点数>=4的最佳帧，best_kps_count={best_kps_count}")
        return None
    # 保存最佳帧到临时文件
    tmpfile = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
    cv2.imwrite(tmpfile.name, best_frame)
    logging.info(f"[extract_best_face_frame] 最佳帧已保存: {tmpfile.name}, 关键点数: {best_kps_count}, 置信度: {best_score}")
    return tmpfile.name 