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
    def __init__(self, debounce_interval=3.0):
        """
        Args:
            debounce_interval (float): 合并消息的窗口时间（秒），默认3秒内的消息会被合并
        """
        self.sendEmailQueue = QueueManager.get(const.QueueName.sendEmailQueue)
        self.debounce_interval = debounce_interval
        
        # 核心缓存结构：{ 文件路径: { "action": 最终动作, "timer": 定时器对象, "dest_path": 移动目标路径 } }
        self.pending_events = {}
        self.lock = threading.Lock()

    def _push_to_queue(self, src_path):
        """定时器触发时调用的函数，真正将合并后的消息推入队列"""
        with self.lock:
            event_data = self.pending_events.pop(src_path, None)
            if not event_data:
                return

        action = event_data["action"]
        dest_path = event_data.get("dest_path")

        # 根据最终状态生成一条干净的消息
        if action == "created":
            msg = f'创建新文件："{src_path}"'
        elif action == "modified":
            msg = f'修改文件："{src_path}"'
        elif action == "deleted":
            msg = f'删除文件："{src_path}"'
        elif action == "moved":
            msg = f'移动文件（或重命名）："{src_path}" ➡ "{dest_path}"'
        else:
            return

        self.sendEmailQueue.put(msg)

    def _handle_event(self, src_path, action, dest_path=None):
        """通用的事件防抖处理逻辑"""
        with self.lock:
            # 如果该文件已有定时任务，直接取消它（重新计时）
            if src_path in self.pending_events:
                self.pending_events[src_path]["timer"].cancel()

            # 状态合并逻辑优化（例如：created + modified -> 依然是 created）
            current_action = action
            if src_path in self.pending_events:
                prev_action = self.pending_events[src_path]["action"]
                if prev_action == "created" and action == "modified":
                    current_action = "created"

            # 创建新的定时器
            timer = threading.Timer(self.debounce_interval, self._push_to_queue, args=[src_path])
            
            self.pending_events[src_path] = {
                "action": current_action,
                "dest_path": dest_path,
                "timer": timer
            }
            timer.start()

    def on_created(self, event):
        if not event.is_directory:
            self._handle_event(event.src_path, "created")

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_event(event.src_path, "modified")

    def on_deleted(self, event):
        if not event.is_directory:
            self._handle_event(event.src_path, "deleted")

    def on_moved(self, event):
        if not event.is_directory:
            # 对于移动操作，我们通常以源路径为 Key 记录
            self._handle_event(event.src_path, "moved", dest_path=event.dest_path)


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
        if not os.path.exists(self.dir):
            Dialog.log(f'错误：监控目录不可达: {self.dir}', Dialog.ERROR)
            return
        
        observer = None
        try:
            fileWatchHandlerObj = FileWatchHandler()
            observer = Observer()
            observer.schedule(fileWatchHandlerObj, self.dir, recursive=True)
            observer.start()
            Dialog.log(f'线程ID={self.id}，监控目录="{self.dir}" 已启动')

            while not self.stopEvent.is_set():
                if not os.path.exists(self.dir):
                    Dialog.log(f'警告：网络路径断开或无法访问: {self.dir}', Dialog.ERROR)
                    break
                sleep(1)
        except Exception as e:
            msg = f'错误：线程ID={self.id}，监控目录="{self.dir}"，捕获到异常：{common.exceptionTraceback2str(e)}'
            Dialog.log(msg, Dialog.ERROR)
        finally:
            if observer:
                observer.stop()
                observer.join(timeout=3)
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