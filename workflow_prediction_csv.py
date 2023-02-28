#!python3
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.
# -*- coding: utf-8 -*-

'''
ワークフロー、予測モジュール一覧から抽出（resourceRequest編集用）
'''

import sys, os
import pandas as pd
import numpy as np

def main():
    '''
    開始点
    '''

    try:
        csv_name = sys.argv[1]
    except:
        sys.exit(1)
    try:
        person = sys.argv[2]
    except:
        sys.exit(2)

    # CSVの読み込み
    if os.path.exists(csv_name) is True:
        # ヘッダー：prediction_id,pbs_node_group
        #df = pd.read_csv(csv_name, lineterminator="\r\n", escapechar='""')
        df = pd.read_csv(csv_name)

    outfile = open("check_prediction_id.lst", "w")
    pbs_node_group_outfile = open("pbs_node_group.csv", "w")
    pbs_node_group_outfile.write("update_column,update_value,where_column\n")
    pbs_node_group_outfile.flush()
    pbs_queue_outfile = open("pbs_queue.csv", "w")
    pbs_queue_outfile.write("update_column,update_value,where_column\n")
    pbs_queue_outfile.flush()
    for i in range(len(df)):
        #if df["pbsNodeGroup (修正後)"][i] == "non-calc-node":
        #    print("%s"%df["修正内容 確認者"][i])
        # pbsNodeGroupの対応
        if df["修正担当"][i] == person and df["修正日"][i] is np.nan:
            prediction_id = int(df["id"][i][1:])
            outfile.write("%s,%s\n"%(prediction_id, df["version"][i]))
            if df["pbsNodeGroup (修正前)"][i] != df["pbsNodeGroup (修正後)"][i]:
                if df["pbsNodeGroup (修正後)"][i] != "-":
                    pbs_node_group_outfile.write("pbs_node_group,%s,prediction_module_id=%s:version=%s\n"%(df["pbsNodeGroup (修正後)"][i], prediction_id, df["version"][i]))
                    pbs_node_group_outfile.flush()
            if df["pbsQueue (修正前)"][i] != df["pbsQueue (修正後)"][i]:
                if df["pbsQueue (修正後)"][i] != "-" and df["pbsQueue (修正後)"][i] is not np.nan:
                    pbs_queue_outfile.write("pbs_queue,%s,prediction_module_id=%s:version=%s\n"%(df["pbsQueue (修正後)"][i], prediction_id, df["version"][i]))
                    pbs_queue_outfile.flush()
    outfile.close()
    pbs_node_group_outfile.close()
    pbs_queue_outfile.close()

if __name__ == "__main__":

    main()
