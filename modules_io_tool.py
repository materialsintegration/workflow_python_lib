#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

'''
modules.xmlを読み込み、指定されたIDのモジュール(複数可)を出力および指定されたmodules.xmlファイルをアセットAPIを使用してMIntシステムへ送り込む
一般的な編集機能はmisrc_prediction_editorに実装予定
'''

#from prediction_module_editor_gui import *
import sys, os
import xml.etree.ElementTree as ET
import datetime
if os.name == "nt":
    import openam_operator
else:
    from openam_operator import openam_operator     # MIシステム認証ライブラリ
#from openam_operator import openam_operator
from getpass import getpass
import json
import requests

def getAllModulesViaAPI(hostname, allmodule_name="modules-all.xml"):
    '''
    APIを使用して登録済み削除済みを除く全予測モジュールを取り出す。
    @param allmodule_name(string) 取り出した後のファイル名
    '''

    #print("予測モデルを取得する側のログイン情報入力")
    if sys.version_info[0] <= 2:
        name = raw_input("ログインID: ")
    else:
        name = input("ログインID: ")
    password = getpass("パスワード: ")

    ret, uid, token = openam_operator.miauth(hostname, name, password)
    #print(token)
    session = requests.Session()
    url = "https://%s:50443/asset-api/v1/prediction-modules"%hostname
    app_format = 'application/json'
    headers = {'Authorization': 'Bearer ' + token,
               'Content-Type': app_format,
               'Accept': app_format}

    ret = session.get(url, headers=headers)

    if ret.status_code == 200:
        print("全予測モジュール情報を取得しました")
        #print(json.dumps(ret.json(), indent=2))
    else:
        print(ret.text)
        #sys.exit(1)
        return False

    #prediction = ret.json()
    outfile = open(allmodule_name, "w")
    #outfile.write(json.dumps(prediction, indent=2, ensure_ascii=False))
    outfile.write(ret.text)
    outfile.close()
    return True

