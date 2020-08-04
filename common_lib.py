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

def nodeREDWorkflowAPI(token, weburl, params=None, invdata=None, json=None, method="get", timeout=(10.0, 30.0), error_print=True):
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
