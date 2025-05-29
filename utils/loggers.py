# utils/logger.py
import logging
import os
from typing import Dict, Optional, Union


def setup_logger(
    name: str,
    level: Union[str, int] = "INFO",
    console_output: bool = True,
    file_output: bool = False,
    file_path: Optional[str] = None,
    format_str: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    propagate: bool = False,
    clear_existing_log: bool = False
) -> logging.Logger:
    """
    创建并配置一个日志器
    
    Args:
        name: 日志器名称
        level: 日志级别，可以是字符串("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")或整数级别值
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
        file_path: 日志文件路径，如果为None且file_output为True，则使用logs/{name}.log
        format_str: 日志格式字符串
        propagate: 是否传播日志到父级日志器
        clear_existing_log: 是否清空现有日志文件
        
    Returns:
        配置好的日志器实例
    """
    # 获取日志级别
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    
    # 获取或创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = propagate
    
    # 清除已有的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(format_str)
    
    # 添加控制台处理器
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(level)
        logger.addHandler(console_handler)
    
    # 添加文件处理器
    if file_output:
        if file_path is None:
            # 确保logs目录存在
            os.makedirs("logs", exist_ok=True)
            file_path = f"logs/{name}.log"
        else:
            # 确保指定的日志文件目录存在
            log_dir = os.path.dirname(file_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
        
        # 如果需要清空日志文件
        if clear_existing_log and os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"--- 日志重置于 {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', None, None))} ---\n")
        
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    
    return logger


def setup_loggers_from_config(config) -> Dict[str, logging.Logger]:
    """
    从配置中创建多个日志器
    
    Args:
        config: 包含日志配置的配置模块或字典
        
    Returns:
        日志器名称到日志器实例的映射
    """
    loggers = {}
    
    # 获取日志配置，如果不存在则使用默认配置
    logger_configs = getattr(config, "LOGGERS", {})
    if not logger_configs:
        # 默认添加一个应用日志器
        loggers["app"] = setup_logger("app", "INFO", True, False)
        return loggers
    
    # 创建每个配置的日志器
    for name, logger_config in logger_configs.items():
        level = logger_config.get("level", "INFO")
        console = logger_config.get("console", True)
        file = logger_config.get("file", False)
        file_path = logger_config.get("file_path", None)
        format_str = logger_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        propagate = logger_config.get("propagate", False)
        clear_log = logger_config.get("clear_log", True)
        
        loggers[name] = setup_logger(
            name=name,
            level=level,
            console_output=console,
            file_output=file,
            file_path=file_path,
            format_str=format_str,
            propagate=propagate,
            clear_existing_log=clear_log
        )
    
    return loggers


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志器，如果不存在则创建
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    # 导入配置
    try:
        import config
        loggers_dict = getattr(config, "_LOGGERS_CACHE", None)
        if loggers_dict is None:
            loggers_dict = setup_loggers_from_config(config)
            # 缓存日志器字典到config
            setattr(config, "_LOGGERS_CACHE", loggers_dict)
        
        if name in loggers_dict:
            return loggers_dict[name]
        else:
            # 自动创建新的日志器
            logger = setup_logger(name, "INFO", True, False)
            loggers_dict[name] = logger
            return logger
    except ImportError:
        # 配置模块不存在时，返回默认日志器
        return setup_logger(name, "INFO", True, False)


def MiraLog(logger_name: str, msg: str = "", log_level: str = "DEBUG"):
    """ 
    默认输出DEBUG级别的日志，正确显示调用者的函数名和行号
    """
    logger = get_logger(logger_name)
    
    # fix: 处理 MiraLog 的 funcname 和 lineno 等信息不符合预期的问题
    if log_level == "INFO":
        logger.info(msg, stacklevel=2)
    elif log_level == "DEBUG":
        logger.debug(msg, stacklevel=2)
    elif log_level == "WARNING":
        logger.warning(msg, stacklevel=2)
    elif log_level == "ERROR":
        logger.error(msg, stacklevel=2)
    elif log_level == "CRITICAL":
        logger.critical(msg, stacklevel=2)
    else:
        logger.info(msg, stacklevel=2)



# def MiraLog(logger_name: str, msg: str = "", log_level: str = "DEBUG"):
#     """ python < 3.8 版本使用这个实现 """
#     import inspect

#     logger = get_logger(logger_name)
    
#     # 获取调用者的栈帧信息
#     caller = inspect.currentframe().f_back
#     filename = caller.f_code.co_filename
#     lineno = caller.f_lineno
#     func_name = caller.f_code.co_name
    
#     # 创建带有正确位置信息的记录
#     extra = {
#         'funcName': func_name,
#         'pathname': filename,
#         'lineno': lineno
#     }
    
#     if log_level == "INFO":
#         logger.info(msg, extra=extra)
#     elif log_level == "DEBUG":
#         logger.debug(msg, extra=extra)
#     elif log_level == "WARNING":
#         logger.warning(msg, extra=extra)
#     elif log_level == "ERROR":
#         logger.error(msg, extra=extra)
#     elif log_level == "CRITICAL":
#         logger.critical(msg, extra=extra)
#     else:
#         logger.info(msg, extra=extra)