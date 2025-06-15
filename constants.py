"""常量"""
import os
import sys
import logging

class Info:
    projectName = 'file-notifier'
    chineseName = '文件变更通知器'

class AutoStart:
    isPackaged: bool = not sys.argv[0].endswith('.py')
    """是否打包成可执行文件"""
    commandStr = ('"' + sys.argv[0] if isPackaged else '"' + sys.executable + '" "' + os.path.abspath(sys.argv[0])) + '" --hidewindow'
    """程序自身的执行命令"""
    autoStartRegPath = r"Software\Microsoft\Windows\CurrentVersion\Run"
    """自启动注册表配置路径"""

class Path:
    programFileDir = os.path.dirname(sys.argv[0])
    """程序文件所在目录"""
    runtimeDir = os.path.dirname(__file__)
    """运行时目录"""

    iconPath = os.path.join(runtimeDir, 'icon.ico')
    """图标文件路径"""
    myDataPath = os.path.join(os.getenv('APPDATA'), Info.projectName)
    """用户数据路径"""
    databasePath = os.path.join(myDataPath, Info.projectName + '.data')
    """数据库路径"""
    databaseTemplatePath = os.path.join(runtimeDir, Info.projectName +'.template')
    """数据库模板路径"""
    dialogPath = os.path.join(myDataPath, Info.projectName + '.log')
    """日志文件路径"""
    fileLockPath = os.path.join(myDataPath, Info.projectName + '.lock')

class QueueName:
    sendEmailQueue = 'send email'
    """发送邮件队列"""
    progressMsgQueue = 'progress message'
    """进展消息队列"""
    blinkingSignalQueue = 'blinking signal'
    """闪烁信号队列"""

class Interval:
    progressMsg = 1000
    """主线程更新进展消息的周期，毫秒"""
    blinkingSignal = 1000
    """主线程检查闪烁信号的周期，毫秒"""

class WindowSize:
    width = 1080
    """窗口默认宽度"""
    height = 600
    """窗口默认高度"""

class DialogConfig:
    """日志配置"""
    format = '[ %(asctime)s %(levelname)-8s 模块：%(name)-16s ] %(message)s'
    dateFormat = '%Y-%m-%d %H:%M:%S'
    level = logging.DEBUG
    encoding = 'utf-8'

class WatchDir:
    cpuLogicalCount = os.cpu_count()
    """CPU逻辑核心数"""
    maxWatchDirThreading = cpuLogicalCount * 4
    """最大监控目录线程数"""
    maxMergeEventCount = 10
    """单次最大合并通知事件数量"""

# 保证数据目录存在
os.makedirs(Path.myDataPath, exist_ok=True)