#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

'''
Node-REDからWF-API経由で指定されたワークフローをJSON形式で保存するスクリプト
※　流用品なので不要な部分が多く残っている
'''

import sys, os
import json
import datetime
import base64
import time
from common_lib import *
import random
import subprocess

prev_workflow_id = None
prev_workflow_info = None

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

def workflow_run(workflow_id, token, url, input_params, number, seed=None):
    '''
    ワークフロー実行
    '''

    global prev_workflow_id
    global prev_workflow_info
    logfile = "workflow_exec.%s.log"%url
    workflow_file = "workflow_%s.json"%workflow_id

    # 前回と同じworkflow_idなら詳細を取得しない。
    if prev_workflow_id != workflow_id:
        weburl = "https://%s:50443/workflow-api/v2/workflows/%s"%(url, workflow_id)
        res = nodeREDWorkflowAPI(token, weburl)
        retval = res.json()
    else:
        retval = prev_workflow_info

    outfile = open(workflow_file, "w")
    outfile.write(json.dumps(retval))
    outfile.close
    sys.exit(0)                                         # ここで終了

def main():
    '''
    開始点
    '''

    token = None
    input_params = {}
    workflow_id = None
    seed = None
    number = "0"

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
        else:
            input_params[items[0]] = items[1]   # 与えるパラメータ

    workflow_run(workflow_id, token, url, input_params, number, seed)

if __name__ == '__main__':
    main()
