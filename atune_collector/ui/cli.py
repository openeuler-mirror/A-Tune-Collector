#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021 Huawei Technologies Co., Ltd.
# A-Tune-Collector is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2021-1-18

"""
Create command line interface supporting data visualization in terminal for A-Tune-Collector.
"""

import curses
import sys
import os
import csv
import argparse
import json
import copy
import threading
import time
from typing import List

from log import logger

sys.path.append(os.path.dirname(__file__) + '/..')
from collect_data import Collector


KEY_RESET = ord('r')
KEY_EXIT = ord('q')
KEY_HELP = ord('h')
KEY_OPTIONS = ord('o')
KEY_ENTER = ord('e')
KEY_LEFT = curses.KEY_LEFT
KEY_RIGHT = curses.KEY_RIGHT
KEY_UP = curses.KEY_UP
KEY_DOWN = curses.KEY_DOWN

COLOR_CYAN_BLACK = 1
COLOR_YELLOW_BLACK = 2
COLOR_MAGENTA_BLACK = 3
COLOR_BLUE_BLACK = 4
COLOR_GREEN_BLACK = 5
COLOR_RED_BLACK = 6
COLOR_WHITE_BLACK = 7

MIN_TERMINAL_WIDTH = 20
MIN_TERMINAL_HEIGHT = 20


