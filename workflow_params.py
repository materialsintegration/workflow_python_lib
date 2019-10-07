#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

'''
Node-REDからWF-API経由で指定されたワークフローを実行するため、パラメータを取得するプログラム
'''

import sys, os
import json
import datetime
import base64
import time
import random
import subprocess

sys.path.append("~/assets/modules/workflow_python/lib")
from common_lib import *

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

def workflow_params(workflow_id, token, url):
    '''
    ワークフロー実行
    '''

    weburl = "https://%s:50443/workflow-api/v2/workflows/%s"%(url, workflow_id)
    res = nodeREDWorkflowAPI(token, weburl)
    retval = res.json()

    revision = 0
    # 最新リビジョンの情報を取得するための検索
    for item in retval["revisions"]:
        if item["workflow_revision"] > revision:
            revision = item["workflow_revision"]
    
    # 最新リビジョンのmiwfを取得する
    miwf_contents = None
    for item in retval["revisions"]:
        if item["workflow_revision"] == revision:
            miwf_contents = item["miwf"]["mainWorkflow"]["diagramModel"]["nodeDataArray"]
    
    #print(json.dumps(miwf_contents, ensure_ascii=False, indent=4))
    
    # 各ポート情報を取得する
    input_ports = []
    output_ports = []
    for item in miwf_contents:
        if item["category"] == "inputdata":
            #print("port name = %s"%item["name"])
            input_ports.append([item["name"], item["descriptor"], item["paramtype"], item["required"]])
    
    for item in miwf_contents:
        if item["category"] == "outputdata":
            output_ports.append([item["name"], item["descriptor"], item["paramtype"]])

    print("input parameters")
    for item in input_ports:
        print("port = %s(%s)"%(item[0], item[3]))
    print("output for results")
    for item in output_ports:
        print("port = %s(%s)"%(item[0], item[2]))

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

    workflow_params(workflow_id, token, url)

if __name__ == '__main__':
    main()
