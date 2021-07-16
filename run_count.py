#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

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
    version = "v3"

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
        elif items[0] == "version":             # バージョン指定
            version = items[1]

    if url is None:
        print("Usage")
        print("   $ python %s token:yyyy misystem:URL"%(sys.argv[0]))
        print("               token  : オプション 64文字のAPIトークン")
        print("             misystem : 必須 dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        print("               siteid : サイトID。開発環境：site00002 運用環境：site00011")
        print("            version   : ワークフローAPIのバージョン指定（デフォルトはv3）")
        sys.exit(1)

    if token is None:
        uid, token = openam_operator.miLogin(url, "MIシステム管理者(%s)のログイン情報"%url)

    weburl = "https://%s:50443/workflow-api/%s/workflows"%(url, version)
    res = mintWorkflowAPI(token, weburl)
    items = res.json()["workflows"]
    print(len(items))

    if url == "nims.mintsys.jp":
        hostid = "192.168.1.231"
    elif url == "u-tokyo.mintsys.jp":
        hostid = "192.168.1.242"
    elif url == "dev-u-tokyo.mintsys.jp":
        hostid = "192.168.1.142"

    for item in items:
        workflow_id = item["workflow_id"].split("/")[-1]
        retval, ret = get_runlist_fromDB(siteid, workflow_id, hostid)
        if len(ret) == 0:
            print("%s はランがありませんでした。"%workflow_id)
        else:
            print("%s は %d個のランがありました"%(workflow_id, len(ret)))

if __name__ == '__main__':

    main()