def extract_modules(modules_filename, predictions, ident_nodelete=False):
    '''
    XMLから指定のモジュールを切り出す。
    '''

    if os.path.exists(modules_filename) is False:
        print("cannot find module files(%s)"%modules_filename)
    if modules_filename[0] == "~":
        home_dir = os.path.expanduser("~")
        modules_filename = os.path.join(home_dir, modules_filename[2:])
    
    et = ET.parse(modules_filename)
    docroot = et.getroot()
    #print(docroot.tag)
    candidate_modules = {}
    for prediction_id in predictions:
        candidate_modules[prediction_id] = []
        for item in docroot:
            #print(item.tag)
            subelem = item.find(".//dc:identifier", {'dc': 'http://purl.org/dc/elements/1.1/'})
            if subelem is None:
                # idefitifieが無い場合対象外とする
                continue
            if subelem.text != prediction_id:
                # 指定したIDと違う物は対象外とする
                continue
            subelem = item.find(".//predictionModuleSchema:version", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
            if subelem is None:
                # versionが無い場合対象外とする
                continue
    
            candidate_modules[prediction_id].append(item)
        if len(candidate_modules[prediction_id]) == 0:
            print("予測モジュールid(%s)は登録がありませんでした。"%prediction_id)
    
    print(len(candidate_modules))
    target_modules = []
    for prediction_id in candidate_modules:
        rev = 0
        miner = 0
        majer = 0
        for item in candidate_modules[prediction_id]:
            #全elementを見るために
            #for element in item.iter():
            #    print("%s - %s"%(element.tag, element.text))
            #print(item.tag)
            subelem = item.find(".//predictionModuleSchema:version", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
            v1 = int(subelem.text.split(".")[0])
            v2 = int(subelem.text.split(".")[1])
            v3 = int(subelem.text.split(".")[2])
            if v1 >= majer or v2 >= miner or v3 >= rev:
                target_module = item
                majer = v1
                miner = v2
                rev = v3
        target_modules.append(target_module)
    
    #root = ET.Element("modules", {"xmlns":"http://www.example.com/predictionModuleSchema", "xmlns:xsi":"http://www.w3.org/2001/XMLSchema-instance", "xsi:schemaLocation":"http://www.example.com/predictionModuleSchema predictionModuleSchema.xsd"})
    root = ET.Element("modules", {"xmlns":"http://www.example.com/predictionModuleSchema", "xsi:schemaLocation":"http://www.example.com/predictionModuleSchema predictionModuleSchema.xsd"})
    for element in target_modules:
        if ident_nodelete is False:
            sube = element.find(".//dc:identifier", {'dc': 'http://purl.org/dc/elements/1.1/'})
            element.remove(sube)
            sube = element.find(".//predictionModuleSchema:version", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
            sube.text = "1.0.0"
        root.append(element)
    
    new_tree = ET.ElementTree(element=root)
    
    #ET.register_namespace("ns0", "http://www.example.com/predictionModuleSchema")
    new_tree.write("prediction_modules.xml", xml_declaration=True, encoding='UTF-8')

def main():
    '''
    開始点
    '''

    predictions = []
    modules_filename = ""
    process_mode = "file"                   # ファイルから切り出し
    ident_nodelete = False
    misystem = "dev-u-tokyo.mintsys.jp"
    go_help = False

    for item in sys.argv:
        if item == "--ident-nodelete":
            ident_nodelete = True
            continue
        items = item.split(":")
        if items[0] == "predictions":
            pmodules = items[1].split(",")
            for pmodule in pmodules:
                predictions.append(pmodule)
        elif items[0] == "mode":
            process_mode = items[1]
        elif items[0] == "modulesfile":
            modules_filename = items[1]
        elif items[0] == "misystem":
            misystem = items[1]
        elif items[0] == "help":
            go_help = True
        #else:
        #    modules_filename = item

    print(str(predictions))
    print(modules_filename)
    if process_mode == "file" or process_mode == "import":
        if modules_filename == "":
            go_help = True
    if process_mode == "file" or process_mode == "export":
        if len(predictions) == 0:
            go_help = True

    if go_help is True:
        print("")
        print("Usage python3.6 %s mode:<mode> predictions:<prediction_id>,[<prediction_id>,<prediction_id>,...] modulesfile:<modules.xml> [--ident-nodelete]"%sys.argv[0])
        print("")
        print("    予測モジュール切り出し、送り込みプログラム")
        print("    バージョン番号は、最新（各数字が最大）のもの")
        print("")
        print("予測モデル切り出し")
        print("             mode : exportを指定するとアセットAPIを使って最新のmodules.xmlを取り出し、これが対象となる。")
        print("                    デフォルトはfile(modulesfileで指定したファイルを使用)である。")
        print("      predictions : Pで始まる予測モジュール番号。assetでinport後、exportしたあとのmodules.xmlを使う")
        print("                    複数指定可")
        print("      modulesfile : asset管理画面から、exportしたXMLファイル。mode:exportを指定した場合は無視される。")
        print("  --ident-nodelete: identifierタグを削除しない。versionを1.0.0に変更しない")
        print("")
        print("予測モデル送り込み")
        print("             mode : import")
        print("      modulesfile : asset管理へ、インポートしたいXMLファイル。")
        print("")
        print("export/import 共通")
        print("         misystem : dev-u-tokyo.minsystem.jpのようなホスト名。")
        print("")  
        sys.exit(1)

    if process_mode == "file":
        extract_modules(modules_filename, predictions, ident_nodelete)
    elif process_mode == "export":
        modules_filename = "modules-all.xml"
        if getAllModulesViaAPI(hostname=misystem) is False:
            sys.exit(1)
        extract_modules(modules_filename, predictions, ident_nodelete)
        pass
    elif process_mode == "import":
        pass
    else:
        print("対応する動作モードがありません")

if __name__ == '__main__':
    main()

