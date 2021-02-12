#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
WF-API呼び出し共通部品
'''

import sys, os
import requests
import json
import datetime
import base64
import codecs
import warnings
if os.name == "nt":
    import openam_operator
else:
    from openam_operator import openam_operator     # MIシステム認証ライブラリ
from getpass import getpass

class timeout_object(object):
    '''
    タイムアウト時にrequestsのレスポンスオブジェクトと似たような振る舞いをするオブジェクト
    '''

    def __init__(self):
        '''
        コンストラクタ

        '''
        self.status_code = None
        self.text = "Timeout"

class connection_error_object(object):
    '''
    接続エラーのための擬似応答オブジェクト
    '''

    def __init__(self):
        '''
        コンストラクタ

        '''
        self.status_code = "-1"
        self.text = ""
        
def getRunUUID(run_id):
    '''
    DBからrun_idに対応する内部ランID（internal_run_id）を取得する。
    '''

    db=mysql.connector.connect(host="127.0.0.1", user="root", password="P@ssw0rd")
    cursor = db.cursor()

def getAuthInfo(url=None):
    '''
    ログイン関数
    '''

    if url is None:
        return False, None, "{'message':'URLが指定されていません'}"

    #print("予測モデルを取得する側のログイン情報入力")
    if sys.version_info[0] <= 2:
        name = raw_input("ログインID: ")
    else:
        name = input("ログインID: ")
    password = getpass("パスワード: ")

    ret, uid, token = openam_operator.miauth(url, name, password)

    return ret, uid, token

def nodeREDWorkflowAPI(token, weburl, params=None, invdata=None, json=None, method="get", timeout=(10.0, 30.0), error_print=True):
    '''
    API呼び出し
    2020/08/17: Y.Manaka 関数名変更のためラッパーを作成する
    '''

    # 2020/08/17 半年後くらいをめどに削除予定なのでメッセージを埋め込む
    warn_msg = "`nodeREDWorkflowAPI`関数は2020年度中に削除予定です。\n変わりに mintWorkflowAPIを使ってください。"
    warnings.warn(warn_msg, UserWarning)

    return mintWorkflowAPI(token, weburl, params, invdata, json, method, timeout, error_print)

def mintWorkflowAPI(token, weburl, params=None, invdata=None, json=None, method="get", timeout=(10.0, 30.0), error_print=True):
    '''
    API呼び出し
    '''

    # ヘッダー
    headers = {'Authorization': 'Bearer ' + token,
               'Content-Type': 'application/json',
               'Accept': 'application/json'}

    #print("header = %s"%str(headers))
    #print("requestBody = %s"%str(invdata))
    # http request
    session = requests.Session()
    session.trust_env = False

    if method == "get":
        try:
            res = session.get(weburl, data=invdata, headers=headers, timeout=timeout)
        except requests.ConnectTimeout:
            res = timeout_object()
            res.text = "サーバーに接続できませんでした（timeout = %s秒)"%timeout[0]
        except requests.ReadTimeout:
            res = timeout_object()
            res.text = "サーバーから応答がありませんでした（timeout = %s秒)"%timeout[1]
        except requests.ConnectionError as e:
            res = connection_error_object()
            res.text += "\n%s"%e
    elif method == "get_noheader":
        try:
            res = session.get(weburl, data=invdata, timeout=timeout)
        except requests.ConnectTimeout:
            res = timeout_object()
            res.text = "サーバーに接続できませんでした（timeout = %s秒)"%timeout[0]
        except requests.ReadTimeout:
            res = timeout_object()
            res.text = "サーバーから応答がありませんでした（timeout = %s秒)"%timeout[1]
        except requests.ConnectionError as e:
            res = connection_error_object()
            res.text += "\n%s"%e
    elif method == "post":
        try:
            res = session.post(weburl, data=invdata, headers=headers, params=params, timeout=timeout)
        except requests.ConnectTimeout:
            res = timeout_object()
            res.text = "サーバーに接続できませんでした（timeout = %s秒)"%timeout[0]
        except requests.ReadTimeout:
            res = timeout_object()
            res.text = "サーバーから応答がありませんでした（timeout = %s秒)"%timeout[1]
        except requests.ConnectionError as e:
            res = connection_error_object()
            res.text += "\n%s"%e
    elif method == "put":
        try:
            res = session.put(weburl, data=invdata, headers=headers, params=params, json=json, timeout=timeout)
        except requests.ConnectTimeout:
            res = timeout_object()
            res.text = "サーバーに接続できませんでした（timeout = %s秒)"%timeout[0]
        except requests.ReadTimeout:
            res = timeout_object()
            res.text = "サーバーから応答がありませんでした（timeout = %s秒)"%timeout[1]
        except requests.ConnectionError as e:
            res = connection_error_object()
            res.text += "\n%s"%e
    
    if res.status_code != 200 and res.status_code != 201:
        if error_print is True:
            sys.stderr.write("%s - \n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
            sys.stderr.write("error   : \n")
            sys.stderr.write('status  : %s\n'%str(res.status_code))
            sys.stderr.write('body    : %s\n'%res.text)
            sys.stderr.write('-------------------------------------------------------------------\n')
            sys.stderr.write('url     : %s\n'%weburl)
            #return False, res
            #sys.exit(1)

    return res

def error_print(res):
    '''
    レスポンスボディのエラー表示
    '''

    print("error   : ")
    print('status  : ' + str(res.status_code))
    print('body    : ' + res.text)
    print('-------------------------------------------------------------------')
    print('url     : ' + weburl)
