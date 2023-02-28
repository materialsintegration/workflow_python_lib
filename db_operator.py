#!python3.6
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
CSVから選択情報と変更情報を得て、DBから選択情報の該当データを変更情報で書き換える。

１）選択情報
　　・カラムと値（where用）
　　・変更対象カラムのを選択するためのカラム（変更時のwhere用）とその値
２）変更情報
　　・変更対象カラムとその値
　　・変更対象選別は、１）の２つめ利用（where）
'''

import sys, os
import shutil
import json
import datetime
import pandas as pd

try:
    import mysql.connector
except:
    print("mysqlライブラリがありません")
    sys.exit(1)

def view_prediction_module_db(hostID, passwd, db_name, target_table, csv_name):
    '''
    予測モジュールに関するDB変更関数
    @param  hostID(string)
    @param passwd(string)
    @param db_name(string)
    @param target_table(string)
    @retval なし
    '''

    sys.stderr.write("hostid        : %s\n"%hostID)
    sys.stderr.write("password      : %s\n"%passwd)
    sys.stderr.write("db name       : %s\n"%db_name)
    sys.stderr.write("table name    : %s\n"%target_table)
    sys.stderr.write("csv name      : %s\n"%csv_name)

    try:
        db = mysql.connector.connect(host=hostID, user="root", password="%s"%passwd)
    except mysql.connector.errors.ProgrammingError as e:
        sys.stderr.write("%s\n"%e)
        sys.exit(1)
    cursor = db.cursor()
    try:
        cursor.execute("use %s"%db_name)
    except mysql.connector.errors.ProgrammingError as e:
        sys.stderr.write("%s\n"%e)
        sys.exit(1)

    check_list = []
    infile = open(csv_name)
    lines = infile.read().split("\n")
    for item in lines:
        if item == "":
            continue
        check_list.append(item)
    infile.close()

    #sys.stderr.write("%s\n"%check_list)
    #sys.stderr.flush()

    print("%20s,%8s,%20s,%20s"%("予測モジュールID", "version", "pbs_queue", "pbs_node_group"))
    for items in check_list:
        items = items.split(",")
        view_cmd = "select pbs_queue,pbs_node_group from resource_request where "
        view_cmd += 'prediction_module_id = "%s" and version = "%s";'%(items[0], items[1])
        #sys.stderr.write("%s\n"%view_cmd)
        #sys.stderr.flush()
        try:
            cursor.execute(view_cmd)
        except mysql.connector.errors.ProgrammingError as e:
            sys.stderr.write("%s\n"%e)
            sys.exit(1)

        rows = cursor.fetchall()

        for item in rows:
            print("%20s|%8s|%20s|%20s"%(items[0], items[1], item[0], item[1]))

def change_prediction_module_db(hostID, passwd, db_name, target_table, csv_name, dryrun=False):
    '''
    予測モジュールに関するDB変更関数
    @param  hostID(string)
    @param passwd(string)
    @param db_name(string)
    @param target_table(string)
    @param csv_name(string)
    @param dryrun(bool)
    @retval なし
    '''

    print("hostid        : %s"%hostID)
    print("password      : %s"%passwd)
    print("db name       : %s"%db_name)
    print("table name    : %s"%target_table)
    #print("modify column : %s"%modify_column)
    print("params file   : %s"%csv_name)
    # CSVの読み込み
    if os.path.exists(csv_name) is True:
        # ヘッダー：prediction_id,pbs_node_group
        df = pd.read_csv(csv_name)

    # 予測モジュールID,
    try:
        db = mysql.connector.connect(host=hostID, user="root", password="%s"%passwd)
    except mysql.connector.errors.ProgrammingError as e:
        print(e)
        sys.exit(1)
    cursor = db.cursor()
    try:
        cursor.execute("use %s"%db_name)
    except mysql.connector.errors.ProgrammingError as e:
        print(e)
        sys.exit(1)

    for i in range(len(df)):
        where_column = df["where_column"][i]
        if where_column == "":
            print("where句の対象がありません。")
            sys.exit(1)
        update_column = df["update_column"][i]
        update_value = df["update_value"][i]
        #print("予測モジュール：%s"%prediction_id)
        review_cmd = 'select %s from %s where '%(update_column, target_table)
        update_cmd = 'update %s set %s = "%s" where '%(target_table, update_column, update_value)
        where_items = where_column.split(":")
        for i in range(len(where_items)):
            items = where_items[i].split("=")
            if len(items) == 1:
                print("where句の対象(%s)が異常です。"%items)
                sys.exit(1)
            where_column = items[0]
            where_value = items[1]    
            if i == 0:
                update_cmd += '%s = "%s"'%(items[0], items[1])
                review_cmd += '%s = "%s"'%(items[0], items[1])

            else:
                update_cmd += ' and %s = "%s"'%(items[0], items[1])
                review_cmd += ' and %s = "%s"'%(items[0], items[1])
        update_cmd += ";"
        review_cmd += ";"
        #cursor.execute('select %s from %s where prediction_module_id = "%s";'%(modify_column, target_table, prediction_id))
        # ----- 変更前
        if dryrun is True:
            #print("%s"%review_cmd)
            print("%s"%update_cmd)
            continue

        print("--- 変更前の値表示")
        print("%s"%review_cmd)
        try:
            cursor.execute(review_cmd)
        except mysql.connector.errors.ProgrammingError as e:
            print(e)
            sys.exit(1)

        rows = cursor.fetchall()

        for item in rows:
            print(item)

        # 変更中
        print("--- update commandの表示")
        print("%s"%update_cmd)
        #sys.exit(0)
        #continue
        try:
            cursor.execute(update_cmd)
        except mysql.connector.errors.ProgrammingError as e:
            print(e)
            sys.exit(1)
        db.commit()

        print("--- 変更後の値の表示")
        print("%s"%review_cmd)
        try:
            cursor.execute(review_cmd)
        except mysql.connector.errors.ProgrammingError as e:
            print(e)
            sys.exit(1)

        rows = cursor.fetchall()

        for item in rows:
            print(item)

    cursor.close()
    db.close()

def main():
    '''
    開始点
    '''

    hostID = None
    passwd = None
    db_name = None
    modify_column = None
    csv_name = None
    target_table = None

    for i in range(len(sys.argv)):
        if i == 1:
            mode = sys.argv[1]
        elif i == 2:
            hostID = sys.argv[2]
        elif i == 3:
            passwd = sys.argv[3]
        elif i == 4:
            db_name = sys.argv[4]
        elif i == 5:
            target_table = sys.argv[5]
        #elif i == 4:
        #    modify_column = sys.argv[4]
        elif i == 6:
            csv_name = sys.argv[6]

    go_help = False
    if hostID is None:
        print("対象DBのホストIDを指定してください。")
        go_help = True
    if passwd is None:
        print("DBのパスワードを指定してください。")
        go_help = True
    if db_name is None:
        print("対象DBの名前を指定してください。")
        go_help = True
    if target_table is None:
        print("変更対象のテーブル名を指定してください。")
        go_help = True
    #if modify_column is None:
    #    print("変更対象を固定(where句)するカラムの名前を指定してください。")
    #    go_help = True
    if csv_name is None:
        print("パラメータファイル名を指定してください。")
        go_help = True

    if go_help is True:
        print("DB一括変更スクリプト")
        print("")
        print("Usage:")
        print("        $ python3.6 %s <mode> <hostid> <password> <db name> <table> [<csv_name>]")
        print("")
        print("        mode       : change->変更、dryrun->テスト、view->取得と表示（標準出力）")
        print("        hostid     : 対象DBのホストID（IPアドレス）")
        print("        password   : 対象DBへのログイン方法")
        print("        db name    : 対象DBの名前")
        print("        target     : 変更対象のテーブル名")
        #print("        where name : 変更先を特定するためのカラム名") 
        print("        csv_name   : パラメータを記述したCSVファイルの名前")
        print("                   : modeがchangeの時は定義一覧のCSV化したファイル")
        print("                   : modeがviewの時は確認用IDとバージョンのリストファイル")
        print("        mode が dryrunの時はmysqlのコマンドを表示するのみ")
        sys.exit(1)


    if mode == "change":
        change_prediction_module_db(hostID, passwd, db_name, target_table, csv_name)
    elif mode == "dryrun":
        change_prediction_module_db(hostID, passwd, db_name, target_table, csv_name, dryrun=True)
    elif mode == "view":
        view_prediction_module_db(hostID, passwd, db_name, target_table, csv_name)
        
if __name__ == "__main__":

    main()
