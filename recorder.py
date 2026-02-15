import os
import subprocess
from datetime import datetime
from enum import Enum


class Recorder:
    def __init__(self, link: str, output: str, identify: int):
        self.identify = identify
        self.link = link
        self.output = output
        self.created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status = Status.PENDING
        # 进程实例
        self.process = None

    def start(self):
        if self.status == Status.RUNNING:
            return

        time = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = os.path.join(self.output, f"{time}.mp4")

        command = ["streamlink", self.link, "best", "-o", filename]

        try:
            self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            self.status = Status.FAILED
            print(f"启动失败: {e}")
            return

        self.status = Status.RUNNING

    def stop(self):
        if self.status == Status.STOPPED or self.process is None:
            return

        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except Exception as e:
            print("终止进程失败:", e)
            self.process.kill()

        self.process = None
        self.status = Status.STOPPED

class Status(Enum):
    PENDING = ("未启动", "pending")
    RUNNING = ("运行中", "running")
    STOPPED = ("已停止", "stopped")
    FAILED = ("运行失败", "failed")

    def __init__(self, text: str, tag: str):
        self.text = text
        self.tag = tag