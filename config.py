# config.py
# 日志配置
# 日志配置
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
    
    # 其他模块日志配置
}

# 配置模型名、API key、模型输入类型等

MODEL_NAME = ""
SUPPORT_VIDEO_AUDIO = False 

OPENAI_API_KEY = "sk-4be3f2729fbf48f7b91dec9f2415cbd7"
OPENAI_API_BASE = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# YouCam API 配置
YOUCAM_API_KEY = "YKzXjdtGCDstjn0A1qIflbTha6j5jIKd"
YOUCAM_SECRET_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDonv79JRS9aFJRVl8W0BTRwMqZPUCuTCKrG+DrvJh0azEixeBxmz09K+IwtlWZufm3CHnUMcsZmJgp5gSYpcT1zHVhYZzSC0Q9vYv7Np3t6X8H/eJ/PXfXZvS04tHU0/8JaZ75SLDLmKRLKCgOwuYvMlSVdsmAUXx6mJLn3TUd/QIDAQAB" 