import logging
import os
from tkinter import messagebox

from interface import create_window

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("latest.log", mode="w", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

if __name__ == '__main__':
    if not os.path.exists("ffmpeg.exe"):
        messagebox.showerror("Error", "请把 ffmpeg.exe 放在该程序同目录")
    else:
        create_window()
