# config.py
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
    # 其他模块日志配置
    
}
