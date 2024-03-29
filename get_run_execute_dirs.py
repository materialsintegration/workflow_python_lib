#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
WF-APIのラン一覧取得からランのリストを取得して、実行時ディレクトリを出力する。
'''

import sys, os
from glob import glob
import subprocess
import datetime
import requests
no_rich = False
try:
    import rich
except:
    no_rich = True

sys.path.append("/home/misystem/assets/modules/workflow_python_lib")
from workflow_runlist import *
from workflow_rundetail import *
from openam_operator import openam_operator

def main():
    '''
    '''

    token = None
    workflow_id = None
    result = False
    extra_cmd = None
    global STOP_FLAG
    run_status = {"completed":"完了",
                  "running":"実行中",
                  "waiting":"待機中"}
    hostid = None
    api_version = "v3"
    start_from = None
    hilite_threashold = None
    only_directory = False

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
        elif items[0] == "excmd":               # 実行中以外の時に実行するコマンドの指定
            extra_cmd = items[1]
        elif items[0] == "threashold":          # 表示する容量をハイライトするしきい値
            hilite_threashold = items[1]
        elif items[0] == "date_from":           # 開始日がこの日付以降のみを対象とする。
            start_from = items[1]
        elif items[0] == "only_directory":      # ディレクトリパスのみ表示して終わり
            only_directory = True
        else:
            input_params[items[0]] = items[1]   # 与えるパラメータ

    if token is None:
        uid, token = openam_operator.miLogin(url, "ログイン情報入力")

    if token is None:
        os.stderr.write("ログインに失敗しました。\n")
        os.stderr.flush()
        sys.exit(1)

    if url == "nims.mintsys.jp" or url == "nims-dev.mintsys.jp":
        hostid = "192.168.1.211"
        api_version = "v6"
    elif url == "u-tokyo.mintsys.jp":
        hostid = "192.168.1.242"
    elif url == "dev-u-tokyo.mintsys.jp":
        hostid = "192.168.1.142"

    if hostid is None:
        os.stderr.write("無効なMIntシステムホスト名です。(%s)\n"%url)
        os.stderr.flush()
        sys.exit(1)

    # ラン一覧を取得する
    headers = {}
    headers["Authorization"] = "Bearer %s"%token
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"
    session = requests.Session()
    print("https://%s:50443/workflow-api/v6/runs"%url)
    print(headers)
    ret = session.get("https://%s:50443/workflow-api/v6/runs"%url, headers=headers)
    if ret.status_code != 200:
        sys.stderr.write("url : %s\nresponse : %s\n"%(url, ret.text))
        sys.stderr.flush()
        return "url : %s\nresponse : %s"%(url, ret.text)
    ## ランIDを得る
    run_dict = ret.json()["runs"]
    run_list = []
    for item in run_dict:
        run = item["run_id"].split("/")[-1]
        run_list.append(run)
    ## ランIDを逆順にする
    run_list.reverse()
    #for run in run_list:
    #    print(run)
    #sys.exit(0)

    outfile = open("gpdb_import.sh", "w")
    outfile.write("#!/bin/bash\n")
    # ランIDの詳細を取得して、gpdb_urlに格納されているURIから実行ディレクトリを得る
    for run_id in run_list:
        #if start_from is not None:
        #    if start_time < run_id["start"]:
        #        pass
        #    else:
        #        #print("run_id : %s は %s より古い(%s)ので対象外です"%(run_id["run_id"], start_time, run_id["start"]))
        #        continue
        #sys.stdout.write("run(%s) 情報："%run_id["run_id"],)
        #sys.stdout.flush()
        #if run_id["deleted"] == "1":
        #    try:
        #        uuid = run_id["uuid"].decode()
        #    except:
        #        uuid = run_id["uuid"]
        #    print("  ランは削除されています。UUID='%s'"%uuid)
        #else:
        #    if only_directory is False:
        #        rundetail = get_rundetail(token, url, siteid, run_id["run_id"], version=api_version)
        #        if rundetail is False:
        #            print("  ランの開始日時：%s"%run_id["start"])
        #            continue
        #        uuid = rundetail["gpdb_url"].split("/")[-1].replace("-", "")
        rundetail = get_rundetail(token, url, siteid, run_id, version=api_version)
        uuid = rundetail["gpdb_url"].split("/")[-1].replace("-", "")
        gpdb_uuid = rundetail["gpdb_url"].split("/")[-1]
        workflow_id = rundetail["workflow_id"].split("/")[-1]
        workflow_revision = rundetail["workflow_revision"]
        #     try:
        #         uuid = run_id["uuid"].decode()
        #     except:
        #         uuid = run_id["uuid"]

        dirname = "/home/misystem/assets/workflow/%s/calculation/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s"%(siteid, uuid[0:2], uuid[2:4], uuid[4:6], uuid[6:8], uuid[8:10], uuid[10:12], uuid[12:14], uuid[14:16], uuid[16:18], uuid[18:20], uuid[20:22], uuid[22:24], uuid[24:26], uuid[26:28], uuid[28:30], uuid[30:32])
        if only_directory is True:
            sys.stderr.write("%s - %s\n"%(run_id["run_id"], dirname))
            sys.stderr.flush()
            continue
        #os.chdir(dirname)
        if os.path.exists(dirname) is False:
            print("%s はありません"%dirname)
            continue
        else:
            outfile.write("# workflow_id = %s / Run = %s "%(workflow_id, run_id))
            if rundetail["status"] == "abend":
                outfile.write("ランは異常終了しています。\n")
            elif rundetail["status"] == "canceled":
                outfile.write("ランはキャンセルされてます。\n")
                continue
            elif rundetail["status"] == "failure":
                outfile.write("ランは起動失敗しています。\n")
                continue
            elif rundetail["status"] == "completed":
                outfile.write("ランは完了しています。(%s)\n"%rundetail["status"])
            else:
                outfile.write("ランは%s状態です。\n"%run_status[rundetail["status"]])
        result_file = "%s/%s_result.csv"%(dirname, gpdb_uuid)
        attrib_file = "%s/%s_attribute.csv"%(dirname, gpdb_uuid)
        outfile.write("../gpdb-importer.sh %s %s %s -charset UTF8 -revision %s -type CALC\n"%(workflow_id, result_file, attrib_file, workflow_revision))
        outfile.flush()
        #if extra_cmd is None:
        #    ret = subprocess.check_output(cmd.split())
        #    amount = ret.decode("utf-8").split("\n")[0]
        #    if no_rich is False and hilite_threashold is not None:
        #        if amount.endswith("K\t.") is True:
        #            s_amount = float(amount.split("K")[0]) * 1024
        #        elif amount.endswith("M\t.") is True:
        #            s_amount = float(amount.split("M")[0]) * 1024 * 1024
        #        elif amount.endswith("G\t.") is True:
        #            s_amount = float(amount.split("G")[0]) * 1024 * 1024 * 1024
        #        elif amount.endswith("T\t.") is True:
        #            s_amount = float(amount.split("T")[0]) * 1024 * 1024 * 1024 * 1024
        #        else:
        #            s_amount = float(amount)
        #        if s_amount > hilite_threashold:
        #            rich.print(" ディレクトリサイズは [bold red]%s[/bold red]"%amount)
        #        else:
        #            print("  ディレクトリサイズは %s"%amount)
        #    else:
        #        print("  ディレクトリサイズは %s"%amount)
        #    print("  ランの開始日時：%s"%run_id["start"])
        #    print("  %s"%dirname)
        #    print("")
        #    continue
        #if run_id["status"] != "running" and run_id["status"] != "waiting":
        #    extra_cmd = extra_cmd.replace("\\", "")
        #    print("  コマンド(%s)実行中"%extra_cmd)
        #    print("  %s"%dirname)
        #    ret = subprocess.run(extra_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #    if ret != "":
        #        sys.stdout.write("  %s"%ret.stdout.decode("utf8"))
        #        sys.stdout.flush()
        #        sys.stderr.write("  %s"%ret.stderr.decode("utf8"))
        #        sys.stderr.flush()
        #    print("")

    outfile.close()

if __name__ == '__main__':
    main()

