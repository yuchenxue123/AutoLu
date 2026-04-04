import json
import logging
import os
from json import JSONDecodeError

__logger = logging.getLogger("DataManager")

__data_directory = "data"

__config_file = os.path.join(__data_directory, "config.json")

__DEFAULT_CONFIG = {
    "mode": "single",
    "segment_time": 1800
}


def __load():
    # 创建文件夹
    if not os.path.exists(__data_directory):
        os.makedirs(__data_directory)

    # 配置文件不存在则创建
    try:
        if not os.path.exists(__config_file):
            with open(__config_file, mode="w", encoding="utf-8") as f:
                json.dump(__DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
            return __DEFAULT_CONFIG
        else:
            with open(__config_file, mode="r", encoding="utf-8") as f:
                data: dict[str, str | int] = json.load(f)
                if data:
                    return data
                else:
                    return __DEFAULT_CONFIG
    except (IOError, JSONDecodeError) as e:
        __logger.error("加载配置失败", e)
        return __DEFAULT_CONFIG


config = __load()
