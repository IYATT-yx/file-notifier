"""
邮件发信客户端实现
"""
from dialog import Dialog

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

Dialog()

class EmailConfig:
    def __init__(self, smtpServer: str, smtpPort: int, senderName: str, senderEmail: str, senderPassword: str, receiverEmail: str, encryption: str = 'SSL'):
        """邮箱配置信息结构
        Args:
            smtpServer (str): SMTP服务器地址
            smtpPort (int): SMTP服务器端口
            senderName (str): 发件人姓名
            senderEmail (str): 发件人邮箱
            senderPassword (str): 发件人邮箱密码
            receiverEmail (str): 收件人邮箱
            encryption (str): 加密方式（SSL 或 STARTTLS）
        """
        self.smtpServer = smtpServer.strip()
        self.smtpPort = smtpPort
        self.senderName = senderName.strip()
        self.senderEmail = senderEmail.strip()
        self.senderPassword = senderPassword.strip()
        self.receiverEmail = receiverEmail.strip()
        self.encryption = encryption

class SmtpClient:
    def __init__(self, emailConfigObj: EmailConfig):
        """SMTP客户端
        
        Args:
            emailConfigObj (EmailConfig): 邮箱配置信息对象
        """
        self.emailConfigObj = emailConfigObj

    def sendEmail(self, subject, body) -> tuple[bool, Exception | None]:
        """发送邮件
        
        Args:
            subject (str): 邮件主题
            body (str): 邮件内容

        Returns:
            tuple[bool, str]: 发送成功返回 (True, None)，发送失败返回 (False, str)
        """
        emailMsg = MIMEMultipart()
        senderName =Header(self.emailConfigObj.senderName, 'utf-8').encode()
        emailMsg['From'] = f'{senderName} <{self.emailConfigObj.senderEmail}>'
        emailMsg['To'] = self.emailConfigObj.receiverEmail
        emailMsg['Subject'] = subject
        emailMsg.attach(MIMEText(body, 'plain'))

        try:
            if self.emailConfigObj.encryption == 'SSL':
                server = smtplib.SMTP_SSL(self.emailConfigObj.smtpServer, self.emailConfigObj.smtpPort)
            else:
                server = smtplib.SMTP(self.emailConfigObj.smtpServer, self.emailConfigObj.smtpPort)
                server.starttls()
            server.login(self.emailConfigObj.senderEmail, self.emailConfigObj.senderPassword)
            server.sendmail(self.emailConfigObj.senderEmail, self.emailConfigObj.receiverEmail, emailMsg.as_string())
            server.quit()
            return True, None
        except Exception as e:
            return False, e
