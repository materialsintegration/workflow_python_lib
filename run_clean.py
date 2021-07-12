#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
ワークフローIDからランのリストを取得して、特定の作業をする
'''

import sys, os
from glob import glob
import subprocess
import datetime
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
        else:
            input_params[items[0]] = items[1]   # 与えるパラメータ

    # 日付の確認
    if start_from is not None:
        if len(start_from.split("/")) == 3:
            start_time = datetime.datetime(int(start_from.split("/")[0]), int(start_from.split("/")[1]), int(start_from.split("/")[2]))
        else:
            print("日付の指定が間違っています。(年/月/日(%s))"%start_from)
            sys.exit(1)

    # しきい値の確認
    if hilite_threashold is not None:
        if hilite_threashold.endswith("t") is True:
            hilite_threashold = float(hilite_threashold.split("t")[0]) * 1024 * 1024 * 1024 * 1024
        elif hilite_threashold.endswith("T") is True:
            hilite_threashold = float(hilite_threashold.split("T")[0]) * 1024 * 1024 * 1024 * 1024
        elif hilite_threashold.endswith("g") is True:
            hilite_threashold = float(hilite_threashold.split("g")[0]) * 1024 * 1024 * 1024
        elif hilite_threashold.endswith("G") is True:
            hilite_threashold = float(hilite_threashold.split("G")[0]) * 1024 * 1024 * 1024
        elif hilite_threashold.endswith("m") is True:
            hilite_threashold = float(hilite_threashold.split("m")[0]) * 1024 * 1024
        elif hilite_threashold.endswith("M") is True:
            hilite_threashold = float(hilite_threashold.split("M")[0]) * 1024 * 1024
        elif hilite_threashold.endswith("k") is True:
            hilite_threashold = float(hilite_threashold.split("k")[0]) * 1024
        elif hilite_threashold.endswith("K") is True:
            hilite_threashold = float(hilite_threashold.split("K")[0]) * 1024
        else:
            hilite_threashold = float(hilite_threashold)
        if no_rich is True:
            print("Rich パッケージが無いのでハイライトされません")

    if token is None:
        uid, token = openam_operator.miLogin(url, "ログイン情報入力")

    if token is None:
        os.stderr.write("ログインに失敗しました。\n")
        os.stderr.flush()
        sys.exit(1)

    if url == "nims.mintsys.jp":
        hostid = "192.168.1.231"
        api_version = "v4"
    elif url == "u-tokyo.mintsys.jp":
        hostid = "192.168.1.242"
    elif url == "dev-u-tokyo.mintsys.jp":
        hostid = "192.168.1.142"

    if hostid is None:
        os.stderr.write("無効なMIntシステムホスト名です。(%s)\n"%url)
        os.stderr.flush()
        sys.exit(1)

    #retval, run_list = get_runlist(token, url, siteid, workflow_id, True)
    retval, run_list = get_runlist_fromDB(siteid, workflow_id, hostid, True)
    cmd = "du -sh"
    if retval is False:
        sys.stderr.write("url : %s\nresponse : %s\n"%(url, run_list.text))
        sys.stderr.flush()
        return "url : %s\nresponse : %s"%(url, run_list.text)

    for run_id in run_list:
        if start_from is not None:
            if start_time < run_id["start"]:
                pass
            else:
                #print("run_id : %s は %s より古い(%s)ので対象外です"%(run_id["run_id"], start_time, run_id["start"]))
                continue
        sys.stdout.write("run(%s) 情報："%run_id["run_id"],)
        sys.stdout.flush()
        if run_id["status"] == "abend":
            print("%s - ランは異常終了しています。"%run_id["end"])
        elif run_id["status"] == "canceled":
            print("%s - ランはキャンセルされてます。"%run_id["end"])
        elif run_id["status"] == "failure":
            print("%s - ランは起動失敗しています。"%run_id["start"])
        elif run_id["status"] == "completed":
            print("%s - ランは完了しています。(%s)"%(run_id["end"], run_id["completion"]))
        else:
            print("%s - ランは%s状態です。"%(run_id["start"], run_status[run_id["status"]]))
        if run_id["deleted"] == "1":
            try:
                uuid = run_id["uuid"].decode()
            except:
                uuid = run_id["uuid"]
            print("  ランは削除されています。UUID='%s'"%uuid)
        else:
            rundetail = get_rundetail(token, url, siteid, run_id["run_id"], version=api_version)
            if rundetail is False:
                print("  ランの開始日時：%s"%run_id["start"])
                continue

            uuid = rundetail["gpdb_url"].split("/")[-1].replace("-", "")
        #dirname = os.path.join("/home/misystem/assets/workflow/%s/calculation/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s"%(siteid, uuid[0:2], uuid[2:4], uuid[4:6], uuid[6:8], uuid[8:10], uuid[10:12], uuid[12:14], uuid[14:16], uuid[16:18], uuid[18:20], uuid[20:22], uuid[22:24], uuid[24:26], uuid[26:28], uuid[28:30], uuid[30:32]), "W000020000000197/W000020000000197_ＮｉーＡｌのγ’析出組織形成（等温時効）_02")
        dirname = "/home/misystem/assets/workflow/%s/calculation/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s"%(siteid, uuid[0:2], uuid[2:4], uuid[4:6], uuid[6:8], uuid[8:10], uuid[10:12], uuid[12:14], uuid[14:16], uuid[16:18], uuid[18:20], uuid[20:22], uuid[22:24], uuid[24:26], uuid[26:28], uuid[28:30], uuid[30:32])
        os.chdir(dirname)
        if extra_cmd is None:
            ret = subprocess.check_output(cmd.split())
            amount = ret.decode("utf-8").split("\n")[0]
            if no_rich is False and hilite_threashold is not None:
                if amount.endswith("K\t.") is True:
                    s_amount = float(amount.split("K")[0]) * 1024
                elif amount.endswith("M\t.") is True:
                    s_amount = float(amount.split("M")[0]) * 1024 * 1024
                elif amount.endswith("G\t.") is True:
                    s_amount = float(amount.split("G")[0]) * 1024 * 1024 * 1024
                elif amount.endswith("T\t.") is True:
                    s_amount = float(amount.split("T")[0]) * 1024 * 1024 * 1024 * 1024
                else:
                    s_amount = float(amount)
                if s_amount > hilite_threashold:
                    rich.print(" ディレクトリサイズは [bold red]%s[/bold red]"%amount)
                else:
                    print("  ディレクトリサイズは %s"%amount)
            else:
                print("  ディレクトリサイズは %s"%amount)
            print("  ランの開始日時：%s"%run_id["start"])
            print("  %s"%dirname)
            print("")
            continue
        if run_id["status"] != "running" and run_id["status"] != "waiting":
            extra_cmd = extra_cmd.replace("\\", "")
            print("  コマンド(%s)実行中"%extra_cmd)
            print("  %s"%dirname)
            ret = subprocess.run(extra_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if ret != "":
                sys.stdout.write("  %s"%ret.stdout.decode("utf8"))
                sys.stdout.flush()
                sys.stderr.write("  %s"%ret.stderr.decode("utf8"))
                sys.stderr.flush()
            print("")

if __name__ == '__main__':
    main()

