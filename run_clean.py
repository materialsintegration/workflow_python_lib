#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

'''
ワークフローIDからランのリストを取得して、特定の作業をする
'''

import sys, os
from glob import glob
import subprocess
import datetime

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
    global STOP_FLAG
    run_status = {"completed":"完了",
                  "running":"実行中",
                  "waiting":"待機中"}

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

    if token is None:
        uid, token = openam_operator.miLogin(url, "ログイン情報入力")

    retval, run_list = get_runlist(token, url, siteid, workflow_id, True)
    cmd = "du -sh"
    if retval is False:
        sys.stderr.write("url : %s\nresponse : %s\n"%(url, run_list.text))
        sys.stderr.flush()
        return "url : %s\nresponse : %s"%(url, run_list.text)

    for run_id in run_list:
        sys.stdout.write("run(%s) 情報："%run_id["run_id"],)
        sys.stdout.flush()
        rundetail = get_rundetail(token, url, siteid, run_id["run_id"])
        #if rundetail["status"] == "abend":
        #    continue
        uuid = rundetail["gpdb_url"].split("/")[-1].replace("-", "")
        #dirname = os.path.join("/home/misystem/assets/workflow/%s/calculation/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s"%(siteid, uuid[0:2], uuid[2:4], uuid[4:6], uuid[6:8], uuid[8:10], uuid[10:12], uuid[12:14], uuid[14:16], uuid[16:18], uuid[18:20], uuid[20:22], uuid[22:24], uuid[24:26], uuid[26:28], uuid[28:30], uuid[30:32]), "W000020000000197/W000020000000197_ＮｉーＡｌのγ’析出組織形成（等温時効）_02")
        dirname = "/home/misystem/assets/workflow/%s/calculation/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s"%(siteid, uuid[0:2], uuid[2:4], uuid[4:6], uuid[6:8], uuid[8:10], uuid[10:12], uuid[12:14], uuid[14:16], uuid[16:18], uuid[18:20], uuid[20:22], uuid[22:24], uuid[24:26], uuid[26:28], uuid[28:30], uuid[30:32])
        os.chdir(dirname)
        ret = subprocess.check_output(cmd.split())
        amount = ret.decode("utf-8").split("\n")[0]

        if rundetail["status"] == "abend":
            print("%s - ランが異常終了しています。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        elif rundetail["status"] == "canceled":
            print("%s - ランがキャンセルされてます。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        elif rundetail["status"] == "failed":
            print("%s - ランが起動失敗しています。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        else:
            print("%s - ランは%s状態です。"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), run_status[rundetail["status"]]))
        print("  ディレクトリサイズは %s"%amount)
        print("  %s"%dirname)

if __name__ == '__main__':
    main()

