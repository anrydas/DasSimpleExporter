import time
from threading import Thread

import psutil
from prometheus_client import Gauge, Enum, Counter, REGISTRY

import app_config

ENUM_UP_DN_STATES = ['up', 'dn']

def get_metric(name):
    return REGISTRY._names_to_collectors.get(name)

def get_gauge_metric(metric_name, descr):
    metric = get_metric(metric_name)
    if metric is None:
        metric = Gauge(metric_name, descr)
    return metric

def get_counter_metric(metric_name, descr):
    metric = get_metric(metric_name)
    if metric is None:
        metric = Counter(metric_name, descr)
    return metric

def get_enum_metric(metric_name, descr, states):
    metric = get_metric(metric_name)
    if metric is None:
        metric = Enum(metric_name, descr, states=states)
    return metric


class AbstractData:
    METRIC_NAME_PREFIX = 'das_'
    def __init__(self, name, interval, prefix=''):
        self.name = name
        self.interval = interval
        self.instance_prefix = prefix
        self.updated_at = int(time.time())

    def set_update_time(self):
        self.updated_at = int(time.time())

    def is_need_to_update(self):
        return self.updated_at + self.interval <= int(time.time())

    def get_metric_name(self, metric_text, name):
        return (self.METRIC_NAME_PREFIX +
                metric_text + '_' +
                (self.instance_prefix + '_' if self.instance_prefix else '') +
                name)

    def print_trigger_info(self):
        if app_config.IS_PRINT_INFO:
            print(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} [INFO]: Touch "{self.name}"')


class DiskData(AbstractData):
    g_total: Gauge
    g_used: Gauge
    g_free: Gauge
    def __init__(self, mount_point='/', total=0, used=0, free=0, interval=60, name='', prefix=''):
        super().__init__(name, interval, prefix)
        self.mount_point = mount_point
        self.total = total
        self.used = used
        self.free = free
        self.g_total = get_gauge_metric(self.get_metric_name('disk_total_bytes', name), 'Total bytes on disk')
        self.g_used = get_gauge_metric(self.get_metric_name('disk_used_bytes', name), 'Used bytes on disk')
        self.g_free = get_gauge_metric(self.get_metric_name('disk_free_bytes', name), 'Free bytes on disk')
        self.set_data(total, used, free)

    def set_data(self, total, used, free):
        self.g_total.set(total)
        self.g_used.set(used)
        self.g_free.set(free)
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
        metric_name = self.get_metric_name('service_health', name)
        self.e_state = get_enum_metric(metric_name, 'Service health', ENUM_UP_DN_STATES)
        self.set_status(is_up)

    def set_status(self, is_up):
        self.is_up = is_up
        self.e_state.state(ENUM_UP_DN_STATES[0] if is_up else ENUM_UP_DN_STATES[1])
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
        metric_name = self.get_metric_name('rest_value', name)
        self.g_value = get_gauge_metric(metric_name, 'Remote REST API Value ' + name)
        self.set_value(value)

    def set_value(self, value):
        self.value = value
        try:
            self.g_value.set(int(value))
        except:
            self.g_value.set(0)

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
        metric_name = self.get_metric_name('shell_value', name)
        self.g_value = get_gauge_metric(metric_name, 'Shell Value ' + name)
        self.set_value(value)

    def set_value(self, value):
        self.value = value
        try:
            self.g_value.set(int(value))
        except:
            self.g_value.set(0)

        self.set_update_time()
        self.print_trigger_info()


class IcmpData(AbstractData):
    e_state: Enum
    def __init__(self, name, ip, count, interval, is_up=False, prefix=''):
        super().__init__(name, interval, prefix)
        self.ip = ip
        self.count = count
        self.is_up = is_up
        metric_name = self.get_metric_name('host_available', name)
        self.e_state = get_enum_metric(metric_name, 'Host availability', ENUM_UP_DN_STATES)
        self.set_status(is_up)

    def set_status(self, is_up):
        self.is_up = is_up
        self.e_state.state(ENUM_UP_DN_STATES[0] if is_up else ENUM_UP_DN_STATES[1])
        self.set_update_time()
        self.print_trigger_info()


