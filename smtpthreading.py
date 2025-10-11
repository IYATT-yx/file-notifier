"""邮件发信线程"""
from smtpclient import EmailConfig, SmtpClient
from dialog import Dialog
from queuemanager import QueueManager
import constants as const
import common

import threading
import queue

Dialog()

class SmtpThreading(threading.Thread):
    instance = None

    def __new__(cls, *args, **kwargs):
        """单例模式，确保只有一个SMTP线程实例"""
        if cls.instance is None:
            cls.instance = super(SmtpThreading, cls).__new__(cls)
        return cls.instance

    def __init__(self, emailConfigObj: EmailConfig):
        """SMTP线程类，用于处理邮件发送任务

        Args:
            emailConfigObj (EmailConfig): 邮箱配置信息对象
        """
        if getattr(self, 'initialized', False):
            return
        threading.Thread.__init__(self)
        self.smtpClientObj = SmtpClient(emailConfigObj)
        self.sendEmailQueue = QueueManager.get(const.QueueName.sendEmailQueue)
        self.progressMsgQueue = QueueManager.get(const.QueueName.progressMsgQueue)
        self.daemon = True  # 设置为守护线程，主线程结束时自动结束
        self.initialized = True
        self.stopEvent = threading.Event()

    def modifyEmailConfig(self, emailConfigObj: EmailConfig):
        """修改邮箱配置
        
        Args:
            emailConfigObj(EmailConfig): 新的用于设置的邮箱配置
        """
        self.stopEvent.clear()
        del self.smtpClientObj
        self.smtpClientObj = SmtpClient(emailConfigObj)
        self.stopEvent.set()

    def run(self):
        self.stopEvent.set()
        while True:
            self.stopEvent.wait()

            # 初始化一个列表来存储邮件内容
            msgList = []
            count = 0

            # 从队列中批量获取消息，最多50个
            while count < const.WatchDir.maxMergeEventCount:
                try:
                    msg = self.sendEmailQueue.get(timeout=1)
                    msgList.append(msg)
                    count += 1
                except queue.Empty:
                    break

            # 如果没有获取到任何消息，继续等待
            if not msgList:
                continue

            # 检查是否有停止信号
            if msg[0] is None:
                del self.smtpClientObj
                msg = '消息：停止邮件发信服务'
                Dialog.log(msg, proggressMsg=False)
                break

            # 消息去重（消除短时间内重复触发事件的消息）
            uniqueMsgList = list(dict.fromkeys(msgList))
            # 合并邮件内容
            emailStr = ''
            for i, m in enumerate(uniqueMsgList, 1):
                emailStr += f'{i} >>>\n{m}\n'
            Dialog.log(f'本次准备通知文件变更数量：{i}')

            # 发送合并后的邮件
            status, error = self.smtpClientObj.sendEmail('文件变更通知', emailStr)
            self.progressMsgQueue.put(f'变更通知内容：\n{emailStr}')
            if status:
                msg = '消息：文件变更通知成功'
                Dialog.log(msg)
            else:
                msg = f'错误：文件变更通知失败。{common.exceptionTraceback2str(error)}'
                Dialog.log(msg, Dialog.ERROR)
            