class DisplayScreen:
    """
    Class for A-Tune-Collector data visualization.
    """

    def __init__(self):
        """
        Initialize and configurate the whole screen and independent windows. 
        """
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(True)
        curses.curs_set(0)

        self.screen.clear()
        self.screen.refresh()

        curses.start_color()
        curses.init_pair(COLOR_CYAN_BLACK, curses.COLOR_CYAN,
                         curses.COLOR_BLACK)
        curses.init_pair(COLOR_YELLOW_BLACK,
                         curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(COLOR_MAGENTA_BLACK,
                         curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(COLOR_BLUE_BLACK, curses.COLOR_BLUE,
                         curses.COLOR_BLACK)
        curses.init_pair(COLOR_GREEN_BLACK,
                         curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(COLOR_RED_BLACK, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(COLOR_WHITE_BLACK,
                         curses.COLOR_WHITE, curses.COLOR_BLACK)

        self.height, self.width = self.screen.getmaxyx()
        self.key = 0
        self.modules = []

    def setup_module_position(self):
        logger.info(f"width = {self.width}, height = {self.height}")
        if self.width > 4 * self.height:
            self.cpu_width = self.width
            self.cpu_height = (self.height-1) // 2
            self.cpu_x = 0
            self.cpu_y = 0
            self.storage_width = self.width // 3
            self.storage_height = self.height // 2
            self.storage_x = 0
            self.storage_y = self.cpu_height
            self.mem_width = self.width // 3
            self.mem_height = (self.height-1) // 2
            self.mem_x = self.storage_width
            self.mem_y = self.cpu_height
            self.network_width = self.width // 3
            self.network_height = (self.height-1) // 2
            self.network_x = self.mem_x + self.mem_width
            self.network_y = self.cpu_height
        else:
            self.cpu_width = self.width
            self.cpu_height = (self.height-1) // 4
            self.cpu_x = 0
            self.cpu_y = 0
            self.storage_width = self.width
            self.storage_height = (self.height-1) // 4
            self.storage_x = 0
            self.storage_y = self.cpu_y + self.cpu_height
            self.mem_width = self.width
            self.mem_height = (self.height-1) // 4
            self.mem_x = 0
            self.mem_y = self.storage_y + self.storage_height
            self.network_width = self.width
            self.network_height = (self.height-1) // 4
            self.network_x = 0
            self.network_y = self.mem_y + self.storage_height

    def check_screen(self):
        self.errstatus = False
        if self.height < MIN_TERMINAL_HEIGHT or self.width < MIN_TERMINAL_WIDTH:
            self.errstatus = True
            errmsg = "[ERROR] Screen size is not enough!"
            notemsg = "resize your window, or press [q] to quit."
            self.screen.addstr(self.height//2, abs(self.width-len(errmsg)) //
                               2, errmsg, curses.color_pair(COLOR_RED_BLACK) | curses.A_BOLD)
            self.screen.addstr(
                self.height//2+1, abs(self.width-len(notemsg))//2, notemsg, curses.A_REVERSE)
            while self.key != KEY_EXIT:
                self.screen.refresh()
                self.height, self.width = self.screen.getmaxyx()
                if self.height >= MIN_TERMINAL_HEIGHT and self.width >= MIN_TERMINAL_WIDTH:
                    self.errstatus = False
                    break
                self.key = self.screen.getch()

    def win_init(self):
        """
        Establish new independent windows.
        Display error message if current screen size is not fitted.
        """
        self.check_screen()
        self.win_cpu = curses.newwin(18, 100, 0, 0)
        self.win_storage = curses.newwin(18, 100, 0, 100)
        self.win_mem = curses.newwin(18, 100, 18, 0)
        self.win_network = curses.newwin(18, 100, 18, 100)
        self.win_perf = curses.newwin(13, 100, 36, 0)
        self.win_system = curses.newwin(13, 100, 36, 100)
        self.win_notebar = curses.newwin(1, self.width, self.height-1, 0)

    def win_adaptive_init(self):
        """
        Establish new independent windows.
        Display error message if current screen size is not fitted.
        """
        self.check_screen()
        self.setup_module_position()
        self.win_cpu = curses.newwin(
            self.cpu_height, self.cpu_width, self.cpu_y, self.cpu_x)
        self.win_storage = curses.newwin(
            self.storage_height, self.storage_width, self.storage_y, self.storage_x)
        self.win_mem = curses.newwin(
            self.mem_height, self.mem_width, self.mem_y, self.mem_x)
        self.win_network = curses.newwin(
            self.network_height, self.network_width, self.network_y, self.network_x)
        self.win_notebar = curses.newwin(1, self.width, self.height-1, 0)

    @staticmethod
    def draw_diagram(window: curses.window, name_y: str, name_x: str,
                     height=10, width=20, begin_y=1, begin_x=1, data: list = None,
                     dmax=None, dmin=None, unit=None, unit_scale=1):
        """
        Plot diagram in a height*width window(default 10*20).

        :window: drawing window
        :name_y: y axis label string
        :name_x: x axis label string
        :height:  
        :width:  
        :begin_y: left start point height
        :begin_x: top start point width
        :data: data points
        """
        if unit is not None:
            name_y = f"{name_y} {unit}"
        win_plot = window.derwin(height, width, begin_y, begin_x)
        win_plot.attrset(curses.A_BOLD)
        # draw y axis line and label
        win_plot.addnstr(0, 0, name_y, min(width, len(name_y)))
        win_plot.vline(1, 0, curses.ACS_VLINE, height-2)
        win_plot.addch(height-1, 0, curses.ACS_LLCORNER)
        # draw x axis line and label
        win_plot.hline(height-1, 1, curses.ACS_HLINE, width-1-len(name_x))
        win_plot.addnstr(height-1, width-1-len(name_x), name_x, len(name_x))
        # draw data graph part
        data_height = height-2
        data_width = width-2-len(name_x)
        win_data = win_plot.derwin(data_height, data_width, 1, 1)
        if data is None or len(data) == 0:
            msg = "NOT COLLECTED"
            win_data.addstr(data_height//2, (data_width-len(msg))//2,
                            msg, curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
        else:
            win_data.clear()
            if dmin is None:
                dmin = min(data)
            if dmax is None:
                dmax = max(data) if max(data) != dmin else 2 * dmin + 1
            # update
            range_str1 = f"(max={round(dmax/unit_scale,1)},min={round(dmin/unit_scale,1)})"
            range_str2 = f"(max={round(dmax/unit_scale,1)})"
            if len(name_y) + len(range_str1) <= width:
                win_plot.addnstr(0, len(name_y), range_str1, width)
            elif len(name_y) + len(range_str2) <= width:
                win_plot.addnstr(0, len(name_y), range_str2, width)
            # draw at most width points
            n = min(data_width, len(data))
            data = data[-n:]
            for xaxis in range(n):
                # calculate point height
                rdata = round((data[xaxis]-dmin)/(dmax-dmin)*data_height)
                rdata = min(data_height, rdata)
                if rdata > 0:
                    win_data.vline(data_height-rdata, xaxis,
                                   curses.ACS_CKBOARD, rdata)
        win_plot.refresh()

    @staticmethod
    def draw_box(window: curses.window, title: str, attr: int = None):
        """
        Draw window border with a bold-type title at top left corner.
        Default title color is YELLOW.
        """
        if attr is None:
            attr = curses.A_BOLD | curses.color_pair(COLOR_YELLOW_BLACK)
        window.box()
        window.addnstr(0, 4, " {} ".format(title),
                       window.getmaxyx()[1]-5, attr)

    @staticmethod
    def draw_progressbar(window: curses.window, name: str, begin_y=1, begin_x=1,
                         barlen=50, info: dict = None):
        """
        Draw progress bar in a window.
        Support at most 7 data class.
        param dict info: {name: data}(data supports string in percentage number format.)
        """
        bar_height = 3
        datasum = sum(info.values())
        height, width = window.getmaxyx()
        name = name[:10]
        cgroup = iter([COLOR_CYAN_BLACK, COLOR_YELLOW_BLACK, COLOR_MAGENTA_BLACK,
                       COLOR_BLUE_BLACK, COLOR_GREEN_BLACK, COLOR_RED_BLACK, COLOR_WHITE_BLACK])
        if len(info.keys()) > 7:
            raise Exception(
                "Catch Too Much Sorts of Data to Draw Prgress Bar! (>7)")
        if (begin_y+bar_height > height) or (begin_x+len(name)+barlen > width-2):
            raise Exception("Progress Bar is out of window!")

        win_progsbar = window.derwin(3, len(name)+barlen+5, begin_y, begin_x)
        win_progsbar.addstr(0, 0, name, curses.A_BOLD)
        xptr1 = xptr2 = len(name) + 1
        for key, data in info.items():
            tlen = round(data / datasum * barlen)
            cnum = next(cgroup)
            cstr = "{}:{}  ".format(key, data)
            win_progsbar.addstr(0, xptr1, " "*tlen,
                                curses.color_pair(cnum) | curses.A_REVERSE)
            win_progsbar.addstr(
                1, xptr2, cstr, curses.A_BOLD | curses.color_pair(cnum))
            xptr1 += tlen
            xptr2 += len(cstr)

    @staticmethod
    def draw_multiline(window: curses.window, begin_y=1, begin_x=1,
                       attr: int = 0, contents: list = None):
        """
        Displays a multi-line string in left-aligned mode.
        """
        height, width = window.getmaxyx()
        if (begin_y + len(contents) >= height) or (begin_x + max([len(i) for i in contents]) >= width):
            raise Exception("Display multi-line: Content out of window!")
        for idx in range(len(contents)):
            window.addstr(begin_y+idx, begin_x, contents[idx], attr)

    def display_welcome(self):
        """
        Display logo 'COLLECTOR', application information and operation notes at the center of the screen.
        """
        logo = ""
        info = ""
        note = ""
        logo += "   _____    ___     _      _        ______    _____ _________   ___     _______  \n"
        logo += "  / ____  / ___ \  | |    | |      |  ___ |  / ____|___   ___|/ ___ \  |  ___  | \n"
        logo += " / /     / /   \ \ | |    | |      | |____  / /        | |   / /   \ \ | |___| | \n"
        logo += "| |     | |     | || |    | |      |  ____|| |         | |  | |     | ||  _   _| \n"
        logo += " \ \ ___ \ \___/ /  \ \ ___\ \ ___ | |____  \ \ ___    | |   \ \___/ / | | \  \  \n"
        logo += "  \ ____  \ ___ /    \ ____|\ ____||______|  \ ____    |_|    \ ___ /  |_|  \__\ \n"
        info += "Welcome to A-Tune-Collector terminal user interface.             \n"
        info += "It can display system status information at 6 dimensions:        \n"
        info += "CPU, memory, network, storage, hardware performance and process.   "
        note += "Press [q] to quit, [e] to enter visualization interface.           "
        win_welcome = curses.newwin(
            10, 100, max(0, (self.height-10)//2), max(0, (self.width-100)//2))
        win_welcome.addstr(0, 0, logo, curses.color_pair(
            COLOR_RED_BLACK) | curses.A_BOLD)
        win_welcome.addstr(6, 0, info, curses.color_pair(
            COLOR_BLUE_BLACK) | curses.A_BOLD)
        win_welcome.addstr(9, 0, note, curses.A_REVERSE | curses.A_BOLD)
        win_welcome.refresh()
        
    def wait_for_enter_or_exit(self):
        """
        Run in a blocked way.
        return "ENTER"
        return "EXIT"
        """
        while True:
            self.key = self.screen.getch()
            if self.key == KEY_ENTER:
                return "ENTER"
            elif self.key == KEY_EXIT:
                return "EXIT"

    def display_cpu(self, avg_data={},
                    plot_data={"ITEM1": [], "ITEM2": []}):
        """
        Display CPU usage information.
        info: usr, nice, sys, iowait, irq, soft, steal, guest, util, cutil
        Need refresh method in the end.
        """
        self.draw_box(self.win_cpu, "CPU")
        if "CPU" not in self.modules:
            height, width = self.win_cpu.getmaxyx()
            info = "NOT COLLECTED"
            self.win_cpu.addstr(height//2-1, (width-len(info))//2-1, info,
                                curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
            self.win_cpu.refresh()
            return None
        item = list(plot_data.keys())
        # draw first cpu diagram, start point position (2,2), width height (10,30)
        self.draw_diagram(
            self.win_cpu, item[0], "Time", 10, 30, 2, 2, plot_data[item[0]], dmax=100, dmin=0)
        # draw second cpu diagram, start point position (2,40), width height (10,30)
        self.draw_diagram(
            self.win_cpu, item[1], "Time", 10, 30, 2, 40, plot_data[item[1]], dmax=100, dmin=0)
        # draw top right digits show
        self.draw_multiline(self.win_cpu, 4, 75, curses.A_BOLD | curses.color_pair(COLOR_MAGENTA_BLACK),
                            contents=["iowait", " ", "guest", " ", "cutil"])
        self.draw_multiline(self.win_cpu, 4, 85, curses.A_BOLD | curses.color_pair(COLOR_BLUE_BLACK),
                            contents=["{} %".format(avg_data["iowait"] if "iowait" in avg_data else "NC"), " ",
                                      "{} %".format(
                                avg_data["guest"] if "guest" in avg_data else "NC"), " ",
            "{} %".format(avg_data["cutil"] if "cutil" in avg_data else "NC")])
        # draw bottom cpu usage proportion bar
        if ("usr", "nice", "sys", "irq", "soft", "steal", "util" in avg_data)[-1]:
            self.draw_progressbar(self.win_cpu, "Usage", 15, 2, 80,
                                  {"us": avg_data["usr"], "ni": avg_data["nice"], "sy": avg_data["sys"],
                                   "ir": avg_data["irq"], "so": avg_data["soft"], "st": avg_data["steal"],
                                   "id": round(100-avg_data["util"], 1)})
        else:
            self.win_cpu.addstr(15, 5, "Progress bar NOT available (lack of data)",
                                curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
        self.win_cpu.refresh()

    def display_cpu_plot(self, plot_name: str, plot_data: List[float] = []):
        """
        Display CPU utility curve plot.
        info: usr, nice, sys, iowait, irq, soft, steal, guest, util, cutil
        Need refresh method in the end.
        """
        self.draw_box(self.win_cpu, "CPU")
        height, width = self.win_cpu.getmaxyx()
        if "CPU" not in self.modules:
            info = "NOT COLLECTED"
            self.win_cpu.addstr(height//2-1, (width-len(info))//2-1, info,
                                curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
            self.win_cpu.refresh()
            return None
        self.draw_diagram(self.win_cpu, plot_name, "Time", height-2,
                          width-2, 1, 1, plot_data, dmax=100, dmin=0)
        self.win_cpu.refresh()
        
    def display_mem(self, avg_data={},
                    plot_data: dict = {"ITEM1": [], "ITEM2": []}):
        """
        Display memory usage information.
        Need refresh method in the end.
        """
        self.draw_box(self.win_mem, "Memory")
        if "MEM" not in self.modules:
            height, width = self.win_mem.getmaxyx()
            info = "NOT COLLECTED"
            self.win_mem.addstr(height//2-1, (width-len(info))//2-1, info,
                                curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
            self.win_mem.refresh()
            return None
        item = list(plot_data.keys())
        rdata = {"total": "MemTotal",
                 "used": "NC",
                 "free": "MemFree",
                 "ava": "MemAvailable",
                 "swapt": "SwapTotal",
                 "swapu": "util.swap",
                 "dirty": "Dirty",
                 "util": "Total_Util"}
        for key, val in rdata.items():
            if val in avg_data:
                rdata[key] = round((avg_data[val] / 1024)
                                   if key != "util" else avg_data[val], 1)
                if key == "free" and rdata["total"] != "NC":
                    rdata["used"] = round(rdata["total"] - rdata["free"], 1)
            else:
                rdata[key] = "NC"

        self.draw_diagram(self.win_mem, item[0], "Time",
                          begin_y=3, begin_x=2, data=plot_data[item[0]])
        self.draw_diagram(self.win_mem, item[1], "Time",
                          begin_y=3, begin_x=30, data=plot_data[item[1]])
        if rdata["used"] != "NC":
            self.draw_progressbar(self.win_mem, "Usage", 2, 55, 35,
                                  {"used": rdata["used"], "free": rdata["free"]})
        else:
            self.win_mem.addstr(2, 55, "Progress bar NOT available (lack of data)",
                                curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
        if rdata["util"] != "NC":
            self.draw_progressbar(self.win_mem, "BWUti", 5, 55, 35,
                                  {"util": rdata["util"], "free": 100-rdata["util"]})
        else:
            self.win_mem.addstr(5, 55, "Progress bar NOT available (lack of data)",
                                curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
        self.draw_multiline(self.win_mem, 8, 60, curses.A_BOLD | curses.color_pair(COLOR_MAGENTA_BLACK),
                            contents=["Total", " ", "Available", " ",
                                      "Swap", " ", "Dirty"])
        self.draw_multiline(self.win_mem, 8, 75, curses.A_BOLD | curses.color_pair(COLOR_BLUE_BLACK),
                            contents=["{} MB".format(rdata["total"]), " ", "{} MB".format(rdata["ava"]), " ",
                                      "{} / {} MB".format(rdata["swapu"], rdata["swapt"]), " ", "{} MB".format(rdata["dirty"])])
        self.win_mem.refresh()

    def display_mem_plot(self, avg_data,
                         plot_name: str, plot_data: List[float] = []):
        """
        Display memory usage information.
        Need refresh method in the end.
        """
        self.draw_box(self.win_mem, "Memory")
        height, width = self.win_mem.getmaxyx()
        if "MEM" not in self.modules:
            info = "NOT COLLECTED"
            self.win_mem.addstr(height//2-1, (width-len(info))//2-1, info,
                                curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
            self.win_mem.refresh()
            return None
        rdata = {"total": "MemTotal",
                 "used": "NC",
                 "free": "MemFree",
                 "ava": "MemAvailable",
                 "swapt": "SwapTotal",
                 "swapu": "util.swap",
                 "dirty": "Dirty",
                 "util": "Total_Util"}
        logger.info("avg_data")
        logger.info(avg_data)
        for key, val in rdata.items():
            if val in avg_data:
                rdata[key] = round((avg_data[val] / 1024)
                                   if key != "util" else avg_data[val], 1)
                if key == "free" and rdata["total"] != "NC":
                    rdata["used"] = round(rdata["total"] - rdata["free"], 1)
            else:
                rdata[key] = "NC"

        self.draw_diagram(self.win_mem, plot_name, "Time", height-2, width-2, 1, 1, data=plot_data,
                          dmax=avg_data['MemTotal'], dmin=0, unit='MB', unit_scale=1024)
        self.win_mem.refresh()

    def display_network(self, dev=None, avg_data={},
                        plot_data: dict = {"ITEM1": [], "ITEM2": []}):
        """
        Display network information which supports multiple NIC devices.
        param dict avg_data: {item:[datalist]}
        Need refresh method in the end.
        """
        self.draw_box(self.win_network, "Network")
        height, width = self.win_network.getmaxyx()
        if "NET" not in self.modules or dev is None or len(dev) == 0:
            info = "NOT COLLECTED"
            self.win_network.addstr(height//2-1, (width-len(info))//2-1, info,
                                    curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
            self.win_network.refresh()
            return None
        item = list(plot_data.keys())
        rdata = {
            "rxkBs": [],
            "rxpcks": [],
            "txkBs": [],
            "txpcks": [],
            "ifutil": [],
            "errs": [],
            "util": []
        }
        for keyr in rdata.keys():
            for keya in avg_data.keys():
                if keyr in keya:
                    if keyr in ("rxkBs", "txkBs"):
                        rdata[keyr].append(round(avg_data[keya] / 1024, 1))
                    else:
                        rdata[keyr].append(round(avg_data[keya], 1))
            nclen = len(dev) - len(rdata[keyr])
            if nclen > 0:
                for _ in range(nclen):
                    rdata[keyr].append("NC")
        info = ["Rx: {} MB/s", "Rx: {} packages/s",
                "Tx: {} MB/s", "Tx: {} packages/s",
                "Utility: {} %", "Err: {} packages/s",
                "ErrUtil: {}"]
        if len(dev) == 1:
            win_nic1 = self.win_network.derwin(height-2, width-2, 1, 1)
            self.draw_box(win_nic1, "NIC: {}".format(dev[0]))
            self.draw_multiline(win_nic1, 5, 4, curses.A_BOLD,
                                contents=[info[i].format(rdata[key][0]) for i, key in enumerate(rdata.keys())])
            self.draw_diagram(
                win_nic1, item[0], "Time", 10, 20, 2, 35, plot_data[item[0]])
            self.draw_diagram(
                win_nic1, item[1], "Time", 10, 20, 2, 65, plot_data[item[1]])
        elif len(dev) >= 2:
            win_nic1 = self.win_network.derwin(height-2, width//2-1, 1, 1)
            win_nic2 = self.win_network.derwin(
                height-2, width//2-1, 1, width//2)
            self.draw_box(win_nic1, "NIC1: {}".format(dev[0]))
            self.draw_box(win_nic2, "NIC2: {}".format(dev[1]))
            self.draw_multiline(win_nic1, 5, 1, curses.A_BOLD,
                                contents=[info[i].format(rdata[key][0]) for i, key in enumerate(rdata.keys())])
            self.draw_multiline(win_nic2, 5, 1, curses.A_BOLD,
                                contents=[info[i].format(rdata[key][1]) for i, key in enumerate(rdata.keys())])
            self.draw_diagram(
                win_nic1, item[0], "Time", 10, 18, 2, 24, plot_data[item[0]])
            self.draw_diagram(
                win_nic2, item[1], "Time", 10, 18, 2, 24, plot_data[item[1]])
        self.win_network.refresh()

    def display_network_plot(self, dev, plot_name: str, plot_data: List[float] = []):
        """
        Display network information which supports multiple NIC devices.
        param dict avg_data: {item:[datalist]}
        Need refresh method in the end.
        """
        self.draw_box(self.win_network, f"Network: {dev[0]}")
        height, width = self.win_network.getmaxyx()
        if "NET" not in self.modules or dev is None or len(dev) == 0:
            info = "NOT COLLECTED"
            self.win_network.addstr(height//2-1, (width-len(info))//2-1, info,
                                    curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
            self.win_network.refresh()
            return None
        label = plot_name
        if label == 'rxkBs':
            label = 'rx kB/s'
        self.draw_diagram(self.win_network, label, "Time", height-2, width-2, 1, 1, plot_data, dmin=0)
        self.win_network.refresh()

    def display_storage(self, dev=None, avg_data={},
                        plot_data: dict = {"ITEM1": [], "ITEM2": []}):
        """
        Display storage information collected by iostat
        param list dev
        param list rs, ws, rMBs, wMBs, ... , util, aqusz
        Need refresh method in the end.
        """
        self.draw_box(self.win_storage, "Storage")
        height, width = self.win_storage.getmaxyx()
        if ("STORAGE" not in self.modules) or (dev is None) or (len(dev) == 0):
            info = "NOT COLLECTED"
            self.win_storage.addstr(height//2-1, (width-len(info))//2-1, info,
                                    curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
            self.win_storage.refresh()
            return None
        item = list(plot_data.keys())
        rdata = {
            "rs": [],
            "ws": [],
            "rMBs": [],
            "wMBs": [],
            "rrqm": [],
            "wrqm": [],
            "rareq-sz": [],
            "wareq-sz": [],
            "r_await": [],
            "w_await": [],
            "aqu-sz": [],
            "util": []
        }
        for keyr in rdata.keys():
            for keya in avg_data.keys():
                if keyr in keya:
                    rdata[keyr].append(round(avg_data[keya], 1))
            nclen = len(dev) - len(rdata[keyr])
            if nclen > 0:
                for _ in range(nclen):
                    rdata[keyr].append("NC")
        info = ["Read Request: {} /s", "Write Request: {} /s",
                "Read Speed: {} MB/s", "Write Speed: {} MB/s",
                "Read Req Merged: {} /s", "Write Req Merged: {} /s",
                "Read Avg Size: {} KB", "Write Avg Size: {} KB",
                "Read Avg Wait: {} ms", "Write Avg Wait: {} ms",
                "Avg Queue Size: {}", "Utility: {} %"]
        if len(dev) == 1:
            win_disk1 = self.win_storage.derwin(height-2, width-2, 1, 1)
            self.draw_box(win_disk1, "Disk: {}".format(dev[0]))
            self.draw_multiline(win_disk1, 2, 2, curses.A_BOLD,
                                contents=[info[i].format(rdata[key][0]) for i, key in enumerate(rdata.keys())])
            self.draw_diagram(
                win_disk1, item[0], "Time", 10, 20, 2, 35, plot_data[item[0]], dmax=100, dmin=0)
            self.draw_diagram(
                win_disk1, item[1], "Time", 10, 20, 2, 65, plot_data[item[1]], dmin=0)
        elif len(dev) >= 2:
            win_disk1 = self.win_storage.derwin(height-2, width//2-1, 1, 1)
            win_disk2 = self.win_storage.derwin(
                height-2, width//2-1, 1, width//2)
            self.draw_box(win_disk1, "Disk1: {}".format(dev[0]))
            self.draw_box(win_disk2, "Disk2: {}".format(dev[1]))
            self.draw_multiline(win_disk1, 2, 1, curses.A_BOLD,
                                contents=[info[i].format(rdata[key][0]) for i, key in enumerate(rdata.keys())])
            self.draw_multiline(win_disk2, 2, 1, curses.A_BOLD,
                                contents=[info[i].format(rdata[i][1]) for i, key in enumerate(rdata.keys())])
            self.draw_diagram(
                win_disk1, item[0], "Time", 8, 18, 2, 24, plot_data[item[0]], dmax=100, dmin=0)
            self.draw_diagram(
                win_disk2, item[1], "Time", 8, 18, 2, 24, plot_data[item[1]], dmin=0)
        self.win_storage.refresh()

    def display_storage_plot(self, dev: str, plot_name: str, plot_data: List[float] = []):
        """
        Display storage information collected by iostat
        param list dev
        param list rs, ws, rMBs, wMBs, ... , util, aqusz
        Need refresh method in the end.
        """
        self.draw_box(self.win_storage, f"Storage: {dev[0]}")
        height, width = self.win_storage.getmaxyx()
        if ("STORAGE" not in self.modules) or (dev is None) or (len(dev) == 0):
            info = "NOT COLLECTED"
            self.win_storage.addstr(height//2-1, (width-len(info))//2-1, info, curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
            self.win_storage.refresh()
            return None
        self.draw_diagram(self.win_storage, plot_name, "Time", height-2, width-2, 1, 1, plot_data, dmin=0)
        self.win_storage.refresh()

    def display_perf(self, avg_data={},
                     plot_data: dict = {"ITEM1": [], "ITEM2": []}):
        """
        param: IPC, CACHE-MISS_RATIO, MPKI, ITLB-LOAD-MISS-RATIO, DTLB-LOAD-MISS-RATIO, SBPI, SBPC
        Need refresh method in the end.
        """
        self.draw_box(self.win_perf, "Hardware Performance")
        height, width = self.win_perf.getmaxyx()
        if "PERF" not in self.modules:
            info = "NOT COLLECTED"
            self.win_perf.addstr(height//2-1, (width-len(info))//2-1, info,
                                 curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
            self.win_perf.refresh()
            return None
        item = list(plot_data.keys())
        rdata = {
            "ipc": "IPC",
            "cmr": "CACHE-MISS-RATIO",
            "mpki": "MPKI",
            "itlbmr": "ITLB-LOAD-MISS-RATIO",
            "dtlbmr": "DTLB-LOAD-MISS-RATIO",
            "sbpi": "SBPI",
            "sbpc": "SBPC",
        }
        for key, val in rdata.items():
            if val in avg_data:
                rdata[key] = avg_data[val]
            else:
                rdata[key] = "NC"
        self.draw_multiline(self.win_perf, 3, 2, curses.A_BOLD,
                            contents=["IPC: {}".format(rdata["ipc"]),
                                      "CMR: {} %".format(rdata["cmr"]),
                                      "MPKI: {}".format(rdata["mpki"]),
                                      "ITLBLMR: {} %".format(
                                rdata["itlbmr"]),
                                "DTLBLMR: {} %".format(
                                rdata["dtlbmr"]),
                                "SBPI: {}".format(rdata["sbpi"]),
                                "SBPC: {}".format(rdata["sbpc"])])

        self.draw_diagram(
            self.win_perf, item[0], "Time", 8, 30, 2, 20, plot_data[item[0]])
        self.draw_diagram(
            self.win_perf, item[1], "Time", 8, 30, 2, 60, plot_data[item[1]])
        self.win_perf.refresh()

    def display_system(self, avg_data={},
                       plot_data: dict = {"ITEM1": [], "ITEM2": []}):
        """
        Display system process and file handle information.
        Need refresh method in the end.
        """
        self.draw_box(self.win_system, "System")
        height, width = self.win_system.getmaxyx()
        if "SYS" not in self.modules:
            info = "NOT COLLECTED"
            self.win_system.addstr(height//2-1, (width-len(info))//2-1, info,
                                   curses.A_BOLD | curses.color_pair(COLOR_RED_BLACK))
            self.win_system.refresh()
            return None
        item = list(plot_data.keys())
        rdata = {
            "procs": "procs",
            "cswchs": "cswchs",
            "runqsz": "runq-sz",
            "plistsz": "plist-sz",
            "ldavg1": "ldavg-1",
            "ldavg5": "ldavg-5",
            "fdutil": "fd-util",
        }
        for key, val in rdata.items():
            if val in avg_data:
                rdata[key] = round(avg_data[val], 1)
            else:
                rdata[key] = "NC"
        self.draw_multiline(self.win_system, 2, 2, curses.A_BOLD,
                            contents=[
                                "New Process: {} proc/s".format(
                                    rdata["procs"]),
                                "Context Switch: {} sw/s".format(
                                    rdata["cswchs"])
                            ])
        self.win_system.hline(4, 2, curses.ACS_HLINE, 30)
        self.draw_multiline(self.win_system, 5, 2, curses.A_BOLD,
                            contents=[
                                "Running Queue Size: {}".format(
                                    rdata["runqsz"]),
                                "Process List Size: {}".format(
                                    rdata["plistsz"]),
                                "Last 1-min Load Average: {}".format(
                                    rdata["ldavg1"]),
                                "Last 5-min Load Average: {}".format(
                                    rdata["ldavg5"])
                            ])
        self.win_system.hline(9, 2, curses.ACS_HLINE, 30)
        self.draw_multiline(self.win_system, 10, 2, curses.A_BOLD,
                            contents=["File Handle Utility: {} %".format(rdata["fdutil"])])
        item = list(plot_data.keys())
        self.draw_diagram(
            self.win_system, item[0], "Time", 8, 20, 2, 35, plot_data[item[0]])
        self.draw_diagram(
            self.win_system, item[1], "Time", 8, 20, 2, 65, plot_data[item[1]])
        self.win_system.refresh()

    def display_notebar(self):
        """
        Need refresh method in the end.
        """
        notebarstr = "[q]: quit [h]: help [o]: options, any other key to refresh"
        self.win_notebar.addstr(
            0, 0, notebarstr + " " * (self.width - len(notebarstr) - 1), curses.A_REVERSE)
        self.win_notebar.refresh()

    def display_from_file(self, csvfile: str = None, jsonfile: str = None, use_collector=False):
        """
        Display welcome page, data, progress bar and diagrams in the whole monitor screen.
        """
        self.win_init()
        try:
            if not self.errstatus:
                json_data = json.load(jsonfile)
                logger.info('json_data')
                logger.info(json_data)
                interval = json_data["interval"]
                nic = json_data["network"].split(",")
                block = json_data["block"].split(",")

                if use_collector:
                    collector = Collector(json_data)
                    logger.info('collector.field_name')
                    logger.info(collector.field_name)
                    fields = list(collector.field_name)
                    csv_data = []
                else:
                    csv_reader = csv.DictReader(csvfile)
                    logger.info('csv_reader.fieldnames')
                    logger.info(csv_reader.fieldnames)
                    fields = csv_reader.fieldnames
                    csv_data = [row for row in csv_reader]
                avg_data = {
                    "CPU": {},
                    "STORAGE": {},
                    "NET": {},
                    "MEM": {},
                    "PERF": {},
                    "SYS": {}
                }
                # field_data = copy.deepcopy(avg_data)

                # for key in fields:
                #     item = key.split('.')
                #     if len(item) > 3:
                #         item[-2] = item[-2] + "." + item[-1]
                #         item.pop()
                #     module, metric = item[0], item[-1]
                #     self.modules.append(module)
                #     field_data[module][metric] = [float(row[key]) for row in csv_data]
                #     avg_data[module][metric] = round(sum(field_data[module][metric]) / len(field_data[module][metric]), 2)
                # del csv_data
                # self.modules = sorted(list(set(self.modules)), key=self.modules.index)
                self.display_welcome()
                if self.wait_for_enter_or_exit() == "ENTER":
                    listening = True

                    def listen_user_input():
                        while listening and self.key != KEY_EXIT:
                            self.key = self.screen.getch()
                    x = threading.Thread(target=listen_user_input, args=())
                    x.start()
                    while self.key != KEY_EXIT:
                        # update field_data
                        self.modules = []
                        field_data = copy.deepcopy(avg_data)
                        if use_collector:
                            data = collector.collect_data()
                            csv_data.append(data)
                            for index, key in enumerate(fields):
                                item = key.split('.')
                                if len(item) > 3:
                                    item[-2] = item[-2] + "." + item[-1]
                                    item.pop()
                                module, metric = item[0], item[-1]
                                self.modules.append(module)
                                field_data[module][metric] = [
                                    float(row[index]) for row in csv_data]
                                avg_data[module][metric] = sum(
                                    field_data[module][metric]) / len(field_data[module][metric])
                                avg_data[module][metric] = round(
                                    avg_data[module][metric], 2)
                        else:
                            for key in fields:
                                item = key.split('.')
                                if len(item) > 3:
                                    item[-2] = item[-2] + "." + item[-1]
                                    item.pop()
                                module, metric = item[0], item[-1]
                                self.modules.append(module)
                                field_data[module][metric] = [
                                    float(row[key]) for row in csv_data]
                                avg_data[module][metric] = round(
                                    sum(field_data[module][metric]) / len(field_data[module][metric]), 2)
                        self.modules = sorted(
                            list(set(self.modules)), key=self.modules.index)

                        # update screen
                        self.height, self.width = self.screen.getmaxyx()
                        self.display_notebar()
                        logger.info("avg_data")
                        logger.info(avg_data["CPU"])
                        logger.info("field_data")
                        logger.info(field_data["CPU"])
                        self.display_cpu(avg_data["CPU"], plot_data={"user %": field_data["CPU"]["usr"],
                                                                     "util %": field_data["CPU"]["util"]})
                        self.display_storage(block, avg_data["STORAGE"], plot_data={"util %": field_data["STORAGE"]["util"],
                                                                                    "ws": field_data["STORAGE"]["ws"]})
                        self.display_network(nic, avg_data["NET"], plot_data={"ifutil": field_data["NET"]["ifutil"],
                                                                              "rxkBs": field_data["NET"]["rxkBs"]})
                        self.display_mem(avg_data["MEM"], plot_data={"Free": field_data["MEM"]["MemFree"],
                                                                     "BWUtil": field_data["MEM"]["Total_Util"]})
                        # self.display_perf(avg_data["PERF"], plot_data={"IPC": field_data["PERF"]["IPC"],
                        #                                                "CMR": field_data["PERF"]["CACHE-MISS-RATIO"]})
                        # self.display_system(avg_data["SYS"], plot_data={"FD Util %": field_data["SYS"]["fd-util"],
                        #                                                 "ldavg-1min": field_data["SYS"]["ldavg-1"]})
                        self.screen.refresh()
                        time.sleep(interval)
                    x.join()
        except Exception as err:
            raise err
        finally:
            self.screen.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

    def display_plot(self, jsonfile: str=None):
        """
        Display welcome page, data, progress bar and diagrams in the whole monitor screen.
        """
        self.win_adaptive_init()
        try:
            if not self.errstatus:
                json_data = json.load(jsonfile)
                logger.info('json_data')
                logger.info(json_data)
                interval = json_data["interval"]
                nic = json_data["network"].split(",")
                block = json_data["block"].split(",")

                collector = Collector(json_data)
                logger.info('collector.field_name')
                logger.info(collector.field_name)
                fields = list(collector.field_name)
                csv_data = []

                avg_data = {
                    "CPU": {},
                    "STORAGE": {},
                    "NET": {},
                    "MEM": {},
                    "PERF": {},
                    "SYS": {}
                }

                listening = True
                def listen_user_input():
                    while listening and self.key != KEY_EXIT:
                        self.key = self.screen.getch()
                x = threading.Thread(target=listen_user_input, args=())
                x.start()
                while self.key != KEY_EXIT:
                    # update field_data
                    self.modules = []
                    field_data = copy.deepcopy(avg_data)
                    data = collector.collect_data()
                    csv_data.append(data)
                    for index, key in enumerate(fields):
                        item = key.split('.')
                        if len(item) > 3:
                            item[-2] = item[-2] + "." + item[-1]
                            item.pop()
                        module, metric = item[0], item[-1]
                        self.modules.append(module)
                        field_data[module][metric] = [float(row[index]) for row in csv_data]
                        avg_data[module][metric] = sum(field_data[module][metric]) / len(field_data[module][metric])
                        avg_data[module][metric] = round(avg_data[module][metric], 2)
                    self.modules = sorted(list(set(self.modules)), key=self.modules.index)

                    # update screen
                    height, width = self.screen.getmaxyx()
                    # TODO: update window if terminal size is changed
                    # if height != self.height or width != self.width:
                    #     self.height, self.width = height, width
                    #     self.win_init()
                    
                    self.display_notebar()
                    self.display_cpu_plot("util %", field_data["CPU"]["util"])
                    self.display_storage_plot(block, "ws", field_data["STORAGE"]["ws"])
                    self.display_network_plot(nic, "rxkBs", field_data["NET"]["rxkBs"])
                    self.display_mem_plot(avg_data['MEM'], "Free", field_data["MEM"]["MemFree"])
                    self.screen.refresh()
                    time.sleep(interval)
        except Exception as err:
            raise err
        finally:
            self.screen.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file',
                        # default="./example/test.csv",
                        default="",
                        help="collected csv data file path")
    parser.add_argument('-c', '--config',
                        default="/etc/atune_collector/collect_data.json",
                        help="collector configuration json file")
    parser.add_argument('-p', '--plot',
                        action='store_true', 
                        default=False, 
                        help="collector use plot mode")
    args = parser.parse_args()
    if args.plot:
        with open(args.config, 'r') as jsonfile:
            scr = DisplayScreen()
            scr.display_plot(jsonfile=jsonfile)
    elif args.file:
        with open(args.file, 'r') as csvfile, open(args.config, 'r') as jsonfile:
            scr = DisplayScreen()
            scr.display_from_file(csvfile=csvfile, jsonfile=jsonfile)
    else:
        with open(args.config, 'r') as jsonfile:
            scr = DisplayScreen()
            scr.display_from_file(jsonfile=jsonfile, use_collector=True)