class InterfaceData(AbstractData):
    g_sent: Counter
    g_receive: Counter
    def __init__(self, name, iface, interval, sent, receive, prefix=''):
        super().__init__(name, interval, prefix)
        self.iface = iface
        self.sent = sent
        self.receive = receive
        sent_metric_name = self.get_metric_name('net_interface_sent_bytes', name)
        self.g_sent = get_counter_metric(sent_metric_name, 'Network Interface bytes sent')
        receive_metric_name = self.get_metric_name('net_interface_receive_bytes', name)
        self.g_receive = get_counter_metric(receive_metric_name, 'Network Interface bytes receive')
        self.set_data(sent, receive)

    def set_data(self, sent, receive):
        sent_delta = sent - self.sent
        recv_delta = receive - self.receive
        self.sent = sent
        self.receive = receive
        self.g_sent.inc(sent_delta)
        self.g_receive.inc(recv_delta)
        self.set_update_time()
        self.print_trigger_info()


class UptimeData(AbstractData):
    START_TIME = int(time.time())
    c_uptime: Counter
    def __init__(self, interval, prefix=''):
        super().__init__('uptime', interval, prefix)
        self.uptime = 0
        metric_name = self.get_metric_name('exporter', self.name)
        self.c_uptime = get_counter_metric(metric_name, 'Exporter Uptime in seconds')
        self.set_data()

    def set_data(self):
        uptime = int(time.time()) - self.START_TIME
        self.c_uptime.inc(uptime - self.uptime)
        self.uptime = uptime
        self.set_update_time()
        self.print_trigger_info()


class SystemData(AbstractData):
    BOOT_TIME = int(psutil.boot_time())
    c_uptime: Counter
    g_cpu: Gauge
    g_memory: Gauge
    g_chassis_temp: Gauge
    g_cpu_temp: Gauge
    def __init__(self, interval, prefix=''):
        super().__init__('system', interval, prefix)
        self.cpu, self.memory, self.uptime, self.ch_temp, self.cpu_temp = 0,0,0,0,0
        self.init_metrics()
        self.set_data()

    def init_metrics(self):
        uptime_metric_name = self.get_metric_name(self.name, 'uptime_seconds')
        self.c_uptime = get_counter_metric(uptime_metric_name, 'System uptime')
        cpu_metric_name = self.get_metric_name(self.name, 'cpu_percent')
        self.g_cpu = get_gauge_metric(cpu_metric_name, 'CPU used percent')
        mem_metric_name = self.get_metric_name(self.name, 'memory_percent')
        self.g_memory = get_gauge_metric(mem_metric_name, 'Memory used percent')
        chassis_temp_metric_name = self.get_metric_name(self.name, 'ChassisTemperature_current')
        self.g_chassis_temp = get_gauge_metric(chassis_temp_metric_name, 'Current Chassis Temperature overall')
        cpu_temp_metric_name = self.get_metric_name(self.name, 'CpuTemperature_current')
        self.g_cpu_temp = get_gauge_metric(cpu_temp_metric_name, 'Current CPU Temperature overall')

    def set_data(self):
        uptime = int(time.time()) - self.BOOT_TIME
        self.c_uptime.inc(uptime - self.uptime)
        self.uptime = uptime
        self.memory = psutil.virtual_memory().percent
        self.g_memory.set(self.memory)
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

            self.g_chassis_temp.set(self.ch_temp)
            self.g_cpu_temp.set(self.cpu_temp)
        except:
            self.ch_temp = -500
            self.cpu_temp = -500
            self.g_chassis_temp.set(self.ch_temp)
            self.g_cpu_temp.set(self.cpu_temp)

        self.set_update_time()
        self.print_trigger_info()

    def set_cpu_percent(self):
        self.cpu = psutil.cpu_percent(1)
        self.g_cpu.set(self.cpu)


if __name__ == '__main__':
    pass
