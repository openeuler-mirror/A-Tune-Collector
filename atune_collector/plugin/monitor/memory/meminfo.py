#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2020 Huawei Technologies Co., Ltd.
# A-Tune is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-12-30

"""
The sub class of the monitor, used to collect the vm stat info.
"""
import inspect
import logging
import subprocess
import getopt
import re

from ..common import Monitor

LOGGER = logging.getLogger(__name__)


class MemInfo(Monitor):
    """To collect the vm stat info"""
    _module = "MEM"
    _purpose = "MEMINFO"
    _option = "/proc/meminfo"

    def __init__(self, user=None):
        Monitor.__init__(self, user)
        self.__cmd = "cat"
        self.__interval = 1
        self.decode.__func__.__doc__ = Monitor.decode.__doc__ % (
            "--fields=MemTotal/MemFree/MemAvailable/Buffers/Cached/SwapCached/Active/Inactive/"
			"Active/Inactive/Active(anon)/Inactive(anon)/Active(file)/Inactive(file)/Unevictable/Mlocked/"
			"SwapTotal/SwapFree/Dirty/Writeback/AnonPages/Mapped/Shmem/Slab/SReclaimable/"
			"SUnreclaim/KernelStack/PageTables/NFS_Unstable/Bounce/WritebackTmp/CommitLimit/"
			"Committed_AS/VmallocTotal/VmallocUsed/VmallocChunk/Percpu/HardwareCorrupted/AnonHugePages/"
			"ShmemHugePages/ShmemPmdMapped/CmaTotal/CmaFree/HugePages_Total/HugePages_Free/HugePages_Rsvd/"
			"HugePages_Surp/Hugepagesize/Hugetlb")

    def _get(self, para=None):
        if para is not None:
            opts, _ = getopt.getopt(para.split(), None, ['interval='])
            for opt, val in opts:
                if opt in '--interval':
                    if val.isdigit():
                        self.__interval = int(val)
                    else:
                        err = ValueError(
                            "Invalid parameter: {opt}={val}".format(
                                opt=opt, val=val))
                        LOGGER.error("%s.%s: %s", self.__class__.__name__,
                                     inspect.stack()[0][3], str(err))
                        raise err
                    continue

        output = subprocess.check_output(
            "{cmd} {opt}".format(
                cmd=self.__cmd,
                opt=self._option).split())
        return output.decode()

    def decode(self, info, para):
        """
        decode the result of the operation
        :param info:  content that needs to be decoded
        :param para:  command line argument
        :returns ret:  operation result
        """
        if para is None:
            return info

        keys = []
        ret = ""

        opts, _ = getopt.getopt(para.split(), None, ['nic=', 'fields=', 'device='])
        for opt, val in opts:
            if opt in '--fields':
                keys.append(val)
                continue

        pattern = re.compile(
            r"(\w+)\:\ {1,}(\d+)",
            re.I | re.UNICODE | re.MULTILINE)
        search_obj = pattern.findall(info)
        search_list = []
        for obj in search_obj:
            search_list.append(obj[0])
            search_list.append(obj[1])

        if len(search_obj) == 0:
            err = LookupError("Fail to find data")
            LOGGER.error("%s.%s: %s", self.__class__.__name__,
                         inspect.stack()[0][3], str(err))
            raise err

        for i in keys:
            ret = ret + " " + search_list[search_list.index(i)+1]
        return ret
