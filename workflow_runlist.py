#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

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

def get_runlist(token, url, siteid, workflow_id):
    '''
    ラン詳細の取得
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param siteid (string) サイトID。e.g. site00002
    @param workflow_id (string) ワークフローID。e.g. W000020000000197
    '''

    weburl = "https://%s:50443/workflow-api/v2/runs"%url
    res = nodeREDWorkflowAPI(token, weburl, timeout=(5.0, 300.0))
    if res.status_code != 200 and res.status_code != 201 and res.status_code != 204:
        if res.status_code is None:
            print("%s - 接続がタイムアウトしました(%s)"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.text))
            return False
        print("%s - 異常な終了コードを受信しました(%d)"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.status_code))
        time.sleep(120)
        print(res.text)
        return False
    runs = res.json()["runs"]
    run_lists = []
    for item in runs:
        if item["workflow_id"].split("/")[-1] == workflow_id:
            if ("description" in item) is True:
                description = item["description"]
            else:
                description = ""
            run_info = {"run_id":item["run_id"].split("/")[-1], "status":item["status"], "description":description}
            #run_lists.append(item["run_id"].split("/")[-1])
            run_lists.append(run_info)

    return run_lists

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
    
        if items[0] == "workflow_id":           # ワークフローID
            workflow_id = items[1]
        elif items[0] == "token":               # APIトークン
            token = items[1]
        elif items[0] == "misystem":            # 環境指定(開発？運用？NIMS？東大？)
            url = items[1]
        elif items[0] == "result":              # 結果取得(True/False)
            result = items[1]
        elif items[0] == "siteid":              # site id(e.g. site00002)
            siteid = items[1]
        else:
            input_params[items[0]] = items[1]   # 与えるパラメータ

    if token is None or workflow_id is None or url is None or siteid is None:
        print("Usage")
        print("   $ python %s workflow_id:Mxxxx token:yyyy misystem:URL siteid:sitexxxxx"%(sys.argv[0]))
        print("          workflow_id : Mで始まる16桁のワークフローID")
        print("               token  : 64文字のAPIトークン")
        print("             misystem : dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        print("              siteid  : siteで＋５桁の数字。site00002など")
        sys.exit(1)

    ret = get_runlist(token, url, siteid, workflow_id)
    print(ret)

if __name__ == '__main__':
    main()
