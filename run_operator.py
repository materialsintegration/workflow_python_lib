#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
DBから取得した、workflow.runの情報から、条件に合うランのinternal_idを返す。
これは古いデータディレクトリの拡張領域への追い出しと、シンボリックリンク作成に使用される。
'''

import sys, os
import codecs
import csv
import datetime
import calendar

from common_lib import *

def read_run_data(filename):
    '''
    csvを利用してCSV出力したDBを読み込み、ランIDをキーにした、
    ワークフローID、開始日時、終了日時からなるリストの辞書を返す。
    @param filename(string)
    @retval dict
    '''

    if os.path.exists(filename) is True:
        infile = open(filename, "r")
    else:
        sys.stderr.write("not found %s file\n"%filename)
        sys.stderr.flush()
        return {}

    lines = csv.reader(infile, delimiter=",", doublequote=True, escapechar="\\", lineterminator="\r\n", quotechar='"', skipinitialspace=True)

    run_infos = {}
    for aline in lines:
        if aline == "":
            continue
        #print("%016d,%32s,%s,%s"%(int(aline[0]),aline[5],aline[21],aline[22]))
        run_infos[aline[0]] = [aline[5], getJstDatetime(aline[21]), getJstDatetime(aline[22])]

    return run_infos

def main():
    '''
    開始点
    '''

    print(len(sys.argv))
    if len(sys.argv) < 3:
        sys.exit(1)

    infile = sys.argv[1]
    siteid = sys.argv[2]

    run_infos = read_run_data(infile)
    # 前回の処理年月の入ったファイル
    if os.path.exists("previous_process.dat") is True:
        infile = open("previous_process.dat", "r")
        line = infile.read().split("\r")[0].split(",")
        year = int(line[0])
        month = int(line[1])
        month += 1
        if month == 13:
            month = 1
            year += 1
        infile.close()
    else:
        run1 = next(iter(run_infos))
        year = run_infos[run1][1].year
        month = run_infos[run1][1].month

    print("%s / %s"%(year, month))
    count = 0
    amount = 0
    outfile = open("create_index.sh", "w")
    outfile.write("#!/bin/bash\n")
    outfile.write("# ラン短縮ディレクトリ作成\n")
    for item in run_infos:
        if run_infos[item][1].year == year and run_infos[item][1].month == month:
            count += 1
            dirname = getExecDirName(siteid, run_infos[item][0])
            ret = getExecDirUsage(dirname)
            if ret[1] == -1 or ret[1] == -2:
                print("実行時ディレクトリ %s は存在していません。"%dirname)
                continue
            amount += ret[1]
            outfile.write('echo "%010d(%s)"\n'%(count, dirname))
            outfile.write("cd %s\n"%dirname)
            outfile.write("/home/misystem/taverna-commandline-tool/remakeFileListAndCache.sh\n")
            print("%s / %s / %s / %s / %s %s"%(item, run_infos[item][0], run_infos[item][1].year, run_infos[item][1].month, ret[0], ret[1]))

    outfile.close()
    print("processed total %d runs"%count)
    print("この期間の総容量は %s"%convert_size(amount))
    outfile = open("previous_process.dat", "w")
    outfile.write("%s,%s\n"%(year, month))

if __name__ == "__main__":

    main()
