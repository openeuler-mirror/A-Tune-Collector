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
# Create: 2020-11-13

"""
The main function for collecting data.
"""
import argparse
import json
import os
import time
import csv

from plugin.plugin import MPI
from werkzeug.utils import secure_filename


class Collector:
    """class for Collector"""

    def __init__(self, data):
        self.data = data
        self.field_name = []
        self.support_multi_block = ['storage']
        self.support_multi_nic = ['network', 'network-err']
        self.support_multi_app = ['process']

    def parse_json(self):
        """parse json data"""
        monitors = []
        for item in self.data["collection_items"]:
            if item["name"] in self.support_multi_app and ('application' not in self.data or
                                                                self.data["application"] == ""):
                continue
            if item["name"] in self.support_multi_app:
                applications = self.data["application"].split(',')
                parameters = ["--interval=%s --app=%s;" %(self.data["interval"], self.data["application"])]
                for application in applications:    
                    for metric in item["metrics"]:
                        self.field_name.append(
                            "%s.%s.%s#%s" % (item["module"], item["purpose"], metric, application))
                        parameters.append("--fields=%s" % metric)
            else:
                parameters = ["--interval=%s;" % self.data["interval"]]
                for metric in item["metrics"]:
                    nics = self.data["network"].split(',')
                    blocks = self.data["block"].split(',')
                    
                    if item["name"] in self.support_multi_nic and len(nics) > 1:
                        for net in nics:
                            self.field_name.append(
                                "%s.%s.%s#%s" % (item["module"], item["purpose"], metric, net))
                    elif item["name"] in self.support_multi_block and len(blocks) > 1:
                        for block in blocks:
                            self.field_name.append(
                                "%s.%s.%s#%s" % (item["module"], item["purpose"], metric, block))
                    else:
                        self.field_name.append("%s.%s.%s" % (item["module"], item["purpose"], metric))
                    parameters.append("--fields=%s" % metric)
                if "threshold" in item:
                    parameters.append("--threshold=%s" % item["threshold"])

            parameters.append("--nic=%s" % self.data["network"])
            parameters.append("--device=%s" % self.data["block"])
            monitors.append([item["module"], item["purpose"], " ".join(parameters)])
        return monitors

    def collect_data(self):
        """collect data"""
        collect_num = self.data["sample_num"]
        if int(collect_num) < 1:
            os.abort("sample_num must be greater than 0")

        mpi = MPI()
        monitors = self.parse_json()
        path = self.data["output_dir"]
        if not os.path.exists(path):
            os.makedirs(path, 0o750)
        file_name = "{}-{}.csv".format(self.data.get("workload_type", "default"),
                                       int(round(time.time() * 1000)))
                                       
        print("start to collect data, csv path is %s" % os.path.join(path, file_name))
        print(" ".join(self.field_name))
        with open(os.path.join(path, file_name), "w") as csvfile:
            writer = csv.writer(csvfile)
            self.field_name.insert(0, "TimeStamp")
            writer.writerow(self.field_name)
            csvfile.flush()
            for _ in range(collect_num):
                raw_data = mpi.get_monitors_data(monitors)
                float_data = [float(num) for num in raw_data]
                str_data = [str(round(value, 3)) for value in float_data]
                print(" ".join(str_data))
                float_data.insert(0, time.strftime("%H:%M:%S"))
                # field_data.append(float_data)
                writer.writerow(float_data)
                csvfile.flush()
        print("finish to collect data, csv path is %s" % os.path.join(path, file_name))


if __name__ == "__main__":
    default_json_path = "/etc/atune_collector/collect_data.json"
    ARG_PARSER = argparse.ArgumentParser(description="input configuration file in json format")
    ARG_PARSER.add_argument('-c', '--config', metavar='json',
                            default=default_json_path, help='input json path')
    ARGS = ARG_PARSER.parse_args()
    filename=secure_filename(ARGS.config)
    with open(ARGS.config, 'r') as file:
        json_data = json.load(file)
    collector = Collector(json_data)
    try:
        collector.collect_data()
    except KeyboardInterrupt:
        print("user stop collect data")