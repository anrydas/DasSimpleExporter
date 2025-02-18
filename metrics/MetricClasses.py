import json
import shutil
from abc import abstractmethod
import time
import platform
import subprocess
from linecache import cache

import requests
import psutil

import app_config

from threading import Thread
from metrics.DataStructures import DiskData, HealthData, IcmpData, ENUM_UP_DN_STATES, InterfaceData, UptimeData, \
    SystemData, RestValueData, ShellValueData

class AbstractMetric:
    metric_key = ""
    config = {}
    def __init__(self, key, config):
        self.metric_key = key
        if key and key in config:
            self.config = config[key]
        self.data_array = []

    @abstractmethod
    def proceed_metric(self):
        pass

    @abstractmethod
    def print_debug_info(self):
        pass


def is_health_check(url, timeout, method, user, pwd, headers, callback=None):
    session = requests.Session()
    if user and pwd:
        session.auth = (user, pwd)
    try:
        response = session.request(
            url=url,
            timeout=timeout,
            method=method,
            headers=headers
        )
        result = response.status_code == 200
        if callback is not None:
            callback(result)
        else:
            return result
    except (requests.ConnectTimeout, requests.exceptions.ConnectionError) as e:
        return False

def get_rest_value(url, timeout, method, user, pwd, headers, callback=None, result_type='single', path=''):
    session = requests.Session()
    if user and pwd:
        session.auth = (user, pwd)
    try:
        response = session.request(
            url=url,
            timeout=timeout,
            method=method,
            headers=headers
        )
        resp = json.loads(response.content.decode().replace("'", '"'))
        result = parse_response(resp, path)
        if not result.isalnum():
            result = 0
        if callback is not None:
            callback(result)
        else:
            return result
    except (requests.ConnectTimeout, requests.exceptions.ConnectionError) as e:
        return 0

def parse_response(resp, path):
    if app_config.RESPONSE_PATH_SEPARATOR in path:
        r = None
        for s in path.split(app_config.RESPONSE_PATH_SEPARATOR):
            if r is None:
                if s in resp:
                    r = resp[s]
                else:
                    return ''
            else:
                if s in r:
                    r = r[s]
                else:
                    return ''
        return r
    else:
        if path in resp:
            return resp[path]
        else:
            return ''

def get_shell_value(command, args, callback=None):
    cmd = [command, ' '.join(str(s) for s in args)]
    try:
        output = subprocess.check_output(cmd)
        if output.isalnum():
            result = int(output)
        else:
            result = 0
    except:
        result = 0

    if callback is not None:
        callback(result)
    else:
        return result

def is_ping(ip, count, callback=None):
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, str(count), ip]
    try:
        output = subprocess.check_output(command)
        result = ('unreachable'.upper() not in str(output).upper() and
                  'could not find'.upper() not in str(output).upper() and
                  'time out'.upper() not in str(output).upper())
    except:
        result = False
    if callback is not None:
        callback(result)
    else:
        return result

def get_net_iface_stat(name):
    return psutil.net_io_counters(pernic=True).get(name)

def get_next_update_time(d):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(d.updated_at + d.interval))


class DiskMetric(AbstractMetric):
    def __init__(self, config, prefix=''):
        super().__init__('disk', config)
        for d in self.config:
            mount_point, interval, name = d['path'], d['interval'], d['name']
            total, used, free = shutil.disk_usage(mount_point)
            self.data_array.append(DiskData(mount_point, total, used, free, interval, name, prefix))

    def proceed_metric(self):
        for d in self.data_array:
            if d.is_need_to_update():
                mount_point = d.mount_point
                d.total, d.used, d.free = shutil.disk_usage(mount_point)
                d.set_data(d.total, d.used, d.free)

    def print_debug_info(self):
        for d in self.data_array:
            print(f'[DEBUG] (next update at {get_next_update_time(d)}) {d.mount_point}: total={d.total // (2 ** 30)} Gb, used={d.used // (2 ** 30)} Gb, free={d.free // (2 ** 30)} Gb')


class HealthMetric(AbstractMetric):
    def __init__(self, config, prefix=''):
        super().__init__('health', config)
        for d in self.config:
            name, url, interval, timeout, method = d['name'], d['url'], d['interval'], d['timeout'], d['method']
            if 'auth' in self.config:
                user = d['auth']['user']
                pwd = d['auth']['pass']
            else:
                user = ''
                pwd = ''
            if 'headers' in self.config:
                headers = d['headers']
            else:
                headers = ''
            result = is_health_check(url, timeout, method, user, pwd, headers)
            self.data_array.append(HealthData(name, url, interval, timeout, result, method, user, pwd, headers, prefix))

    def proceed_metric(self):
        for d in self.data_array:
            if d.is_need_to_update():
                thread = Thread(target=is_health_check, args=(d.url, d.timeout, d.method, d.user, d.password, d.headers, d.set_status))
                thread.start()

    def print_debug_info(self):
        for d in self.data_array:
            print(f'[DEBUG] (next update at {get_next_update_time(d)}) {d.url}: {ENUM_UP_DN_STATES[0].upper() if d.is_up else ENUM_UP_DN_STATES[1].upper()}')


