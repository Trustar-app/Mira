import asyncio
import base64
import os
from pathlib import Path

import app.agent as ag
from app.llm import LLM
from app.logger import logger


def image_to_base64(image_path) -> str:
    """将图片转换为base64字符串"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')


def video_to_base64(video_path) -> str:
    with open(video_path, "rb") as video_file:
        return base64.b64encode(video_file.read()).decode('utf-8')

async def main(agent):
    prompt = "点评这个视频"
    prompt2 = "点评周迅的素颜照"
    image_base64 = image_to_base64("./data/zhouxun.png")
    video_base64 = video_to_base64("data/output_3s.mp4")


    # result = await agent.run(text_request=prompt, image_request=image_base64)
    print("--------------------------------------------------- 第一次对话 ---------------------------------------------------")
    result = await agent.run(text_request=prompt, video_request=video_base64)
    # result = await agent.run(text_request=prompt)
    print(result)

    print(
        "--------------------------------------------------- 第二次对话 ---------------------------------------------------")
    result = await agent.run(text_request=prompt2, image_request=image_base64)
    print(result)

myagent = ag.QwenOmniAgent(llm=LLM(config_name="omni"))
if __name__ == '__main__':
    asyncio.run(main(myagent))
    print("debug point")


