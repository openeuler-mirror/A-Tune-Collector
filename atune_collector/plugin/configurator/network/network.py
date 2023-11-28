#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2019 Huawei Technologies Co., Ltd.
# A-Tune is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2023-08-22

"""
The sub class of the Configurator, used to extend script for network for CPI.
"""

import re
import logging
import os
import math
import configparser
import subprocess

from ..exceptions import SetConfigError
from ..common import Configurator

LOGGER = logging.getLogger(__name__)


class Network(Configurator):
    _module = "NETWORK"
    _submod = "NETWORK"


    def __init__(self, user=None):
        Configurator.__init__(self, user)
        self._cmd_map = {'xps': ['all', 'off', 'half', 'separate', 'multi'],
                'rps': ['all', 'off', 'half', 'separate', 'multi'],
                'rfs': ['on', 'off']}
        self._nic = self._get_nic()
        self._queue_dir = '/sys/class/net/{}/queues'.format(self._nic)

    def _get_nic(self):
        if not os.path.isfile('/etc/atuned/atuned.cnf'):
            raise SetConfigError('Cannot get network name')
        config = configparser.ConfigParser()
        config.read('/etc/atuned/atuned.cnf')
        return config.get('system', 'network')

    def _get_init(self, pattern):
        dir_strs = shell_cmd(['ls', self._queue_dir], 
                'Failed to get dir under {}'.format(self._queue_dir))
        dir_list = re.findall(pattern, dir_strs)
        dir_list = sorted(dir_list, key=lambda x: int(x.split('-')[1]))
        core_num = os.cpu_count()
        return dir_list, core_num

    def _set_cpus(self, key, value, pattern):
        dir_list, core_num = self._get_init(pattern)
                
        multi_qs = len(dir_list)
        stride = 1 if core_num // multi_qs == 0 else core_num // multi_qs
        stragglers = 0 if core_num <= multi_qs else core_num % multi_qs
        cur_cpu = 0
        for index, dir_name in enumerate(dir_list):
            file_path = '{}/{}/{}_cpus'.format(self._queue_dir, dir_name, key)
            shell_cmd(['cat', file_path],
                    'Failed to set {}={}: does not support for {}'.format(key, value, key))

            if value == 'off':
                set_value = '0'
            elif value == 'all':
                set_value = 'f' * (core_num // 4)
                if core_num % 4 != 0:
                    bin_num = int('0b' + '1' * (core_num % 4), 2)
                    set_value = f"{bin_num:x}" + set_value
            elif value == 'half':
                half_num = core_num // 2
                if core_num == 1:
                    val_format = 1
                elif key == 'rps':
                    offset = index % (half_num + core_num % 2)
                    val_format = 1 << offset
                else:
                    offset = index % half_num
                    val_format = 1 << (offset + half_num + core_num % 2)
                set_value = f"{val_format:x}"
            elif value == 'separate':
                num = 1 << (index % core_num)
                set_value = f"{num:x}"
            elif value == 'multi': # value = multi:
                list_cpu = []
                gsize = stride if index >= stragglers else stride + 1
                for _ in range(gsize):
                    list_cpu.append(cur_cpu)
                    cur_cpu += 1
                set_value = self._u32list(list_cpu)
            else:
                raise SetConfigError("cannot set {} to {}".format(key, value))

            shell_cmd(['sh', '-c', 'echo {} > {}'.format(set_value, file_path)],
                    'Failed to set {} to {}'.format(key, file_path))
        return 0

    @staticmethod
    def _u32list(cpulist):
        max_cpu = 0
        ii = 0

        for _cpu in cpulist:
            max_cpu = max(max_cpu, _cpu)

        #init a bitmap
        map = [0] * (max_cpu + 1)

        # set bit map according to cpulist
        for _cpu in cpulist:
            map[_cpu] = 1

        #format a u32list
        seg = 0
        mask = ''
        for ii in range(max_cpu + 1):
            if ii % 4 == 0 and ii != 0:
                seg = format(seg, 'x')
                mask = seg + mask
                seg = 0
            if ii % 32 == 0 and ii != 0:
                mask = ',' + mask
            cur = map[ii]
            if cur == 1:
                val = 1 << (ii % 4)
                seg += val

        if seg != 0:
            seg = format(seg, 'x')
            mask = seg + mask
        return mask
    
    def _set_rfs(self, value, pattern):
        dir_list, _ = self._get_init(pattern)
        for dir_name in dir_list:
            file_path = '{}/{}/rps_flow_cnt'.format(self._queue_dir, dir_name)
            shell_cmd(['cat', file_path],
                    'Failed to set rfs={}: does not support for rfs'.format(value))
            if value == 'off':
                set_value = 0
            elif value == 'on':
                set_value = 4096
            else:
                raise SetConfigError("cannot set rfs to {}".format(value))
            shell_cmd(['sh', '-c', 'echo {} > {}'.format(set_value, file_path)],
                    'Failed to set rfs to {}'.format(file_path))
            
        if value == 'off':
            entries = 0
        elif value == 'on':
            entries = 4096 * len(dir_list)
        entries_path = '/proc/sys/net/core/rps_sock_flow_entries'
        shell_cmd(['sh', '-c', 'echo {} > {}'.format(entries, entries_path)],
                    'Failed to set rfs to {}'.format(entries_path))
        return 0

    def _set(self, key, value):
        if not key.lower() in self._cmd_map or not value.lower() in self._cmd_map[key.lower()]:
            raise SetConfigError("Invalid value {}={}".format(key, value))

        if key == 'xps':
            self._set_cpus(key.lower(), value.lower(), r'tx-\d+')
        elif key == 'rps':
            self._set_cpus(key.lower(), value.lower(), r'rx-\d+')
        elif key == 'rfs':
            self._set_rfs(value.lower(), r'rx-\d+')

        return 0
    
    def _get(self, key, _):
        pass
    
    def _backup(self, config, _):
        return str(config)

    @staticmethod
    def check(config1, config2):
        return True


def shell_cmd(cmd, error_message):
    output = subprocess.run(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if output.returncode != 0:
        raise SetConfigError(error_message)
    return output.stdout.decode()

