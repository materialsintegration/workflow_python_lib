#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

'''
指定したワークフローIDのワークフローをポート名とパラメータファイルを指定して実行する
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

prev_workflow_id = None
input_ports_prev = None
output_ports_prev = None
STOP_FLAG = False
siteids = {"dev-u-tokyo.mintsys.jp":"site00002",
            "nims.mintsys.jp":"site00011",
            "u-tokyo.mintsys.jp":"site00001"}

api_url ="https://%s:50443/workflow-api/v3/runs"

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

def workflow_run(workflow_id, token, url, input_params, number="-1", timeout=None, seed=None, siteid="site00002", description=None, downloaddir=None):
    '''
    ワークフロー実行
    @param workflow_id (string) Wで始まる16桁のワークフローID。e.g. W000020000000197
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param input_params (list) <ポート名>:<ファイル名>のリスト。
    @param number (string) 文字指定の連続実行数。-1の場合は1回で終了。
    @param timeout (int) 実行中のままこの秒数が過ぎた場合はキャンセルを実行して終了。データ取得はしない。
    @param descriotion (string) 代わりの説明文
    @param downloaddir (string) /tmp/<RUN番号> に変わる保存場所（ディレクトリ名）。起点はカレントディレクトリ
    '''

    global prev_workflow_id
    global input_ports_prev
    global output_ports_prev
    global STOP_FLAG

    logfile = "workflow_exec.%s.log"%url

    # 前回と同じworkflow_idなら詳細を取得しない。
    if prev_workflow_id != workflow_id:
        miwf_contents, input_ports, output_ports = extract_workflow_params(workflow_id, token, url)
        if miwf_contents is False:
            sys.stderr.write("%s - ワークフローの情報を取得できませんでした。終了します。。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), workflow_id))
            sys.exit(1)
    else:
        input_ports = input_ports_prev
        output_ports = output_ports_prev

    prev_workflow_id = workflow_id
    input_ports_prev = input_ports
    output_ports_prev = output_ports
    tool_names = []
    for item in miwf_contents:
        if ("category" in item) is True:
            if item["category"] == "module" or item["category"] == "workflow":
                if ("name" in item) is True:
                    tool_names.append(item["name"])

    # Runパラメータの構築
    run_params = {}
    run_params["description"] = "API経由ワークフロー実行 %s\n\n"%datetime.datetime.now()
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
                #print("inputfile = %s"%creep_in)
                params["input_data_file"] = base64.b64encode(open(input_params[input_item], "rb").read()).decode('utf-8')
                #print(params["input_data_file"])
            elif target_item[2] == "asset":
                params["asset_id"] = target_item[1]
            elif target_item[2] == "value" or target_item[2] == "bool":
                params["input_data_value"] = target_item[1]
    
            workflow_params.append(params)
            #print(params)
    
    run_params["workflow_parameters"] = workflow_params
    
    # ワークフローの実行
    retry_count = 0
    outfile = open(logfile, "a")
    while True:
        #weburl = "https://%s:50443/workflow-api/v2/runs"%(url)
        weburl = api_url%(url)
        params = {"workflow_id":"%s"%workflow_id}
        res = mintWorkflowAPI(token, weburl, params, json.dumps(run_params), method="post", timeout=(300.0, 300.0), error_print=False)
        
        # 実行の可否
        if res.status_code != 200 and res.status_code != 201:
            if res.status_code is None:         # タイムアウトだった
                sys.stderr.write("%s - 実行できませんでした。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.text))
            elif res.status_code == 400:
                sys.stderr.write("%s - 「%s(%s)」により実行できませんでした。終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.json()["errors"][0]["message"], res.json()["errors"][0]["code"]))
                outfile.write("\n%s - - 「%s(%s)」により実行できませんでした。終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.json()["errors"][0]["message"], res.json()["errors"][0]["code"]))
                outfile.close()
                return
            else:
                sys.stderr.write("%s - False 実行できませんでした。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), json.dumps(res.json(), indent=2, ensure_ascii=False)))
            if number == "-1":
                if retry_count == 1:
                    sys.stderr.write("%s - 実行リトライカウントオーバー。終了します。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                    outfile.write("%s - - 実行リトライカウントオーバー。終了します。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                    outfile.close()
                    return
                else:
                    retry_count += 1
                    sys.stderr.write("%s - ６０秒後、実行リトライ。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                    time.sleep(60)
                    continue
            else:
                # 起動に失敗したら、しばらく待って、tomcat@apiを再実行してまたしばらく待って、続行する。
                print("%s - 60秒後にtomcat@apiを再実行します。"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                time.sleep(60)
                subprocess.call("systemctl restart tomcat@api", shell=True, executable='/bin/bash')
                print("%s - tomcat@apiを再起動しました。120秒後にランを再開します。"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                time.sleep(120)
            return
            
        else:
            # ラン番号の取得
            runid = res.json()["run_id"]
            #print("%s"%json.dumps(res.json(), indent=2, ensure_ascii=False))
            #runid = "http://sipmi.org/workflow/runs/R000010000000403"
            runid = runid.split("/")[-1]
            #print("%s - ワークフロー実行中（%s）"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), runid))
            sys.stdout.write("%s - ワークフロー実行中（%s）\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), runid))
            sys.stdout.flush()
            sys.stderr.write("%s\n"%runid)
            sys.stderr.flush()
            url_runid = int(runid[1:])
            sys.stdout.write("%s - ラン詳細ページ  https://%s/workflow/runs/%s\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), url, url_runid))
            sys.stdout.flush()
            outfile.write("%s - %s :"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), runid))
            for item in input_params:
                if input_params[item] == "initial_setting.dat":
                    continue
                if mimetypes.guess_type(input_params[item])[1] != "None":
                    continue
    
                #print("param file name = %s"%input_params[item])
                #sys.stderr.write("param file name = %s\n"%input_params[item])
                infile = open(input_params[item])
                value = infile.read().split("\n")[0]
                outfile.write("%s=%s,"%(item, value))
                infile.close()
            #outfile.write("\n")
            #outfile.close()
            #status_out("ワークフロー実行中（%s）"%runid)
            if number != "-1":
                return
            break
    
    # ラン終了待機
    start_time = None
    working_dir = None
    #weburl = "https://%s:50443/workflow-api/v2/runs/%s"%(url, runid)
    weburl = api_url%url + "/" + runid
    #print("ワークフロー実行中...")
    while True:
        res = mintWorkflowAPI(token, weburl)
        if res.status_code != 200 and res.status_code != 201 and res.status_code != 204:
            if res.status_code is None:         # タイムアウトだった
                sys.stderr.write("%s - タイムアウトしました。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.text))
                sys.stderr.flush()
            else:
                sys.stderr.write("%s - 異常な終了コードを受信しました(%d)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.status_code))
                sys.stderr.flush()
            time.sleep(120)
            continue
        retval = res.json()
        if working_dir is None and ("gpdb_url" in retval) is True:
            uuid = retval["gpdb_url"].split("/")[-1].replace("-", "")
            dirname = "/home/misystem/assets/workflow/%s/calculation/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s"%(siteid, uuid[0:2], uuid[2:4], uuid[4:6], uuid[6:8], uuid[8:10], uuid[10:12], uuid[12:14], uuid[14:16], uuid[16:18], uuid[18:20], uuid[20:22], uuid[22:24], uuid[24:26], uuid[26:28], uuid[28:30], uuid[30:32])
            sys.stdout.write("%s - 実行ディレクトリ %s\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), dirname))
            sys.stdout.flush()
            working_dir = dirname
        if retval["status"] == "running" or retval["status"] == "waiting" or retval["status"] == "paused":
            # タイムアウト判定用の開始時間(wating=TorqueによるQueue待ち時間を除くため)
            if start_time is None and retval["status"] == "running":
                start_time = datetime.datetime.now()
            # タイムアウト判定
            if timeout is not None and retval["status"] == "running":
                estimated = datetime.datetime.now() - start_time
                if estimated > timeout: 
                    sys.stderr.write("%s - 実行中のままタイムアウト時間を越えました。(%d) 終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.status_code))
                    sys.stderr.flush()
                    outfile.write(" 実行中のままタイムアウト時間を越えました。(%s : %d) 終了します。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.status_code))
                    outfile.close()
                    sys.exit(1)
            pass
        elif retval["status"] == "abend" or retval["status"] == "canceled":
            if retval["status"] == "abend":
                sys.stderr.write("%s - ランが異常終了しました。実行を終了します。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                sys.stderr.flush()
                outfile.write(" ランが異常終了しました。実行を終了します。(%s)\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
            else:
                sys.stderr.write("%s - ランがキャンセルされました。実行を終了します。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                sys.stderr.flush()
                outfile.write(" ランがキャンセルされました。実行を終了します。(%s)\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))

            get_rundetail(token, url, siteid, runid, False, tool_names, False)
            outfile.close()
            sys.exit(1)
        else:
            #print("ラン実行ステータスが%sに変化したのを確認しました"%retval["status"])
            sys.stdout.write("%s - ラン実行ステータスが%sに変化したのを確認しました\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), retval["status"]))
            sys.stdout.flush()
            if retval["status"] != "completed":
                sys.stderr.write("%s - ランは正常終了しませんでした。\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
                sys.stderr.flush()
                outfile.write(" ランは正常終了しませんでした。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
                outfile.close()
                sys.exit(1)
                get_rundetail(token, url, siteid, runid, False, tool_names, False)
            break
    
        time.sleep(5)      # 問い合わせ間隔30秒
    #
    #print("ワークフロー実行終了")
    sys.stdout.write("%s - ワークフロー実行終了\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    sys.stdout.flush()
    outfile.write(" ワークフロー実行終了(%s)\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
    outfile.close()
    
    #time.sleep(10)
    # 結果ファイルの取得
    #weburl = "https://%s:50443/workflow-api/v2/runs/%s/data"%(url, runid)
    weburl = api_url%url + "/%s/data"%runid
    if downloaddir is None:
        os.mkdir("/tmp/%s"%runid)
    else:
        if os.path.exists(downloaddir) is False:
            os.mkdir("./%s"%downloaddir)
        os.mkdir("./%s/%s"%(downloaddir, runid))
    retry_count = 0
    while True:
        if STOP_FLAG is True:
            sys.exit(1)
        res = mintWorkflowAPI(token, weburl)
        if res.status_code != 200 and res.status_code != 201:
            if res.status_code is None:         # タイムアウトだった
                sys.stderr.write("%s - タイムアウトしました。(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.text))
                sys.stderr.flush()
            elif res.status_code == 500:
                #sys.stderr.write("%s\n"%res.text)
                sys.stderr.write("%s\n"%json.dumps(res.json(), indent=2, ensure_ascii=False))
            else:
                sys.stderr.write("%s\n"%json.dumps(res.json(), indent=2, ensure_ascii=False))
            if retry_count == 5:
                sys.stderr.write("%s - 結果取得失敗。終了します。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                sys.stderr.flush()
                get_rundetail(token, url, siteid, runid, False, tool_names, False)
                sys.exit(1)
            else:
                sys.stderr.write("%s - 結果取得失敗。５分後に再取得を試みます。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                sys.stderr.flush()
                time.sleep(300.0)
            retry_count += 1
            continue
        wf_tools = res.json()["url_list"][0]['workflow_tools'] 
        outputfilenames = {}
        if len(wf_tools) == 0:
            sys.stderr.write("%s - 結果を取得できなかった？\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
            sys.stderr.flush()
            #sys.exit(1)
            continue
        get_file = False
        # tool_outputsが取得できたかどうか
        all_null = True
        for tool in wf_tools:
            tool_outputs = tool["tool_outputs"]
            if len(tool_outputs) == 0:
                pass
            else:
                all_null = False

        if all_null is True:
            if retry_count == 5:
                sys.stderr.write('tool["tool_outputs"] が空？取得できませんでした。終了します。\n')
                sys.stderr.flush()
                get_rundetail(token, url, siteid, runid, False, tool_names, False)
                sys.exit(1)
            else:
                sys.stderr.write('モジュール名(%s)のtool["tool_outputs"] が空？５秒後に再取得します。\n'%tool["tool_name"])
                sys.stderr.flush()
                time.sleep(5.0)
                retry_count += 1
            continue
        # ここまでくれば情報取得成功？
        break

    for tool in wf_tools:
        tool_outputs = tool["tool_outputs"]
        for item in tool_outputs:
            if downloaddir is None:
                filename = "/tmp/%s/%s"%(runid, item["parameter_name"])
            else:
                filename = "./%s/%s/%s"%(downloaddir, runid, item["parameter_name"])
            outputfilenames[item["parameter_name"]] = filename
            #print("outputfile:%s"%item["file_path"])
            #sys.stderr.write("file size = %s\n"%item["file_size"])
            weburl = item["file_path"]
            sys.stdout.write("%s - %s 取得中...\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), item["parameter_name"]))
            sys.stdout.flush()
            # sile_sizeが無いポートの対処
            if ("file_size" in item) is False:
                sys.stderr.write("%s - ファイルサイズが取得できないので、ファイルを取得しません。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                sys.stderr.write("URL は %s\n"%weburl)
                sys.stderr.flush()
                if len(tool_outputs) == 1:
                    get_file = True
                continue
            filesize = int(item["file_size"])
            # ファイルサイズで取得するしないを判定する。基準は１Gバイト
            if filesize > (1024 * 1024 * 1024):
                sys.stderr.write("%s - ファイルサイズが１Ｇバイトを越えるので、取得しません。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                sys.stderr.write("file size = %s\n"%item["file_size"])
                sys.stderr.write("URL は %s\n"%weburl)
                sys.stderr.flush()
                continue
            if len(weburl.split("/")) == 7:
                sys.stderr.write("file_size(%d)はあるが、URL(%s)が不完全なので取得しません。\n"%(item["file_size"], weburl))
                sys.stderr.flush()
                continue
            while True:
                try:
                    timeout = (10.0, 600.0)
                    res = mintWorkflowAPI(token, weburl, method="get_noheader", timeout=timeout)
                except MemoryError:
                    sys.stderr.write("%s\n"%traceback.format_exc())
                    sys.stderr.write("%s - ファイルの取得に失敗しました(MemoryError)\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
                    sys.stderr.write("file size = %s\n"%item["file_size"])
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
                sys.stderr.write("%sのファイルの保存に失敗しました\n"%item["parameter_name"])
                sys.stderr.write("file size = %s\n"%item["file_size"])
                sys.stderr.flush()
            sys.stdout.write("%s:%s\n"%(item["parameter_name"], filename))
            sys.stdout.flush()
            #print("%s:%s"%(item["parameter_name"], filename))
            #print("%s:%s"%(item["parameter_name"], res.text))
            get_file = True
         
#        if get_file is True:
#            break

def wait_running_number_api(url, token, number):
    '''
    現在実行中(runningまたはwating)のランの数がnumber以下になるまで待つ。API版
    '''

    global STOP_FLAG
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'Accept': 'application/json'}
    session = requests.Session()
    #weburl = "https://%s:50443/workflow-api/v2/runs"%url
    weburl = api_url%url

    number = int(number)
    while True:
        if STOP_FLAG is True:
            print("")
            sys.exit(0)

        ret = session.get(weburl, headers=headers)
        if ret.status_code != 200 and ret.status_code != 201:
            sys.stderr.write("システム異常？(%d)終了します。"%ret.status_code)
            sys.exit(1)
        else:
            running = []
            runs = ret.json()["runs"]
            for item in runs:
                if item["status"] == "running" or item["status"] == "waiting":
                    running.append(item)
        if len(running) <= number:
            return
        else:
            print(".", flush=True, end="")
            time.sleep(300)

def wait_running_number_db(number):
    '''
    現在実行中(runningまたはwating)のランの数がnumber以下になるまで待つ。mysql直接版
    '''

    global STOP_FLAG

    number = int(number)
    while True:
        if STOP_FLAG is True:
            print("")
            sys.exit(0)

        db = mysql.connector.connect(host="127.0.0.1", user="root", password="P@ssw0rd")
        cursor = db.cursor()
        cursor.execute("use workflow")
        cursor.execute("""select count(run_id) from workflow.run where run_status = 1 and deleted = 0;""")
        rows = cursor.fetchall()
        cursor.close()
        db.close()

        if rows[0][0] <= number:
            return
        else:
            print(".", flush=True, end="")
            time.sleep(300)

def main():
    '''
    '''

    token = None
    input_params = {}
    workflow_id = None
    seed = None
    number = "-1"
    timeout = None
    siteid = "site00002"
    description = None
    downloaddir = None
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
        elif items[0] == "number":              # 回数指定
            number = items[1]
        elif items[0] == "seed":                # random種の指定
            seed = items[1]
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
        else:
            input_params[items[0]] = items[1]   # 与えるパラメータ

    if token is None or workflow_id is None or url is None:
        print("Usage")
        print("   $ python %s workflow_id:Mxxxx token:yyyy misystem:URL <port-name>:<filename for port> ..."%(sys.argv[0]))
        print("          workflow_id : 必須 Rで始まる15桁のランID")
        print("               token  : 必須 64文字のAPIトークン")
        print("             misystem : 必須 dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        print("    <port-name>:<filename for port> : ポート名とそれに対応するファイル名を必要な数だけ。")
        print("                      : 必要なポート名はworkflow_params.pyで取得する。")
        print("              timeout : 連続実行でない場合に、実行中のままこの時間（秒指定）を越えた場合に、キャンセルして終了する。")
        print("          description : ランの説明に記入する文章。")
        print("          downloaddir : 実行完了後の出力ポートファイルのダウンロード場所の指定（指定はカレントディレクトリ基準）")
        print("                        downloaddir/<RUN番号>/ポート名")
        print("                        デフォルトは/tmp/<RUN番号>ディレクトリ")
        sys.exit(1)

    '''
    numberの回数分WFを実行する。
    '''

    if seed is None:
        random.seed(time.time())
    else:
        random.seed(seed)

    signal.signal(signal.SIGINT, signal_handler)

    #for i in range(int(number)):
    i = 1
    while True:
        for item in input_params:
            if item == "経過温度" or item == "等温時効":
                outfile = open(input_params[item], "w")
                temp = 973.0 + random.uniform(-100, 100)
                outfile.write("%0.2f\n"%temp)
                outfile.close()
            elif item == "析出相の体積分率":
                outfile = open(input_params[item], "w")
                value = 0.165 + (0.165 * random.uniform(-10,10) / 100)
                outfile.write("%0.3f\n"%value)
                outfile.close()

        if number != "-1":
            # 同時実行数がnumber以下になるまで待つ。
            print("waiting run number under %s..."%number, flush=True, end=""),
            if STOP_FLAG is True:
                print("")
                break
            if has_mysql is True:
                wait_running_number_db(number)
            else:
                wait_running_number(url, token, number)
            print("\n------ %06s -------"%i)
        workflow_run(workflow_id, token, url, input_params, number, timeout, seed, siteid, description, downloaddir)
        time.sleep(1.0)
        if number == "-1":
            break
        print("Next workflow will start after 30 seconds")
        #time.sleep(10)             # 次のランを10秒後に実行する
        i += 1

if __name__ == '__main__':
    main()
