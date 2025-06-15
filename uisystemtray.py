"""托盘"""
import constants as const

import pystray
import tkinter as tk
from threading import Thread
from PIL import Image

class SystemTray(Thread):
    def __init__(self, root: tk.Tk, extraMenuList: list[pystray.MenuItem] = []):
        """初始化系统托盘图标

        Args:
            root (tk.Tk): 主窗口
        """
        super().__init__()
        self.root = root
        self.extraMenuList = extraMenuList
        # 设置为守护线程
        self.daemon = True

    def showWindow(self):
        """显示主窗口"""
        self.root.after(0, self.root.deiconify)

    def stopSystemTray(self):
        self.icon.stop()

    def run(self):
        """启动托盘图标"""
        menu = pystray.Menu(
            pystray.MenuItem('打开窗口', self.showWindow, default=True),
            *self.extraMenuList
        )

        img = Image.open(const.Path.iconPath)
        self.icon = pystray.Icon(const.Info.chineseName, img, const.Info.chineseName, menu)
        self.icon.run()