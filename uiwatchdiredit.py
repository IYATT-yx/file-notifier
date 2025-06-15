"""监控目录编辑控件"""
from typewatchdir import WatchDir, BoolStr
from databaseoperator import DatabaseOperator
import common
from dialog import Dialog
import constants as const
from queuemanager import QueueManager

import os
import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox

Dialog()

class DirInputDialog(simpledialog.Dialog):
    def __init__(self, parent, title, initialPath='', initialStatus=1):
        """文件夹选择对话框

        Args:
            parent (tk.Tk): 父窗口
            title (str): 窗口标题
            initialPath (str, optional): 初始路径
        """
        self.initialPath = initialPath
        self.initialStatus = initialStatus
        self.inputResult = None
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text='路径：').grid(row=0, column=0, sticky=tk.W)

        # 路径输入框
        self.dirInputVar = tk.StringVar(value=self.initialPath)
        dirInputEntry = tk.Entry(master, textvariable=self.dirInputVar, width=50)
        dirInputEntry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)

        # 状态启用勾选框
        self.statusVar = tk.IntVar(value=self.initialStatus)
        tk.Checkbutton(master, text='启用监控', variable=self.statusVar).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

        tk.Button(master, text='浏览目录', command=self.browse).grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        return dirInputEntry

    def browse(self):
        """浏览文件夹
        """
        if self.initialPath != '':
            dir = filedialog.askdirectory(initialdir=self.initialPath)
        else:
            dir = filedialog.askdirectory()
        if dir:
            dir = os.path.normpath(dir)
            self.dirInputVar.set(dir)

    def validate(self):
        inputDir = os.path.normpath(self.dirInputVar.get())
        if os.path.exists(inputDir):
            self.inputResult = (inputDir, self.statusVar.get())
            return True
        else:
            self.inputResult = None
            msg = '错误：输入的路径不存在'
            Dialog.log(msg, Dialog.ERROR)
            messagebox.showerror("错误", msg)
            return False

    def buttonbox(self):
        """重写buttonbox方法以实现汉化"""
        box = tk.Frame(self)

        w = tk.Button(box, text="确定", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = tk.Button(box, text="取消", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)

        box.pack()

class WatchDirEdit(tk.Frame):
    def __init__(self, master):
        """监控目录编辑控件
        """
        super().__init__(master)
        self.blinkingSignalQueue = QueueManager.get(const.QueueName.blinkingSignalQueue)
        self.create()

    def create(self):
        self.tree = ttk.Treeview(self, columns=('id', 'dir', 'status'), show='headings')
        self.tree.heading('id', text='ID')
        self.tree.heading('dir', text='监控目录')
        self.tree.heading('status', text='是否监控')
        self.tree.column('id', anchor=tk.CENTER, width=50, stretch=False)
        self.tree.column('dir', anchor=tk.W, width=400)
        self.tree.column('status', anchor=tk.CENTER, width=100, stretch=False)

        vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, rowspan=2, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, rowspan=2, sticky=tk.NS)

        self.tree.bind('<Double-1>', self.onDoubleClick)
        self.tree.bind('<Delete>', self.deleteSelected)

        tk.Button(self, text='新建', command=self.addRow).grid(row=0, column=2, sticky=tk.NSEW)
        tk.Button(self, text='删除', command=self.deleteSelected).grid(row=1, column=2, sticky=tk.NSEW)

        self.rowconfigure([0, 1], weight=1)
        self.columnconfigure(0, weight=1)

    def update(self, watchDirObjs: list[WatchDir]):
        for watchDirObj in watchDirObjs:
            self.tree.insert('', 'end', iid=watchDirObj.id, values=(watchDirObj.id, watchDirObj.dir, BoolStr.int2chinese(watchDirObj.status)))

    def clearWatchDir(self):
        """清空监控目录树视图"""
        self.tree.delete(*self.tree.get_children())

    def addRow(self):
        dirInputDlg = DirInputDialog(self, '添加监控路径')
        if dirInputDlg.inputResult:
            watchDirObjList = self.getWatchDirObjList()
            usedIds = [watchDirObj.id for watchDirObj in watchDirObjList]
            newId = 1

            while newId in usedIds:
                newId += 1

            newWatchDirObj = WatchDir(
                id=newId,
                dir=dirInputDlg.inputResult[0],
                status=dirInputDlg.inputResult[1]
            )
            deletingIdx = self.checkDuplicates(watchDirObjList, newWatchDirObj)
            if deletingIdx == -1:
                msg = '消息：新添加的监控目录已存在或被已有监控目录包含'
                Dialog.log(msg, Dialog.INFO)
                return
            elif deletingIdx == -2:
                DatabaseOperator.addWatchDir(newWatchDirObj)
                watchDirObjList.append(newWatchDirObj)
                self.clearWatchDir()
                self.update(watchDirObjList)
                msg = '消息：添加监控目录成功'
                Dialog.log(msg)
            else:
                deletingWatchDirObjId = watchDirObjList[deletingIdx].id
                DatabaseOperator.deleteWatchDir(deletingWatchDirObjId)
                DatabaseOperator.addWatchDir(newWatchDirObj)
                watchDirObjList.pop(deletingIdx)
                watchDirObjList.append(newWatchDirObj)
                self.clearWatchDir()
                self.update(watchDirObjList)
                msg = '消息：新添加目录范围大于已有目录，替换原有目录'
                Dialog.log(msg, Dialog.INFO)
            self.blinkingSignalQueue.put(True)

    def selectListIdxById(self, watchDirObjList: WatchDir, id: int) -> int:
        """根据 ID 查找 WatchDirObjList 列表索引
        
        Args:
            watchDirObjList (list[WatchDir]): WatchDirObj 列表
            id (int): WatchDirObj ID

        Returns:
            int: 索引，-1 表示未找到
        """
        for idx, WatchDirObj in enumerate(watchDirObjList):
            if WatchDirObj.id == id:
                return idx
        return -1

    def editRow(self, id: int):
        """
        编辑指定行

        Args:
            id (int): 行ID
        """
        if id:
            id = int(id)
            watchDirDict = self.tree.set(id)
            watchDirObj = WatchDir(id=watchDirDict['id'], dir=watchDirDict['dir'], status=BoolStr.chinese2int(watchDirDict['status']))
            dirInputDlg = DirInputDialog(self, '编辑监控路径', watchDirObj.dir, watchDirObj.status)
            if dirInputDlg.inputResult is not None:
                watchDirObjList = self.getWatchDirObjList()
                editWatchDirObj = WatchDir(
                    id=id,
                    dir=dirInputDlg.inputResult[0],
                    status=dirInputDlg.inputResult[1]
                )
                editIdx = self.selectListIdxById(watchDirObjList, id)
                if editIdx == -1:
                    msg = '错误：程序异常错误'
                    Dialog.log(msg, Dialog.CRITICAL)
                    return
                otherWatchDirObjList = watchDirObjList
                otherWatchDirObjList.pop(editIdx)
                deletingIdx = self.checkDuplicates(otherWatchDirObjList, editWatchDirObj)
                if deletingIdx == -1:
                    msg = '消息：编辑后的监控目录已存在或被已有其它监控目录包含，不进行修改'
                    Dialog.log(msg, Dialog.INFO)
                    return
                elif deletingIdx == -2:
                    DatabaseOperator.updateWatchDir(editWatchDirObj)
                    otherWatchDirObjList.append(editWatchDirObj)
                    self.clearWatchDir()
                    self.update(otherWatchDirObjList)
                    msg = '消息：编辑监控目录成功'
                    Dialog.log(msg)
                else:
                    deletingWatchDirObjId = otherWatchDirObjList[deletingIdx].id
                    DatabaseOperator.deleteWatchDir(deletingWatchDirObjId)
                    DatabaseOperator.updateWatchDir(editWatchDirObj)
                    otherWatchDirObjList.pop(deletingIdx)
                    otherWatchDirObjList.append(editWatchDirObj)
                    self.clearWatchDir()
                    self.update(otherWatchDirObjList)
                    msg = '消息：编辑后的目录范围大于已有其它目录，替换其它目录'
                    Dialog.log(msg, Dialog.INFO)
                self.blinkingSignalQueue.put(True)
                    
    def onDoubleClick(self, event: tk.Event):
        rowId = self.tree.identify_row(event.y)
        self.editRow(rowId)

    def deleteSelected(self, event: tk.Event = None):
        selectedRows = self.tree.selection()
        for id in selectedRows:
            self.tree.delete(id)
            DatabaseOperator.deleteWatchDir(id)
            msg = '消息：删除监控目录成功'
            Dialog.log(msg)
            self.blinkingSignalQueue.put(True)

    def getWatchDirObjList(self) -> list[WatchDir]:
        """从监控目录控件获取 WatchDirObj 列表"""
        watchDirObjList = []
        for id in self.tree.get_children():
            rowDict = self.tree.set(id)
            watchDirObj = WatchDir(
                id=rowDict['id'],
                dir=rowDict['dir'],
                status=BoolStr.chinese2int(rowDict['status'])
            )
            watchDirObjList.append(watchDirObj)
        return watchDirObjList
    
    def checkDuplicates(self, watchDirObjList: list[WatchDir], watchDirObj: WatchDir) -> int:
        """检查重复
        
        Args:
            watchDirObjList (list[WatchDir]): WatchDirObj 列表
            watchDirObj (WatchDir): WatchDirObj

        Returns:
            int: 不需要变动旧的返回 -1；完全新增返回 -2；如果要采用新的对象，返回旧列表中需要删除对象的下标
            """
        for idx, existingWatchDirObj in enumerate(watchDirObjList):
            # 重复路径保留旧的
            if existingWatchDirObj.dir == watchDirObj.dir:
                return -1

            # 新添加目录是否为旧目录的子目录，保留旧的
            if common.checkSubpath(existingWatchDirObj.dir, watchDirObj.dir):
                return -1
            
            # 旧目录是否为新目录的子目录，保留新的
            if common.checkSubpath(watchDirObj.dir, existingWatchDirObj.dir):
                return idx
            
        return -2
    