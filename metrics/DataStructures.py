import time
from threading import Thread

import psutil
from prometheus_client import Gauge, Enum, Counter, REGISTRY

import app_config

ENUM_UP_DN_STATES = ['up', 'dn']

def get_metric(name):
    return REGISTRY._names_to_collectors.get(name)

def get_gauge_metric(metric_name, descr, labels=None):
    if labels is None:
        labels = []
    metric = get_metric(metric_name)
    if metric is None:
        if labels:
            metric = Gauge(metric_name, descr, labelnames=labels)
        else:
            metric = Gauge(metric_name, descr)
    return metric

def get_counter_metric(metric_name, descr, labels=None):
    metric = get_metric(metric_name)
    if metric is None:
        if labels:
            metric = Counter(metric_name, descr, labelnames=labels)
        else:
            metric = Counter(metric_name, descr)
    return metric

def get_enum_metric(metric_name, descr, states, labels=None):
    metric = get_metric(metric_name)
    if metric is None:
        if labels:
            metric = Enum(metric_name, descr, states=states, labelnames=labels)
        else:
            metric = Enum(metric_name, descr, states=states)
    return metric

def get_time_millis():
    return round(time.time() * 1000)


class AbstractData:
    g_collect: Gauge
    def __init__(self, name, interval, prefix=''):
        self.name = name
        self.interval = interval
        self.instance_prefix = prefix
        self.updated_at = int(time.time())
        self.g_collect = get_gauge_metric('das_collect_time_ms',
                                          'Total time spent collecting metrics [name] on [server] in milliseconds',
                                          ['server', 'name'])
        self.g_collect.labels(server=prefix, name=name)
        self.g_collect.labels(server=prefix, name=name)
        self.g_collect.labels(server=prefix, name=name)
        self.g_collect.labels(server=prefix, name=name)
        self.g_collect.labels(server=prefix, name=name)
        self.g_collect.labels(server=prefix, name=name)
        self.g_collect.labels(server=prefix, name=name)
        self.g_collect.labels(server=prefix, name=name)

    def set_update_time(self):
        self.updated_at = int(time.time())

    def is_need_to_update(self):
        return self.updated_at + self.interval <= int(time.time())

    def set_collect_time(self, value=0):
        self.g_collect.labels(server=self.instance_prefix, name=self.name).set(value)

    def print_trigger_info(self):
        if app_config.IS_PRINT_INFO:
            print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} [INFO]: Touch "{self.name}"')


class DiskData(AbstractData):
    g_all: Gauge
    def __init__(self, mount_point='/', total=0, used=0, free=0, interval=60, name='', prefix=''):
        super().__init__(name, interval, prefix)
        self.mount_point = mount_point
        self.total = total
        self.used = used
        self.free = free
        self.g_all = get_gauge_metric('das_disk_bytes',
                                      'Bytes [total, used, free] on [mount_point] for [server]',
                                      ['name', 'mount', 'server', 'metric'])
        self.g_all.labels(name=name, mount=mount_point, server=self.instance_prefix, metric='total')
        self.g_all.labels(name=name, mount=mount_point, server=self.instance_prefix, metric='used')
        self.g_all.labels(name=name, mount=mount_point, server=self.instance_prefix, metric='free')
        self.set_data(total, used, free)

    def set_data(self, total, used, free):
        time_ms = get_time_millis()
        self.g_all.labels(name=self.name, mount=self.mount_point, server=self.instance_prefix, metric='total').set(total)
        self.g_all.labels(name=self.name, mount=self.mount_point, server=self.instance_prefix, metric='used').set(used)
        self.g_all.labels(name=self.name, mount=self.mount_point, server=self.instance_prefix, metric='free').set(free)
        self.set_collect_time(get_time_millis() - time_ms)
        self.set_update_time()
        self.print_trigger_info()


class HealthData(AbstractData):
    e_state: Enum
    def __init__(self, name, url, interval, timeout, is_up=False, method='GET', user=None, password=None, headers=None, prefix=''):
        super().__init__(name, interval, prefix)
        if headers is None:
            headers = {}
        self.url = url
        self.timeout = timeout
        self.is_up = is_up
        self.method = method.upper()
        self.user = user
        self.password = password
        self.headers = headers
        self.e_state = get_enum_metric('das_service_health',
                                       'Service [name, url, method, server] health',
                                       ENUM_UP_DN_STATES,['name', 'url', 'method', 'server'])
        self.e_state.labels(name=name, url=url, method=method, server=self.instance_prefix)
        self.set_data(is_up)

    def set_data(self, is_up):
        time_ms = get_time_millis()
        self.is_up = is_up
        self.e_state.labels(name=self.name, url=self.url, method=self.method, server=self.instance_prefix).state(ENUM_UP_DN_STATES[0] if is_up else ENUM_UP_DN_STATES[1])
        self.set_collect_time(get_time_millis() - time_ms)
        self.set_update_time()
        self.print_trigger_info()


