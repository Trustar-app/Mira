import logging
import av
import insightface
import numpy as np
import tempfile
import cv2
import os
import requests
import json
from config import YOUCAM_API_KEY, YOUCAM_SECRET_KEY, OPENAI_API_BASE, OPENAI_API_KEY
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from utils.loggers import MiraLog
import base64
import io
import tempfile
import time
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

def get_access_token():
    """
    获取YouCam API的access_token。
    :return: access_token（str）
    """
    # 替换为实际 client_id 和 client_secret
    client_id = YOUCAM_API_KEY
    client_secret_pem = f"""-----BEGIN PUBLIC KEY-----
    {YOUCAM_SECRET_KEY}
    -----END PUBLIC KEY-----"""

    # 1. 构造待加密的字符串
    timestamp = str(int(time.time() * 1000))  # 当前时间戳（毫秒）
    message = f"client_id={client_id}&timestamp={timestamp}".encode('utf-8')

    # 2. 加载公钥
    public_key = serialization.load_pem_public_key(client_secret_pem.encode('utf-8'))

    # 3. 使用公钥加密
    encrypted = public_key.encrypt(
        message,
        padding.PKCS1v15()
    )

    # 4. 对加密结果进行 Base64 编码，得到 id_token
    id_token = base64.b64encode(encrypted).decode('utf-8')

    # 5. 构造认证请求
    url = "https://yce-api-01.perfectcorp.com/s2s/v1.0/client/auth"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "client_id": client_id,
        "id_token": id_token
    }

    # 6. 发送 POST 请求获取 access_token
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        access_token = response.json()["result"]["access_token"]
        MiraLog("skin_analysis", f"[get_access_token] 获取access_token成功: {access_token}")
        return access_token
    else:
        MiraLog("skin_analysis", f"[get_access_token] 获取access_token失败: {response.text}", "ERROR")
        return None



# YouCam肤质分析API封装
def upload_image_for_skin_analysis(image_bytes, access_token):
    """
    上传图片到YouCam服务器，用于肤质分析
    
    Args:
        image_bytes: 二进制图像数据
        access_token: 访问令牌
        
    Returns:
        str: 上传成功后返回的file_id
    """
    MiraLog("skin_analysis", "开始准备上传肤质分析图片")
    
    # 1. 首先获取上传URL
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    file_size = len(image_bytes)
    payload = {
        "files": [
            {
                "content_type": "image/jpeg",
                "file_name": "skin_analysis.jpg",
                "file_size": file_size
            }
        ]
    }
    
    MiraLog("skin_analysis", "请求上传URL")
    resp = requests.post(
        "https://yce-api-01.perfectcorp.com/s2s/v1.1/file/skin-analysis",
        headers=headers,
        json=payload
    )
    
    if resp.status_code != 200:
        MiraLog("skin_analysis", f"获取上传URL失败：{resp.text}", "ERROR")
        raise RuntimeError(f"获取上传URL失败：{resp.text}")
    
    MiraLog("skin_analysis", f"获取上传URL成功，响应: {resp.text}")
    
    # 2. 解析响应获取上传URL和文件ID
    response_data = resp.json()
    file_data = response_data["result"]["files"][0]
    file_id = file_data["file_id"]
    upload_request = file_data["requests"][0]
    
    upload_url = upload_request["url"]
    upload_headers = upload_request["headers"]
    upload_method = upload_request["method"]
    
    MiraLog("skin_analysis", f"获取上传URL成功，file_id: {file_id}")
    
    # 3. 上传文件到指定URL
    MiraLog("skin_analysis", f"开始上传文件到{upload_url}")
    
    if upload_method.upper() == "PUT":
        upload_resp = requests.put(
            upload_url,
            headers=upload_headers,
            data=image_bytes
        )
    else:  # 默认使用POST
        upload_resp = requests.post(
            upload_url,
            headers=upload_headers,
            data=image_bytes
        )
        
    if upload_resp.status_code not in [200, 201, 204]:
        MiraLog("skin_analysis", f"上传文件失败：状态码 {upload_resp.status_code}, 响应: {upload_resp.text}", "ERROR")
        raise RuntimeError(f"上传文件失败：状态码 {upload_resp.status_code}")
    
    MiraLog("skin_analysis", f"文件上传成功，file_id: {file_id}")
    return file_id

