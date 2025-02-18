## Das Simple Exporter
### _Das Simple metrics Exporter for Prometheus_

[![Python](https://img.shields.io/badge/Python-3-green)](https://www.python.org) [![Prometheus](https://img.shields.io/badge/Prometheus-project-orange)](https://prometheus.io/) [![Grafana](https://img.shields.io/badge/Grafana-project-orange)](https://grafana.com/) [![Docker](https://img.shields.io/badge/Docker-project-blue)](https://www.docker.com/)

### 💡 Purpose
Create configurable lightweight application to collect some metrics

### 📃 Features
- lightweight and system resources friendly
- [configurable application](#AppConfig)
- [configurable metrics](#MetricsConfig) to be collected
- supported several [metric types](#MetricTypes)
- hot reload metrics if configuration changed
- could be used as [regular application](#StartRegular), as [systemctl service](#StartService) or a [Docker application](#StartDocker)
- supports JSON, PROPERTIES and YAML configuration formats

### 📌 Using
_To use specific configuration format the `app_config.CONFIG_FILE_NAME` variable need to be changed. The default config file format is **JSON**_

#### Application Configuration <a id='AppConfig' />
Default config stored in `./configs/` directory in Application dir. To change its location the `app_config.CONFIGS_DIR` variable need to be changed.

**_Application config changes to take effect the application need to be restarted._**

The Default Application config is:
```json
{
  "monitor": {
    "config": {
      "debug": "false",
      "print_info": "false",
      "interval_seconds": 30,
      "uptime_update_seconds": 60,
      "port": 15200,
      "stop_file_name": "/stop",
      "response_path_separator": "|"
    }
  }
}
```
- `debug` and `print_info` values need for debug purpose and used to output the debugging information into standard output.
- `interval_seconds` - metrics update time in seconds. Indicates how often every metric will be touch to check if its need to be updated. Every metric have its own update interval.
- `uptime_update_seconds` - the Application uptime metric update interval in seconds.
- `port` - port on which the Exporter's service to be started
- `stop_file_name` - if this file name appears in application's directory the Application will be stopped.
- `response_path_separator` - the response path separator. Used in `rest_value` metric configuration.

#### Metrics Configuration<a id='MetricsConfig' />
There are some embedded metrics in the Exporter:
- Exporter uptime
- System uptime
- CPU used percents
- Memory used percents
- Chassis temperature
- CPU temperature

Default config stored in `./configs/config.json` file. To change it the `app_config.CONFIG_METRICS_FILE_NAME` variable need to be changed.

The Default Application config is (no custom metrics are configured):
```json
{
  "monitor": {
    "instance_prefix": "",
    "metrics": {
      "disk": [],
      "health": [],
      "ping": [],
      "iface": [],
      "rest_value": [],
      "shell_value": []
    }
  }
}
```
`instance_prefix` - prefix that identifies Instance the Exporter launched on. It used to [create the Metric name](#MetricName). May be empty.

<a id='MetricTypes' />**The Exporter supports following types of metrics:**
**Common parameters:**
- `name` - parameter used in every metric to identify it. **Required**.
- `interval` - time interval in seconds the metric will be updated. **Required**.

#### Disk (or mount point) Metrics<a id='DiscMetrics' />
**_Monitors the Mount Point's sizes: `total`, `used`, `free` space in bytes_**
```json
{
  "name": "root",
  "path": "/",
  "interval": 20
}
```
- `path` - FS path to mount point which size will be monitored

#### Service Health Metrics
**_Monitors the Service's Health by http request: if 200 code in response - the service is `up`, otherwise - the service is `dn`_**
```json
{
  "name": "google",
  "url": "https://google.com",
  "method": "GET",
  "auth": {
    "user": "",
    "pass": ""
  },
  "headers": {
    "d1": "d1",
    "d2": "d2"
  },
  "interval": 30,
  "timeout": 1
}
```
- `url` - URL to be monitored
- `methd` - method to send request
- `auth` - authentication section. Optional
  - `user` - user name
  - `pass` - user password
- `headers` - http headers section to be sent to the host. Optional. The header's key-value pairs will be sent as is.
- `timeout` - timeout to wait for response

#### ICMP (Ping) Metrics
**_Monitors the Host Health by `ping` command: if ip address reachable - the service is `up`, otherwise - the service is `dn`_**
```json
{
  "name": "Router",
  "ip": "192.168.0.1",
  "interval": 30,
  "count": 1
}
```
- `ip` - IP Address or DNS name of the host
- `count` - pings count

#### Network Interface Metrics
**_Monitors the Network Interface metrics: send and receive bytes_**
```json
{
  "name": "Eth0",
  "iface": "eth0",
  "interval": 15
}
```
- `iface` - system name of network interface (i.e. `eth0`, `lo0`, `wlp4s0`, etc.)

#### REST value Metrics
**_Gets the responses value from http request to REST service_**
```json
{
  "name": "MyService",
  "url": "http://localhost:8080/api/v1/api",
  "method": "POST",
  "auth": {
    "user": "",
    "pass": ""
  },
  "headers": {
    "d1": "d1",
    "d2": "d2"
  },
  "result_type": "single",
  "result_path": "result",
  "interval": 30,
  "timeout": 2
}
```
- `url` - URL to be monitored
- `methd` - method to send request
- `auth` - authentication section. Optional
  - `user` - user name
  - `pass` - user password
- `headers` - http headers section to be sent to the host. Optional. The header's key-value pairs will be sent as is.
- `result_type` - type of result. The `single` type supported yet.
- `result_path` - path to result value in response JSON separated by `app_config.RESPONSE_PATH_SEPARATOR` character. Could be configured in [Application config](#AppConfig).
- `timeout` - timeout to wait for response

#### Shell value Metrics
**_Gets the shell command executed result value_**
```json
{
  "name": "shell",
  "command": "echo",
  "args": [3],
  "interval": 5
}
```
- `command` - command to be executed
- `args` - CLI arguments to be provided to the command
In example above the metric will return integer value 3.

<a id='MetricName' />**The metric name creates as follows:**
- uses Metric Prefix, actually `das_`
- uses `metric_text` given to every metric while it creating
- uses `instance_prefix` given in metric configuration
- uses `name` given in metric configuration
**Note:** there are no doubles in metrics names supported by Prometheus. If so the exception occurs ant the application will be stopped.

### 🚀 Launching the application
Use provided `install.sh` script to prepare application to use as service. Or use following shell commands to initialize the Python's Virtual env.
```shell
python3 -m venv .venv
. ./.venv/bin/activate
pip install -r requirements.txt
deactivate
```

#### Regular application<a id='StartRegular' />
In application directory:
```shell
. ./.venv/bin/activate
python ./main.py
```

##### System service (preferred option)<a id='StartService' />
Prepare the [dasExporter.service](dasExporter.service) file. Then launch commands:
```shell
sudo ln -s "$( cd -- $(dirname $0) >/dev/null 2>&1 ; pwd -P )/dasExporter.service" /etc/systemd/system/dasExporter.service
sudo systemctl daemon-reload
sudo systemctl start dasExporter
sudo systemctl enable dasExporter
```
To view service status use `sudo systemctl status dasExporter`
To restart the service use `sudo systemctl restart dasExporter`
To stop the service use `sudo systemctl stop dasExporter`

##### Docker application<a id='StartDocker' />
Use provided [docker-compose.yaml](docker-compose.yaml) and [Dockerfile](Dockerfile) files to launch Exporter in docker container.

**_Make sure you provided all mounts you need to be monitored in `volume` section in the `docker-compose.yaml` file and made according changes in [Disc Metrics Configuration](#DiscMetrics)._**

**Note:** In Docker some functions may be unavailable.

###### _Made by -=:dAs:=-_