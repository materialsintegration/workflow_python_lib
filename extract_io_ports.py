#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
modules.xmlのinPortsとoutPortsコンテンツから、モジュール実行プログラム用のポートリスト(テンプレート）を作成する。
作成したテンプレートを完成させモジュール実行スクリプトの先頭でimportして使用する。
'''

import sys, os
import xml.etree.ElementTree as ET
import datetime

if len(sys.argv) < 3:
    print("")
    print("Usage python3.6 %s <prediction_id> <modules.xml> [-c[:前段のモジュール名]]"%sys.argv[0])
    print("")
    print("    バージョン番号は、最新（各数字が最大）のもの")
    print("")
    print("    prediction_id : Pで始まる予測モジュール番号。assetでinport後、exportしたあとのmodules.xmlを使う")
    print("    modules.xml   : assetで、exportしたXMLファイル。")
    print("        -c        : チェックオンリー。パラメータの長さのみ計算")
    print("  :前段のモジュール名 : 一つ前の予測モジュール名を一つ")
    print("                  : Wxxxxxyyyyyyyyyy_予測モジュール名_02 という形式")
    print("")
    sys.exit(1)

prediction_id = sys.argv[1]
modules_filename = sys.argv[2]
check_only = False
instead_input = None
if len(sys.argv) == 4:
    print(sys.argv[3])
    items = sys.argv[3].split(":")
    if items[0] == "-c":
        check_only = True
    if len(items) == 2:
        instead_input = items[1]

print(len(sys.argv))
print(prediction_id)
print(modules_filename)

if os.path.exists(modules_filename) is False:
    print("cannot find module files(%s)"%modules_filename)

et = ET.parse(modules_filename)
docroot = et.getroot()
print(docroot.tag)
candidate_modules = []
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

    candidate_modules.append(item)

print(len(candidate_modules))
rev = 0
miner = 0
majer = 0
target_module = None
for item in candidate_modules:
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

object_name = target_module.find(".//predictionModuleSchema:objectPath", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"}).text
object_name = object_name.replace("-", "_")
# objectPathの実行スクリプト名
object_exec_name = object_name.split("/")[-1]
object_name = object_name.split("/")[-1].split(".")[0]
# パラメータ設定ファイル名
object_import = object_name + "_import.py"
object_file_name = object_name.split("/")[-1]
object_package_name = object_name + "_import"
p_id = target_module.find(".//dc:identifier", {'dc': 'http://purl.org/dc/elements/1.1/'})
version = target_module.find(".//predictionModuleSchema:version", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
module_name = target_module.find(".//dc:title", {'dc': 'http://purl.org/dc/elements/1.1/'}).text
module_name = module_name.replace("-", "")
module_name = module_name.replace("/", "")
module_name = module_name.replace("'", "")
module_len = len(str.encode(module_name)) + 3       # _01の数を追加しておく
print("prediction module id = %s / version = %s"%(p_id.text, version.text))

amount = 0                                          # argsの長さを概算見積り
additional_len = 2 + 1 + 16 + 1 + 3 + 1             # -- と ワークフローID/ と / と _01 と前後の空白
                                                    # inputはこれに、inputの5バイト
                                                    # outportはこれに、ワークフローID_モジュール名のバイト数
# まずはパラメータ長さの出力
# inport
args = ""
items = target_module.find(".//predictionModuleSchema:inputPorts", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
for item in items:
    subitem = item.find(".//predictionModuleSchema:name", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
    if instead_input is not None:
        amount += (len(str.encode(subitem.text)) * 2) + additional_len + len(str.encode(instead_input))
    else:
        amount += (len(str.encode(subitem.text)) * 2) + additional_len + 5

    args += "--%s "%subitem.text
    if instead_input is not None:
        args += "Wxxxx2xxxxxxxxxx/%s/%s_01 "%(subitem.text, instead_input)
    else:
        args += "Wxxxx2xxxxxxxxxx/input/%s_01 "%subitem.text

# outport
items = target_module.find(".//predictionModuleSchema:outputPorts", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
count = 0
for item in items:
    subitem = item.find(".//predictionModuleSchema:name", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
    amount += (len(str.encode(subitem.text)) * 2) + additional_len + module_len + 16
    args += "--%s "%subitem.text
    args += "Wxxxx2xxxxxxxxxx/Wxxxx2xxxxxxxxxx_%s_01/%s "%(module_name, subitem.text)

print("args 長さ:%d(%d)"%(amount, len(str.encode(args))))
print(args)
if check_only is True:
    sys.exit(0)

# ファイルの出力
outfile = open(object_import, "w")
outfile.write("# %s用 ポート変換テーブル\n"%object_file_name)
outfile.write("# objectPathの実行ファイルの先頭でimportして使う\n")
outfile.write("# このファイルは自動生成されたのち、不足分を追加して使用する。\n")
outfile.write("# create at %s\n"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
# inport
items = target_module.find(".//predictionModuleSchema:inputPorts", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
count = 0
for item in items:
    subitem = item.find(".//predictionModuleSchema:name", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
    #print(subitem.text)
    if count == 0:
        outfile.write("inputports = {'%s':'',"%subitem.text)
    else:
        outfile.write("\n")
        outfile.write("              '%s':'',"%subitem.text)
    count += 1
outfile.write("}\n")

# outport
items = target_module.find(".//predictionModuleSchema:outputPorts", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
count = 0
for item in items:
    subitem = item.find(".//predictionModuleSchema:name", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
    if count == 0:
        outfile.write("outputports = {'%s':'',"%subitem.text)
    else:
        outfile.write("\n")
        outfile.write("               '%s':'',"%subitem.text)
    count += 1
outfile.write("}\n")

# in_realnames
items = target_module.find(".//predictionModuleSchema:inputPorts", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
count = 0
for item in items:
    subitem = item.find(".//predictionModuleSchema:name", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
    #print(subitem.text)
    if count == 0:
        outfile.write("in_realnames = {'%s':'',"%subitem.text)
    else:
        outfile.write("\n")
        outfile.write("                '%s':'',"%subitem.text)
    count += 1
outfile.write("}\n")

# out_realnames
items = target_module.find(".//predictionModuleSchema:outputPorts", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
count = 0
for item in items:
    subitem = item.find(".//predictionModuleSchema:name", {"predictionModuleSchema": "http://www.example.com/predictionModuleSchema"})
    if count == 0:
        outfile.write("out_realnames = {'':'%s',"%subitem.text)
    else:
        outfile.write("\n")
        outfile.write("                 '':'%s',"%subitem.text)
    count += 1
outfile.write("}\n")
outfile.close()

# 実行スクリプト雛形作成
outfile = open(object_exec_name, "w")
outfile.write("#!/usr/bin/python3.6\n")
outfile.write("# -*- coding: utf-8 -*-\n")
outfile.write("# Copyright (c) The University of Tokyo and\n")
outfile.write("# National Institute for Materials Science (NIMS). All rights reserved.\n")
outfile.write("# This document may not be reproduced or transmitted in any form,\n")
outfile.write("# in whole or in part, without the express written permission of\n")
outfile.write("# the copyright owners.\n")
outfile.write("\n")
outfile.write("'''\n")
outfile.write("ここにスクリプトの概要を記述する。\n")
outfile.write("'''\n")
outfile.write("\n")
outfile.write("import os, sys\n")
outfile.write('sys.path.append("/home/misystem/assets/modules/workflow_python_lib")\n')
outfile.write("from workflow_lib import *\n")
outfile.write("\n")
outfile.write("# ポート情報設定ファイル取り込み\n")
outfile.write("from %s import *\n"%object_package_name)
outfile.write("\n")
outfile.write("# モジュール初期化\n")
outfile.write("wf_tool = MIApiCommandClass()\n")
outfile.write("wf_tool.setInportNames(inputports)\n")
outfile.write("wf_tool.setOutportNames(outputports)\n")
outfile.write("wf_tool.setRealName(in_realnames, out_realnames)\n")
outfile.write("#入力、出力の実ファイルとパラメータ名の自動変換をしない場合は、以下のフラグをそれぞれFalseにする。\n")
outfile.write("#どちらもデフォルトFalseなので未指定でも可。\n")
outfile.write("wf_tool.Initialize(translate_input=True, translate_output=True)\n")
outfile.write("\n")
outfile.write('cmd = "ここに実行プログラムを設定する"\n')
outfile.write("\n")
outfile.write("wf_tool.ExecSolver(cmd)\n")
outfile.write("\n")
outfile.write("sys.exit(0)\n")
