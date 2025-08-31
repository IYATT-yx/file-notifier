"""数据库操作"""
from smtpclient import EmailConfig
from typewatchdir import WatchDir

import sqlite3

class DatabaseOperator:
    connector: sqlite3.Connection = None
    """数据库连接对象"""
    cursor: sqlite3.Cursor = None
    """数据库游标对象"""

    @staticmethod
    def close():
        """关闭数据库
        """
        DatabaseOperator.cursor.close()
        DatabaseOperator.connector.close()
        DatabaseOperator.connector = None
        DatabaseOperator.cursor = None

    @staticmethod
    def connect(databasePath: str):
        """连接数据库
        """
        if DatabaseOperator.cursor is not None:
            DatabaseOperator.close()

        DatabaseOperator.connector = sqlite3.connect(databasePath)
        DatabaseOperator.cursor = DatabaseOperator.connector.cursor()

    @staticmethod
    def readEmailConfig() -> EmailConfig:
        """读取邮箱配置

        Returns:
            EmailConfig: 邮箱配置对象
        """
        if DatabaseOperator.cursor is None:
            raise RuntimeError('未连接数据库')
        DatabaseOperator.cursor.execute('select * from emailConfig where id = 0')
        headers = [description[0] for description in DatabaseOperator.cursor.description]
        row = DatabaseOperator.cursor.fetchone()
        emailConfigDict = dict(zip(headers, row))
        emailConfigObj = EmailConfig(
            smtpServer=emailConfigDict['smtpServer'],
            smtpPort=emailConfigDict['smtpPort'],
            senderName=emailConfigDict['senderName'],
            senderEmail=emailConfigDict['senderEmail'],
            senderPassword=emailConfigDict['senderPassword'],
            receiverEmail=emailConfigDict['receiverEmail'],
            encryption=emailConfigDict['encryption'],
        )
        return emailConfigObj
    
    @staticmethod
    def updateEmailConfig(emailConfigObj: EmailConfig):
        """更新邮箱配置

        Args:
            emailConfigObj (EmailConfig): 邮箱配置对象
        """
        if DatabaseOperator.cursor is None:
            raise RuntimeError('未连接数据库')
        
        emailConfigDict = vars(emailConfigObj)
        setClause = ', '.join([f'{k} = ?' for k in emailConfigDict])
        values = list(emailConfigDict.values())

        sql = f'update emailConfig set {setClause} where id = 0'
        DatabaseOperator.cursor.execute(sql, values)
        DatabaseOperator.connector.commit()

    @staticmethod
    def readWatchDir() -> list[WatchDir]:
        """读取监控目录配置
        """
        if DatabaseOperator.cursor is None:
            raise RuntimeError('未连接数据库')
        DatabaseOperator.cursor.execute('select * from watchDir')
        rows = DatabaseOperator.cursor.fetchall()
        headers = [description[0] for description in DatabaseOperator.cursor.description]
        watchDirList = []
        for row in rows:
            record = dict(zip(headers, row))
            watchDir = WatchDir(
                id=record['id'],
                dir=record['dir'],
                status=record['status']
            )
            watchDirList.append(watchDir)

        return watchDirList
    
    @staticmethod
    def updateWatchDir(watchDirObj: WatchDir):
        """更新监控目录配置
        """
        if DatabaseOperator.cursor is None:
            raise RuntimeError('未连接数据库')
        updateFields = vars(watchDirObj)
        setClause = ', '.join([f'{k} = ?' for k in updateFields if k != 'id'])
        values = [ value for key, value in updateFields.items() if key != 'id' ]
        values.append(watchDirObj.id)

        sql = f'update watchDir set {setClause} where id = ?'
        DatabaseOperator.cursor.execute(sql, values)
        DatabaseOperator.connector.commit()

    @staticmethod
    def addWatchDir(watchDirObj: WatchDir):
        """添加监控目录配置
        """
        if DatabaseOperator.cursor is None:
            raise RuntimeError('未连接数据库')
        DatabaseOperator.cursor.execute('insert into watchDir (id, dir, status) values (?, ?, ?)', (watchDirObj.id, watchDirObj.dir, watchDirObj.status))
        DatabaseOperator.connector.commit()

    @staticmethod
    def deleteWatchDir(watchDirId: int):
        """删除监控目录配置
        """
        if DatabaseOperator.cursor is None:
            raise RuntimeError('未连接数据库')
        DatabaseOperator.cursor.execute('delete from watchDir where id = ?', (watchDirId,))
        DatabaseOperator.connector.commit()    

    # @staticmethod
    # def updateStatus(status: int):
    #     """更新状态
    #     """
    #     if DatabaseOperator.cursor is None:
    #         raise RuntimeError('未连接数据库')
    #     if status not in [0, 1]:
    #         raise ValueError('status 只能是 0 或 1')
    #     DatabaseOperator.cursor.execute('update status set status = ? where id = 0', (status,))
    #     DatabaseOperator.connector.commit()

    # @staticmethod
    # def readStatus() -> int:
    #     """读取状态
    #     """
    #     if DatabaseOperator.cursor is None:
    #         raise RuntimeError('未连接数据库')
    #     DatabaseOperator.cursor.execute('select status from status where id = 0')
    #     status = DatabaseOperator.cursor.fetchone()[0]
    #     return status

