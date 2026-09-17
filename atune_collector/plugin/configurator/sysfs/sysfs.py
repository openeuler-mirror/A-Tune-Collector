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
# Create: 2019-10-29

"""
The sub class of the Configurator, used to change the /sys/* config.
"""

import os
import re

from ..common import Configurator


class Sysfs(Configurator):
    """To change the /sys/* config"""
    _module = "SYSFS"
    _submod = "SYSFS"
    _option = "/sys"

    def __init__(self, user=None):
        Configurator.__init__(self, user)

    def _getpath(self, key):
        """
        Build the sysfs path for the given key and make sure it can not
        escape the sysfs option base directory.

        :param key: The sysfs config key, relative to self._option
        :returns: The validated absolute path
        :raises ValueError: Fail, invalid key or path traversal attempt
        """
        if not isinstance(key, str) or not key or "\x00" in key:
            raise ValueError("Invalid sysfs key: {!r}".format(key))

        base = os.path.realpath(self._option)
        path = os.path.realpath(os.path.join(base, key))
        if path != base and not path.startswith(base + os.sep):
            raise ValueError("Invalid sysfs key: {!r}".format(key))
        return path

    def _get(self, key, _):
        path = self._getpath(key)
        with open(path, mode='r',
                  buffering=-1, encoding=None, errors=None, newline=None, closefd=True) as file:
            ret = file.read()

        pattern = r".*\[(.*)\].*"
        search_obj = re.search(pattern, ret, re.UNICODE | re.MULTILINE)
        if search_obj is not None:
            return search_obj.group(1)
        return ret

    def _set(self, key, value):
        if not isinstance(value, str) or "\x00" in value:
            raise ValueError("Invalid sysfs value for key: {!r}".format(key))
        path = self._getpath(key)
        with open(path, mode='w',
                  buffering=-1, encoding=None, errors=None, newline=None, closefd=True) as file:
            file.write(value)
        return 0

    @staticmethod
    def check(_, __):
        """check"""
        return True
