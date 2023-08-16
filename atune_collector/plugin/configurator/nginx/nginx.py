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
# Create: 2023-07-14

"""
The sub class of the Configurator, used to extend script for /etc/nginx/nginx.conf for CPI.
"""

import logging
import os
import subprocess

from ..exceptions import SetConfigError
from ..common import Configurator

LOGGER = logging.getLogger(__name__)


class Nginx(Configurator):
    _module = "NGINX"
    _submod = "NGINX"

    def __init__(self, user=None):
        Configurator.__init__(self, user)
        self.__file_dir = "/etc/nginx/"
        self.__file_path = self.__file_dir + "nginx.conf"
        self.__line = "{key} {value};\n"
        self.__key_match = r"^([a-zA-Z]+(_[a-zA-Z]+)*.?[a-zA-Z]+)*$"
        self.__ind = {"main": [0, 0]}

    def _init_file(self):
        if not os.path.isdir(self.__file_dir):
            os.mkdir(self.__file_dir)
            os.chmod(self.__file_dir, 0o755)
        if not os.path.isfile(self.__file_path):
            with open(self.__file_path, 'w', 0o644):
                pass
            os.chmod(self.__file_path, 0o644)
        self._set_index()

    def _get_lines(self):
        with open(self.__file_path, 'r', 0o444) as f:
            lines = f.readlines()
        return lines

    def _set_lines(self, lines):
        with open(self.__file_path, 'w', 0o644) as f:
            f.writelines(lines)

    def _set_index(self):
        lines = self._get_lines()
        filo = []
        ind = []
        filo.append("start")
        ind.append(0)
        is_https_server = False
        for i, line in enumerate(lines):
            if i == len(lines) - 1:
                self.__ind["main"] = [ind.pop(), i]
                del filo, ind
            if line.strip().startswith("}"):
                close = filo.pop()
                close_ind = ind.pop()
                if close.startswith("events"):
                    self.__ind["events"] = [close_ind, i]
                if close.startswith("http"):
                    self.__ind["http"] = [close_ind, i]
                if close.startswith("server"):
                    if is_https_server:
                        self.__ind["https_server"] = [close_ind, i]
                    else:
                        self.__ind["http_server"] = [close_ind, i]
                    is_https_server = False
            if "{" in line.strip().split("#")[0]:
                filo.append(line.strip())
                ind.append(i)
            if line.strip().startswith("ssl_"):
                is_https_server = True

    def _check_key(self, key):
        if len(key) == 0:
            return False, 0
        count = 1
        if not ('a' <= key[0] <= 'z' or 'A' <= key[0] <= 'Z'):
            return False, count
        for i in range(1, len(key)):
            if key[i] == '_' or key[i] == '.':
                if not ('a' <= key[i - 1] <= 'z' or 'A' <= key[i - 1] <= 'Z'):
                    return False, count
                if i == len(key) - 1:
                    return False, count
                if key[i] == '.':
                    count = count + 1
            elif 'a' <= key[i] <= 'z' or 'A' <= key[i] <= 'Z':
                continue
            else:
                return False, count
        return True, count

    def _update_index(self, after_ind):
        for key in self.__ind:
            for i, val in enumerate(self.__ind[key]):
                if val > after_ind:
                    self.__ind[key][i] = val + 1

    def _append_lines(self, section, key, value):
        lines = self._get_lines()
        filo = []
        for i in range(self.__ind[section][0], self.__ind[section][1]):
            curr_line = lines[i].strip()
            if "{" in curr_line.split("#")[0]:
                filo.append(lines[i].strip())
            elif curr_line.startswith("}"):
                filo.pop()
            elif section == 'main' and len(filo) > 0:
                continue
            elif len(filo) > 1:
                continue
            elif curr_line.startswith(key + " ") or curr_line.startswith(key + "\t"):
                new_line = lines[i].split(key)[0]
                new_line = new_line + self.__line.format(key=key, value=value)
                lines[i] = new_line
                return lines
        new_line = ""
        if section != "main" and not "server" in section:
            new_line = lines[self.__ind[section][0]].split(section)[0] + "    "
        elif "server" in section:
            new_line = lines[self.__ind[section][0]].split("server")[0] + "    "
        new_line = new_line + self.__line.format(key=key, value=value)
        lines.insert(self.__ind[section][0] + 1, new_line)
        self._update_index(self.__ind[section][0])
        return lines

    def _set_main_section(self, key, value):
        return self._append_lines("main", key, value)

    def _set_event_section(self, key, value):
        if "events" not in self.__ind:
            raise SetConfigError("No events section")
        return self._append_lines("events", key, value)

    def _set_http_section(self, key, value):
        if "http" not in self.__ind:
            raise SetConfigError("No http section")
        return self._append_lines("http", key, value)

    def _set_http_server(self, key, value):
        if "http_server" not in self.__ind:
            raise SetConfigError("No http server in http section")
        return self._append_lines("http_server", key, value)

    def _set_https_server(self, key, value):
        if "https_server" not in self.__ind:
            raise SetConfigError("No https server in http section")
        return self._append_lines("https_server", key, value)

    def _set(self, key, value):
        self._init_file()
        valid, count = self._check_key(key)
        if not valid or count < 1 or count > 3:
            raise SetConfigError("Invalid value {}".format(key))
        if value == "!CPU_CORE!":
            value = rewrite_value(value)
        lines = []
        try:
            if count == 1:
                lines = self._set_main_section(key, value)
            elif count == 2 and key.split('.')[0] == "events":
                lines = self._set_event_section(key.split('.')[1], value)
            elif key.split('.')[0] == "http":
                if count == 2:
                    lines = self._set_http_section(key.split('.')[1], value)
                elif count == 3:
                    if key.split('.')[1] == "http":
                        lines = self._set_http_server(key.split('.')[2], value)
                    elif key.split('.')[1] == "https":
                        lines = self._set_https_server(key.split('.')[2], value)
                    else:
                        raise SetConfigError("Invalid value {}".format(key))
                else:
                    raise SetConfigError("Invalid value {}".format(key))
            else:
                raise SetConfigError("Invalid value {}".format(key))
        except SetConfigError as err:
            raise err
        self._set_lines(lines)
        return 0
    
    def _get(self, key, _):
        pass
    
    def _backup(self, config, _):
        return str(config)

    @staticmethod
    def check(config1, config2):
        return True

def rewrite_value(value):
    command = ["grep", "processor", "/proc/cpuinfo"]
    output = subprocess.run(command, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if output.returncode != 0:
        raise SetConfigError("Failed to get cpu number")
    return output.stdout.decode().count("\n")