def start_skin_analysis_task(file_id, access_token):
    """
    发起肤质分析任务
    
    Args:
        file_id: 上传图片获得的ID
        access_token: 访问令牌
        
    Returns:
        str: 任务ID
    """
    MiraLog("skin_analysis", f"开始发起肤质分析任务，file_id: {file_id}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 构建符合API要求的请求结构 - 根据官方示例
    payload = {
        "request_id": int(time.time()),
        "payload": {
            "file_sets": {
                "src_ids": [file_id]
            },
            "actions": [
                {
                    "id": 0,
                    "params": {},
                    "dst_actions": [
                        "wrinkle", "pore", "texture", "acne", 
                        "oiliness", "radiance", "dark_circle_v2"
                    ]
                }
            ]
        }
    }
    
    MiraLog("skin_analysis", f"发送肤质分析请求：{json.dumps(payload)}")
    
    resp = requests.post(
        "https://yce-api-01.perfectcorp.com/s2s/v1.0/task/skin-analysis",
        headers=headers,
        json=payload
    )
    
    if resp.status_code != 200:
        MiraLog("skin_analysis", f"AI分析任务发起失败：{resp.text}", "ERROR")
        raise RuntimeError(f"AI分析任务发起失败：{resp.text}")
    
    MiraLog("skin_analysis", f"分析任务API响应：{resp.text}")
    task_id = resp.json()["result"]["task_id"]
    MiraLog("skin_analysis", f"AI分析任务发起成功，task_id: {task_id}")
    return task_id

def poll_skin_analysis_task(task_id, access_token, max_retries=30):
    """
    轮询肤质分析任务状态并下载结果
    
    Args:
        task_id: 任务ID
        access_token: 访问令牌
        max_retries: 最大重试次数
        
    Returns:
        dict: 分析结果
    """
    MiraLog("skin_analysis", f"开始轮询任务状态，task_id: {task_id}")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    retry_count = 0
    
    while retry_count < max_retries:
        resp = requests.get(
            f"https://yce-api-01.perfectcorp.com/s2s/v1.0/task/skin-analysis?task_id={task_id}",
            headers=headers
        )
        
        if resp.status_code != 200:
            MiraLog("skin_analysis", f"查询任务状态失败：{resp.text}", "ERROR")
            raise RuntimeError(f"查询任务状态失败：{resp.text}")
            
        result = resp.json()["result"]
        
        if result["status"] == "success":
            MiraLog("skin_analysis", "任务完成")
            # 获取结果下载URL
            download_url = result["results"][0]["data"][0]["url"]
            MiraLog("skin_analysis", f"获取到结果下载URL: {download_url}")
            
            # 下载结果ZIP文件
            zip_response = requests.get(download_url)
            if zip_response.status_code != 200:
                MiraLog("skin_analysis", f"下载结果文件失败: {zip_response.status_code}", "ERROR")
                raise RuntimeError(f"下载结果文件失败: {zip_response.status_code}")
            
            # 解析结果
            import io
            import zipfile
            import json
            
            with zipfile.ZipFile(io.BytesIO(zip_response.content)) as zip_file:
                # 查找结果JSON文件
                json_files = [f for f in zip_file.namelist() if f.endswith('score_info.json')]
                if not json_files:
                    MiraLog("skin_analysis", "ZIP文件中未找到结果JSON", "ERROR")
                    raise RuntimeError("ZIP文件中未找到结果JSON")
                
                # 读取JSON结果
                with zip_file.open(json_files[0]) as json_file:
                    analysis_result = json.load(json_file)
                    MiraLog("skin_analysis", f"解析结果成功: {json.dumps(analysis_result, ensure_ascii=False)}")
                    return analysis_result
            
        elif result["status"] == "error":
            error_msg = result.get("error_message", "未知错误")
            error_code = result.get("error", "unknown")
            MiraLog("skin_analysis", f"AI分析失败：{error_code} - {error_msg}", "ERROR")
            raise RuntimeError(f"AI分析失败：{error_code} - {error_msg}")
        
        # 按照API返回的轮询间隔等待
        wait_time = result.get("polling_interval", 1000) / 1000.0
        MiraLog("skin_analysis", f"任务进行中，等待 {wait_time} 秒后重试")
        import time
        time.sleep(wait_time)
        retry_count += 1
    
    raise RuntimeError(f"轮询超时，任务可能仍在处理中")

def skin_analysis(image_base64):
    """
    调用 YouCam API 进行肤质分析。
    :param image_base64: base64编码的图像数据字符串
    :return: 原始分析结果，异常时抛出异常或返回 None
    """
    import base64
    
    MiraLog("skin_analysis", f"开始肤质分析，输入base64图片长度: {len(image_base64) if image_base64 else 0}")
    
    # 1. 获取 access_token
    access_token = os.environ.get("YOUCAM_ACCESS_TOKEN")
    if not access_token:
        access_token = get_access_token()
        if access_token is not None:
            os.environ["YOUCAM_ACCESS_TOKEN"] = access_token
        else:
            MiraLog("skin_analysis", "获取access_token失败", "ERROR")
            raise RuntimeError("获取access_token失败")
    
    # 2. 准备图片数据
    if not image_base64:
        MiraLog("skin_analysis", "未提供base64图像数据", "ERROR")
        raise ValueError("未提供base64图像数据")
    
    # 去除可能的base64前缀
    if ',' in image_base64:
        image_base64 = image_base64.split(',', 1)[1]
    
    # 解码base64数据
    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception as e:
        MiraLog("skin_analysis", f"Base64解码失败: {e}", "ERROR")
        raise ValueError(f"Base64解码失败: {e}")
    
    # 3. 上传图片
    file_id = upload_image_for_skin_analysis(image_bytes, access_token)
    
    # 4. 发起肤质分析任务
    task_id = start_skin_analysis_task(file_id, access_token)
    
    # 5. 轮询任务状态
    result = poll_skin_analysis_task(task_id, access_token)
    
    MiraLog("skin_analysis", "肤质分析完成")
    return result

# AI肤质分析结果反馈生成

def skin_feedback(data):
    """
    用大模型生成肤质分析反馈。
    :param data: 肤质分析原始结果
    :return: 反馈文本（str）
    """
    MiraLog("skin_analysis", f"[skin_feedback] 生成反馈，输入数据: {data}")
    SYSTEM_PROMPT = (
        "你是用户贴心的人性化健康伴侣Mira。请根据用户的肤质检测结果，生成一段自然、连贯、温暖的中文聊天回复。"
        "回复内容应尽量涵盖以下四个方面，但不要生硬分条或罗列：\n"
        "—— 检测完成的温馨提示\n"
        "—— 针对用户肤质的专业分析和建议\n"
        "—— 充满关怀和鼓励的情感反馈\n"
        "—— 贴心的下一步互动建议\n"
        "请用亲切、鼓励、自然的语气，将这些内容巧妙融合在一段聊天回复中，让用户感受到陪伴和支持。\n"
        "用户肤质检测原始数据如下：\n"
        f"{data}"
    )
    llm = ChatOpenAI(model_name="qwen2.5-vl-72b-instruct", temperature=0, openai_api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content="请生成反馈")
    ]
    # 返回生成器，流式输出
    def stream_gen():
        for chunk in llm.stream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content
    return stream_gen()

