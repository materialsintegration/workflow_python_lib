#!python3.6
# -*- coding: utf-8 -*-

'''
matplotlibを使用してヒストグラムをプロットしてみる
'''

import matplotlib.pyplot as plt
import numpy as np
import sys, os
from mpl_toolkits.mplot3d import Axes3D

if len(sys.argv) < 2:
    sys.exit(1)

if os.path.exists(sys.argv[1]) is True:
    datafile_name = sys.argv[1]
else:
    sys.exit(1)

infile = open(datafile_name, "r")
lines = infile.read().split("\n")

btr_list = []

for items in lines:
    if items == "":
        continue
    item = items.split()
    if len(item) == 13 and item[11] != "None":
        value = float(item[11])
        if value < 190:
            continue
        btr_list.append(float("%.3f"%value))

#print(btr_list)
plt.hist(btr_list, bins=50)
plt.show()

