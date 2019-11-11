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

def nodeREDWorkflowAPI(token, weburl, params=None, invdata=None, method="get"):
    '''
    API呼び出し
    '''

    # ヘッダー
    headers = {'Authorization': 'Bearer ' + token,
               'Content-Type': 'application/json',
               'Accept': 'application/json'}

    # http request
    session = requests.Session()
    session.trust_env = False

    if method == "get":
        res = session.get(weburl, data=invdata, headers=headers)
    elif method == "get_noheader":
        res = session.get(weburl, data=invdata)
    elif method == "post":
        res = session.post(weburl, data=invdata, headers=headers, params=params)
    
    if res.status_code != 200 and res.status_code != 201:
        print("error   : ")
        print('status  : ' + str(res.status_code))
        print('body    : ' + res.text)
        print('-------------------------------------------------------------------')
        print('url     : ' + weburl)
        #return False, res
        #sys.exit(1)

    return res

