import json
import logging
import os
import subprocess
import sys
import typing
from datetime import datetime
from enum import Enum
from pathlib import Path
from subprocess import Popen
from threading import Thread

logger = logging.getLogger("Recorder")

class Status(Enum):
    PENDING = ("未启动", "pending")
    ANALYZE = ("解析中", "analyze")
    RUNNING = ("运行中", "running")
    STOPPED = ("已停止", "stopped")
    FAILED = ("运行失败", "failed")

    def __init__(self, text: str, tag: str):
        self.text = text
        self.tag = tag


def __get_resource(path):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    result = os.path.join(base, path)
    return result

STREAMLINK = __get_resource("streamlink.exe")

def _check_streamlink(link: str, callback: typing.Callable[[bool], None]) -> None:
    """我不会 asyncio """
    def _worker():
        try:
            subprocess.run(
                [STREAMLINK, link],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=FLAGS
            )
            logger.info("解析成功的表现")
            callback(True)
        except subprocess.TimeoutExpired as e:
            logger.error(e)
            callback(False)
        except FileNotFoundError as e:
            logger.error(e)
            callback(False)

    Thread(target=_worker, daemon=True).start()

__default_config = {
  "mode": "single",
  "segment_time": 1800
}

FLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

def __load_json():
    default = {}
    file = "config.json"
    try:
        if not os.path.exists(file):
            with open(file, "w", encoding="utf-8") as f:
                json.dump(__default_config, f, ensure_ascii=False, indent=4)
                return __default_config
        else:
            with open("config.json", "r", encoding="utf-8") as f:
                data = json.load(f)

        if data is None:
            return default

        return data
    except (FileNotFoundError, json.JSONDecodeError, OSError, UnicodeDecodeError) as _:
        logger.error(_)
        return default

config = __load_json()

class Recorder:

    def __init__(self, name: str, link: str, output: str, identify: int):
        self.name = name
        self.identify = identify
        self.link = link
        self.output = output
        self.time: datetime = datetime.now()
        self.status = Status.PENDING

        # 日志
        self.logger = logging.getLogger(self.name)

        self._streamlink_process: Popen | None = None

    def start(self):
        if self.status == Status.RUNNING:
            return

        self.status = Status.ANALYZE

        self.logger.info("解析链接中")

        # TODO: 轮询
        _check_streamlink(self.link, self._on_result)

    def _on_result(self, ok: bool) -> None:
        if not ok:
            self.logger.error("解析链接失败，未找到播放流")
            self.status = Status.FAILED
            return

        self.logger.info("解析成功")

        self.status = Status.RUNNING

        self._start_process()

    def _start_process(self):
        filename = os.path.join(
            self.output,
            self.name,
            self.time.strftime("%Y%m%d%H%M%S"),
            "record.mp4"
        )

        streamlink_command = [
            STREAMLINK,
            self.link,
            "best",
            "-o", filename
        ]

        try:
            self._streamlink_process = subprocess.Popen(
                streamlink_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
                creationflags=FLAGS
            )

            self._read_stream(self._streamlink_process.stdout,  f"[streamlink]")
        except Exception as e:
            self.status = Status.FAILED
            self.logger.error(f"启动失败: {e}")
            return

    def _read_stream(self, pipe: typing.IO, prefix: str):
        def job():
            for line in iter(pipe.readline, ""):
                if line:
                    self.logger.info(f"{prefix} {line.strip()}")
        Thread(target=job, daemon=True).start()

    def stop(self):
        if self.status == Status.STOPPED or self.status == Status.PENDING:
            return

        self.status = Status.STOPPED

        self.cleanup()

        self._streamlink_process = None
        self.status = Status.PENDING

    def cleanup(self):
        self._kill_process(self._streamlink_process)

    @staticmethod
    def _kill_process(process: Popen | None):
        if process:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()


class SegmentsRecorder(Recorder):

    def __init__(self, name: str, link: str, output: str, identify: int):
        super().__init__(name, link, output, identify)
        self._ffmpeg_process: Popen | None = None

    def _start_process(self):
        self._record_segment()

    def _record_segment(self):

        output_dir = Path(os.path.join(
            os.path.normpath(self.output),
            self.name,
            self.time.strftime("%Y%m%d%H%M%S")
        ))

        output_dir.mkdir(parents=True, exist_ok=True)

        filename = os.path.join(
            str(output_dir),
            f"seg-%03d.mp4"
        )

        streamlink_command = [
            STREAMLINK,
            self.link,
            "best",
            "-o", "-"
        ]

        segment_time = str(config.get("segment_time"))

        ffmpeg_command = [
            "ffmpeg.exe",
            "-i", "pipe:0",
            "-c:v", "copy",
            "-c:a", "copy",
            "-f", "segment",
            "-segment_time", segment_time,
            "-segment_start_number", "1",
            "-reset_timestamps", "1",
            "-y",
            filename
        ]

        try:
            self._streamlink_process = subprocess.Popen(
                streamlink_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                creationflags=FLAGS
            )

            self._ffmpeg_process = subprocess.Popen(
                ffmpeg_command,
                stdin=self._streamlink_process.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                creationflags=FLAGS
            )

            self._streamlink_process.stdout.close()

            self._read_stream(self._streamlink_process.stderr, prefix="[streamlink]")
            self._read_stream(self._ffmpeg_process.stderr, prefix="[ffmpeg]")

            self._streamlink_process.wait()
            self._ffmpeg_process.wait()
        except subprocess.TimeoutExpired:
            pass

    def stop(self):
        if self.status == Status.STOPPED or self.status == Status.PENDING:
            return

        self.status = Status.STOPPED

        self.cleanup()

        self._streamlink_process = None
        self._ffmpeg_process = None
        self.status = Status.PENDING

    def cleanup(self):
        super().cleanup()
        self._kill_process(self._ffmpeg_process)
