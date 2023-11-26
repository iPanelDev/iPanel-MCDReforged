from threading import Thread

from mcdreforged.api.all import *

from .config import Config
from .logger import logger
from .metadata import PLUGIN_METADATA
from .ws_connection import WsConnnection, inputs, outputs, unload

connection = WsConnnection(Config())


# MCDR插件事件

def on_load(server: PluginServerInterface, prev_module):
    '''插件被加载'''
    logger.info(
        'iPanel-MCDReforged@{}加载成功.'.format(PLUGIN_METADATA.get('version')))
    Thread(
        target=connection.connect,
        name='WSConnection',
        daemon=True).start()
    Thread(
        target=connection.sync_cache,
        daemon=True,
        name='SyncCache').start()


def on_unload(server: PluginServerInterface):
    '''插件被卸载'''
    global unload
    unload = True
    connection.config.reconnect.enable = False
    connection.disconnect()


# 服务器事件

def on_server_start(server: PluginServerInterface):
    '''服务器启动'''
    connection.send('broadcast', 'server_start')
    server.set_exit_after_stop_flag(False)  # 关闭服务器停止后退出


def on_server_stop(server: PluginServerInterface, server_return_code: int):
    '''服务器停止'''
    connection.send('broadcast', 'server_stop', server_return_code)


def on_info(server: PluginServerInterface, info: Info):
    '''服务器输出'''

    if not server.is_server_running() or (info.content.startswith('!!MCDR') and info.source):
        # 屏蔽未启动和“!!MCDR”之类的内置指令
        return

    if info.source:
        inputs.append(info.raw_content)
        return

    outputs.append(info.raw_content)
