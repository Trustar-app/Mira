# Mira 智能化妆镜

本项目为基于 LangGraph + LangChain + Gradio 的智能化妆镜 MVP。

## 目录结构

- app.py：应用入口，组合 Gradio UI 与 LangGraph 调用
- workflows/：工作流与节点处理逻辑
- tools/：多媒体与 AI 工具
- prompts/：提示词与格式化工具
- config.py：配置文件
- requirements.txt：依赖包

## 功能简介

- 视频/音频/文本输入
- 意图识别与多轮对话
- 肤质检测、产品推荐、化妆指导
- 用户档案与进度管理

> 详细设计与实现请见 design.md 