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

def get_runiofile(token, url, siteid, runid, with_result=False, thread_num=0):
    '''
    入出力ファイルURL一覧の取得
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param siteid (string) サイトID。e.g. site00002
    @param runid (string) ランID。e.g. R000020000365545
    @param with_result (bool) この関数を実行時、情報を標準エラーに出力するか
    '''

    # 結果ファイルの取得
    weburl = "https://%s:50443/workflow-api/v2/runs/%s/data"%(url, runid)
    retry_count = 0
    while True:
        if STOP_FLAG is True:
            return False, ""
        res = nodeREDWorkflowAPI(token, weburl, error_print=with_result)
        if res.status_code != 200 and res.status_code != 201:
            if res.status_code == 500:
                #sys.stderr.write("%s\n"%res.text)
                try:
                    sys.stderr.write("%s\n"%json.dumps(res.json(), indent=2, ensure_ascii=False))
                except:
                    sys.stderr.write("%s\n"%json.text)
            elif res.status_code == 503:
                if res.json()["errors"][0]["code"] == "0011":
                    continue
            elif res.status_code == 404:
                if res.json()["errors"][0]["code"] == "0007":
                    return False, ""
            else:
                try:
                    sys.stderr.write("code:%d\n%s\n"%(res.status_code, json.dumps(res.json(), indent=2, ensure_ascii=False)))
                except:
                    sys.stderr.write("code:%d\n%s\n"%(res.status_code, res.text))
            if retry_count == 1:
                sys.stderr.write("%s -- %03d : 結果取得失敗。終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), thread_num))
                return False, ""
            else:
                sys.stderr.write("%s -- %03d : 結果取得失敗。10秒後に再取得を試みます。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), thread_num))
                time.sleep(10.0)
            retry_count += 1
            continue
        else:
            break

    loop_num = 0
    io_dict = {}
    io_dict[runid] = {}
    for url_list in res.json()["url_list"]:

        #sys.stderr.write("%s\n"%json.dumps(url_list, indent=2, ensure_ascii=False))
        if with_result is True:
            sys.stderr.write("run id(%s) の loop番号 %d 番目のIOポート URLの抽出\n"%(runid, loop_num))
        io_dict[runid]["loop"] = loop_num
        outputfilenames = {}
        if len(url_list) == 0:
            sys.stderr.write("%s -- %03d : 結果を取得できなかった？\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), thread_num))
            #sys.exit(1)
            return False, ""

        # 入力ポートの処理
        tool_inputs = url_list["workflow_inputs"]
        if len(tool_inputs) == 0:
            sys.stderr.write('url_list["workflow_tools"]["tool_inputs"] が空？取得できませんでした。次を処理します。\n')
            continue
        if with_result is True:
            sys.stderr.write("response contentes for input for workflow\n")
            sys.stderr.write("%s\n"%json.dumps(tool_inputs, indent=2, ensure_ascii=False))
        for item in tool_inputs:
            param_name = item["parameter_name"].split("_")[0]
            #io_dict[runid][item["parameter_name"]] = [item["file_path"], item["file_size"]]
            io_dict[runid][param_name] = [item["file_path"], item["file_size"]]

        # 出力ポートの処理
        tool_outputs = url_list["workflow_outputs"]
        if len(tool_outputs) == 0:
            sys.stderr.write('url_list["workflow_tools"]["tool_outputs"] が空？取得できませんでした。次を処理します。\n')
            continue
        if with_result is True:
            sys.stderr.write("response contentes for output for workflow\n")
            sys.stderr.write("%s\n"%json.dumps(tool_outputs, indent=2, ensure_ascii=False))
        for item in tool_outputs:
            param_name = item["parameter_name"].split("_")[0]
            io_dict[runid][param_name] = [item["file_path"], item["file_size"]]
     
        loop_num += 1

    return True, io_dict

def main():
    '''
    '''

    token = None
    run_id = None
    url = None
    siteid = None
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
            if items[1] == "true":
                result = True
            else:
                result = False
        elif items[0] == "siteid":              # site id(e.g. site00002)
            siteid = items[1]
        else:
            input_params[items[0]] = items[1]   # 与えるパラメータ

    if token is None or run_id is None or url is None or siteid is None:
        print("Usage")
        print("   $ python %s run_id:Rxxxx token:yyyy misystem:URL"%(sys.argv[0]))
        print("               run_id : Rで始まる15桁のランID")
        print("               token  : 64文字のAPIトークン")
        print("             misystem : dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        print("              siteid  : siteで＋５桁の数字。site00002など")
        sys.exit(1)

    ret, ret_dict = get_runiofile(token, url, siteid, run_id, result)
    sys.stderr.write("%s\n"%json.dumps(ret_dict, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
