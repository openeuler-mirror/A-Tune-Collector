English | [简体中文](./README.md)
# A-Tune-Collector

#### Introduction
The A-Tune-Collector is used to collect various system resources and can also be used as the collector of the A-Tune project.

#### Installation

If the collector is used for the A-Tune project, run the following command to install the collector.

```
python3 setup.py install
```

#### Instructions

Collection Command Format

```
cd atune_collector
python3 collect_data.py [OPTIONS]
```

Parameter Description

| Parameter    | Description                                                  |
| ------------ | ------------------------------------------------------------ |
| --config, -c | Specifies the json file to be parsed. The json file is used to configure the system resource information to be collected. If this parameter is not specified, the /etc/atune_collector/collect_data.json file is read by default. |

Example

- Use the default collection resource configuration file.

  ```
  python3 collect_data.py
  ```

- Use the specified collection resource configuration file.

  ```
  python3 collect_data.py -c collect_data.json
  ```

Configuration Description

Table 1 The file of collect_data.json

| Name             | Description                                                  | Type             | Value Range |
| ---------------- | ------------------------------------------------------------ | ---------------- | ----------- |
| network          | Specifies the NIC to be collected.                           | Character string | -           |
| block            | Specifies the disk to be collected.                          | Character string | -           |
| sample_num       | Specifies the sample num to be collected.                    | Integer          | >0          |
| interval         | Interval for collecting data, in seconds.                    | Integer          | >0          |
| output_dir       | File path for storing collected data.                        | Character string | -           |
| workload_type    | Application load type of the collection environment. The default value is default. | Character string | -           |
| collection_items | Table 2 lists the system parameters to be collected.         | List             | -           |

Table 2 Description of collection_items configuration items

| Name      | Description                                                  | Type             | Value Range |
| --------- | ------------------------------------------------------------ | ---------------- | ----------- |
| name      | Name of the item to be collected.                            | Character string | -           |
| module    | Category of the item to be collected. The category must match the definition of the corresponding collection module. | Character string | -           |
| purpose   | Type of the item to be collected. The type must match the definition of the corresponding collection module. | Character string | -           |
| metrics   | Indicators of the item to be collected.                      | List             | -           |
| threshold | Threshold of the item to be collected.                       | Integer          | -           |

Example

The following is an example of the collect_data.json file.

```
{
  "network": "eth0",
  "block": "sda",
  "sample_num": 20,
  "interval": 5,
  "output_dir": "/var/atuned/collect_data",
  "workload_type": "default",
  "collection_items": [
    {
      "name": "cpu",
      "module": "CPU",
      "purpose": "STAT",
      "metrics": [
        "usr",
        "nice",
        "sys",
        "iowait",
        "irq",
        "soft",
        "steal",
        "guest",
        "util",
        "cutil"
      ],
      "threshold": 30
    },
    {
      "name": "storage",
      "module": "STORAGE",
      "purpose": "STAT",
      "metrics": [
        "rs",
        "ws",
        "rMBs",
        "wMBs",
        "rrqm",
        "wrqm",
        "rareq-sz",
        "wareq-sz",
        "r_await",
        "w_await",
        "util",
        "aqu-sz"
      ]
    },
    {
      "name": "network",
      "module": "NET",
      "purpose": "STAT",
      "metrics": [
        "rxkBs",
        "txkBs",
        "rxpcks",
        "txpcks",
        "ifutil"
      ]
    },
    {
      "name": "network-err",
      "module": "NET",
      "purpose": "ESTAT",
      "metrics": [
        "errs",
        "util"
      ]
    },
    {
      "name": "mem.band",
      "module": "MEM",
      "purpose": "BANDWIDTH",
      "metrics": [
        "Total_Util"
      ]
    },
    {
      "name": "perf",
      "module": "PERF",
      "purpose": "STAT",
      "metrics": [
        "IPC",
        "CACHE-MISS-RATIO",
        "MPKI",
        "ITLB-LOAD-MISS-RATIO",
        "DTLB-LOAD-MISS-RATIO",
        "SBPI",
        "SBPC"
      ]
    },
    {
      "name": "vmstat",
      "module": "MEM",
      "purpose": "VMSTAT",
      "metrics": [
        "procs.b",
        "memory.swpd",
        "io.bo",
        "system.in",
        "system.cs",
        "util.swap",
        "util.cpu",
        "procs.r"
      ]
    },
    {
      "name": "sys.task",
      "module": "SYS",
      "purpose": "TASKS",
      "metrics": [
        "procs",
        "cswchs"
      ]
    },
    {
      "name": "sys.ldavg",
      "module": "SYS",
      "purpose": "LDAVG",
      "metrics": [
        "runq-sz",
        "plist-sz",
        "ldavg-1",
        "ldavg-5"
      ]
    },
    {
      "name": "file.util",
      "module": "SYS",
      "purpose": "FDUTIL",
      "metrics": [
        "fd-util"
      ]
    }
  ]
}
```

#### Relate Information

A-Tune project：https://gitee.com/openeuler/A-Tune
