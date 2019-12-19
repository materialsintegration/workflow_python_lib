#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

'''
ワークフローAPIを使用して、指定されたランのステータスを変更する
'''

import sys, os
import json
import datetime
import base64
import time

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

def change_run_status(run_id, token, url):
    '''
    指定されたランのステータスを「canceled」へ変更する。現状これのみの変更が可能な仕様なので固定である。
    @param run_id (string) ランID。e.g. R000020000000197
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    '''

    retry_count = 0
    while True:
        weburl = "https://%s:50443/workflow-api/v2/runs/%s"%(url, run_id)
        data = {"status": "canceled"}
        res = nodeREDWorkflowAPI(token, weburl, json=data, method="put")

        retry_count += 1
        if res.status_code != 200 and res.status_code != 201:
            if retry_count > 5:
                sys.stderr.write("%s - cannot get workflow infomation for run_id(%s). reached retry count, giving up.\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), run_id))
                return False, None, None
            else:
                sys.stderr.write("%s - cannot get workflow infomation for run_id(%s). wating 1 minuts.\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), run_id))
                sys.stderr.write(res.text)
                time.sleep(60)
                continue

        retval = res.json()
        break
    
    return retval

def main():
    '''
    開始点
    '''

    token = None
    input_params = {}
    run_id = None
    seed = None
    number = "0"

    for items in sys.argv:
        items = items.split(":")
        if len(items) != 2:
            continue
    
        if items[0] == "run_id":           # ワークフローID
            run_id = items[1]
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
    
    if token is None or run_id is None or url is None:
        print("Usage")
        print("   $ python %s run_id:Mxxxx token:yyyy misystem:URL"%(sys.argv[0]))
        print("          run_id : Rで始まる16桁のランID")
        print("               token  : 64文字のAPIトークン")
        print("             misystem : dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        sys.exit(1)

    ret = change_run_status(run_id, token, url)

    print(ret)
if __name__ == '__main__':
    main()
