import json
import os
from pathlib import Path

from .constants import CONFIG_PATH, DEFAULT_CONFIG, PATH
from .logger import logger
from .metadata import PLUGIN_METADATA


class Config():
    '''配置'''
    class WebSocket():
        '''ws配置'''

        def __init__(self, websocketConfig: dict):
            self.addr: str = websocketConfig.get('addr')
            self.password: str = websocketConfig.get('password')

            if not isinstance(self.addr, str):
                raise TypeError('`config.websocket.addr`类型不正确')

            if not isinstance(self.password, str):
                raise TypeError('`config.websocket.password`类型不正确')

    class Reconnect():
        '''重连配置'''

        def __init__(self, reconnectConfig: dict):
            self.enable: bool = reconnectConfig.get('enable')
            self.interval: int = reconnectConfig.get('interval')
            self.maxTimes: int = reconnectConfig.get('maxTimes')

            if not isinstance(self.enable, bool):
                raise TypeError('`config.reconnect.enable`类型不正确')

            if not isinstance(self.enable, int):
                raise TypeError('`config.reconnect.interval`类型不正确')

            if not isinstance(self.maxTimes, int):
                raise TypeError('`config.reconnect.maxTimes`类型不正确')

            if self.maxTimes < 0:
                raise ValueError('`config.reconnect.maxTimes`值过小')

    def __init__(self):
        self.__config__ = self.load()

    def write(self):
        '''写入文件'''
        Path(PATH).mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf8') as file:
            file.write(json.dumps(DEFAULT_CONFIG,
                       ensure_ascii=False, indent=4))

    def load(self):
        '''读取'''
        if not os.path.exists(CONFIG_PATH):
            self.write()
            raise FileNotFoundError(
                '配置文件"{}"未找到，已重新创建。请打开修改相应配置后使用【!!MCDR plg ra】重新加载此插件'.format(CONFIG_PATH))

        with open(CONFIG_PATH, 'r', encoding='utf8') as file:
            text = file.read()

        config: dict = json.loads(text)
        self.custom_name = config.get('custonName')
        if not self.custom_name or len(self.custom_name) == 0:
            self.custom_name = 'MCDReforged#{}'.format(
                PLUGIN_METADATA['version'])
            logger.warning(
                '"config.customName"为空，将使用默认名称"{}"'.format(self.custom_name))

        self.reconnect = self.Reconnect(config.get('reconnect'))
        self.websocket = self.WebSocket(config.get('websocket'))
