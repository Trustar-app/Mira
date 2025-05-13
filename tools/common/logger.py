import logging
import sys
import os

def get_logger(name, log_file=None):
    """
    获取 logger 实例。
    :param name: 日志名称
    :param log_file: 日志文件名（可选）
    :return: logger 对象
    """
    if log_file is None:
        log_file = "logs/mira.log"
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    logger = logging.getLogger(f"{name}:{log_file}")
    if not logger.handlers:
        # 控制台输出
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        # 文件输出
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger