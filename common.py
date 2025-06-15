"""公共实现"""
import constants as const
from dialog import Dialog

import os
import shutil
import msvcrt
from tkinter import messagebox as mb
import sys
import traceback

Dialog()

def copyDatabaseFile():
    """复制数据库文件"""
    shutil.copy(const.Path.databaseTemplatePath, const.Path.databasePath)

def checkDatabaseFile():
    """检查数据库文件
    如果不存在数据库文件就复制模板
    """
    if not os.path.exists(const.Path.databasePath):
        copyDatabaseFile()

def singleInstanceCheck():
    """单实例检查"""
    fp = open(const.Path.fileLockPath, 'w')
    try:
        msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
    except:
        Dialog.log('程序重复运行', Dialog.WARNING)
        mb.showwarning('警告', '已有实例运行中，请勿重复启动')
        sys.exit(0)
    return fp

def checkSubpath(base: str, test: str) -> bool:
    """检查 test 是否是 base 的子路径
    
    Args:
        base (str): 基础路径
        test (str): 测试路径
        
    Returns:
        bool: 是否为子路径
    """
    base = os.path.normcase(os.path.normpath(base))
    test = os.path.normcase(os.path.normpath(test))

    if os.path.splitdrive(base)[0] != os.path.splitdrive(test)[0]:
        return False

    return os.path.commonpath([base, test]) == base and base != test
        
def exceptionTraceback2str(e: Exception) -> str:
    """
    将异常对象的完整 traceback 信息转换为字符串。

    Args:
        e (Exception): 异常对象。

    Returns:
        str: 包含异常类型、错误信息和调用栈的完整字符串表示。
    """
    return ''.join(traceback.format_exception(type(e), e, e.__traceback__))