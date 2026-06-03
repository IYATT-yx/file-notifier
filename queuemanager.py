"""
file: queuemanager.py
description: 队列管理
author: IYATT-yx
copyright:  Copyright (c) 2026 IYATT-yx.
            Licensed under the MIT License. See LICENSE file in the project root for full license information.
"""
from queue import Queue
from threading import Lock

class QueueManager:
    queueDict: dict[str: Queue] = {}
    lock = Lock()

    @staticmethod
    def get(name: str) -> Queue | None:
        """获取队列
        
        Args:
            name (str): 队列名称

        Returns:
            Queue | None: 队列对象。提供的队列名称非字符串时返回 None。
            """
        if not isinstance(name, str):
            return None
        with QueueManager.lock:
            if name not in QueueManager.queueDict:
                QueueManager.queueDict[name] = Queue()
            return QueueManager.queueDict[name]
    