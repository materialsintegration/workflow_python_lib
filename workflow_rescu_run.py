#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
実行中のランのうち、終了（TorqueのJob終了が行われているもの）を対象に、
apdbサーバーでジョブ終了していて、GPDB登録が行われていないものを登録を行うコマンドを発行する。
'''

import requests
import time
import subprocess

headers={'Authorization': 'Bearer 13bedfd69583faa62be240fcbcd0c0c0b542bc92e1352070f150f8a309f441ed',
 'Content-Type': 'application/json'}

session=requests.Session()
ret=session.get("https://dev-u-tokyo.mintsys.jp:50443/workflow-api/v2/runs", headers=headers) 

runlist = ret.json()["runs"]

running = []
# 実行中のランIDを取得する
for item in runlist:
    if item["status"] == "running":
        running.append(item["run_id"].split("/")[-1])

# 実行中のランIDの詳細を取得し、GPDB URLを取得する。
gpdb_url = []
body = {"status":"canceled"}
for item in running:
    ret = session.get("https://dev-u-tokyo.mintsys.jp:50443/workflow-api/v2/runs/%s"%item, headers=headers) 

    rundetail = ret.json()
    if ("gpdb_url" in rundetail) is True:
        gpdb_url.append(rundetail["gpdb_url"].split("/")[-1].replace("-", ""))
    else:
        continue

# 得られたGPDB URLで、以下のコマンドを実行する。
for item in gpdb_url:
    print('wget -q "http://192.168.2.242:8010/workflow/jobupdate/updateExitCode?internalRunId=%s&toolShellName=P000029000001036-1.2.0--16.sh&exitCode=0&userId=200000100000001&userLoginId=1&loopNumber=" -O -'%item)
    subprocess.call('wget -q "http://192.168.2.242:8010/workflow/jobupdate/updateExitCode?internalRunId=%s&toolShellName=P000029000001036-1.2.0--16.sh&exitCode=0&userId=200000100000001&userLoginId=1&loopNumber=" -O -'%item, shell=True)
    time.sleep(2.0)

# 該当ランをキャンセルへ変更する。
for item in running:
    ret = session.put("https://dev-u-tokyo.mintsys.jp:50443/workflow-api/v2/runs/%s"%item, headers=headers, json=body) 
    print(ret.text)
    time.sleep(1.0)
