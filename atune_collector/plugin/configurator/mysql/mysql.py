#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2023 Huawei Technologies Co., Ltd.
# A-Tune is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2023-07-11

"""
The sub class of the Configurator, used to change the /etc/my.cnf config.
"""


import logging
import os
from ..common import Configurator

LOGGER = logging.getLogger(__name__)

class Mysql(Configurator):
    _module = "MYSQL"
    _submod = "MYSQL"

    def __init__(self, user=None):
        Configurator.__init__(self, user)
        self.__cmd = ""
        self.__file_path = "/etc/my.cnf"
        self.__mysqld_ind = -1

    def _init_file(self):
        if not os.path.isfile(self.__file_path):
            with open(self.__file_path, 'w', 0o644):
                pass
            os.chmod(self.__file_path, 0o644)
        self.__check_mysqld()

    def __check_mysqld(self):
        with open(self.__file_path, 'r') as f:
            lines = f.readlines()

        for line in lines:
            self.__mysqld_ind = self.__mysqld_ind + 1
            if line[:-1] == '[mysqld]':
                self.__mysqld_ind = self.__mysqld_ind + 1
                return

        lines.insert(self.__mysqld_ind, "[mysqld]\n")
        self.__mysqld_ind = self.__mysqld_ind + 1
        with open(self.__file_path, 'w') as f:
            f.writelines(lines)

    def __check_file_exists(self, lines, start_with):
        ind = -1
        for line in lines:
            ind = ind + 1
            if line.split('=')[0].rstrip() == start_with:
                return True, ind
        return False, ind
    
    def _set(self, key, value):
        self._init_file()
        with open(self.__file_path, 'r', 0o400) as f:
            lines = f.readlines()

        key_exist, ind = self.__check_file_exists(lines, key)
        new_line = key + " = " + value + "\n"
        if not key_exist:
            lines.insert(self.__mysqld_ind, new_line)
        else:
            lines[ind] = new_line

        with open(self.__file_path, 'w', 0o644) as f:
            f.writelines(lines)
        return 0

    def _get(self, key, _):
        pass

    def _backup(self, config, _):
        return str(config)

    @staticmethod
    def check(config1, config2):
        return True

