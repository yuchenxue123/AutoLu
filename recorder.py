import asyncio
import io
import logging
import os
import subprocess
import threading
import typing
from datetime import datetime
from enum import Enum
from subprocess import Popen
from threading import Thread

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("recorder.log", mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class Status(Enum):
    PENDING = ("未启动", "pending")
    ANALYZE = ("解析中", "analyze")
    RUNNING = ("运行中", "running")
    STOPPED = ("已停止", "stopped")
    FAILED = ("运行失败", "failed")

    def __init__(self, text: str, tag: str):
        self.text = text
        self.tag = tag


def _read_stream(pipe: typing.IO, prefix: str):
    for line in iter(pipe.readline, ""):
        if line:
            logger.info(f"{prefix} {line.strip()}")


def _check_streamlink(link: str) -> bool:
    try:
        subprocess.run(
            ["streamlink", link],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return True
    except subprocess.TimeoutExpired:
        return False
    except FileNotFoundError:
        return False


class Recorder:
    def __init__(self, name: str, link: str, output: str, identify: int):
        self.name = name
        self.identify = identify
        self.link = link
        self.output = output
        self.created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status = Status.PENDING

        self._process: Popen | None = None

    def start(self):
        if self.status == Status.RUNNING:
            return

        if _check_streamlink(self.link):
            logger.info("very")
            return

        time = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = os.path.join(self.output, f"{self.name}-{time}.mp4")

        streamlink_command = [
            "streamlink",
            self.link,
            "best",
            "-o", filename
        ]

        try:
            self._process = subprocess.Popen(
                streamlink_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1
            )

            Thread(
                target=_read_stream,
                args=(self._process.stdout, f"[Streamlink-{self.name}]"),
                daemon=True
            ).start()
        except Exception as e:
            self.status = Status.FAILED
            logger.error(f"启动失败: {e}")
            return

        self.status = Status.RUNNING

    def stop(self):
        if self.status == Status.STOPPED or self.status == Status.PENDING:
            return

        self.status = Status.STOPPED

        try:
            self._process.terminate()
            self._process.wait(timeout=5)
        except Exception as e:
            logger.error(f"终止进程失败: {e}")
            self._process.kill()

        self._process = None
        self.status = Status.PENDING


class SegmentsRecorder(Recorder):

    def start(self):
        pass

