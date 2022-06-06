#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
指定したワークフローIDのワークフローをポート名とパラメータファイルを指定してフィードバックラン実行する
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
import mimetypes

try:
    import mysql.connector
    has_mysql = True
except:
    has_mysql = False
from common_lib import *
from workflow_params import *
from workflow_rundetail import *
from openam_operator import openam_operator

prev_workflow_id = None
input_ports_prev = None
output_ports_prev = None
STOP_FLAG = False
siteids = {"dev-u-tokyo.mintsys.jp":"site00002",
            "nims.mintsys.jp":"site00011",
            "u-tokyo.mintsys.jp":"site00001"}
RUN_STATUS = {"canceled":"キャンセル", "failure":"起動失敗", "running":"実行中",
              "waiting":"待機中", "paused":"一時停止", "abend":"異常終了"}

api_url ="https://%s:%s/workflow-api/%s/runs"
CHARSET_DEF = 'utf-8'

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

def workflow_log(messages, logfile):
    '''
    ランID毎に開始時間と顛末を記録する。排他制御を行い、並列実行にい備える。
    出力先はこれまでoutfileで出力してきたファイル名()と同じ
    @param messages(string)
    '''

    loglock_file = ".%s"%logfile
    while True:
        if os.path.exists(loglock_file) is False:
            break
        # ロックファイルがあれば１秒待つ
        time.sleep(1.0)

    # ロックファイル作成
    outfile = open(loglock_file, "w")
    outfile.close()

    # ログ出力
    outfile = open(logfile, "a")
    outfile.write("%s\n"%messages)
    outfile.close()

    # ロックファイル削除
    if os.path.exists(loglock_file) is True:    # 別プロセスが絶妙なタイミングでここを実行したときの対策。
        os.remove(loglock_file)

def paramsToJsonParams(input_params, input_ports):
    '''
    実行時パラメータの指定からAPI実行用のJSON形式への変換。パラメータファイルの存在確認付。
    @param input_params (list)
    @retval json
    '''

    workflow_params =[]
    for input_item in input_params:
        target_item = None
        for item in input_ports:
            #if item[0] == input_item:
            if item[0].startswith(input_item) is True:
                #print("input port name = %s"%item)
                target_item = item
        if target_item is not None:
            params = {}
            params["input_name"] = target_item[0]
            if target_item[2] == "file":
                if os.path.exists(input_params[input_item]) is False:
                    sys.stderr.write("パラメータファイル(%s)がありません。終了します。\n"%input_params[input_item])
                    sys.stderr.flush()
                    sys.exit(1)
                params["input_data_file"] = base64.b64encode(open(input_params[input_item], "rb").read()).decode('utf-8')
            elif target_item[2] == "asset":
                params["asset_id"] = target_item[1]
            elif target_item[2] == "value" or target_item[2] == "bool":
                params["input_data_value"] = target_item[1]
    
            workflow_params.append(params)

    return workflow_params

