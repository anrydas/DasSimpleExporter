#!/usr/bin/python3
# Prometheus Metrics by -=:dAs:=-

import os
import sys
import time

import metrics.MetricClasses as M
import app_config

from config_file import read_config as read_cfg
from prometheus_client import start_http_server

def read_app_config():
    j, _ = read_cfg(app_config.CONFIG_FILE_NAME)
    config = j['monitor']['config']
    return config

def read_metrics_config():
    j, app_config.CONFIG_METRICS_FILE_TIMESTAMP = read_cfg(app_config.CONFIG_METRICS_FILE_NAME)
    metrics = j['monitor']['metrics']
    if 'instance_prefix' in j['monitor']:
        prefix = j['monitor']['instance_prefix']
    else:
        prefix = ''
    return metrics, prefix

def is_need_to_stop():
    return os.path.isfile(app_config.STOP_SERVER_FILE_NAME)

def get_config_value(cfg, name, default):
    return cfg[name] if name in cfg else default

def parse_config(cfg):
    app_config.IS_DEBUG = get_config_value(cfg, 'debug', app_config.IS_DEBUG).lower() == 'true'
    app_config.IS_PRINT_INFO = get_config_value(cfg, 'print_info', app_config.IS_PRINT_INFO).lower() == 'true'
    app_config.SLEEP_THREAD_SECONDS = get_config_value(cfg, 'interval_seconds', app_config.SLEEP_THREAD_SECONDS)
    app_config.SERVER_PORT = get_config_value(cfg, 'port', app_config.SERVER_PORT)
    app_config.UPTIME_UPDATE_SECONDS = get_config_value(cfg, 'uptime_update_seconds', app_config.UPTIME_UPDATE_SECONDS)
    app_config.SYSTEM_UPDATE_SECONDS = get_config_value(cfg, 'system_update_seconds', app_config.SYSTEM_UPDATE_SECONDS)
    app_config.RESPONSE_PATH_SEPARATOR = get_config_value(cfg, 'response_path_separator', app_config.RESPONSE_PATH_SEPARATOR)
    file_name = get_config_value(cfg, 'stop_file_name', app_config.STOP_SERVER_FILE_NAME)
    app_config.STOP_SERVER_FILE_NAME = app_config.SCRIPT_PATH + (file_name if file_name.startswith('/')  else '/' + file_name)

def init_metric_entities(data):
    return {
        M.DiskMetric(data),
        M.HealthMetric(data),
        M.IcmpMetric(data),
        M.InterfaceMetric(data),
        M.RestValueMetric(data),
        M.ShellValueMetric(data),
        M.UptimeMetric(app_config.UPTIME_UPDATE_SECONDS),
        M.SystemMetric(app_config.SYSTEM_UPDATE_SECONDS)
    }

def is_need_to_reload_config():
    return app_config.CONFIG_METRICS_FILE_TIMESTAMP != os.path.getmtime(app_config.CONFIG_METRICS_FILE_NAME)

def print_config_info_debug():
    print('-=: Debug Mode :=-')
    print(f'\tAPP_VERSION={app_config.APP_VERSION}')
    print(f'\tSCRIPT_PATH={app_config.SCRIPT_PATH}')
    print(f'\tCONFIGS_DIR={app_config.CONFIGS_DIR}')
    print(f'\tCONFIG_FILE_NAME={app_config.CONFIG_FILE_NAME}')
    print(f'\tCONFIG_METRICS_FILE_NAME={app_config.CONFIG_METRICS_FILE_NAME}')
    print(f'\tSTOP_SERVER_FILE_NAME={app_config.STOP_SERVER_FILE_NAME}')
    print(f'\tRESPONSE_PATH_SEPARATOR={app_config.RESPONSE_PATH_SEPARATOR}')
    print(f'\t---')
    print(f'\tSERVER_PORT={app_config.SERVER_PORT}')
    print(f'\tSLEEP_THREAD_SECONDS={app_config.SLEEP_THREAD_SECONDS}')
    print(f'\tUPTIME_UPDATE_SECONDS={app_config.UPTIME_UPDATE_SECONDS}')
    print(f'\tSYSTEM_UPDATE_SECONDS={app_config.SYSTEM_UPDATE_SECONDS}')
    print(f'\t---')
    print(f'\tIS_PRINT_INFO={app_config.IS_PRINT_INFO}')

def main():
    print(f'-=: Collector started (version {app_config.APP_VERSION}) :=-')
    if os.path.isfile(app_config.CONFIG_FILE_NAME):
        config = read_app_config()
        parse_config(config)
    if app_config.IS_DEBUG:
        print_config_info_debug()

    metrics_config, app_config.INSTANCE_PREFIX = read_metrics_config()
    metric_objects = init_metric_entities(metrics_config)

    start_http_server(app_config.SERVER_PORT)

    while True:
        if is_need_to_stop():
            os.remove(app_config.STOP_SERVER_FILE_NAME)
            print("-=: Collector stopped :=-")
            sys.exit(0)

        if is_need_to_reload_config():
            print('-=: Reloading metrics configuration :=-')
            metrics_config, app_config.INSTANCE_PREFIX = read_metrics_config()
            metric_objects = init_metric_entities(metrics_config)
            print('-=: Metrics configuration reloaded :=-')

        for m in metric_objects:
            m.proceed_metric()
            if app_config.IS_DEBUG:
                m.print_debug_info()

        if app_config.IS_DEBUG:
            print('- - -')

        time.sleep(app_config.SLEEP_THREAD_SECONDS)


if __name__ == '__main__':
    main()

