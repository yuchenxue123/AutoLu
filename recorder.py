import subprocess

class Recorder:
    def __init__(self, url: str, directory: str):
        self.url = url
        self.directory = directory

    def start(self):
        print("Starting recorder...")

class BiliRecorder(Recorder):
    def __init__(self, url: str, directory: str):
        super().__init__(url, directory)

    def start(self):
        print("Starting bili recorder...")
        command = [
            "streamlink",
            self.url,
            "best",
            "-o", self.directory
        ]
        subprocess.call(command)
