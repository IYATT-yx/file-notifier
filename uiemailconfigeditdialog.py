"""邮箱配置编辑控件"""
from smtpclient import EmailConfig, SmtpClient
import constants as const
from databaseoperator import DatabaseOperator

import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog, messagebox as mb

class EmailConfigEditDialog(simpledialog.Dialog):
    def __init__(self, parent, title='邮箱配置编辑'):
        """邮箱配置编辑控件

        Args:
            emailQueue (tuple[Queue, Queue]): 邮箱队列。第一个是发送邮件队列，第二个是邮件发送结果队列。
        """
        self.emailConfigObj = DatabaseOperator.readEmailConfig()
        self.backupEmailConfigObj = self.emailConfigObj
        self.emailConfigObjResult = None
        super().__init__(parent, title)

    def body(self, master):
        tk.Label(master, text='服务器地址：').grid(row=0, column=0, sticky=tk.W)
        tk.Label(master, text=' : ').grid(row=0, column=2, sticky=tk.EW)
        tk.Label(master, text='加密：').grid(row=1, column=0, sticky=tk.W)
        tk.Label(master, text='发件人名称：').grid(row=2, column=0, sticky=tk.W)
        tk.Label(master, text='邮箱：').grid(row=3, column=0, sticky=tk.W)
        tk.Label(master, text='密码：').grid(row=4, column=0, sticky=tk.W)
        tk.Label(master, text='收件邮箱：').grid(row=5, column=0, sticky=tk.W)

        self.smtpServerVar = tk.StringVar()
        self.portVar = tk.IntVar()
        self.encryptionVar = tk.StringVar()
        self.senderNameVar = tk.StringVar()
        self.senderEmailVar = tk.StringVar()
        self.senderPasswordVar = tk.StringVar()
        self.receiverEmailVar = tk.StringVar()

        tk.Entry(master, textvariable=self.smtpServerVar).grid(row=0, column=1, sticky=tk.EW)
        tk.Entry(master, textvariable=self.portVar, width=6).grid(row=0, column=3, sticky=tk.EW)

        encryptionCombo = ttk.Combobox(master, textvariable=self.encryptionVar, state="readonly", width=10)
        encryptionCombo['values'] = ('SSL', 'STARTTLS')
        encryptionCombo.current(0)
        encryptionCombo.grid(row=1, column=1, sticky=tk.W)

        tk.Entry(master, textvariable=self.senderNameVar).grid(row=2, column=1, columnspan=3, sticky=tk.EW)
        tk.Entry(master, textvariable=self.senderEmailVar).grid(row=3, column=1, columnspan=3, sticky=tk.EW)
        self.passwordEntry = tk.Entry(master, textvariable=self.senderPasswordVar, show='*')
        self.passwordEntry.grid(row=4, column=1, columnspan=3, sticky=tk.EW)
        tk.Entry(master, textvariable=self.receiverEmailVar).grid(row=5, column=1, columnspan=3, sticky=tk.EW)

        self.changePasswordVisibilityButton = tk.Button(master, text='显示密码', command=self.onChangePasswordVisibility)
        self.changePasswordVisibilityButton.grid(row=4, column=4, sticky=tk.EW)

        self.testEmailButton = tk.Button(master, text='测试配置', bd=5, command=self.onTestEmailButton)
        self.testEmailButton.grid(row=6, column=0, columnspan=5, sticky=tk.NSEW)

        # 初始化内容
        self.updateUI(self.emailConfigObj)

    def onTestEmailButton(self):
        self.testEmailButton['text'] = '发送中...'
        self.update_idletasks()
        smtpClientObj = SmtpClient(self.getEmailConfigObj())
        status, err = smtpClientObj.sendEmail(const.Info.chineseName + ' 测试邮件', '这是一封测试邮件')
        if not status:
            mb.showerror('测试邮件发送失败', err)
        del smtpClientObj
        self.testEmailButton['text'] = '测试配置'

    def onChangePasswordVisibility(self):
        if self.passwordEntry['show'] == '*':
            self.changePasswordVisibilityButton['text'] = '隐藏密码'
            self.passwordEntry['show'] = ''
        else:
            self.changePasswordVisibilityButton['text'] = '显示密码'
            self.passwordEntry['show'] = '*'

    def updateUI(self, emailConfigObj: EmailConfig):
        """更新控件内容

        Args:
            emailConfig (dict): 邮箱配置
        """
        self.smtpServerVar.set(emailConfigObj.smtpServer)
        self.portVar.set(emailConfigObj.smtpPort)
        self.encryptionVar.set(emailConfigObj.encryption)
        self.senderNameVar.set(emailConfigObj.senderName)
        self.senderEmailVar.set(emailConfigObj.senderEmail)
        self.senderPasswordVar.set(emailConfigObj.senderPassword)
        self.receiverEmailVar.set(emailConfigObj.receiverEmail)
    
    def getEmailConfigObj(self):
        """获取邮箱配置对象"""
        return EmailConfig(
            self.smtpServerVar.get().strip(),
            self.portVar.get(),
            self.senderNameVar.get().strip(),
            self.senderEmailVar.get().strip(),
            self.senderPasswordVar.get().strip(),
            self.receiverEmailVar.get().strip(),
            self.encryptionVar.get()
        )

    def apply(self):
        self.emailConfigObjResult = self.getEmailConfigObj()
    
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
