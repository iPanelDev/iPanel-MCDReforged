import os
import platform
import time

import psutil
from mcdreforged.api.all import *
from psutil import Process


def get_sys_info() -> dict:
    '''获取系统信息'''
    mem = psutil.virtual_memory()
    return {
        'os': platform.platform(),
        'cpu_name': platform.processor(),
        'cpu_usage': psutil.cpu_percent(),
        'total_ram': mem.total,
        'free_ram': mem.free,
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
            'cpu_usage': cpu_usage,
            'filename': file_name,
            'run_time': get_time_str(time_span)
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
