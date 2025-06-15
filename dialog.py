import constants as const
from queuemanager import QueueManager

import logging
import inspect
from tkinter import messagebox as mb
from queue import Queue

class Dialog:
    DEBUG: int = logging.DEBUG
    INFO: int = logging.INFO
    WARNING: int = logging.WARNING
    ERROR: int = logging.ERROR
    CRITICAL: int = logging.CRITICAL

    progressMsgQueue: Queue = None

    def __init__(self):
        """
        日志记录器初始化
        """
        # 用上级调用者所在的模块名称作为日志记录器名称
        loggerName = inspect.getmodule(inspect.currentframe().f_back).__name__
        logger = logging.getLogger(loggerName)
        if logger.hasHandlers():
            return
        
        # 文件输出日志
        fileHandler = logging.FileHandler(const.Path.dialogPath, encoding=const.DialogConfig.encoding)
        formatter = logging.Formatter(const.DialogConfig.format, const.DialogConfig.dateFormat)
        fileHandler.setFormatter(formatter)
        logger.addHandler(fileHandler)
        logger.setLevel(const.DialogConfig.level)
        Dialog.progressMsgQueue = QueueManager.get(const.QueueName.progressMsgQueue)

    @staticmethod
    def log(message: str, dialogLevel: int = DEBUG, proggressMsg: bool = True):
        """
        写日志

        Params:
            message: 日志信息
            dialogLevel: 日志类型
            proggressMsg: 是否将日志信息放入进展消息队列
        """
        loggerName = inspect.getmodule(inspect.currentframe().f_back).__name__
        logger = logging.getLogger(loggerName)
        if not logger.hasHandlers():
            mb.showerror('错误', '日志记录器未初始化，请初始化后使用！')
            return
        callerFrame = inspect.currentframe().f_back
        callerFunctionName = callerFrame.f_code.co_name
        callerLineno = callerFrame.f_lineno
        messageDetail = f'【{callerLineno:<3} 行，{callerFunctionName}()】 {message}'
        logger.log(dialogLevel, messageDetail)
        if proggressMsg:
            Dialog.progressMsgQueue.put(message)