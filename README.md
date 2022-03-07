[English](./README.en.md) | 简体中文
# A-Tune-Collector

#### 介绍
A-Tune-Collector用于各类系统资源的数据采集，也可以作为A-Tune项目的采集器。


#### 安装教程

若作为采集器给A-Tune项目使用，需要执行如下命令进行安装

```
python3 setup.py install
```

#### 使用说明

采集命令格式

```
cd atune_collector
python3 collect_data.py [OPTIONS]
```

参数说明

| 参数         | 描述                                                         |
| ------------ | ------------------------------------------------------------ |
| --config, -c | 指定待解析的json文件，json文件用于配置待采集的系统资源信息；若不指定该选项，默认读取/etc/atune_collector/collect_data.json文件 |

使用示例

- 使用默认的采集资源配置文件

  ```
  python3 collect_data.py
  ```

- 使用指定的采集资源配置文件

  ```
  python3 collect_data.py -c collect_data.json
  ```

配置说明

表1 collect_data.json文件

| **配置名称**     | **配置说明**                          | **参数类型** | **取值范围** |
| ---------------- | ------------------------------------- | ------------ | ------------ |
| network          | 待采集的指定网卡                      | 字符串       | -            |
| block            | 待采集的指定磁盘                      | 字符串       | -            |
| sample_num       | 待采集的次数                          | 整型         | >0           |
| interval         | 待采集的间隔时间，单位为秒            | 整型         | >0           |
| output_dir       | 采集完后数据存储的文件路径            | 字符串       | -            |
| workload_type    | 采集环境的应用负载类型，用作输出文件名，默认为default | 字符串       | -            |
| collection_items | 需要采集的系统参数项，参见表2         | 列表         | -            |

最终采集完后，数据将保存为: `${output_dir}/${workload_type}-${finish_timestamp}.csv`

表2 collection_items项配置说明

| **配置名称** | **配置说明**                                             | **参数类型** | **取值范围** |
| ------------ | -------------------------------------------------------- | ------------ | ------------ |
| name         | 待采集项的名称                                           | 字符串       | -            |
| module       | 待采集项的所属分类，该分类需要与对应采集模块的定义相匹配 | 字符串       | -            |
| purpose      | 待采集项的所属类型，该类型需要与对应采集模块的定义相匹配 | 字符串       | -            |
| metrics      | 待采集项的具体指标                                       | 列表         | -            |
| threshold    | 待采集项的门限值                                         | 整型         | -            |

配置示例

collect_data.json文件配置示例：

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

#### 相关信息

A-Tune项目地址：https://gitee.com/openeuler/A-Tune