def extract_best_face_frame(video_base64):
    """
    从base64编码的视频中采样关键帧，做人脸检测，选取最佳帧，返回最佳帧的base64编码图片。
    :param video_base64: base64编码的视频数据
    :return: 最佳帧图片的base64编码(str)，无有效帧时返回 None
    """

    MiraLog("skin_analysis", f"[extract_best_face_frame] 接收到base64视频数据，长度: {len(video_base64) if video_base64 else 0}")
    
    if not video_base64:
        MiraLog("skin_analysis", "[extract_best_face_frame] base64视频数据为空", "WARNING")
        return None
    
    # 将base64数据解码为二进制
    try:
        # 去除可能的base64前缀
        if ',' in video_base64:
            video_base64 = video_base64.split(',', 1)[1]
        
        # 处理base64填充问题
        missing_padding = len(video_base64) % 4
        if missing_padding:
            video_base64 += '=' * (4 - missing_padding)
        
        video_data = base64.b64decode(video_base64)
    except Exception as e:
        MiraLog("skin_analysis", f"[extract_best_face_frame] base64解码失败: {e}", "ERROR")
        return None
    
    # 创建临时文件来存储视频数据，因为av库更好地支持文件
    temp_video_file = None
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
            temp_video_file = temp_file.name
            temp_file.write(video_data)
        
        # 采样关键帧（I帧）
        max_frames = 100
        keyframes = []
        
        container = av.open(temp_video_file)
        for frame in container.decode(video=0):
            if frame.key_frame:
                img = frame.to_ndarray(format='bgr24')
                keyframes.append(img)
                if len(keyframes) >= max_frames:
                    break
        
        MiraLog("skin_analysis", f"[extract_best_face_frame] 采样到关键帧数: {len(keyframes)}")
        
        if not keyframes:
            MiraLog("skin_analysis", "[extract_best_face_frame] 未采样到任何关键帧", "WARNING")
            return None
        
        # 人脸检测与关键点提取
        model = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        model.prepare(ctx_id=0)
        
        best_score = -1
        best_kps_count = 0
        best_frame = None
        
        for idx, frame in enumerate(keyframes):
            faces = model.get(frame)
            MiraLog("skin_analysis", f"[extract_best_face_frame] 第{idx+1}帧检测到人脸数: {len(faces) if faces else 0}")
            
            if not faces:
                continue
                
            face = faces[0]
            kps = face.kps
            kps_count = kps.shape[0]
            score = face.det_score
            
            MiraLog("skin_analysis", f"[extract_best_face_frame] 第{idx+1}帧关键点数: {kps_count}, 置信度: {score}")
            
            if kps_count < 5:
                continue
                
            if kps_count > best_kps_count or (kps_count == best_kps_count and score > best_score):
                best_kps_count = kps_count
                best_score = score
                best_frame = frame
        
        if best_frame is None or best_kps_count < 4:
            MiraLog("skin_analysis", f"[extract_best_face_frame] 未找到关键点数>=4的最佳帧，best_kps_count={best_kps_count}", "WARNING")
            return None
        
        # 将最佳帧转换为base64
        _, buffer = cv2.imencode('.jpg', best_frame)
        jpg_as_text = base64.b64encode(buffer).decode('utf-8')
        
        MiraLog("skin_analysis", f"[extract_best_face_frame] 已选取最佳帧，关键点数: {best_kps_count}, 置信度: {best_score}")
        return jpg_as_text
        
    except Exception as e:
        MiraLog("skin_analysis", f"[extract_best_face_frame] 处理过程发生异常: {e}", "ERROR")
        import traceback
        MiraLog("skin_analysis", traceback.format_exc(), "ERROR")
        return None
        
    finally:
        # 清理临时文件
        if temp_video_file and os.path.exists(temp_video_file):
            try:
                os.unlink(temp_video_file)
            except:
                pass 

