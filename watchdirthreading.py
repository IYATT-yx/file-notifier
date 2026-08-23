"""
file: watchdirthreading.py
description: 变更监视器线程
author: IYATT-yx
copyright:  Copyright (c) 2026 IYATT-yx.
            Licensed under the MIT License. See LICENSE file in the project root for full license information.
"""
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
        try:
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
        except Exception as e:
            # 异步定时器内的异常如果逃逸，会导致整个程序崩溃且主线程无法捕获
            Dialog.log(f"防抖队列推送发生异步异常: {str(e)}", Dialog.ERROR)

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
        """监控目录工作业务"""
        self.id = watchDirObj.id
        self.dir = watchDirObj.dir
        self.stopEvent = stopEvent

    def _safe_check_path(self):
        """安全地检查网络路径是否真正可用，防止 os.path.exists 虚假唤醒"""
        try:
            if not os.path.exists(self.dir):
                return False
            # 对于网络共享，仅 exists 不够，尝试读取属性以确保网络通道真的活着
            os.stat(self.dir)
            return True
        except Exception:
            return False

    def run(self):
        Dialog.log(f'线程ID={self.id}，监控路径="{self.dir}" 守护进程已启动')
        
        observer = None
        is_connected = False  # 标记当前是否处于正常监控状态

        while not self.stopEvent.is_set():
            # 1. 检查路径是否可用
            path_exists = self._safe_check_path()

            if path_exists:
                if not is_connected:
                    try:
                        Dialog.log(f'线程ID={self.id}：检测到路径可用，正在初始化监控...')
                        fileWatchHandlerObj = FileWatchHandler()
                        observer = Observer()
                        observer.schedule(fileWatchHandlerObj, self.dir, recursive=True)
                        observer.start()
                        
                        is_connected = True
                        Dialog.log(f'线程ID={self.id}，监控目录="{self.dir}" 已成功启动/恢复')
                    except Exception as e:
                        Dialog.log(f'线程ID={self.id}：初始化监控失败，等待重试... 错误: {str(e)}', Dialog.ERROR)
                        # 危险区域：初始化失败时，不要激进清理
                        observer = None
                        is_connected = False
            else:
                if is_connected:
                    # 关键修改点：网络路径已断开！
                    Dialog.log(f'警告：网络路径断开或无法访问，监控已暂停: {self.dir}', Dialog.ERROR)
                    
                    # 【核心避坑】绝对不要在共享网络断开后调用 observer.stop() 和 join()
                    # 此时底层的 Windows 句柄已经因为网络断开而失效，调用 join 必然导致主线程或子线程永久死锁或崩溃
                    if observer:
                        try:
                            # 仅尝试轻量级停止，绝不 join 阻塞
                            observer.stop()
                        except Exception:
                            pass
                        observer = None  # 直接丢弃引用，交给垃圾回收
                    is_connected = False

            # 2. 如果处于连接状态，检查 observer 是否还在健康运行
            if is_connected and observer:
                try:
                    if not observer.is_alive():
                        Dialog.log(f'警告：线程ID={self.id} 的 Observer 异常终止，尝试重新连接...', Dialog.ERROR)
                        is_connected = False
                        observer = None
                except Exception:
                    # 防止由于底层句柄彻底失效导致 is_alive() 本身抛出 Windows 异常
                    is_connected = False
                    observer = None

            # 3. 频率控制：断开时延长检查间隔（10秒），降低对断开网络重连的系统负担
            sleep_time = 2 if is_connected else 10
            
            for _ in range(sleep_time):
                if self.stopEvent.is_set():
                    break
                sleep(1)

        # 4. 线程退出清理（正常退出时）
        if observer:
            try:
                # 只有在网络正常连通的情况下退出，才执行标准的 stop 和 join
                if self._safe_check_path():
                    observer.stop()
                    observer.join(timeout=2)
            except Exception:
                pass
        Dialog.log(f'线程ID={self.id}，监控目录="{self.dir}" 已彻底停止', Dialog.INFO)

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