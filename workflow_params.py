#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
ワークフローAPIを使用して、指定されたワークフローの入出力ポート名情報を出力する
'''

import sys, os
import json
import datetime
import base64
import time

sys.path.append("~/assets/modules/workflow_python/lib")
from common_lib import *
from openam_operator import openam_operator

CHARSET_DEF = 'utf-8'

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

def extract_workflow_params(workflow_id, token, url, port="50443", version="v3"):
    '''
    ワークフロー詳細情報を取得
    @param workflow_id (string) ワークフローID。e.g. W000020000000197
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    '''

    retry_count = 0
    while True:
        weburl = "https://%s:%s/workflow-api/%s/workflows/%s"%(url, port, version, workflow_id)
        res = mintWorkflowAPI(token, weburl)

        retry_count += 1
        if res.status_code != 200 and res.status_code != 201:
            if res.status_code == 401 and res.json()["errors"][0]["code"] == "0002":
                sys.stderr.write("%s - api failed(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), res.json()["errors"][0]["message"]))
                sys.stderr.flush()
                return False, None, None
            if retry_count > 5:
                sys.stderr.write("%s - cannot get workflow infomation for workflow_id(%s). reached retry count, giving up.\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), workflow_id))
                return False, None, None
            else:
                sys.stderr.write("%s - cannot get workflow infomation for workflow_id(%s). wating 5 minuts.\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), workflow_id))
                time.sleep(300)
                continue

        retval = res.json()
    
        revision = 0
        # 最新リビジョンの情報を取得するための検索
        if ("revisions" in retval) is True:
            for item in retval["revisions"]:
                if item["workflow_revision"] > revision:
                    revision = item["workflow_revision"]
        else:
            if retry_count > 5:
                sys.stderr.write("%s - cannot get workflow infomation for workflow_id(%s/revisions). reached retry count, giving up.\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), workflow_id))
                return False, None, None
            else:
                sys.stderr.write("%s - cannot get workflow infomation for workflow_id(%s/revisions). wating 5 minuts.\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), workflow_id))
                time.sleep(300)
                continue
        
        # 最新リビジョンのmiwfを取得する
        miwf_contents = None
        if ("revisions" in retval) is True:
            for item in retval["revisions"]:
                if item["workflow_revision"] == revision:
                    miwf_contents = item["miwf"]["mainWorkflow"]["diagramModel"]["nodeDataArray"]
        else:
            if retry_count > 5:
                sys.stderr.write("%s - cannot get workflow infomation for workflow_id(%s/contents of miwf). reached retry count, giving up.\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), workflow_id))
                return False, None, None
            else:
                sys.stderr.write("%s - cannot get workflow infomation for workflow_id(%s/contents of miwf). wating 5 minuts.\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), workflow_id))
                time.sleep(300)
                continue
        
        #print(json.dumps(miwf_contents, ensure_ascii=False, indent=4))
        
        # 各ポート情報を取得する
        input_ports = []
        output_ports = []
        for item in miwf_contents:
            if item["category"] == "inputdata":
                #print("port name = %s"%item["name"])
                input_ports.append([item["name"], item["descriptor"], item["paramtype"], item["required"]])
            if item["category"] == "inputlist":
                input_ports.append([item["name"], item["descriptor"], item["paramtype"], item["required"]])
        
        for item in miwf_contents:
            if item["category"] == "outputdata":
                output_ports.append([item["name"], item["descriptor"], item["paramtype"]])

        break
    return miwf_contents, input_ports, output_ports

def main():
    '''
    開始点
    '''

    token = None
    input_params = {}
    workflow_id = None
    seed = None
    number = "0"
    version = "v3"
    config = None
    conf_file = None
    port = "50443"

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
        elif items[0] == "version":             # APIバージョン指定
            version = items[1]
        elif items[0] == "conf":                # 構成ファイル
            conf_file = items[1]
        elif items[0] == "port":
            port = items[1]
        else:
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
            elif item == "version":
                version = config["version"]
            elif item == "port":
                port = config["port"]
            else:
                sys.stderr.write("未知のキー(%s)です。"%item)
                sys.stderr.flush()

    if workflow_id is None or url is None:
        print("Usage")
        print("   $ python %s workflow_id:Mxxxx token:yyyy misystem:URL"%(sys.argv[0]))
        print("          workflow_id : Mで始まる16桁のワークフローID")
        print("               token  : 64文字のAPIトークン")
        print("             misystem : dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        print("               conf   : 構成ファイルの指定")
        sys.exit(1)

    # APIトークンの取得
    if token is None:
        uid, token = openam_operator.miLogin(url, "ログイン情報入力")

    if token is None:
        os.stderr.write("ログインに失敗しました。\n")
        os.stderr.flush()
        sys.exit(1)

    miwf, input_ports, output_ports = extract_workflow_params(workflow_id, token, url, port, version)

    print("input parameters")
    for item in input_ports:
        print("port = %s(%s)"%(item[0], item[3]))
    print("output for results")
    for item in output_ports:
        print("port = %s(%s)"%(item[0], item[2]))


if __name__ == '__main__':
    main()
