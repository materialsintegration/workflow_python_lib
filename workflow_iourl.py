#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

'''
入出力URL一覧取得
'''

import sys, os
import shutil
import json
import datetime
import base64
import time
import random
import subprocess
import signal
import traceback

from common_lib import *
from workflow_params import *

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

def get_rundetail(token, url, siteid, runid, with_result=False):
    '''
    入出力ファイルURL一覧の取得
    '''

    # まずは詳細取得
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

    # 結果ファイルの取得
    weburl = "https://%s:50443/workflow-api/v2/runs/%s/data"%(url, runid)
    if os.path.exists("/tmp/%s"%runid) is True:
        shutil.rmtree("/tmp/%s"%runid)
    os.mkdir("/tmp/%s"%runid)
    retry_count = 0
    while True:
        if STOP_FLAG is True:
            return False, ""
        res = nodeREDWorkflowAPI(token, weburl)
        if res.status_code != 200 and res.status_code != 201:
            if retry_count == 5:
                sys.stderr.write("%s - 結果取得失敗。終了します。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                return False, ""
            else:
                sys.stderr.write("%s - 結果取得失敗。５分後に再取得を試みます。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                time.sleep(300.0)
            retry_count += 1
            if res.status_code == 500:
                sys.stderr.write("%s\n"%res.text)
            else:
                sys.stderr.write("%s\n"%json.dumps(res.json(), indent=2, ensure_ascii=False))
            return False, ""
        wf_tools = res.json()["url_list"][0]['workflow_tools'] 
        outputfilenames = {}
        if len(wf_tools) == 0:
            sys.stderr.write("%s - 結果を取得できなかった？\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
            #sys.exit(1)
            return ""
        get_file = False
        for tool in wf_tools:
            tool_outputs = tool["tool_outputs"]
            if len(tool_outputs) == 0:
                if retry_count == 5:
                    sys.stderr.write('tool["tool_outputs"] が空？取得できませんでした。終了します。\n')
                    return False, ""
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
                sys.stderr.write('getting output file %s for tool(%s)...'%(item['file_path'].split("/")[-1], item['parameter_name']))
                res = nodeREDWorkflowAPI(token, weburl, method="get_noheader")
                sys.stderr.write('\nreturn status(%s)\n'%res.status_code)
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
    workflow_id = None
    result = False
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
        else:
            input_params[items[0]] = items[1]   # 与えるパラメータ

    get_rundetail(token, url, siteid, run_id, result)

if __name__ == '__main__':
    main()
