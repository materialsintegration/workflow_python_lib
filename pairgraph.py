#!python3.6
# -*- coding: utf-8 -*-

'''
matplotlib/seaborn/pandasを使用してペアグラフをプロットしてみる
'''

import matplotlib.pyplot as plt
import numpy as np
import sys, os
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import seaborn as sns

if len(sys.argv) < 2:
    sys.exit(1)

if os.path.exists(sys.argv[1]) is True:
    datafile_name = sys.argv[1]
else:
    sys.exit(1)
if len(sys.argv) == 3:
    outfilename = sys.argv[2]
else:
    outfilename1 = "%s_class.png"%os.path.splitext(datafile_name)[0]
    outfilename2 = "%s_default.png"%os.path.splitext(datafile_name)[0]

infile = open(datafile_name, "r")
lines = infile.read().split("\n")
headers = lines[0].split()
btr_list = {'btr_bins':[]}
btr_min = btr_max = None                            # クラス分け用の最大値、最小値取得用
for i in range(1, len(headers)):
    btr_list[headers[i]] = []

    for l in range(1, len(lines)):
        if lines[l] == "":
            continue
        item = lines[l].split()
        if len(item) != 13:
            continue
        if item[11] == "None":
            continue
        btr_value = float(item[11])
        if btr_value < 190:
            continue
        gammap = float(item[12])
        if gammap < 0.2:
            continue
        # 最大値最小値
        if btr_min is None:
            btr_min = btr_value
        if btr_max is None:
            btr_max = btr_value
        if btr_min > btr_value:
            btr_min = btr_value
        if btr_max < btr_value:
            btr_max = btr_value
        # データフレーム用辞書作成
        value = float(item[i])
        btr_list[headers[i]].append(value)

# BTRのクラス分けように、ラベル作成
step = (btr_max - btr_min) / 5.0
for i in range(len(btr_list["BTR"])):
    btr_value = btr_list["BTR"][i]
    if btr_min <= btr_value and btr_value < btr_min + step:
        btr_list["btr_bins"].append("btrstep1")
    elif btr_min + step <= btr_value and btr_value < btr_min + (step * 2):
        btr_list["btr_bins"].append("btrstep2")
    elif btr_min + (step * 2) <= btr_value and btr_value < btr_min + (step * 3):
        btr_list["btr_bins"].append("btrstep3")
    elif btr_min + (step * 3) <= btr_value and btr_value < btr_min + (step * 4):
        btr_list["btr_bins"].append("btrstep4")
    elif btr_min + (step * 4) <= btr_value and btr_value <= btr_min + (step * 5):
        btr_list["btr_bins"].append("btrstep5")

# データフレーム作成
df = pd.DataFrame(btr_list)
print(df.head())
print(df.dtypes)
print(len(df))

# ペアプロット作成
pg = sns.pairplot(df, hue='btr_bins', diag_kind='hist').savefig(outfilename1)
#pg = sns.pairplot(df, hue='btr_bins', diag_kind='kde').savefig("test.png")
pg = sns.pairplot(df).savefig(outfilename2)
