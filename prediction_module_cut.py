#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-

'''
modules.xmlを読み込み、指定されたIDのモジュールのみを出力する
一般的な編集機能はmisrc_prediction_editorに実装予定
'''

#from prediction_module_editor_gui import *
import sys, os
import xml.etree.ElementTree as ET
import datetime

if len(sys.argv) < 3:
    print("")
    print("Usage python3.6 %s <prediction_id> [<prediction_id> <prediction_id> ...] <modules.xml>"%sys.argv[0])
    print("")
    print("    予測モジュール切り出しプログラム")
    print("    バージョン番号は、最新（各数字が最大）のもの")
    print("")
    print("    prediction_id : Pで始まる予測モジュール番号。assetでinport後、exportしたあとのmodules.xmlを使う")
    print("                    複数指定可")
    print("    modules.xml   : assetで、exportしたXMLファイル。パラメータ列の最後に指定する")
    print("")
    sys.exit(1)

predictions = []
for item in sys.argv:
    if item.startswith("P") is True:
        predictions.append(item)
    else:
        modules_filename = item

print(str(predictions))
print(modules_filename)

if os.path.exists(modules_filename) is False:
    print("cannot find module files(%s)"%modules_filename)

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

root = ET.Element("modules", {"xmlns":"http://www.example.com/predictionModuleSchema", "xmlns:xsi":"http://www.w3.org/2001/XMLSchema-instance", "xsi:schemaLocation":"http://www.example.com/predictionModuleSchema predictionModuleSchema.xsd"})
for element in target_modules:
    sube = element.find(".//dc:identifier", {'dc': 'http://purl.org/dc/elements/1.1/'})
    element.remove(sube)
    sube = element.find(".//predictionModuleSchema:version", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
    sube.text = "1.0.0"
    root.append(element)

new_tree = ET.ElementTree(element=root)

#ET.register_namespace("ns0", "http://www.example.com/predictionModuleSchema")
new_tree.write("prediction_modules.xml", xml_declaration=True, encoding='UTF-8')