def workflow_feedbackstart(workflow_id, token, url, port, input_params, max_count, timeout=None, seed=None, description=None, exec_retry_count=5, version="v4"):
    '''
    フィードバックラン実行
    @param workflow_id (string) Wで始まる16桁のワークフローID。e.g. W000020000000197
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param port (string) ポート番号。
    @param input_params (list) <ポート名>:<ファイル名>のリスト。
    @param max_count (string) 起動時に指定する最大回数。
    @param timeout (int) 実行中のままこの秒数が過ぎた場合はキャンセルを実行して終了。データ取得はしない。
    @param descriotion (string) 代わりの説明文
    @param exec_retry_count (int) ワークフロー実行時APIの応答でエラーが返ってきたときこの回数までリトライしてだめならFalseで返る。
    @retval (bool, str) boolとstringのタプル。 実行不可能だったらFalse。正常実行できたらTrue。TrueのときフィードバックランID
    '''

    global prev_workflow_id
    global input_ports_prev
    global output_ports_prev
    global STOP_FLAG

    logfile = "workflow_exec.%s.log"%url

    # パラメータ構築用にワークフロー詳細情報を取得する。
    miwf_contents, input_ports, output_ports = extract_workflow_params(workflow_id, token, url, port, version)
    if miwf_contents is False:
        sys.stderr.write("%s - ワークフローの情報を取得できませんでした。終了します。。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), workflow_id))
        sys.stderr.flush()
        sys.exit(1)

    print("input_ports = %s"%input_ports)

    # Runパラメータの構築
    run_params = {}
    try:
        run_params["max_loop_count"] = int(max_count)
    except:
        sys.stderr.write("フィードバックラン開始パラメータのmax_count(%s)が整数ではありません？\n"%max_count)
        sys.stderr.flush()
        sys.exit(1)
    run_params["description"] = "フィードバックラン実行(開始時刻：%s)\n\n"%datetime.datetime.now()
    if description is None:
        run_params["description"] += "parameter\n"
        for item in input_params:
            if input_params[item] == "initial_setting.dat":
                continue
            if mimetypes.guess_type(input_params[item])[1] != "None":
                continue
            run_params["description"] += "%-20s:"%item
            infile = open(input_params[item])
            value = "%s"%infile.read().split("\n")[0]
            run_params["description"] += "%s\n"%value
    else:
        run_params["description"] = "%s\n"%description
    
    #run_params["workflow_parameters"] = paramsToJsonParams(input_params, input_ports)
    run_params["workflow_parameters"] = []
    
    # 入力ポート辞書の保存
    outfile = open("input_ports.json", "w")
    json.dump(input_ports, outfile, indent=4)
    outfile.close()
    
    # ワークフローの実行
    retry_count = 0
    #outfile = open(logfile, "a")
    outmessage = ""
    while True:
        weburl = "https://%s:%s/workflow-api/%s/feedbackruns"%(url, port, version)
        #weburl = api_url%(url, version)
        params = {"workflow_id":"%s"%workflow_id}
        sys.stdout.write("%s - フィードバックラン開始します。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        sys.stdout.write("   %s\n"%run_params)
        sys.stdout.flush()
        res = mintWorkflowAPI(token, weburl, params, json.dumps(run_params), method="post", timeout=(300.0, 300.0), error_print=False)
        
        # 実行の可否
        if res.status_code != 200 and res.status_code != 201:
            if res.status_code is None:         # タイムアウトだった
                sys.stderr.write("%s - 実行できませんでした。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.text))
                sys.stderr.flush()
            elif res.status_code == 400:
                sys.stderr.write("%s - 「%s(%s)」により実行できませんでした。終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.json()["errors"][0]["message"], res.json()["errors"][0]["code"]))
                sys.stderr.flush()
                message = "%s - - 「%s(%s)」により実行できませんでした。終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.json()["errors"][0]["message"], res.json()["errors"][0]["code"])
                workflow_log(message, logfile)
                sys.exit(1)
            elif res.status_code == 401:
                if res.json()["code"] == "0002":
                    sys.stderr.write("%s - 「%s(%s)」により実行できませんでした。終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.json()["errors"][0]["message"], res.json()["errors"][0]["code"]))
                    sys.stderr.flush()
                    message = "%s - - 「%s(%s)」により実行できませんでした。終了します。"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.json()["errors"][0]["message"], res.json()["errors"][0]["code"])
                    workflow_log(message, logfile)
                    sys.exit(1)
            else:
                sys.stderr.write("%s - False 実行できませんでした。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), json.dumps(res.json(), indent=2, ensure_ascii=False)))
            if retry_count == exec_retry_count:
                sys.stderr.write("%s - 実行リトライカウントオーバー。終了します。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                sys.stderr.flush()
                message = "%s - - 実行リトライカウントオーバー。終了します。"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
                workflow_log(message, logfile)
                sys.exit(1)
            else:
                retry_count += 1
                sys.stderr.write("%s - ６０秒後、実行リトライ。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                sys.stderr.flush()
                time.sleep(60)
                continue
            
        else:
            # フィードバックランIDの取得
            runid = res.json()["run_id"]
            runid = runid.split("/")[-1]
            sys.stdout.write("%s - フィードバックラン実行中（%s）\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), runid))
            sys.stdout.flush()
            sys.stderr.write("%s\n"%runid)
            sys.stderr.flush()
            url_runid = int(runid[1:])
            sys.stdout.write("%s - ラン詳細ページ  https://%s/workflow/runs/%s\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), url, url_runid))
            sys.stdout.flush()
            sys.stdout.write("%s\n"%run_params)
            sys.stdout.flush()
            sys.exit(0)

def workflow_feedbackrun(feedbackrun_id, token, url, port, input_params=None, timeout=(2.0, 300.0), version="v4", downloaddir="/tmp"):
    '''
    フィードバックラン１回実行
    @param feedbackrun_id (string)
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param port (string) ポート番号。
    @param input_params (list) <ポート名>:<ファイル名>のリスト。
    @param timeout (int) 実行中のままこの秒数が過ぎた場合はキャンセルを実行して終了。データ取得はしない。
    @param version (string)
    @param downloaddir (string)
    '''
    # フィードバックラン１回実行後、ラン終了待機
    weburl = "https://%s:%s/workflow-api/%s/feedbackruns/%s/loops"%(url, port, version, feedbackrun_id)

    # input_ports辞書の読み込み
    if os.path.exists("input_ports.json") is True:
        infile = open("input_ports.json")
        input_ports = json.load(infile)
        infile.close()
    else:
        sys.stderr.write("入力ポートの辞書を保存したファイル(input_ports.json)がありません。終了します。\n")
        sys.stderr.flush()
        sys.exit(1)

    # Runパラメータの構築
    run_params = {}
    run_params["workflow_parameters"] = paramsToJsonParams(input_params, input_ports)
    params = {}

    # フィードバックラン１回実行
    sys.stdout.write("%s - フィードバックランを１回実行します。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    sys.stdout.flush()
    res = mintWorkflowAPI(token, weburl, params, json.dumps(run_params), method="put", timeout=(300.0, 300.0), error_print=False)
    if res.status_code != 200 and res.status_code != 201 and res.status_code != 204:
        if res.status_code is None:         # タイムアウトだった
            sys.stderr.write("%s - タイムアウトしました。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.text))
            sys.stderr.flush()
        elif res.status_code == "-1":       # 例外発生の異常終了
            sys.stderr.write("%s - 例外が発生しました。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.text))
            sys.stderr.flush()
        elif res.status_code == 400:        # エラー処理
            sys.stderr.write("%s - 「%s(%s)」により実行できませんでした。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.json()["errors"][0]["message"], res.json()["errors"][0]["code"]))
            sys.stderr.flush()
        else:
            sys.stderr.write("%s - 異常な終了コードを受信しました(%d)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.status_code))
            sys.stderr.flush()

        sys.stderr.write("URL : %s\n"%weburl)
        sys.stderr.write("パラメータ : %s\n"%run_params)
        sys.stderr.flush()
        sys.exit(1)
    else:
        #print("ラン実行ステータスが%sに変化したのを確認しました"%retval["status"])
        sys.stdout.write("%s - フィードバックランが終了しました。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        sys.stdout.flush()

    # ダウンロードディレクトリの準備
    if downloaddir is None:
        if os.path.exists("/tmp/%s"%feedbackrun_id) is False:
            os.mkdir("/tmp/%s"%feedbackrun_id)
    else:
        if downloaddir.startswith("/tmp") is False:         # tempfile指定などが使われた？
            if os.path.exists(downloaddir) is False:
                os.mkdir("./%s"%downloaddir)
            if os.path.exists("./%s/%s"%(downloaddir, feedbackrun_id)) is False:
                os.mkdir("./%s/%s"%(downloaddir, feedbackrun_id))
        else:
            if os.path.exists("./%s/%s"%(downloaddir, feedbackrun_id)) is False:
                os.mkdir("%s/%s"%(downloaddir, feedbackrun_id))

    # 出力ポートファイルのダウンロード
    for item in res.json()["output_data_values"]:
        headers_for_assetapi = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/octet-stream', 'Accept': 'application/octet-stream'}
        if downloaddir is None:
            filename = "/tmp/%s/%s"%(feedbackrun_id, item["output_name"])
        else:
            if downloaddir.startswith("/tmp") is False:         # tempfile指定などが使われた？
                filename = "./%s/%s/%s"%(downloaddir, feedbackrun_id, item["output_name"])
            else:
                filename = "%s/%s/%s"%(downloaddir, feedbackrun_id, item["output_name"])
        #outputfilenames[item["output_name"]] = filename
        weburl = item["output_data_value"]
        if port != "50443":
            weburl = weburl.replace(":50443", ":%s"%port)
        sys.stdout.write("%s - %s 取得中...\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), item["output_name"]))
        sys.stdout.flush()
        while True:
            try:
                timeout = (10.0, 600.0)
                res = mintWorkflowAPI(token, weburl, method="get", headers=headers_for_assetapi, timeout=timeout)
            except MemoryError:
                sys.stderr.write("%s\n"%traceback.format_exc())
                sys.stderr.write("%s - ファイルの取得に失敗しました(MemoryError)\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                #sys.stderr.write("file size = %s\n"%item["file_size"])
                sys.stderr.flush()
                break
            if res.status_code == 500:
                sys.stderr.write("%s - 結果を取得できませんでした。５分後に再取得します。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                sys.stderr.flush()
                time.sleep(300)
                continue
            else:
                break
        if res.status_code is None:         # タイムアウトだった
            sys.stderr.write("%s - タイムアウトしました。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.text))
            sys.stderr.flush()
            continue
        try:
            outputfile = open(filename, "wb")
            #outfile.write("%s"%res.text)
            outputfile.write(res.content)
            outputfile.close()
        except:
            sys.stderr.write("%s\n"%traceback.format_exc())
            sys.stderr.write("%sのファイルの保存に失敗しました\n"%item["output_name"])
            sys.stderr.flush()
        sys.stdout.write("%s:%s\n"%(item["output_name"], filename))
        sys.stdout.flush()
    sys.exit(0)

def workflow_feedbackstop(feedbackrun_id, token, url, port, timeout, stop_status="completed", version="v4", downloaddir=None, nodownload=True):
    '''
    フィードバックランの停止
    @param feedbackrun_id (string)
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param port (string) ポート番号。
    @param timeout (float, float)
    @param stop_status (string)
    @param version (string)
    @param downloaddir (string) /tmp/<RUN番号> に変わる保存場所（ディレクトリ名）。起点はカレントディレクトリ
    @param nodownload (bool) Trueなら実行終了後の出力ポートデータを取得しない。デフォルトは(True)しない。
    '''

    # フィードバック停止
    if stop_status == "cancel" or stop_status == "canceled":
        weburl = "https://%s:%s/workflow-api/%s/runs/%s"%(url, port, version, feedbackrun_id)
        stop_status = "canceled"
    else:
        weburl = "https://%s:%s/workflow-api/%s/feedbackruns/%s"%(url, port, version, feedbackrun_id)
    # Runパラメータの構築
    run_params = {"status":"%s"%stop_status}
    params = {}

    # フィードバックラン１回実行
    res = mintWorkflowAPI(token, weburl, params, json.dumps(run_params), method="put", timeout=(300.0, 300.0), error_print=False)

    sys.stdout.write("%s - ワークフロー実行終了\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    sys.stdout.flush()

    # 2021年7月現在、ダウンロードはしない、で運用する。
    if nodownload is True:                  # 実行終了後のダウンロードをしない
        sys.stdout.write("%s - 出力ポートのダウンロードはしません\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        sys.stdout.flush()
        sys.exit(0)

def main():
    '''
    '''

    token = None
    input_params = {}
    workflow_id = None
    number = "-1"
    timeout = None
    siteid = "site00002"
    description = None
    downloaddir = None
    nodownload = True
    config = None
    conf_file = None
    version = "v4"
    fmode = None
    feedbackrun_id = None
    stop_status = "completed"
    print_help = True
    max_count = "99"
    port = "50443"
    global STOP_FLAG

    for i in range(1, len(sys.argv)):
        #items = items.split(":")
        #if len(items) != 2:
        #    continue
        item = sys.argv[i]

        if item.startswith("--"):
            if item == "--download":
                nodownload = False
            continue
        items = []
        items.append(item[0:item.index(":")])
        items.append(item[item.index(":") + 1:])

        if items[0] == "workflow_id":           # ワークフローID
            workflow_id = items[1]
        elif items[0] == "token":               # APIトークン
            token = items[1]
        elif items[0] == "misystem":            # 環境指定(開発？運用？NIMS？東大？)
            url = items[1]
        elif items[0] == "number":              # 回数指定
            number = items[1]
        elif items[0] == "timeout":             # タイムアウト値
            try:
                timeout = int(items[1])
            except:
                timeout = None
        elif items[0] == "siteid":              # site ID
            siteid = items[1]
        elif items[0] == "description":         # 説明
            description = items[1]
        elif items[0] == "downloaddir":         # ダウンロードディレクトリの指定
            downloaddir = items[1]
        elif items[0] == "conf":                # パラメータ構成ファイル
            conf_file = items[1]
        elif items[0] == "version":             # APIバージョン指定
            version = items[1]
        elif items[0] == "mode":                # フィードバックランのモード(start/run/stop)
            fmode = items[1]
        elif items[0] == "feedback_id":         # 制御したいフィードバックランのID
            feedbackrun_id = items[1]
        elif items[0] == "status":              # フィードバックランの停止コード
            stop_status = items[1]
        elif items[0] == "max_count":           # 最大回数
            max_count = items[1]
        elif items[0] == "port":                # ポート番号
            port = items[1]
        else:
            if len(items) != 2:
                continue
            input_params[items[0]] = items[1]   # 与えるパラメータ

    if conf_file is not None:
        sys.stdout.write("パラメータを構成ファイル(%s)から読み込みます。\n"%conf_file)
        infile = open(conf_file, "r", encoding=CHARSET_DEF)
        try:
            config = json.load(infile)
        except json.decoder.JSONDecodeError as e:
            sys.stderr.write("%sを読み込み中の例外キャッチ\n"%conf_file)
            sys.stderr.write("%s\n"%e)
            sys.exit(1)
        infile.close()

    if config is not None:
        for item in list(config.keys()):
            if item == "workflow_id":
                workflow_id = config["workflow_id"]
            elif item == "token":
                token = config["token"]
            elif item == "misystem":
                url = config["misystem"]
            elif item == "timeout":
                timeout = int(config["timeout"])
            elif item == "siteid":
                siteid = config["siteid"]
            elif item == "description":
                description = config["description"]
            elif item == "downloaddir":
                downloaddir = config["downloaddir"]
            elif item == "port":
                port = config["port"]
            else:
                sys.stderr.write("未知のキー(%s)です。"%item)
                sys.stderr.flush()

    if token is not None:
        if url is not None:
            if fmode is not None:
                print_help = False
    if fmode == "start" and workflow_id is None:
        print_help = False

    if fmode == "run" or fmode == "stop":
        if feedbackrun_id is None:
            print_help = False

    if print_help is True:
        print("Usage")
        print("   $ python %s workflow_id:Mxxxx token:yyyy misystem:URL <port-name>:<filename for port> [OPTIONS]..."%(sys.argv[0]))
        print("               token  : 非必須 64文字のAPIトークン。指定しなければログインから取得。")
        print("             misystem : 必須 dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        print("    <port-name>:<filename for port> : ポート名とそれに対応するファイル名を必要な数だけ。")
        print("                      : 必要なポート名はworkflow_params.pyで取得する。")
        print("              timeout : 連続実行でない場合に、実行中のままこの時間（秒指定）を越えた場合に、キャンセルして終了する。")
        print("          description : ランの説明に記入する文章。")
        print("                 mode : 必須 start/run/stopのどれかを指定する。")
        print("                      : start フィードバックラン開始。正常開始できればstdoutにIDが表示される。")
        print("                      : run フィードバックラン１回開始。実行完了で戻ってくる。")
        print("                      : stop フィードバックラン終了。statusで終了状態を指定する。")
        print("          workflow_id : mode:startの時に必要 Rで始まる15桁のランID")
        print("          feedback_id : mode:runまたはstopの時に必要な操作対象のランID")
        print("                 conf : 構成ファイルの指定")
        print("    OPTIONS")
        print("        --download    : 実行終了後の出力ポートのダウンロードを行う。")
        print("                      : デフォルトダウンロードは行わない。")
        print("                      : mode:stop時に有効。")
        print("          downloaddir : 実行完了後の出力ポートファイルのダウンロード場所の指定（指定はカレントディレクトリ基準）")
        print("                        downloaddir/<RUN番号>/ポート名")
        print("                        デフォルトは/tmp/<RUN番号>ディレクトリ")
        print("                      : mode:stop時に有効。")
        print("                satus : mode:stop時に指定する。complete、abend、cancelを指定する。")
        print("                      : 無指定はcompleteとなる。")
        print("            max_count : 起動したランが実行できる最大回数。無指定は暫定100回。")
        sys.exit(1)

    # APIトークンの取得
    if token is None:
        uid, token = openam_operator.miLogin(url, "ログイン情報入力")

    if token is None:
        sys.stderr.write("ログインに失敗しました。\n")
        sys.stderr.flush()
        sys.exit(1)

    signal.signal(signal.SIGINT, signal_handler)

    if fmode == "start":
        workflow_feedbackstart(workflow_id, token, url, port, input_params, max_count, timeout, siteid, description, version=version)
    elif fmode == "run":
        workflow_feedbackrun(feedbackrun_id, token, url, port, input_params, timeout, version=version, downloaddir=downloaddir)
    elif fmode == "stop":
        workflow_feedbackstop(feedbackrun_id, token, url, port, timeout, stop_status, version=version)
    else:
        sys.stderr.write("不明なモード(%s)です。"%fmode)
        sys.stderr.flush()
        sys.exit(1)

if __name__ == '__main__':
    main()
