import datetime
import json
import sys
from time import sleep
from hashlib import md5

from mcdreforged.api.all import *
from websocket import WebSocketApp

from .config import Config
from .logger import logger
from .packet import Packet
from .utils import get_instance_id, get_server_info, get_system_info

inputs = []
outputs = []
unload = False


class WsConnnection():
    '''ws连接对象'''

    def __init__(self, config: Config) -> None:
        self.config = config
        self.config.websocket.password = self.config.websocket.password
        self.__check__()
        self.verified = False
        self.reason = None
        self.restart_times = 0

    def __check__(self):
        '''检查输入值'''
        if not isinstance(self.config.websocket.addr, str):
            raise TypeError('`address`类型不正确')

        if not isinstance(self.config.websocket.password, str):
            raise TypeError('`password`类型不正确')

        if len(self.config.websocket.addr) == 0:
            raise ValueError('`address`为空')

        if len(self.config.websocket.password) == 0:
            raise ValueError('`password`为空')

        if not self.config.websocket.addr.startswith(('ws://', 'wss://')):
            raise ValueError('`address`格式不正确')

    def wait_for_reconnect(self):
        '''等待重连'''
        sleep(self.config.reconnect.interval/1000)
        logger.info('尝试重连中...{}/{}'.format(self.restart_times,
                    self.config.reconnect.maxTimes))
        self.connect()

    def connect(self):
        '''连接'''
        self._ws = WebSocketApp(
            self.config.websocket.addr,
            on_open=self.on_open,
            on_close=self.on_close,
            on_error=self.on_error,
            on_message=self.on_message
        )
        self._ws.run_forever()

    def disconnect(self):
        '''断开连接'''
        self._ws.close()

    def on_open(self, this: WebSocketApp):
        '''开启事件'''
        logger.info('已连接到"{}"'.format(self.config.websocket.addr))

        time = datetime.datetime.now().isoformat()
        self.send('request',
                  'verify',
                  {
                      'time': time,
                      'md5': md5('{}.{}'.format(time, self.config.websocket.password).encode(encoding='UTF-8')).hexdigest(),
                      'customName': self.config.custom_name,
                      'metadata': {
                          'name': 'MCDReforged',
                          'environment': 'Python {}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
                      },
                      'instanceId': get_instance_id()
                  })

    def on_close(self, this: WebSocketApp, code: int = 0, _: str = None):
        '''关闭事件'''
        if code is not None:
            logger.warning('连接已断开(Code: {})'.format(code))
        else:
            logger.warning('连接已断开')

        if self.reason:
            logger.warning('原因：{}'.format(self.reason))

        if not self.verified:
            logger.warning('貌似没有成功连接过，自动重连已关闭。请检查地址是否配置正确')
        elif self.restart_times < self.config.reconnect.maxTimes and self.config.reconnect.enable:
            self.restart_times += 1
            self.wait_for_reconnect()

    def on_error(self, this: WebSocketApp, e: Exception):
        '''错误事件'''
        logger.error(e)

    def on_message(self, this: WebSocketApp, msg: str):
        '''消息事件'''
        packet = Packet(msg)
        match packet.type:
            case 'event':
                self.events_handle(packet)

            case 'request':
                self.actions_handle(packet)

            case _:
                logger.warning('接收到不支持的数据包类型：{}'.format(packet.type))

    def actions_handle(self, packet: Packet):
        '''处理action数据包'''
        match packet.sub_type:

            case 'heartbeat':
                # 心跳
                self.send(
                    'return',
                    'heartbeat',
                    {
                        'system': get_system_info(),
                        'server': get_server_info()
                    }
                )

            case 'server_start':
                PluginServerInterface.get_instance().start()

            case 'server_stop':
                PluginServerInterface.get_instance().stop()

            case 'server_kill':
                PluginServerInterface.get_instance().kill()

            case 'server_input':
                instance = PluginServerInterface.get_instance()
                if not instance.is_server_running:
                    return

                list = []
                for line in packet.data:
                    if not isinstance(line, str):
                        continue

                    instance.execute(line)
                    list.append(line)

                self.send('broadcast', 'server_input', list)

    def events_handle(self, packet: Packet):
        '''处理event数据包'''
        match packet.sub_type:
            case 'verify_result':
                if packet.data.get('success'):
                    logger.info('[Host] 验证通过')
                    self.verified = True
                    self.restart_times = 0
                else:
                    logger.info('[Host] 验证失败: {}'.format(
                        packet.data.get('reason')))

            case 'disconnection':
                self.reason = packet.data.get('reason')

    def send(self, type: str, sub_type: str, data: dict | str = None):
        '''发送数据包'''
        try:
            self._ws.send(json.dumps({
                'type': type,
                'subType': sub_type,
                'data': data
            }, ensure_ascii=False))
        except Exception as e:
            logger.exception(e)

    def sync_cache(self):
        '''同步缓存'''
        while not unload:
            if len(inputs) > 0:
                self.send('broadcast', 'server_input', inputs)
                inputs.clear()

            if len(outputs) > 0:
                self.send('broadcast', 'server_output', outputs)
                outputs.clear()

            sleep(0.25)
