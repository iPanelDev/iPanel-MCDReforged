import os
import platform
import re
import time
import uuid
from pathlib import Path

import psutil
from mcdreforged.api.all import *
from psutil import Process

from .constants import ID_PATH, PATH
from .logger import logger


def get_system_info() -> dict:
    '''获取系统信息'''
    mem = psutil.virtual_memory()
    return {
        'os': platform.platform(),
        'cpuName': platform.processor(),
        'cpuUsage': psutil.cpu_percent(),
        'totalRam': mem.total/1024,
        'freeRam': mem.free/1024,
    }


def get_server_info() -> dict:
    mcdr = PluginServerInterface.get_instance()
    if mcdr.is_server_running():
        pids = mcdr.get_server_pid_all()
        cpu_usage = 0
        file_name = None
        time_span = 0

        for i in pids:
            try:
                cpu_usage = cpu_usage + Process(i).cpu_percent()
            except:
                continue

        try:
            current_process = Process(mcdr.get_server_pid())
            time_span = time.time() - current_process.create_time()
            file_name = os.path.basename(current_process.exe())
        except:
            pass

        return {
            'status': True,
            'usage': cpu_usage,
            'filename': file_name,
            'runTime': get_time_str(time_span),
            'version': mcdr.get_server_information().version
        }
    return {
        'status': False
    }


def get_time_str(time_span: float | int):
    '''获取时间文本'''
    if time_span < 60*60:
        return '{}m'.format(round(time_span/60, 1))

    if time_span < 60*60*24:
        return '{}h'.format(round(time_span/60/60, 1))

    return '{}d'.format(round(time_span/60/60/24, 1))


def get_instance_id() -> str:
    if os.path.exists(ID_PATH):
        with open(ID_PATH, 'r', encoding='utf8') as file:
            line = file.readline()
        if re.fullmatch(r'^[a-zA-Z0-9]{32}$', line):
            return line

    u = uuid.uuid4()
    Path(PATH).mkdir(parents=True, exist_ok=True)
    with open(ID_PATH, 'w', encoding='utf8') as file:
        file.write(u.hex)
    logger.warning('实例ID文件未找到，已重新生成：{}'.format(u.hex))
    return u.hex
