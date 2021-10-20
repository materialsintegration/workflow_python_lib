#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
'''
入力ファイル結合ツール（汎用）

2021/05/12 Y.Manaka
  このスクリプトは他のスクリプトのためにworkflow_python_libに移しました。
  /home/misystem/assets/modules/phase_transformation/scriptには後方互換性のためにシンボリックリンクとしました。
  /home/misystem/assets/modules/phase_transformation/script/combine_input_file.pyを編集した場合は、
  /home/misystem/assets/modules/workflow_python_libでのcommit/pushをお願いします。
'''

import os
import sys
import argparse

# codec
encode = "utf-8"

# =======================================
# main
# =======================================

def readInputFile(filename):
    dat = ""
    if os.path.exists(filename) is True:
        with open(filename, 'r', encoding=encode) as fp:
            dat = fp.read()
    else:
        print("-- readInputFile() ファイルが存在しません。" + filename)
        sys.exit(1)

    return dat


def main():

    # 引数取得
    parser = argparse.ArgumentParser()
    parser.add_argument('output_file_name')
    parser.add_argument('-i', '--input_files', nargs='*', required=True)

    args = parser.parse_args()

    print(args.output_file_name)
    print(args.input_files)

    # 出力ファイル名
    outfilename = args.output_file_name

    # 入力ファイル名リスト
    input_files = args.input_files
#
#    # =======================================
#    # ファイルから読込
#    # =======================================
    header = []
    data = []

    for input_file in input_files:
        input_data = readInputFile(input_file)
        header.append(input_file)
        data.append(input_data.split("\n")[0])

    # =======================================
    # ファイル出力
    # =======================================
    with open(outfilename, 'w', encoding=encode) as fp:
        fp.write(",".join(header) + '\n')
        fp.write(",".join(data) + '\n')

if __name__ == '__main__':
    main()
