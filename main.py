from interface import create_window
import logging

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
    create_window()
