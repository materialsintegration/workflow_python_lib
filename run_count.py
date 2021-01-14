#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

'''
ワークフロー一覧から個々のIDによるランの数を返す。
'''

import sys, os
import requests
from workflow_runlist import *
from openam_operator import openam_operator     # MIシステム認証ライブラリ
from common_lib import *

def main():
    '''
    開始点
    '''

    url = None
    token = None
    timeout = None
    siteid = "site00002"

    for items in sys.argv:
        items = items.split(":")
        if len(items) != 2:
            continue
    
        if items[0] == "token":               # APIトークン
            token = items[1]
        elif items[0] == "misystem":            # 環境指定(開発？運用？NIMS？東大？)
            url = items[1]
        elif items[0] == "timeout":             # タイムアウト値
            try:
                timeout = int(items[1])
            except:
                timeout = None
        elif items[0] == "siteid":              # site ID
            siteid = items[1]

    if url is None:
        print("Usage")
        print("   $ python %s token:yyyy misystem:URL"%(sys.argv[0]))
        print("               token  : オプション 64文字のAPIトークン")
        print("             misystem : 必須 dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        sys.exit(1)

    if token is None:
        uid, token = openam_operator.miLogin(url, "MIシステム管理者(%s)のログイン情報"%url)

    weburl = "https://%s:50443/workflow-api/v2/workflows"%url
    res = nodeREDWorkflowAPI(token, weburl)
    items = res.json()["workflows"]
    print(len(items))

    for item in items:
        workflow_id = item["workflow_id"].split("/")[-1]
        retval, ret = get_runlist_fromDB(siteid, workflow_id)
        if len(ret) == 0:
            print("%s はランがありませんでした。"%workflow_id)
        else:
            print("%s は %d個のランがありました"%(workflow_id, len(ret)))

if __name__ == '__main__':

    main()
