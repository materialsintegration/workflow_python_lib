#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
ワークフローを登録する
'''

import sys
import json
import datetime

from common_lib import mintWorkflowAPI

CHARSET_DEF = 'utf-8'

api_url = "https://%s:50443/workflow-api/%s/workflows"


def workflow_create(token, url, name, description, prediction_model_id, reference_workflow_id,
                    reference_workflow_revision, miwf, version):
    '''
    ワークフロー登録
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param name (string) 登録するワークフロー名
    @param description (string) 登録するワークフローの説明
    @param prediction_model_id (string) 登録するワークフローに設定する予測モデルID。URI形式
    @param reference_workflow_id (string) 登録するワークフローに関連付けたいワークフローID。URI形式
    @param reference_workflow_revision (int) 関連付けたいワークフローのリビジョン番号
    @param miwf (json) 登録するワークフローに設定する、ワークフロー定義
    @param version (string) ワークフローAPIのバージョン。vを付けること
    @retval ワークフローID（W+15桁の数値）(string)
    '''

    workflow_id = None

    # パラメータの構築
    add_params = {}
    add_params["name"] = name
    add_params["description"] = description
    add_params["prediction_model_id"] = prediction_model_id
    add_params["reference_workflow_id"] = reference_workflow_id
    add_params["reference_workflow_revision"] = reference_workflow_revision
    add_params["miwf"] = miwf

    # ワークフローの登録
    weburl = api_url % (url, version)
    params = {}
    res = mintWorkflowAPI(token, weburl, params, json.dumps(add_params), method="post",
                          timeout=(300.0, 300.0), error_print=False)

    # 実行結果チェック
    endtime = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    if res.status_code != 200 and res.status_code != 201:
        if res.status_code is None:         # タイムアウトだった
            sys.stderr.write("%s - 登録できませんでした。(%s)\n" % (endtime, res.text))
            sys.stderr.flush()
        else:
            sys.stderr.write("%s - 登録できませんでした。(%s)\n" % (endtime, json.dumps(res.json(),
                                                                             indent=2,
                                                                             ensure_ascii=False)))
    else:
        # ワークフローIDの取得
        workflow_id = res.json()["workflow_id"]

        sys.stdout.write("%s - ワークフロー登録終了 - %s\n" % (endtime, workflow_id))
        sys.stdout.flush()

        # URI形式からID部分のみ切り出し
        workflow_id = workflow_id.split("/")[-1]

    return workflow_id


def main():
    """
    メイン処理.

    """
    token = None
    url = None
    name = None
    description = None
    prediction_model_id = None
    reference_workflow_id = None
    reference_workflow_revision = None
    miwf_file = None
    miwf = None
    wf_api_version = "v4"

    for i in range(1, len(sys.argv)):
        item = sys.argv[i]
        print(item)

        items = []
        items.append(item[0:item.index(":")])
        items.append(item[item.index(":") + 1:])

        if items[0] == "token":                 # APIトークン
            token = items[1]
        elif items[0] == "misystem":            # 環境指定(開発？運用？NIMS？東大？)
            url = items[1]
        elif items[0] == "name":                # ワークフロー名
            name = items[1]
        elif items[0] == "description":         # ワークフローの説明
            description = items[1]
        elif items[0] == "prediction_model_id":           # 設定する予測モデルID
            prediction_model_id = items[1]
        elif items[0] == "reference_workflow_id":         # 設定する予測モデルID
            reference_workflow_id = items[1]
        elif items[0] == "reference_workflow_revision":   # 設定する予測モデルID
            reference_workflow_revision = items[1]
        elif items[0] == "miwf_file":          # ワークフロー定義ファイル名
            miwf_file = items[1]
        elif items[0] == "wf_api_version":     # ワークフローAPIバージョン(vを付けること)。未指定時のデフォルト値はv4
            wf_api_version = items[1]

    if token is None or name is None or url is None:
        print("Usage")
        print("   $ python %s token:yyyy misystem:URL name:workflow_name ..." % (sys.argv[0]))
        print("                     token  : 必須 64文字のAPIトークン")
        print("                   misystem : 必須 dev-u-tokyo.mintsys.jpのようなMIntシステムのURL")
        print("                       name : 必須 登録するワークフロー名")
        print("                description : 登録するワークフローの説明")
        print("        prediction_model_id : 登録するワークフローに設定する予測モデルID。URI形式")
        print("      reference_workflow_id : 登録するワークフローに関連付けたいワークフローID。URI形式")
        print("reference_workflow_revision : 関連付けたいワークフローのリビジョン番号(数値)")
        print("                  miwf_file : 登録するワークフローに設定する、ワークフロー定義ファイル名")
        print("             wf_api_version : ワークフローAPIバージョン(vを付けること)。未指定時のデフォルト値はv4")
        sys.exit(1)

    # ワークフロー定義ファイル読み込み
    if miwf_file:
        with open(miwf_file, 'r', encoding=CHARSET_DEF) as f:
            miwf = json.load(f)

    # ワークフロー登録
    workflow_id = workflow_create(token, url, name, description, prediction_model_id,
                                  reference_workflow_id, reference_workflow_revision, miwf,
                                  wf_api_version)

    if workflow_id is None:
        sys.exit(1)


if __name__ == '__main__':
    main()