def skin_analysis_by_QwenYi(image_base64):
    """
    调用 QwenYi API 进行肤质分析。
    :param image_base64: base64编码的图像数据字符串
    :return: 原始分析结果，异常时抛出异常或返回 None
    """
    SYSTEM_PROMPT = (
        "你是一个专业的皮肤健康检测人员，请根据用户的照片检测结果，生成一个json形式的肤质检测结果。\n"
        "针对：斑点、皱纹、毛孔、发红、出油、痘痘、黑眼圈、眼袋、泪沟、皮肤紧致度 这10个维度，给出评分（0～10分，0分表示没有，10分表示非常严重）\n"
        "针对：肤质类型 给出类型（油性，干性，中性，混合性）\n"
        "请用json格式输出，不要输出任何解释。\n"
    )

    # 创建图文输入 message
    image_data_url = f"data:image/jpeg;base64,{image_base64}"
    image_message = HumanMessage(content=[
        {
            "type": "image_url",
            "image_url": {
                "url": image_data_url,
            }
        }
    ])

    llm = ChatOpenAI(model_name="qwen2.5-vl-72b-instruct", temperature=0, openai_api_key=OPENAI_API_KEY, openai_api_base=OPENAI_API_BASE).with_structured_output(method="json_mode")
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        image_message
    ]
    feedback = llm.invoke(messages)

    MiraLog("skin_analysis", f"[skin_feedback] 反馈内容: {feedback}")
    return feedback 