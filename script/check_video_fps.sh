#!/bin/bash

# 需要安装 ffmpeg 工具
# 检查视频的帧率
# 参数: 视频文件路径
# 返回: 视频的帧率

video_path=$1
ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of default=noprint_wrappers=1:nokey=1 $video_path
