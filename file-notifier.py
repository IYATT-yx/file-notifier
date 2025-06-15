from application import Application
import constants as const
from dialog import Dialog
import common

import tkinter as tk
import sys
from tkinter import messagebox as mb
import os

Dialog()

def main():
    root = tk.Tk()
    root.title(const.Info.chineseName)
    root.iconbitmap(const.Path.iconPath)
    if '--hidewindow' in sys.argv:
        Application(root, hidden=True)
    else:
        Application(root, hidden=False)
    
    root.mainloop()

if __name__ == '__main__':
    lockFp = common.singleInstanceCheck()
    try:
        main()
    except Exception as e:
        err = f'捕获到未处置的异常：{common.exceptionTraceback2str(e)}'
        Dialog.log(err, Dialog.CRITICAL, False)
        mb.showerror('意外错误', err)
    finally:
        lockFp.close()
        os.remove(const.Path.fileLockPath)
