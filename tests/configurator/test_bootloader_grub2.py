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
Test case.
"""

from atune_collector.plugin.configurator.bootloader.grub2 import Grub2
from atune_collector.plugin.configurator.exceptions import GetConfigError


class TestBootloaderCmdline:
    """ test bootloader grub2"""
    user = "UT"

    def test_get_bootloader_grub2(self):
        """test get bootloader grub2"""
        try:
            grub2 = Grub2(self.user)
            grub2.get("bootloader")
            assert False
        except GetConfigError:
            assert True