class RestValueData(AbstractData):
    g_value: Gauge
    def __init__(self, name, url, interval, timeout, value=None, method='GET', user=None, password=None, headers=None, prefix='',
                 result_type='single', result_path=''):
        super().__init__(name, interval, prefix)
        if headers is None:
            headers = {}
        self.url = url
        self.timeout = timeout
        self.method = method.upper()
        self.user = user
        self.password = password
        self.headers = headers
        self.value = value
        self.type = result_type
        self.path = result_path
        self.g_value = get_gauge_metric('das_rest_value',
                                        'Remote REST API [name, url, method, server] Value',
                                        ['name', 'url', 'method', 'server'])
        self.g_value.labels(name=name, url=url, method=method, server=self.instance_prefix)
        self.set_data(value)

    def set_data(self, value):
        time_ms = get_time_millis()
        self.value = value
        try:
            self.g_value.labels(name=self.name, url=self.url, method=self.method, server=self.instance_prefix).set(int(value))
        except:
            self.g_value.labels(name=self.name, url=self.url, method=self.method, server=self.instance_prefix).set(0)

        self.set_collect_time(get_time_millis() - time_ms)
        self.set_update_time()
        self.print_trigger_info()


class ShellValueData(AbstractData):
    g_value: Gauge
    def __init__(self, name, interval, command, value=None, args=None, prefix=''):
        super().__init__(name, interval, prefix)
        if args is None:
            args = {}
        self.command = command
        self.value = value
        self.args = args
        self.g_value = get_gauge_metric('das_shell_value',
                                        'Shell [name, command, server] Value',
                                        ['name', 'command', 'server'])
        self.g_value.labels(name=name, command=command, server=self.instance_prefix)
        self.set_data(value)

    def set_data(self, value):
        time_ms = get_time_millis()
        self.value = value
        try:
            self.g_value.labels(name=self.name, command=self.command, server=self.instance_prefix).set(int(value))
        except:
            self.g_value.labels(name=self.name, command=self.command, server=self.instance_prefix).set(0)

        self.set_collect_time(get_time_millis() - time_ms)
        self.set_update_time()
        self.print_trigger_info()


class IcmpData(AbstractData):
    e_state: Enum
    def __init__(self, name, ip, count, interval, is_up=False, prefix=''):
        super().__init__(name, interval, prefix)
        self.ip = ip
        self.count = count
        self.is_up = is_up
        self.e_state = get_enum_metric('das_host_available',
                                       'Host [name, ip, server] availability',
                                       ENUM_UP_DN_STATES, ['name', 'ip', 'server'])
        self.e_state.labels(name=name, ip=ip, server=self.instance_prefix)
        self.set_data(is_up)

    def set_data(self, is_up):
        time_ms = get_time_millis()
        self.is_up = is_up
        self.e_state.labels(name=self.name, ip=self.ip, server=self.instance_prefix).state(ENUM_UP_DN_STATES[0] if is_up else ENUM_UP_DN_STATES[1])
        self.set_collect_time(get_time_millis() - time_ms)
        self.set_update_time()
        self.print_trigger_info()


class InterfaceData(AbstractData):
    g_all: Counter
    def __init__(self, name, iface, interval, sent, receive, prefix=''):
        super().__init__(name, interval, prefix)
        self.iface = iface
        self.sent = sent
        self.receive = receive
        self.g_all = get_counter_metric('das_net_interface_bytes',
                                        'Network Interface [name, server, metric=[sent,receive]] bytes',
                                        ['name', 'server', 'metric'])
        self.g_all.labels(name=name, server=self.instance_prefix, metric='sent')
        self.g_all.labels(name=name, server=self.instance_prefix, metric='receive')
        self.set_data(sent, receive)

    def set_data(self, sent, receive):
        time_ms = get_time_millis()
        sent_delta = sent - self.sent
        recv_delta = receive - self.receive
        self.sent = sent
        self.receive = receive
        self.g_all.labels(name=self.name, server=self.instance_prefix, metric='sent').inc(sent_delta)
        self.g_all.labels(name=self.name, server=self.instance_prefix, metric='receive').inc(recv_delta)
        self.set_collect_time(get_time_millis() - time_ms)
        self.set_update_time()
        self.print_trigger_info()


