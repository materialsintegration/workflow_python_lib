#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

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
from getpass import getpass
from openam_operator import openam_operator

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

def get_runiofile(token, url, siteid, runid, with_result=False, thread_num=0, timeout=(2.0, 30.0), debug=False, read_uncomplete=False):
    '''
    入出力ファイルURL一覧の取得
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param siteid (string) サイトID。e.g. site00002
    @param runid (string) ランID。e.g. R000020000365545
    @param with_result (bool) この関数を実行時、情報を標準エラーに出力するか
    @param timeout (tuple) タイムアウトを接続確立用とその後の応答用の２つを指定する
    @param debug (bool) Trueなら応答ボディを表示して終わり
    @param read_uncomplete (bool) file_pathキーの値の最後がrun/で終わっていても読む。
    '''

    # 結果ファイルの取得
    #weburl = "https://%s:50443/workflow-api/v2/runs/%s/data"%(url, runid)
    weburl = "https://%s:50443/workflow-api/v3/runs/%s/data"%(url, runid)
    retry_count = 0
    while True:
        if STOP_FLAG is True:
            return False, ""
        if type(timeout) == list:
            timeout = tuple(timeout)
        res = mintWorkflowAPI(token, weburl, error_print=with_result, timeout=timeout)
        if res.status_code != 200 and res.status_code != 201:
            if res.status_code == 500:
                #sys.stderr.write("%s\n"%res.text)
                try:
                    sys.stderr.write("%s\n"%json.dumps(res.json(), indent=2, ensure_ascii=False))
                except:
                    sys.stderr.write("%s\n"%res.text)
            elif res.status_code == 503:
                if res.json()["errors"][0]["code"] == "0011":
                    continue
            elif res.status_code == 404:
                if res.json()["errors"][0]["code"] == "0007":
                    return False, ""
            elif res.status_code is None:
                sys.stderr.write("%s -- %03d : RunID(%s) 結果取得失敗(%s)。終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), thread_num, runid, res.text))
                return False, "%s -- %03d : RunID(%s) 結果取得失敗(%s)。終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), thread_num, runid, res.text)
            else:
                try:
                    sys.stderr.write("code:%d\n%s\n"%(res.status_code, json.dumps(res.json(), indent=2, ensure_ascii=False)))
                except:
                    sys.stderr.write("code:%d\n%s\n"%(res.status_code, res.text))
            if retry_count == 1:
                sys.stderr.write("%s -- %03d : RunID(%s) 結果取得失敗。終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), thread_num, runid))
                return False, "%s -- %03d : RunID(%s) 結果取得失敗。終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), thread_num, runid)
            else:
                sys.stderr.write("%s -- %03d : RunID(%s) 結果取得失敗。10秒後に再取得を試みます。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), thread_num, runid))
                time.sleep(10.0)
            retry_count += 1
            continue
        else:
            break

    loop_num = 0

    if debug is True:
        print(json.dumps(res.json(), indent=2, ensure_ascii=False))
        sys.exit(0)

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

        # ワークフロー入力ポートの処理
        workflow_inputs = url_list["workflow_inputs"]
        if len(workflow_inputs) == 0:
            sys.stderr.write('url_list["workflow_inputs"] が空？取得できませんでした。次を処理します。\n')
            continue
        if with_result is True:
            sys.stderr.write("response contentes for input for workflow\n")
            sys.stderr.write("%s\n"%json.dumps(workflow_inputs, indent=2, ensure_ascii=False))
        for item in workflow_inputs:
            #param_name = item["parameter_name"].split("_")[0]
            params = item["parameter_name"].split("_")
            #sys.stdout.write("workflow input (%s) の処理中\n"%params)
            param_name = ""
            #==> 2021/04/05: Rosenbrock_x のような01が無いポートに対応する。
            try:
                int(params[-1])
                params.pop(-1)
            except:
                pass
            param_name = "_".join(params)
            #for i in range(0, len(params) - 1):
            #    if i == 0:
            #        param_name = params[i]
            #    else:
            #        param_name += "_" + params[i]
            #<== 2021/04/05
            if ("file_size" in item) is True and item["file_path"].split("/")[-2] != "runs":
                io_dict[runid][param_name] = [item["file_path"], item["file_size"]]
            else:
                sys.stderr.write("run_id(%s) のworkflow_inputsのうち%sのポートのURLが不完全です\n"%(runid, item["parameter_name"]))
                sys.stderr.flush()
                if read_uncomplete is True:
                    io_dict[runid][param_name] = [item["file_path"], item["file_size"]]

        # ワークフロー出力ポートの処理
        workflow_outputs = url_list["workflow_outputs"]
        if len(workflow_outputs) == 0:
            sys.stderr.write('url_list["workflow_outputs"] が空？取得できませんでした。次を処理します。\n')
            continue
        if with_result is True:
            sys.stderr.write("response contentes for output for workflow\n")
            sys.stderr.write("%s\n"%json.dumps(workflow_outputs, indent=2, ensure_ascii=False))
        for item in workflow_outputs:
            #param_name = item["parameter_name"].split("_")[0]
            params = item["parameter_name"].split("_")
            #sys.stdout.write("workflow output (%s) の処理中\n"%params)
            param_name = ""
            #==> 2021/04/05: Rosenbrock_x のような01が無いポートに対応する。
            try:
                int(params[-1])
                params.pop(-1)
            except:
                pass
            param_name = "_".join(params)
            #for i in range(0, len(params) - 1):
            #    if i == 0:
            #        param_name = params[i]
            #    else:
            #        param_name += "_" + params[i]
            #<== 2021/04/05
            if ("file_size" in item) is True and item["file_path"].split("/")[-2] != "runs":
                io_dict[runid][param_name] = [item["file_path"], item["file_size"]]
            else:
                sys.stderr.write("run_id(%s) のworkflow_outputsのうち%sのポートのURLが不完全です\n"%(runid, item["parameter_name"]))
                sys.stderr.flush()
                if read_uncomplete is True:
                    io_dict[runid][param_name] = [item["file_path"], item["file_size"]]

        # 各ツールの出力ポートの処理
        tools_outputs = url_list["workflow_tools"]
        if len(tools_outputs) == 0:
            sys.stderr.write('url_list["workflow_tools"] が空？取得できませんでした。次を処理します。\n')
            continue
        for workflow_tool in tools_outputs:
            tool_outputs = workflow_tool["tool_outputs"]
            if len(tool_outputs) == 0:
                sys.stderr.write('ツール名（%s）のurl_list["workflow_tools"][tool_outputs] が空？取得できませんでした。次を処理します。\n'%workflow_tool["tool_name"])
                continue

            if with_result is True:
                sys.stderr.write("response contentes for output for tool(%s)\n"%workflow_tool["tool_name"])
                sys.stderr.write("%s\n"%json.dumps(tool_outputs, indent=2, ensure_ascii=False))
            for item in tool_outputs:
                #param_name = item["parameter_name"].split("_")[0]
                #==> 2021/04/08: ものによって_01が付与される？ための対処
                #param_name = item["parameter_name"]
                params = item["parameter_name"].split("_")
                param_name = ""
                try:
                    int(params[-1])
                    params.pop(-1)
                except:
                    pass
                param_name = "_".join(params)
                #<== 2021/04/08
                #sys.stdout.write("tool (%s) output (%s) の処理中\n"%(workflow_tool["tool_name"], param_name))
                if ("file_size" in item) is True and item["file_path"].split("/")[-2] != "runs":
                    if item["file_size"] != 0:
                        io_dict[runid][param_name] = [item["file_path"], item["file_size"]]
                else:
                    sys.stderr.write("run_id(%s) のtool(%s)のoutputのうち%sのポートのURLが不完全です\n"%(runid, workflow_tool["tool_name"], item["parameter_name"]))
                    sys.stderr.flush()
                    if read_uncomplete is True:
                        io_dict[runid][param_name] = [item["file_path"], item["file_size"]]
     
        loop_num += 1

    return True, io_dict

def main():
    '''
    '''

    token = None
    run_id = None
    url = None
    siteid = "site00002"
    result = False
    timeout = [10, 30]
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
            if items[1] == "true":
                result = True
            else:
                result = False
        elif items[0] == "siteid":              # site id(e.g. site00002)
            siteid = items[1]
        elif items[0] == "timeout":             # タイムアウト
            try:
                timeout[1] = int(items[1])
            except:
                pass
        elif items[0] == "debug":               # デバッグ（応答ボディのみ表示して終わり）
            debug = True
        else:
            input_params[items[0]] = items[1]   # 与えるパラメータ

    if run_id is None or url is None:
        print("Usage")
        print("   $ python %s run_id:Rxxxx token:yyyy misystem:URL"%(sys.argv[0]))
        print("               run_id : Rで始まる15桁のランID")
        print("               token  : 64文字のAPIトークン")
        print("             misystem : dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        print("              siteid  : siteで＋５桁の数字。site00002など")
        print("             timeout  : 読み込みタイムアウトを設定する。秒。接続確立時ではない。")
        sys.exit(1)

    timeout = tuple(timeout)
    if debug is True:
        print("応答のみ返します。")
    if token is None:
        if sys.version_info[0] <= 2:
            name = raw_input("ログインID: ")
        else:
            name = input("ログインID: ")
        password = getpass("パスワード: ")
        ret, uid, token = openam_operator.miauth(url, name, password)
    ret, ret_dict = get_runiofile(token, url, siteid, run_id, result, timeout=timeout, debug=debug)
    sys.stderr.write("%s\n"%json.dumps(ret_dict, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
