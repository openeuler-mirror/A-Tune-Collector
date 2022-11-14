#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2022 Huawei Technologies Co., Ltd.
# A-Tune is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2022-10-14

"""
The sub class of the monitor, used to collect the process sched info
"""
import inspect
import logging
import subprocess
import getopt
import re
from ..common import Monitor

LOGGER = logging.getLogger(__name__)


class ProcSched(Monitor):
    """To collect the process sched info"""
    _module = "PROCESS"
    _purpose = "SCHED"
    _option = "/proc/{}/sched"

    def __init__(self, user=None):
        Monitor.__init__(self, user)
        self.__cmd = "cat"
        self.__interval = 1
        self.__applications = []
        self.__pids = []
 
    def _get(self, para=None):
        output = ""
        pids = []
        if para is not None:
            opts, _ = getopt.getopt(para.split(), None, ['interval=', 'app='])
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
                elif opt in '--app':
                    if val is not None:
                        self.__applications = val.split(',')
                    else:
                        err = ValueError(
                            "{opt} parameter is none".format(
                                opt=opt))
                        LOGGER.error("%s.%s: %s", self.__class__.__name__,
                                     inspect.stack()[0][3], str(err))
                        raise err
        
        for app in self.__applications:
            pid = subprocess.getoutput(
                "ps -A | grep {} | awk '{{print $1}}'".format(app)).split()[0]
            pids.append(pid)
        self.__pids = pids

        for pid in self.__pids:
            out = subprocess.check_output(
                "{cmd} {opt}".format(
                    cmd=self.__cmd,
                    opt=self._option.format(pid)).split())
            output = output + "" + out.decode()
        return output

    def decode(self, info, para):
        """
        decode the result of the operation
        :param info:  content that needs to be decoded
        :param para:  command line argument
        :returns ret:  operation result
        """

        if para is None:
            return info
        
        start = 0
        keys = []
        ret = ""

        opts, _ = getopt.getopt(para.split(), None, ['nic=', 'fields=', 'device='])
        for opt, val in opts:
            if opt in '--fields':
                keys.append(val)
                continue

        pattern = re.compile(
            r"(\w+)\ {1,}\:\ {1,}(\d+.\d+)",
            re.I | re.UNICODE | re.MULTILINE)
        search_obj = pattern.findall(info)
        search_list = []
        for obj in search_obj:
            if obj[0][:3] == "nr_":
                search_list.append(obj[0][3:])
            else:
                search_list.append(obj[0])
            search_list.append(obj[1])
        if len(search_obj) == 0:
            err = LookupError("Fail to find data")
            LOGGER.error("%s.%s: %s", self.__class__.__name__,
                         inspect.stack()[0][3], str(err))
            raise err

        while start <= len(self.__applications) * len(keys):  
            for key in keys:
                ret = ret + " " + search_list[search_list.index(key, start)+1]
                start = search_list.index(key, start) + 1
        return ret