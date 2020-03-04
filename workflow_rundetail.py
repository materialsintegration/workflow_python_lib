#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

'''
指定したランIDの詳細情報を取得する。
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

def get_rundetail(token, url, siteid, runid, with_result=False, debug=False):
    '''
    ラン詳細の取得
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param siteid (string) サイトID。e.g. site00002
    @param run_id (string) ランID。e.g. R000020000365545
    '''

    weburl = "https://%s:50443/workflow-api/v2/runs/%s"%(url, runid)
    res = nodeREDWorkflowAPI(token, weburl)
    if res.status_code != 200 and res.status_code != 201 and res.status_code != 204:
        print("%s - 異常な終了コードを受信しました(%d)"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.status_code))
        time.sleep(120)
        sys.exit(1)
    retval = res.json()
    if retval["status"] == "running" or retval["status"] == "waiting" or retval["status"] == "paused":
        pass
    elif retval["status"] == "abend" or retval["status"] == "canceled":
        if retval["status"] == "abend":
            sys.stderr.write("%s - ランが異常終了しています。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        else:
            sys.stderr.write("%s - ランがキャンセルされてます。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))

    if debug is True:
        print("%s\n"%json.dumps(retval, indent=2, ensure_ascii=False))
    uuid = retval["gpdb_url"].split("/")[-1].replace("-", "")
    dirname = "/home/misystem/assets/workflow/%s/calculation/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s"%(siteid, uuid[0:2], uuid[2:4], uuid[4:6], uuid[6:8], uuid[8:10], uuid[10:12], uuid[12:14], uuid[14:16], uuid[16:18], uuid[18:20], uuid[20:22], uuid[22:24], uuid[24:26], uuid[26:28], uuid[28:30], uuid[30:32])
    if debug is True:
        print(dirname)

    if with_result is False:
        return retval

    # 結果ファイルの取得
    weburl = "https://%s:50443/workflow-api/v2/runs/%s/data"%(url, runid)
    os.mkdir("/tmp/%s"%runid)
    retry_count = 0
    while True:
        if STOP_FLAG is True:
            sys.exit(1)
        res = nodeREDWorkflowAPI(token, weburl)
        if res.status_code != 200 and res.status_code != 201:
            if retry_count == 5:
                sys.stderr.write("%s - 結果取得失敗。終了します。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                sys.exit(1)
            else:
                sys.stderr.write("%s - 結果取得失敗。５分後に再取得を試みます。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                time.sleep(300.0)
            retry_count += 1
            if res.status_code == 500:
                sys.stderr.write("%s\n"%res.text)
            else:
                sys.stderr.write("%s\n"%json.dumps(res.json(), indent=2, ensure_ascii=False))
            sys.exit(1)
        wf_tools = res.json()["url_list"][0]['workflow_tools'] 
        outputfilenames = {}
        if len(wf_tools) == 0:
            sys.stderr.write("%s - 結果を取得できなかった？\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
            #sys.exit(1)
            sys.exit(1)
        get_file = False
        for tool in wf_tools:
            tool_outputs = tool["tool_outputs"]
            if len(tool_outputs) == 0:
                if retry_count == 5:
                    sys.stderr.write('tool["tool_outputs"] が空？取得できませんでした。終了します。\n')
                    sys.exit(1)
                else:
                    sys.stderr.write('tool["tool_outputs"] が空？５秒後に再取得します。\n')
                    time.sleep(5.0)
                    retry_count += 1
                    break
            for item in tool_outputs:
                filename = "/tmp/%s/%s"%(runid, item["parameter_name"])
                outputfilenames[item["parameter_name"]] = filename
                #print("outputfile:%s"%item["file_path"])
                #sys.stderr.write("file size = %s\n"%item["file_size"])
                weburl = item["file_path"]
                res = nodeREDWorkflowAPI(token, weburl, method="get_noheader")
                try:
                    outfile = open(filename, "w")
                    outfile.write("%s"%res.text)
                    outfile.close()
                except:
                    sys.stderr.write("%s\n"%traceback.format_exc())
                    sys.stderr.write("%sのファイルの保存に失敗しました\n"%item["parameter_name"])
                    sys.stderr.write("file size = %s\n"%item["file_size"])
                #sys.stderr.write("%s:%s\n"%(item["parameter_name"], filename))
                print("%s:%s"%(item["parameter_name"], filename))
                #print("%s:%s"%(item["parameter_name"], res.text))
                get_file = True
         
        if get_file is True:
            break

def main():
    '''
    '''

    token = None
    run_id = None
    result = False
    siteid = None
    url = None
    debug = False
    global STOP_FLAG

    for items in sys.argv:
        items = items.split(":")
        if len(items) != 2:
            continue
    
        if items[0] == "run_id":                # ワークフローID
            run_id = items[1]
        elif items[0] == "token":               # APIトークン
            token = items[1]
        elif items[0] == "misystem":            # 環境指定(開発？運用？NIMS？東大？)
            url = items[1]
        elif items[0] == "result":              # 結果取得(True/False)
            result = items[1]
        elif items[0] == "siteid":              # site id(e.g. site00002)
            siteid = items[1]
        elif items[0] == "debug":
            debug = True
        else:
            input_params[items[0]] = items[1]   # 与えるパラメータ

    if token is None or run_id is None or url is None or siteid is None:
        print("Usage")
        print("   $ python %s run_id:Mxxxx token:yyyy misystem:URL"%(sys.argv[0]))
        print("               run_id : Rで始まる15桁のランID")
        print("               token  : 64文字のAPIトークン")
        print("             misystem : dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        print("              siteid  : siteで＋５桁の数字。site00002など")
        sys.exit(1)

    get_rundetail(token, url, siteid, run_id, result, debug)

if __name__ == '__main__':
    main()
