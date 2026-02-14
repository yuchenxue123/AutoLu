from recorder import BiliRecorder

if __name__ == '__main__':
    recorder = BiliRecorder("https://live.bilibili.com/923833", "./output")
    recorder.start()