class UptimeData(AbstractData):
    START_TIME = int(time.time())
    c_uptime: Counter
    def __init__(self, interval, prefix=''):
        super().__init__('uptime', interval, prefix)
        self.uptime = 0
        self.c_uptime = get_counter_metric('das_exporter',
                                           'Exporter Uptime for [server] in seconds',
                                           ['server'])
        self.c_uptime.labels(server=self.instance_prefix)
        self.set_data()

    def set_data(self):
        time_ms = get_time_millis()
        uptime = int(time.time()) - self.START_TIME
        self.c_uptime.labels(server=self.instance_prefix).inc(uptime - self.uptime)
        self.uptime = uptime
        self.set_collect_time(get_time_millis() - time_ms)
        self.set_update_time()
        self.print_trigger_info()


class SystemData(AbstractData):
    BOOT_TIME = int(psutil.boot_time())
    c_uptime: Counter
    g_cpu: Gauge
    g_memory: Gauge
    g_tempr: Gauge
    g_cpu_temp: Gauge
    def __init__(self, interval, prefix=''):
        super().__init__('system', interval, prefix)
        self.cpu, self.memory, self.uptime, self.ch_temp, self.cpu_temp = 0,0,0,0,0
        self.init_metrics()
        self.set_data()

    def init_metrics(self):
        self.c_uptime = get_counter_metric('das_uptime_seconds', 'System uptime on [server]', ['server'])
        self.c_uptime.labels(server=self.instance_prefix)
        self.g_cpu = get_gauge_metric('das_cpu_percent', 'CPU used percent on [server]', ['server'])
        self.g_cpu.labels(server=self.instance_prefix)
        self.g_memory = get_gauge_metric('das_memory_percent', 'Memory used percent on [server]', ['server'])
        self.g_memory.labels(server=self.instance_prefix)
        self.g_tempr = get_gauge_metric('das_temperature', 'Temperature of [type] overall on [server]', ['metric', 'server'])
        self.g_tempr.labels(server=self.instance_prefix, metric='CPU')
        self.g_tempr.labels(server=self.instance_prefix, metric='Chassis')

    def set_data(self):
        time_ms = get_time_millis()
        uptime = int(time.time()) - self.BOOT_TIME
        self.c_uptime.labels(server=self.instance_prefix).inc(uptime - self.uptime)
        self.uptime = uptime
        self.memory = psutil.virtual_memory().percent
        self.g_memory.labels(server=self.instance_prefix).set(self.memory)
        Thread(target=self.set_cpu_percent()).run()

        try:
            avg_temp = 0
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                self.cpu_temp = temps["coretemp"][0].current
            elif 'cpu_thermal' in temps:
                self.cpu_temp = temps["cpu_thermal"][0].current
            else:
                # if no coretemp we try to get an average temperature
                temp, amount = 0, 0
                for i in temps.keys():
                    if i != 'acpitz':
                        temp += temps.get(i)[0].current
                        amount += 1
                self.cpu_temp = temp // amount

            if 'acpitz' in temps:
                self.ch_temp = temps["acpitz"][0].current
            else:
                self.ch_temp = self.cpu_temp

            self.g_tempr.labels(server=self.instance_prefix, metric='Chassis').set(self.ch_temp)
            self.g_tempr.labels(server=self.instance_prefix, metric='CPU').set(self.cpu_temp)
        except:
            self.ch_temp = -500
            self.cpu_temp = -500
            self.g_tempr.labels(server=self.instance_prefix, metric='Chassis').set(self.ch_temp)
            self.g_tempr.labels(server=self.instance_prefix, metric='CPU').set(self.cpu_temp)

        self.set_collect_time(get_time_millis() - time_ms)
        self.set_update_time()
        self.print_trigger_info()

    def set_cpu_percent(self):
        self.cpu = psutil.cpu_percent(1)
        self.g_cpu.labels(server=self.instance_prefix).set(self.cpu)


if __name__ == '__main__':
    pass
