#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

'''
WF-API呼び出し共通部品
'''

import sys, os
import requests
import json
import datetime
import base64
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

def mintWorkflowAPI(token, weburl, params=None, invdata=None, json=None, method="get", timeout=(10.0, 30.0), error_print=True):
    '''
    API呼び出し
    2020/08/17: Y.Manaka 関数名変更のためラッパーを作成する
    '''

    return nodeREDWorkflowAPI(token, weburl, params, invdata, json, method, timeout, error_print)

    # ヘッダー
def nodeREDWorkflowAPI(token, weburl, params=None, invdata=None, json=None, method="get", timeout=(10.0, 30.0), error_print=True):
    '''
    API呼び出し
    '''

    # 2020/08/17 半年後くらいをめどに削除予定なのでメッセージを埋め込む
    warn_msg = "`nodeREDWorkflowAPI`関数は2020年度中に削除予定です。"
    warnings.warn(warn_msg, UserWarning)

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
    elif method == "get_noheader":
        try:
            res = session.get(weburl, data=invdata, timeout=timeout)
        except requests.ConnectTimeout:
            res = timeout_object()
            res.text = "サーバーに接続できませんでした（timeout = %s秒)"%timeout[0]
        except requests.ReadTimeout:
            res = timeout_object()
            res.text = "サーバーから応答がありませんでした（timeout = %s秒)"%timeout[1]
    elif method == "post":
        try:
            res = session.post(weburl, data=invdata, headers=headers, params=params, timeout=timeout)
        except requests.ConnectTimeout:
            res = timeout_object()
            res.text = "サーバーに接続できませんでした（timeout = %s秒)"%timeout[0]
        except requests.ReadTimeout:
            res = timeout_object()
            res.text = "サーバーから応答がありませんでした（timeout = %s秒)"%timeout[1]
    elif method == "put":
        try:
            res = session.put(weburl, data=invdata, headers=headers, params=params, json=json, timeout=timeout)
        except requests.ConnectTimeout:
            res = timeout_object()
            res.text = "サーバーに接続できませんでした（timeout = %s秒)"%timeout[0]
        except requests.ReadTimeout:
            res = timeout_object()
            res.text = "サーバーから応答がありませんでした（timeout = %s秒)"%timeout[1]
    
    if res.status_code != 200 and res.status_code != 201:
        if error_print is True:
            print("error   : ")
            print('status  : ' + str(res.status_code))
            print('body    : ' + res.text)
            print('-------------------------------------------------------------------')
            print('url     : ' + weburl)
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
