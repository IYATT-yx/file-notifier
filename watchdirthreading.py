from uiwatchdiredit import WatchDir
import constants as const
from dialog import Dialog
from queuemanager import QueueManager
import common

import concurrent.futures
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from tkinter import messagebox as mb
import threading
from functools import partial
from time import sleep

Dialog()

from watchdog.events import FileSystemEventHandler
import os

class FileWatchHandler(FileSystemEventHandler):
    def __init__(self):
        self.sendEmailQueue = QueueManager.get(const.QueueName.sendEmailQueue)

    def shouldIgnore(self, path):
        filename = os.path.basename(path).lower()
        return filename.startswith('~$') or filename.endswith('.tmp') or filename.endswith('.bak')

    def on_created(self, event):
        if not event.is_directory and not self.shouldIgnore(event.src_path):
            msg = f'创建新文件："{event.src_path}"'
            self.sendEmailQueue.put(msg)

    def on_modified(self, event):
        if not event.is_directory and not self.shouldIgnore(event.src_path):
            msg = f'修改文件："{event.src_path}"'
            self.sendEmailQueue.put(msg)

    def on_deleted(self, event):
        if not event.is_directory and not self.shouldIgnore(event.src_path):
            msg = f'删除文件："{event.src_path}"'
            self.sendEmailQueue.put(msg)

    def on_moved(self, event):
        if not event.is_directory and not self.shouldIgnore(event.src_path) and not self.shouldIgnore(event.dest_path):
            msg = f'移动文件（或重命名）："{event.src_path}" ➡ "{event.dest_path}"'
            self.sendEmailQueue.put(msg)


class WatchDirWorker:
    def __init__(self, watchDirObj: WatchDir, stopEvent: threading.Event):
        """监控目录工作业务
        
        Args:
            watchDirObj (WatchDir): 监控目录对象
            stopEvent (threading.Event): 停止事件
            sendEmailQueue (Queue): 发送邮件队列
            root (tkinter.Tk): 主线程窗口对象
        """
        self.id = watchDirObj.id
        self.dir = watchDirObj.dir
        self.stopEvent = stopEvent

    def run(self):
        observer = None
        try:
            fileWatchHandlerObj = FileWatchHandler()
            observer = Observer()
            observer.schedule(fileWatchHandlerObj, self.dir, recursive=True)
            observer.start()
            Dialog.log(f'线程ID={self.id}，监控目录="{self.dir}" 已启动')

            while not self.stopEvent.is_set():
                sleep(1)
        except Exception as e:
            msg = f'错误：线程ID={self.id}，监控目录="{self.dir}"，捕获到异常：{common.exceptionTraceback2str(e)}'
            Dialog.log(msg, Dialog.ERROR)
        finally:
            if observer:
                observer.stop()
                observer.join()
            msg = f'线程ID={self.id}，监控目录="{self.dir}" 已停止'
            Dialog.log(msg, Dialog.INFO)

class WatchDirThreadPoolManager:
            def __init__(self, watchDirObjList: list[WatchDir]):
                self.watchDirObjList = watchDirObjList
                self.stopEvent = threading.Event()
                self.executor = None
                self.workers = []

            def start(self):
                self.stopEvent.clear()
                self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=const.WatchDir.maxWatchDirThreading)
                numWorkers = 0
                for watchDirObj in self.watchDirObjList:
                    if watchDirObj.status == 1:
                        worker = WatchDirWorker(watchDirObj, self.stopEvent)
                        future = self.executor.submit(worker.run)
                        future.add_done_callback(
                            partial(self.futureExceptionHandler, watchDirObj)
                        )
                        self.workers.append(future)
                        numWorkers += 1
                return numWorkers

            def stop(self):
                self.stopEvent.set()
                if self.executor is not None:
                    self.executor.shutdown(wait=True)

            def updateWatchDirObjList(self, watchDirObjList: list[WatchDir]):
                self.stop()
                self.watchDirObjList = watchDirObjList
                return self.start()

            def futureExceptionHandler(self, watchDirObj: WatchDir, future: concurrent.futures.Future):
                e = future.exception()
                if e is not None:
                    msg = f'错误：线程ID={watchDirObj.id}，监控目录="{watchDirObj.dir}"，捕获到异常：{common.exceptionTraceback2str(e)}'
                    Dialog.log(msg, Dialog.ERROR)