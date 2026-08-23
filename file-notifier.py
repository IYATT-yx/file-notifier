"""
file: file-notifier.py
description: 文件变更通知器
author: IYATT-yx
copyright:  Copyright (c) 2026 IYATT-yx.
            Licensed under the MIT License. See LICENSE file in the project root for full license information.
"""
from application import Application
import constants as const
from dialog import Dialog
import common

import tkinter as tk
import sys
from tkinter import messagebox as mb
import os
import subprocess
import time


def run_worker():
    """子进程-业务逻辑"""
    Dialog()
    lockFp = common.singleInstanceCheck()
    
    try:
        root = tk.Tk()
        root.title(const.Info.chineseName)
        root.iconbitmap(const.Path.iconPath)
        
        hidden = '--hidewindow' in sys.argv
        Application(root, hidden=hidden)
        
        root.mainloop()
    except Exception as e:
        err = f'捕获到未处置的异常：{common.exceptionTraceback2str(e)}'
        Dialog.log(err, Dialog.CRITICAL, False)
        mb.showerror('意外错误', err)
    finally:
        try:
            lockFp.close()
            if os.path.exists(const.Path.fileLockPath):
                os.remove(const.Path.fileLockPath)
        except Exception:
            pass

def run_watchdog():
    """守护进程逻辑（父进程运行），负责应对底层 C/Win32 API 崩溃导致的进程退出"""
    Dialog()
    Dialog.log("[Watchdog] 文件监视守护服务已启动...", Dialog.INFO, False)
    
    # 判断是否处于打包状态
    is_packaged = not sys.argv[0].endswith('.py')
    
    # 根据打包状态正确构造子进程调用命令
    if is_packaged:
        worker_args = [sys.argv[0], "--worker"] + [arg for arg in sys.argv[1:] if arg != "--worker"]
    else:
        script_path = os.path.abspath(sys.argv[0])
        worker_args = [sys.executable, script_path, "--worker"] + [arg for arg in sys.argv[1:] if arg != "--worker"]

    while True:
        # 在启动子进程前，先强制清理残留的锁文件（防止底层崩溃导致锁文件没删，子进程单例检查失败）
        if os.path.exists(const.Path.fileLockPath):
            try:
                os.remove(const.Path.fileLockPath)
            except Exception:
                pass

        Dialog.log("正在启动文件监视核心...", Dialog.INFO, False)
        
        # 启动子进程
        process = subprocess.Popen(worker_args)
        exit_code = process.wait()

        if exit_code == 0:
            Dialog.log("[Watchdog] 核心进程已正常退出，守护服务终止。", Dialog.INFO, False)
            break

        # 否则说明发生了异常崩溃（如局域网断开触发的 C 层面崩溃）
        Dialog.log(f"警告：监视进程崩溃退出 (Exit Code: {exit_code})，5秒后自动重试...", Dialog.WARNING, False)
        time.sleep(5)

if __name__ == '__main__':
    # 通过内部参数区分当前进程是“守护父进程”还是“工作子进程”
    if "--worker" in sys.argv:
        run_worker()
    else:
        run_watchdog()