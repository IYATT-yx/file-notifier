"""应用"""
import common
import constants as const
from uisystemtray import SystemTray
from uiemailconfigeditdialog import EmailConfigEditDialog
from blinkingbutton import BlinkingButton
from uiwatchdiredit import WatchDirEdit
from databaseoperator import DatabaseOperator
from autostart import AutoStart
from smtpthreading import SmtpThreading
from watchdirthreading import WatchDirThreadPoolManager
from dialog import Dialog
from queuemanager import QueueManager
from buildtime import buildTime

import tkinter as tk
from tkinter import messagebox as mb
import queue
import os
import pystray
import threading
import datetime

Dialog()

class Application(tk.Frame):
    def __init__(self, root: tk.Tk, hidden: bool = False):
        """初始化应用程序窗口
        Args:
            root (tk.Tk): 主窗口
            hidden (bool): 是否隐藏主窗口，默认为False
        """
        # 连接数据库
        common.checkDatabaseFile()
        DatabaseOperator.connect(const.Path.databasePath)

        # 资源对象
        self.watchDirThreadPoolManagerObj = None
        self.systemTray = None
        self.smtpThreadingObj = None
        self.root = root

        self.sendEmailQueue = QueueManager.get(const.QueueName.sendEmailQueue)
        self.progressMsgQueue = QueueManager.get(const.QueueName.progressMsgQueue)
        self.blinkingSignalQueue = QueueManager.get(const.QueueName.blinkingSignalQueue)

        # 初始化准备
        super().__init__(root)
        self.root.protocol('WM_DELETE_WINDOW', self.onClosing)
        if hidden:
            Dialog.log('隐藏窗口启动', proggressMsg=False)
            self.root.withdraw()
        else:
            Dialog.log('正常启动', proggressMsg=False)
        self.pack(fill=tk.BOTH, expand=True)
        self.rowconfigure(0, weight=1)
        self.columnconfigure([0, 1, 2, 3, 4], weight=1)

        self.createWidgets()
        # self.checkCrash()

    def createWidgets(self):
        """创建应用程序控件"""
        # 监控路径编辑框 (0, 0:4)
        self.watchDirEditObj = WatchDirEdit(self)
        self.watchDirEditObj.grid(row=0, column=0, columnspan=5, sticky=tk.NSEW)
        watchDirObjList = DatabaseOperator.readWatchDir()
        self.watchDirEditObj.update(watchDirObjList)
        # 状态显示文本框 (1, 0:4) 滚动条 (1, 5)
        self.progressMsgShowText = tk.Text(self, wrap=tk.WORD, height=20, state=tk.DISABLED)
        self.progressMsgShowText.grid(row=1, column=0, columnspan=5, sticky=tk.NSEW)
        scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.progressMsgShowText.yview)
        scrollbar.grid(row=1, column=5, sticky=tk.NSEW)
        self.progressMsgShowText.configure(yscrollcommand=scrollbar.set)
        self.progressMsgCounter = 0
        """进展消息计数"""
        # 重启按钮 (2, 0:1)
        self.restartButton = BlinkingButton(self, blinkColor='red', blinkInterval=200, text='重新启动', bd=5, command=self.onRestartButton)
        self.restartButton.grid(row=2, column=0, columnspan=2, sticky=tk.EW)
        # 退出按钮 (2, 3:4)
        tk.Button(self, text='退出', bd=5, command=self.exitApp) \
        .grid(row=2, column=3, columnspan=2, sticky=tk.EW)
        # 创建托盘
        extraMenuList = [
            pystray.MenuItem('退出', self.exitApp)
        ]
        self.systemTray = SystemTray(self.root, extraMenuList)
        self.systemTray.start()
        # 创建菜单栏
        self.createMenuBar()

        # 设置窗口居中
        self.root.after_idle(self.centerWindow)
        # 启动服务
        self.root.after_idle(self.startServices)

    # def checkCrash(self):
    #     """检查上次程序是否崩溃"""
    #     if DatabaseOperator.readStatus() == 1:
    #         msg = '警告：检测到上次程序异常关闭，请检查日志文件。'
    #         Dialog.log(msg, Dialog.WARNING, proggressMsg=False)
    #         mb.showwarning('警告', msg)
    #     DatabaseOperator.updateStatus(1)

    def centerWindow(self):
        """窗口居中"""
        self.update_idletasks()
        x = int((self.winfo_screenwidth() - const.WindowSize.width) / 2)
        y = int((self.winfo_screenheight() - const.WindowSize.height) / 2)
        self.root.geometry(f'{const.WindowSize.width}x{const.WindowSize.height}+{x}+{y}')

    def startServices(self):
        """启动服务"""
        # 启动邮箱线程
        emailConfigObj = DatabaseOperator.readEmailConfig()
        self.smtpThreadingObj = SmtpThreading(emailConfigObj)
        self.smtpThreadingObj.start()
        msg = '消息：完成邮箱线程启动'
        Dialog.log(msg)
        # 启动监控线程
        watchDirObjList = self.watchDirEditObj.getWatchDirObjList()
        self.watchDirThreadPoolManagerObj = WatchDirThreadPoolManager(watchDirObjList)
        numberWorkers = self.watchDirThreadPoolManagerObj.start()
        msg = f'消息：CPU 逻辑线程数：{const.WatchDir.cpuLogicalCount}，最大监控目录数量：{const.WatchDir.maxWatchDirThreading}'
        Dialog.log(msg)
        msg = f'消息：完成监控服务启动，已监控{numberWorkers}个目录。'
        Dialog.log(msg)
        # 启动进展更新
        self.startUpdateProgressMsgText()
        # 启动闪烁信号检查
        self.startCheckBlinkingSignal()

    def createMenuBar(self):
        """创建菜单栏"""
        menuBar = tk.Menu(self)
        self.root.config(menu=menuBar)

        # 设置菜单
        settingsMenu = tk.Menu(menuBar, tearoff=0)
        menuBar.add_cascade(label="设置", menu=settingsMenu)
        settingsMenu.add_command(label="邮箱配置", command=self.onOpenEmailConfig)
        settingsMenu.add_command(label="重置设置", command=self.onResetSettings)

        # 设置菜单 -> 开机自启动
        isAutoStart, err = AutoStart.checkAutoStart()
        if err is not None:
            Dialog.log(f'警告：检查开机自启动失败，错误信息：{common.exceptionTraceback2str(err)}', Dialog.ERROR, proggressMsg=False)
            mb.showerror(title='错误', message='检查开机自启动失败，请手动检查系统设置。')
        self.isAutoStartVar = tk.BooleanVar(value=isAutoStart)
        settingsMenu.add_checkbutton(label='开机自启动', variable=self.isAutoStartVar, command=self.onSwitchAutoStart)

        # 帮助菜单
        helpMenu = tk.Menu(menuBar, tearoff=0)
        menuBar.add_cascade(label="帮助", menu=helpMenu)
        # 帮助菜单 -> 调试菜单
        debugMenu = tk.Menu(helpMenu, tearoff=0)
        helpMenu.add_cascade(label='调试', menu=debugMenu)
        debugMenu.add_command(label='打开日志文件', command=lambda: os.startfile(const.Path.dialogPath))
        debugMenu.add_command(label='打开数据目录', command=lambda: os.startfile(const.Path.myDataPath))
        # 帮助菜单 -> 关于
        helpMenu.add_command(label='关于', command=self.showAbout)

    def startUpdateProgressMsgText(self):
        """开始更新进展消息文本框"""
        try:
            while True:
                msg = self.progressMsgQueue.get_nowait()
                self.progressMsgCounter += 1
                self.progressMsgShowText.config(state=tk.NORMAL)
                self.progressMsgShowText.insert(tk.END, '【' + str(self.progressMsgCounter) + '】' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + '\n' + msg + '\n')
                self.progressMsgShowText.see(tk.END)
                self.progressMsgShowText.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        finally:
            self.root.after(const.Interval.progressMsg, self.startUpdateProgressMsgText)

    def startCheckBlinkingSignal(self):
        """开始检查闪烁信号"""
        try:
            while True:
                self.blinkingSignalQueue.get_nowait()
                self.restartButton.startBlinking()
        except queue.Empty:
            pass
        finally:
            self.root.after(const.Interval.blinkingSignal, self.startCheckBlinkingSignal)

    def onRestartButton(self):
        """重启服务按钮"""
        Dialog.log('消息：开始重启服务...')
        self.restartButton.stopBlinking()

        # 更新邮箱配置生效
        emailConfigObj = DatabaseOperator.readEmailConfig()
        self.smtpThreadingObj.modifyEmailConfig(emailConfigObj)
        Dialog.log('消息：新的邮箱配置开始生效')

        # 重新启动监控服务
        watchDirObjList = self.watchDirEditObj.getWatchDirObjList()
        numberWorkers = self.watchDirThreadPoolManagerObj.updateWatchDirObjList(watchDirObjList)
        Dialog.log(f'消息：重新启动{numberWorkers}个监控服务')

    def showAbout(self):
        mb.showinfo('关于', f'{const.Info.projectName} {const.Info.chineseName}\n{buildTime}\nIYATT-yx iyatt@iyatt.com')

    def exitApp(self):
        """正常执行退出的流程
        """
        # 关闭监控线程
        if self.watchDirThreadPoolManagerObj is not None:
            self.watchDirThreadPoolManagerObj.stop()
        # 关闭邮箱
        if self.smtpThreadingObj is not None:
            sendEmailQueue = QueueManager.get(const.QueueName.sendEmailQueue)
            sendEmailQueue.put(None)
        # 关闭托盘
        if self.systemTray is not None:
            self.systemTray.stopSystemTray()

        # 20250613
        # 数据库是在主线程打开的，不能在其它线程操作
        # 所以托盘线程执行退出的时候要把操作放到主线程的事件循环中执行
        # 但是主线程里执行退出时用 after 修改数据库又会无效，尚未搞清楚原因？？？？？？？？
        # 所以就直接根据是主线程还是其它线程区别执行方法
        if threading.current_thread() == threading.main_thread():
            # DatabaseOperator.updateStatus(0)
            DatabaseOperator.close()
            Dialog.log('主窗口执行退出流程\n', proggressMsg=False)
        else:
            # self.root.after(0, DatabaseOperator.updateStatus, 0)
            self.root.after(0, DatabaseOperator.close)
            Dialog.log('托盘执行退出流程\n', proggressMsg=False)

        # 关闭窗口
        self.root.after(0, self.root.destroy())

    def onSwitchAutoStart(self):
        """切换开机自动动设置"""
        if self.isAutoStartVar.get():
            status, err = AutoStart.setAutoStart()
            if status:
                msg = '消息：设置自启动成功'
            else:
                msg = f'错误：设置自启动失败，错误信息：{common.exceptionTraceback2str(err)}'
                self.isAutoStartVar.set(False)
        else:
            status, err = AutoStart.unsetAutoStart()
            if status:
                msg = '消息：取消自启动成功'
            else:
                msg = f'错误：取消自启动失败，错误信息：{common.exceptionTraceback2str(err)}'
                self.isAutoStartVar.set(True)
        if not status:
            mb.showerror('错误', msg)
        Dialog.log(msg)

    def onResetSettings(self):
        """重置设置"""
        DatabaseOperator.close()
        common.copyDatabaseFile()
        DatabaseOperator.connect(const.Path.databasePath)
        Dialog.log('消息：已重置设置')

    def onOpenEmailConfig(self):
        """打开邮箱配置编辑对话框"""
        emailConfigEditDlg = EmailConfigEditDialog(self)
        if emailConfigEditDlg.emailConfigObjResult is not None:
            DatabaseOperator.updateEmailConfig(emailConfigEditDlg.emailConfigObjResult)
            self.restartButton.startBlinking()
            Dialog.log('消息：已修改邮箱配置')
            return
        Dialog.log('消息：取消修改邮箱配置')

    def onClosing(self):
        """窗口关闭事件回调"""
        self.root.withdraw()
        Dialog.log('消息：点击关闭按钮隐藏窗口')
