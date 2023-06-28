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
import subprocess
import math

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
    cursor.execute("user workflow")
    cursor.execute("""select internal_run_id from run where run_id='""" + run_id + """';""")
    rows = cursor.fetchall()

    result = []
    for item in rows:
        result.append(item)

    cursor.close()
    db.close()

    return result

def getAuthInfo(url=None):
    '''
    ログイン関数
    '''

    if url is None:
        return False, None, "{'message':'URLが指定されていません'}"

    #print("予測モデルを取得する側のログイン情報入力")
    #if sys.version_info[0] <= 2:
    #    name = raw_input("ログインID: ")
    #else:
    #    name = input("ログインID: ")
    #password = getpass("パスワード: ")

    #ret, uid, token = openam_operator.miauth(url, name, password)
    uid, token = openam_operator.miLogin(url, "%s のログイン情報"%url)

    ret = True
    if uid is None:
        ret = False

    return ret, uid, token

def nodeREDWorkflowAPI(token, weburl, params=None, invdata=None, json=None, headers=None, method="get", timeout=(10.0, 30.0), error_print=True):
    '''
    API呼び出し
    2020/08/17: Y.Manaka 関数名変更のためラッパーを作成する
    '''

    # 2020/08/17 半年後くらいをめどに削除予定なのでメッセージを埋め込む
    warn_msg = "`nodeREDWorkflowAPI`関数は2020年度中に削除予定です。\n変わりに mintWorkflowAPIを使ってください。"
    warnings.warn(warn_msg, UserWarning)

    return mintWorkflowAPI(token, weburl, params, invdata, json, headers, method, timeout, error_print)

def mintWorkflowAPI(token, weburl, params=None, invdata=None, json=None, headers=None, method="get", timeout=(10.0, 60.0), error_print=True):
    '''
    API呼び出し
    '''


    if headers is None:
        # ヘッダー
        headers = {'Authorization': 'Bearer ' + token,
               'Content-Type': 'application/json',
               'Accept': 'application/json',
               'Connection': 'close'}

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
            sys.stderr.write("%s - API実行に失敗しました。\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
            #sys.stderr.write("error   : \n")
            sys.stderr.write('status  : %s\n'%str(res.status_code))
            try:
                sys.stderr.write('code    : %s\n'%res.json()["errors"][0]["code"])
                sys.stderr.write('message : %s\n'%res.json()["errors"][0]["message"])
                sys.stderr.write('-------------------------------------------------------------------\n')
                sys.stderr.write('url     : %s\n'%weburl)
            except:
                sys.stderr.write('body    : %s\n'%res.text)
                sys.stderr.write('-------------------------------------------------------------------\n')
                sys.stderr.write('url     : %s\n'%weburl)
            #return False, res
            #sys.exit(1)

    session.close()
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

def utc_to_jst(timestamp_utc):
    '''
    タイムゾーン変換：UTCからJSTへ
    '''
    datetime_utc = datetime.datetime.strptime(timestamp_utc + "+0000", "%Y-%m-%d %H:%M:%S.%f%z")
    datetime_jst = datetime_utc.astimezone(datetime.timezone(datetime.timedelta(hours=+9)))
    timestamp_jst = datetime.datetime.strftime(datetime_jst, '%Y-%m-%d %H:%M:%S.%f')
    return timestamp_jst

def getJstDatetime(utc_time):
    '''
    標準時から日本時間へ変更した、dateteimオブジェクトを返す
    '''

    jst_start_time = utc_time.split("Z")[0] + ".00000"
    jst_start_time = jst_start_time.replace("T", " ")
    retval = utc_to_jst(jst_start_time)
    YYMMDD = retval.split()[0]
    hhmmss = retval.split()[1]
    Y = int(YYMMDD.split("-")[0])
    M = int(YYMMDD.split("-")[1])
    D = int(YYMMDD.split("-")[2])
    h = int(hhmmss.split(":")[0])
    m = int(hhmmss.split(":")[1])
    s = int(hhmmss.split(":")[2].split(".")[0])
    return datetime.datetime(Y, M, D, h, m, s)

def getExecDirName(siteid, internal_run_id):
    '''
    サイトIDとinternal_run_idから実行時ディレクトリ名を組み立てて返す。
    @param siteid(string) e.g. site00011/site00002
    @param internal_run_id(string) workflow.run DBテーブルのinternal_run_id(32文字)の文字列
    @retval (string) 実行時ディレクトリ。/home/misystem/assets/workflow/siteid/calculation/....
    '''

    ret = ""
    if len(siteid) != 9:
        ret = "siteid charactor length is not 9"
        return ret
    if len(internal_run_id) != 32:
        ret = "internal_run id charactor lenth is not 32"
        return ret

    dirname = "/home/misystem/assets/workflow/%s/calculation/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s/%s"%(siteid, internal_run_id[0:2], internal_run_id[2:4], internal_run_id[4:6], internal_run_id[6:8], internal_run_id[8:10], internal_run_id[10:12], internal_run_id[12:14], internal_run_id[14:16], internal_run_id[16:18], internal_run_id[18:20], internal_run_id[20:22], internal_run_id[22:24], internal_run_id[24:26], internal_run_id[26:28], internal_run_id[28:30], internal_run_id[30:32])

    return dirname

def getExecDirUsage(directory_path):
    '''
    directory_pathで与えられたディレクトリの容量をタプルで返す。
    @param directory_path(string)
    @retval tuple 0:du -shコマンドの表示をそのまま。1:単位なし、バイト値、int型に変換した値。
    '''

    if os.path.exists(directory_path) is False:
        return [directory_path,-1]
    if os.path.isdir(directory_path) is False:
        return [directory_path,-2]

    cwd = os.getcwd()
    os.chdir(directory_path)
    cmd = "du -sh"
    ret = subprocess.check_output(cmd.split())
    amount = ret.decode("utf-8").split("\n")[0]
    if amount.endswith("K\t.") is True:
        s_amount = float(amount.split("K")[0]) * 1024
    elif amount.endswith("M\t.") is True:
        s_amount = float(amount.split("M")[0]) * 1024 * 1024
    elif amount.endswith("G\t.") is True:
        s_amount = float(amount.split("G")[0]) * 1024 * 1024 * 1024
    elif amount.endswith("T\t.") is True:
        s_amount = float(amount.split("T")[0]) * 1024 * 1024 * 1024 * 1024
    else:
        s_amount = float(amount)

    os.chdir(cwd)
    return amount, s_amount

def convert_size(size):
    '''
    単位を付与する（主にバイト以降）
    @param size(floatまたはint)
    @retval 単位付与した数字と単位のタプル
    '''

    units = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB")
    i = math.floor(math.log(size, 1024)) if size > 0 else 0
    size = round(size / 1024 ** i, 2)

    return f"{size} {units[i]}"
