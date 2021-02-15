#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
ラン一覧から指定のワークフローで実行したランのIDをリストで返す
'''

import sys, os
import json
import datetime
import base64
import time
import random
import subprocess
import signal
import traceback
import datetime

try:
    import mysql.connector
    has_mysql = True
except:
    has_mysql = False
from common_lib import *
from workflow_params import *

prev_workflow_id = None
input_ports_prev = None
output_ports_prev = None
STOP_FLAG = False

DB_RUN_STATUS={"1":"running",
               "2":"waiting",
               "3":"canceled",
               "4":"paused",
               "5":"completed",
               "9":"failure",
               "99":"abend"}

def signal_handler(signum, frame):
    '''
    '''

    global STOP_FLAG
    if signum == 2:         # ctrl + C
        STOP_FLAG = True

def status_out(message=""):
    '''
    状態メッセージをステータス専用ファイルに書き込む。
    毎度、上書きして以前の状態は残さない？
    ステータス専用ファイルは現状は１つだけ。
    そのうちラン毎のファイルにする必要アリ。
    '''

    outfile = open("/tmp/status.log", "w")
    outfile.write("%s"%message)
    outfile.flush()
    outfile.close()

def utc_to_jst(timestamp_utc):
    '''
    タイムゾーン変換：UTCからJSTへ
    '''
    datetime_utc = datetime.datetime.strptime(timestamp_utc + "+0000", "%Y-%m-%d %H:%M:%S.%f%z")
    datetime_jst = datetime_utc.astimezone(datetime.timezone(datetime.timedelta(hours=+9)))
    timestamp_jst = datetime.datetime.strftime(datetime_jst, '%Y-%m-%d %H:%M:%S.%f')
    return timestamp_jst

def getJstDatetime(utc_time):
    '''
    標準時から日本時間へ変更した、dateteimオブジェクトを返す
    '''

    jst_start_time = utc_time.split("Z")[0] + ".00000"
    jst_start_time = jst_start_time.replace("T", " ")
    retval = utc_to_jst(jst_start_time)
    YYMMDD = retval.split()[0]
    hhmmss = retval.split()[1]
    Y = int(YYMMDD.split("-")[0])
    M = int(YYMMDD.split("-")[1])
    D = int(YYMMDD.split("-")[2])
    h = int(hhmmss.split(":")[0])
    m = int(hhmmss.split(":")[1])
    s = int(hhmmss.split(":")[2].split(".")[0])
    return datetime.datetime(Y, M, D, h, m, s)

def get_runlist_fromDB(siteid, workflow_id, hostID='127.0.0.1', only_runlist=False):
    '''
    DBから直接ラン詳細の取得
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param siteid (string) サイトID。e.g. site00002
    @param workflow_id (string) ワークフローID。e.g. W000020000000197
    @param only_runlist (bool) Trueの場合、ラン一覧で得られる情報のみを返す。ラン詳細までは返さない。
    '''

    global has_mysql

    if has_mysql is False:
        return False, "DB接続方法を持ち合わせていません。"

    site_id = int(siteid[5:])
    w_id = "%d%s"%(site_id, workflow_id[6:])

    db = mysql.connector.connect(host=hostID, user="root", password="P@ssw0rd")
    cursor = db.cursor()
    cursor.execute("use workflow")
    cursor.execute("""select * from workflow.run where workflow_id='""" + w_id + """';""")
    rows = cursor.fetchall()
    cursor.close()
    db.close()

    run_lists = []
    for item in rows:
        run_info = {}
        run_info["run_id"] = "R%015d"%item[0]
        run_info["status"] = DB_RUN_STATUS[str(item[6])]
        run_info["description"] = item[3]
        run_info["start"] = item[19]
        run_info["end"] = item[20]
        run_info["completion"] = item[10]
        run_info["workflow_name"] = ""
        run_info["uuid"] = item[5]
        run_info["deleted"] = str(item[15])
        run_lists.append(run_info)

    return True, run_lists

def get_runlist(token, url, siteid, workflow_id, only_runlist=False):
    '''
    ラン詳細の取得
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param siteid (string) サイトID。e.g. site00002
    @param workflow_id (string) ワークフローID。e.g. W000020000000197
    @param only_runlist (bool) Trueの場合、ラン一覧で得られる情報のみを返す。ラン詳細までは返さない。
    '''

    weburl = "https://%s:50443/workflow-api/v3/runs?workflow_id=%s"%(url, workflow_id)
    res = nodeREDWorkflowAPI(token, weburl, timeout=(5.0, 300.0))
    if res.status_code != 200 and res.status_code != 201 and res.status_code != 204:
        if res.status_code is None:
            print("%s - 接続がタイムアウトしました(%s)"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.text))
            return False, res
        print("%s - 異常な終了コードを受信しました(%d)"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.status_code))
        time.sleep(120)
        print(res.text)
        return False, res

    runs = res.json()["runs"]
    run_lists = []

    # 2020/08/17追加
    if only_runlist is True:
        for item in runs:
            if ("description" in item) is True:
                description = item["description"]
            else:
                description = ""
            run_info = {"run_id":item["run_id"].split("/")[-1], "status":item["status"], "description":description, "start":getJstDatetime(item["creation_time"]), "workflow_name":item["workflow_name"], "deleted":"0"}
            if ("completion_time" in item) is True:
                run_info["completion"] = getJstDatetime(item["completion_time"])
            run_lists.append(run_info)
        return True, run_lists

    for item in runs:
        #if item["workflow_id"].split("/")[-1] == workflow_id:
        #    if ("description" in item) is True:
        #        description = item["description"]
        #    else:
        #        description = ""
        #    run_info = {"run_id":item["run_id"].split("/")[-1], "status":item["status"], "description":description}
        #    #run_lists.append(item["run_id"].split("/")[-1])
        #    run_lists.append(run_info)
        if ("description" in item) is True:
            description = item["description"]
        else:
            description = ""
        #run_info = {"run_id":item["run_id"].split("/")[-1]}
        run_info = item
        run_info["status"] = item["status"]
        run_info["description"] = description
        # ラン詳細取得
        weburl = "https://%s:50443/workflow-api/v3/runs/%s"%(url, run_info["run_id"].split("/")[-1])
        run_res = nodeREDWorkflowAPI(token, weburl, timeout=(5.0, 300.0))
        if res.status_code != 200 and res.status_code != 201 and res.status_code != 204:
            if res.status_code is None:
                print("%s - 接続がタイムアウトしました(%s)"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.text))
                return False, res
            print("%s - 異常な終了コードを受信しました(%d)"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.status_code))
            run_info["uuid"] = "unknown"
            run_info["start"] = "unknown"
            run_info["end"] = "unknown"
        else:
            run_info["uuid"] = run_res.json()["gpdb_url"].split("/")[-1]
            run_info["start"] = getJstDatetime(run_res.json()["creation_time"])
            run_info["end"] = getJstDatetime(run_res.json()["modified_time"])
        run_lists.append(run_info)

    return True, run_lists

def main():
    '''
    '''

    token = None
    workflow_id = None
    result = False
    url = None
    siteid = None
    global STOP_FLAG

    for items in sys.argv:
        items = items.split(":")
        if len(items) != 2:
            continue
    
        print("processing parameter %s"%items[0])
        if items[0] == "workflow_id":           # ワークフローID
            workflow_id = items[1]
            print("workflow_id is %s"%items[1])
        elif items[0] == "token":               # APIトークン
            token = items[1]
            print("token is %s"%items[1])
        elif items[0] == "misystem":            # 環境指定(開発？運用？NIMS？東大？)
            url = items[1]
            print("url for misystem is %s"%items[1])
        elif items[0] == "result":              # 結果取得(True/False)
            result = items[1]
        elif items[0] == "siteid":              # site id(e.g. site00002)
            siteid = items[1]
            print("siteid is %s"%items[1])
        else:
            input_params[items[0]] = items[1]   # 与えるパラメータ

    # token指定が無い場合ログイン情報取得
    if token is None and url is not None:

        ret, uid, token = getAuthInfo(url)

        if ret is False:
            print(uid.json())
            print("ログインに失敗しました。")

    if token is None or workflow_id is None or url is None or siteid is None:
        print("Usage")
        print("   $ python %s workflow_id:Mxxxx [token:yyyy] misystem:URL siteid:sitexxxxx"%(sys.argv[0]))
        print("          workflow_id : Mで始まる16桁のワークフローID")
        print("               token  : 64文字のAPIトークン")
        print("             misystem : dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        print("              siteid  : siteで＋５桁の数字。site00002など")
        sys.exit(1)

    retval, res = get_runlist(token, url, siteid, workflow_id)
    if retval is False:
        sys.exit(1)
    for item in res:
        print("RunID : %s"%item["run_id"])
        print("               開始 : %s"%item["start"].strftime("%Y/%m/%d %H:%M:%S"))
        print("               終了 : %s"%item["end"].strftime("%Y/%m/%d %H:%M:%S"))
        print("         ステータス : %s"%item["status"])
        print("        ラン詳細URL : https://%s/workflow/runs/%s"%(url, int(item["run_id"].split("/")[-1][1:])))
        uuid = item["uuid"].split("/")[-1].replace("-", "")
        dirname = "/home/misystem/assets/workflow/%s/calculation/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s"%(siteid, uuid[0:2], uuid[2:4], uuid[4:6], uuid[6:8], uuid[8:10], uuid[10:12], uuid[12:14], uuid[14:16], uuid[16:18], uuid[18:20], uuid[20:22], uuid[22:24], uuid[24:26], uuid[26:28], uuid[28:30], uuid[30:32])
        print("  実行時ディレクトリ: %s"%dirname)

if __name__ == '__main__':
    main()
