# config.py
# 日志配置

# Mira 首次见面打招呼提示词
MIRA_GREETING_PROMPT = """
# 信息源
## 用户画像
{user_profile}

## 用户产品目录
{products_directory}

## 日常信息
当前时间：{current_time}
季节：{season}

# 主动发消息
你需要根据当前的时间、季节等信息，从信息源中灵活提取有用的细节，结合你的角色设定和世界观，主动给用户发一条定制化的打招呼消息。
消息应该：
1. 简短有趣
2. 介绍自己是谁
3. 简要说明主要功能（个人档案创建、产品分析与推荐、肤质分析、化妆护肤指导、日常聊天）
4. 询问用户想要体验哪项功能
"""

LOGGERS = {
    # 应用主日志
    "app": {
        "level": "DEBUG",          # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
        "console": True,          # 是否输出到控制台
        "file": True,             # 是否输出到文件
        "file_path": "logs/app.log",  # 日志文件路径
        "format": "[%(asctime)s][%(name)s][%(funcName)s %(lineno)d] %(message)s",  # 日志格式
        "clear_log": True,  # 启动时清空日志文件
        "propagate": False        # 是否传播到父级日志器
    },
    
    # mira_graph 日志
    "mira_graph": {
        "level": "DEBUG",         
        "console": True,
        "file": True,
        "file_path": "logs/mira_graph.log",
        "format": "[%(asctime)s][%(name)s][%(funcName)s %(lineno)d] %(message)s",  # 日志格式
        "clear_log": True,  # 启动时清空日志文件
        "propagate": False        # 是否传播到父级日志器
    },

    # 皮肤分析模块日志
    "skin_analysis": {
        "level": "DEBUG",         
        "console": True,
        "file": True,
        "file_path": "logs/skin_analysis.log",
        "format": "[%(asctime)s][%(name)s][%(funcName)s %(lineno)d] %(message)s",  # 日志格式
        "clear_log": True,  # 启动时清空日志文件
        "propagate": False        # 是否传播到父级日志器
    },

    # 用户建档模块日志
    "user_profile_creation": {
        "level": "DEBUG",         
        "console": True,
        "file": True,
        "file_path": "logs/user_profile_creation.log",
        "format": "[%(asctime)s][%(name)s][%(funcName)s %(lineno)d] %(message)s",  # 日志格式
        "clear_log": True,  # 启动时清空日志文件
        "propagate": False        # 是否传播到父级日志器
    },
    

    # 产品识别模块日志
    "product_recognition": {
        "level": "DEBUG",         
        "console": True,
        "file": True,
        "file_path": "logs/product_recognition.log",
        "format": "[%(asctime)s][%(name)s][%(funcName)s %(lineno)d] %(message)s",  # 日志格式
        "clear_log": True,  # 启动时清空日志文件
        "propagate": False        # 是否传播到父级日志器
    },

    # tts 日志
    "tts": {
        "level": "DEBUG",         
        "console": True,
        "file": True,
        "file_path": "logs/tts.log",
        "format": "[%(asctime)s][%(name)s][%(funcName)s %(lineno)d] %(message)s",  # 日志格式
        "clear_log": True,  # 启动时清空日志文件
        "propagate": False        # 是否传播到父级日志器
    },

    # 其他模块日志配置
    
}
