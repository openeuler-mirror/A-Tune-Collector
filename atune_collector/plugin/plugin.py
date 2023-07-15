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
The plugin for monitor and configurator.
"""
import inspect
import logging
import threading
import time

from .configurator.common import Configurator

from .monitor.common import Monitor

LOGGER = logging.getLogger(__name__)


class ThreadedCall(threading.Thread):
    """class for function threaded calling"""

    def __init__(self, func, args=()):
        super(ThreadedCall, self).__init__()
        self.func = func
        self.args = args
        self.result = None

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        """start a new thread"""
        threading.Thread.join(self)
        try:
            return self.result
        except Exception as err:
            return err


class MPI:
    """The monitor plugin"""

    def __init__(self):
        """
        Initialize the monitor plugin class,
        including creating monitor instance.

        :param: None
        :returns: None
        :raises: None
        """
        self._all_mpi = []
        all_modules = []
        all_purposes = []
        for sub_class in Monitor.__subclasses__():
            self._all_mpi.append(sub_class())
            all_modules.append(sub_class.module())
            all_purposes.append(sub_class.purpose())
        self.get_monitors.__func__.__doc__ = self.get_monitors.__func__.__doc__ % (
            set(all_modules), set(all_purposes))

    def get_monitors(self, module=None, purpose=None):
        """
        Get monitor list of 'module' for 'purpose'.

        :param module(optional): %s
        :param purpose(optional): %s
        :returns list: Success, all found monitors or null
        :raises: None
        """
        mpis = []
        for subclass_ins in self._all_mpi:
            if (module is not None) and (subclass_ins.module() != module):
                continue
            if (purpose is not None) and (subclass_ins.purpose() != purpose):
                continue
            mpis.append(subclass_ins)
        return mpis

    def get_monitor(self, module, purpose):
        """
        Get monitor instance of 'module' for 'purpose'.

        :param module & purpose: %s
        :returns mpi: Success, the found monitor
        :raises LookupError: Fail, find monitor error
        """
        mpis = self.get_monitors(module, purpose)
        if len(mpis) != 1:
            err = LookupError("Find {} {}-{} monitors".format(
                len(mpis), module, purpose))
            LOGGER.error("MPI.%s: %s", inspect.stack()[0][3], str(err))
            raise err
        return mpis[0]

    def get_monitor_pooled(self, module, purpose, pool):
        """
        Get monitor of 'module' for 'purpose' in pool.

        :param module & purpose: see get_monitor()
        :param pool: monitors pool for looking up
        :returns mpi: Success, the found monitor
        :raises LookupError: Fail, find monitor error
        """
        mpis = []
        for subclass_ins in pool:
            if (module is not None) and (subclass_ins.module() != module):
                continue
            if (purpose is not None) and (subclass_ins.purpose() != purpose):
                continue
            mpis.append(subclass_ins)

        if len(mpis) != 1:
            err = LookupError("Find {} {}-{} monitors in pool".format(
                len(mpis), module, purpose))
            LOGGER.error("MPI.%s: %s", inspect.stack()[0][3], str(err))
            raise err
        return mpis[0]

    def get_monitors_data(self, monitors, pool=None):
        """
        Get given monitors report data in one.

        :param monitors: ((module, purpose, options), ...)
                options is for report(para)
        :param pool: monitors pool for looking up
        :returns list: Success, decoded data strings of all given monitors
        :returns Exceptions: Success, formatted info
        :raises LookupError: Fail, find monitor error
        """
        mts = []
        for m_mpi in monitors:
            if pool is None:
                mon = self.get_monitor(m_mpi[0], m_mpi[1])
            else:
                mon = self.get_monitor_pooled(m_mpi[0], m_mpi[1], pool)
            m_thread = ThreadedCall(mon.report, ("data", None, m_mpi[2]))
            mts.append(m_thread)
            m_thread.start()

        rets = []
        for m_thread in mts:
            start = time.time()
            ret = m_thread.get_result()
            end = time.time()
            LOGGER.debug("MPI.%s: Cost %s s to call %s, ret=%s", inspect.stack()[0][3],
                         end - start, m_thread.func, str(ret))
            if isinstance(ret, Exception):
                return ret
            rets += ret
        return rets


class CPI:
    """The configurator plugin"""

    def __init__(self):
        """
        Initialize the configurator plugin class,
        including creating configurator instance.

        :param: None
        :returns: None
        :raises: None
        """
        self._all_cpi = []
        all_modules = []
        all_submods = []
        for sub_class in Configurator.__subclasses__():
            self._all_cpi.append(sub_class())
            all_modules.append(sub_class.module())
            all_submods.append(sub_class.submod())
        self.get_configurators.__func__.__doc__ = self.get_configurators.__func__.__doc__ % (
            set(all_modules), set(all_submods))

    def get_configurators(self, module=None, submod=None):
        """
        Get configurator list of 'module'.'submod'.

        :param module(optional): %s
        :param submod(optional): %s
        :returns list: Success, all found configurators or null
        :raises: None
        """
        cpis = []
        for subclass_ins in self._all_cpi:
            if (module is not None) and (subclass_ins.module() != module):
                continue
            if (submod is not None) and (subclass_ins.submod() != submod):
                continue
            cpis.append(subclass_ins)
        return cpis

    def get_configurator(self, module, submod):
        """
        Get configurator of 'module'.'submod'.

        :param module & submod: %s
        :returns cpi: Success, the found configurator
        :raises LookupError: Fail, find configurator error
        """
        cpis = self.get_configurators(module, submod)
        if len(cpis) != 1:
            err = LookupError("Find {} {}-{} configurators".format(
                len(cpis), module, submod))
            LOGGER.error("CPI.%s: %s", inspect.stack()[0][3], str(err))
            raise err
        return cpis[0]
