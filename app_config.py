import os

SCRIPT_PATH = os.path.dirname(__file__)
CONFIGS_DIR = SCRIPT_PATH + "/configs"
CONFIG_FILE_NAME = CONFIGS_DIR + "/config.json"
CONFIG_METRICS_FILE_NAME = CONFIGS_DIR + ("/metrics.json" if os.name.upper() == "POSIX" else "/metrics_win.json") # for debug purpose only
STOP_SERVER_FILE_NAME = SCRIPT_PATH + "/stop"
RESPONSE_PATH_SEPARATOR = '|'
CONFIG_METRICS_FILE_TIMESTAMP = 0.0

INSTANCE_PREFIX = ''
SERVER_PORT = 15200
SLEEP_THREAD_SECONDS = 30
UPTIME_UPDATE_SECONDS = 60
SYSTEM_UPDATE_SECONDS = 20

IS_DEBUG = False
IS_PRINT_INFO = False

if __name__ == "__main__":
    pass
