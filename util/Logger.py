import os
import logging
from loguru import logger
import multiprocessing
import time



def create_logger(log_filename="output.log", log_dir="log"):
    # 确保日志文件夹存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    # 获取当前年-月-日-小时-分钟
    # time_str = time.strftime("%Y-%m-%d", time.localtime(time.time()))
    # log_path = log_path.replace(".log", f"_{time_str}.log")
    # 获取日志文件的绝对路径
    log_path = os.path.join(log_dir, log_filename)

    
    logger = multiprocessing.get_logger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(levelname)s] %(asctime)s [ %(processName)s][%(filename)s:%(lineno)d, %(funcName)s] %(message)s"
    )
    handler = logging.FileHandler(log_path,encoding='utf-8')
    handler.setFormatter(formatter)

    # log to console as well
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)

    # this bit will make sure you won't have
    # duplicated messages in the output
    if not len(logger.handlers):
        logger.addHandler(handler)
        logger.addHandler(consoleHandler)

    return logger


