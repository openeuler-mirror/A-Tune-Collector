#!/bin/sh
# Copyright (c) 2020 Huawei Technologies Co., Ltd.
# A-Tune is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Create: 2020-03-02

declare -A default=(["UserTasksMax"]="4096")

keywords=$(echo "$@" | awk '{print $1}')
value=$(echo "$@" | awk '{print $2}')
result=$(cat /etc/systemd/logind.conf | grep -w "^$keywords" | awk -F "=" '{print$2}')
if [[ "$result" == "" ]]; then
  echo "$keywords ${default["$keywords"]}"
else
  echo "$keywords $result"
fi