class IcmpMetric(AbstractMetric):
    def __init__(self, config, prefix=''):
        super().__init__('ping', config)
        for d in self.config:
            name, ip, count, interval = d['name'], d['ip'], d['count'], d['interval']
            result = is_ping(ip, count)
            self.data_array.append(IcmpData(name, ip, count, interval, result, prefix))

    def proceed_metric(self):
        for d in self.data_array:
            if d.is_need_to_update():
                thread = Thread(target=is_ping, args=(d.ip, d.count, d.set_status))
                thread.start()

    def print_debug_info(self):
        for d in self.data_array:
            print(f'[DEBUG] (next update at {get_next_update_time(d)}) {d.ip}: {"UP" if d.is_up else "DN"}')


class InterfaceMetric(AbstractMetric):
    def __init__(self, config, prefix=''):
        super().__init__('iface', config)
        for d in self.config:
            name, iface, interval = d['name'], d['iface'], d['interval']
            result = get_net_iface_stat(iface)
            self.data_array.append(InterfaceData(name, iface, interval, result.bytes_sent, result.bytes_recv, prefix))

    def proceed_metric(self):
        for d in self.data_array:
            if d.is_need_to_update():
                result = get_net_iface_stat(d.iface)
                d.set_data(result.bytes_sent, result.bytes_recv)

    def print_debug_info(self):
        for d in self.data_array:
            print(f'[DEBUG] (next update at {get_next_update_time(d)}) {d.iface}: sent={d.sent}, receive={d.receive}')


class RestValueMetric(AbstractMetric):
    def __init__(self, config, prefix=''):
        super().__init__('rest_value', config)
        for d in self.config:
            name, url, interval, timeout, method = d['name'], d['url'], d['interval'], d['timeout'], d['method']
            if 'auth' in self.config:
                user = d['auth']['user']
                pwd = d['auth']['pass']
            else:
                user = ''
                pwd = ''
            if 'headers' in self.config:
                headers = d['headers']
            else:
                headers = ''
            result_type, result_path = d['result_type'], d['result_path']
            result = get_rest_value(url=url, timeout=timeout, method=method, user=user, pwd=pwd, headers=headers,
                                    result_type=result_type, path=result_path)
            self.data_array.append(RestValueData(name, url, interval, timeout, result, method, user, pwd, headers, prefix, result_type, result_path))

    def proceed_metric(self):
        for d in self.data_array:
            if d.is_need_to_update():
                thread = Thread(target=get_rest_value, args=(d.url, d.timeout, d.method, d.user, d.password, d.headers,
                                                             d.set_value, d.type, d.path))
                thread.start()

    def print_debug_info(self):
        for d in self.data_array:
            print(f'[DEBUG] (next update at {get_next_update_time(d)}) on {d.url}: by {d.method} in {d.path} got value="{d.value}"')


class ShellValueMetric(AbstractMetric):
    def __init__(self, config, prefix=''):
        super().__init__('shell_value', config)
        for d in self.config:
            name, command, interval, args = d['name'], d['command'], d['interval'], d['args']
            result = get_shell_value(command, args)
            self.data_array.append(ShellValueData(name, interval, command, result, args, prefix))

    def proceed_metric(self):
        for d in self.data_array:
            if d.is_need_to_update():
                thread = Thread(target=get_shell_value, args=(d.command, d.args, d.set_value))
                thread.start()

    def print_debug_info(self):
        for d in self.data_array:
            print(f'[DEBUG] (next update at {get_next_update_time(d)}) on local shell: by command {d.command} with args="{d.args}" got value="{d.value}"')


class UptimeMetric(AbstractMetric):
    def __init__(self, interval):
        super().__init__(None, {})
        self.data_array.append(UptimeData(interval))

    def proceed_metric(self):
        for d in self.data_array:
            if d.is_need_to_update():
                d.set_data()

    def print_debug_info(self):
        for d in self.data_array:
            print(f'[DEBUG] (next update at {get_next_update_time(d)}) Uptime: {d.uptime}')


class SystemMetric(AbstractMetric):
    def __init__(self, interval):
        super().__init__(None, {})
        self.data_array.append(SystemData(interval, app_config.INSTANCE_PREFIX))

    def proceed_metric(self):
        for d in self.data_array:
            if d.is_need_to_update():
                d.set_data()

    def print_debug_info(self):
        for d in self.data_array:
            print(f'[DEBUG] (next update at {get_next_update_time(d)}) CPU: {d.cpu}% Mem: {d.memory}% Uptime: {d.uptime}s '
                  f'CPU temperature: {d.cpu_temp} Chassis temperature: {d.ch_temp}')


if __name__ == '__main__':
    pass
