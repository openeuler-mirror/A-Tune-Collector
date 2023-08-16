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
# Create: 2023-07-13

"""
The sub class of the Configurator, used to change the redis config.
"""

import logging
import os
import subprocess
from ..exceptions import GetConfigError, SetConfigError
from ..common import Configurator

LOGGER = logging.getLogger(__name__)


class Redis(Configurator):
    _module = "REDIS"
    _submod = "REDIS"

    def __init__(self, user=None):
        Configurator.__init__(self, user)
        self.__lines = "{key} {value}"
        self.__re = r"^#\?\s*{key}\s* "
        self.__file_dir = "/etc/redis/"
        self.__file_path = self.__file_dir + "redis.conf"

    def _init_file(self):
        if not os.path.isdir(self.__file_dir):
            os.mkdir(self.__file_dir)
            os.chmod(self.__file_dir, 0o755)
        if not os.path.isfile(self.__file_path):
            with open(self.__file_path, 'w', 0o600):
                pass
            os.chmod(self.__file_path, 0o644)

    def _set(self, key, value):
        self._init_file()
        re_cmd = self.__re.format(key=key)
        grep_cmd = [r"grep", re_cmd, self.__file_path]
        out, err = self.execute_cmd(grep_cmd)
        if len(err) != 0:
            raise SetConfigError("Failed to set {}: {}".format(key, err))
        num_lines = out.count("\n")
        new_line = self.__lines.format(key=key, value=value)
        if num_lines == 0:
            with open(self.__file_path, 'a', 0o644) as f:
                f.write(new_line + '\n')
        elif num_lines == 1:
            sed_cmd = [r"sed", "-i", r"s/{}.*$/{}/g".format(re_cmd, new_line), self.__file_path]
            _, err_rep = self.execute_cmd(sed_cmd)
            if len(err_rep) > 0:
                raise SetConfigError("Failed to set {}: {}".format(key, err_rep))
        else:
            raise SetConfigError("Failed to set {}: more than 1 key has same name".format(key))
        return 0

    def _get(self, key, _):
        pass

    def _backup(self, config, _):
        return str(config)

    @staticmethod
    def check(config1, config2):
        return True

    @staticmethod
    def execute_cmd(cmd):
        output = subprocess.run(cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output.stdout.decode(), output.stderr.decode()[:-1]


