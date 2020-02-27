#!python3.6
# -*- coding: utf-8 -*-

'''
matplotlibを使用して二次元ガウス分布図を作成する
'''

import matplotlib.pyplot as plt
import numpy as np
import sys, os
from mpl_toolkits.mplot3d import Axes3D

if len(sys.argv) < 4:
    sys.exit(1)

filename = sys.argv[1]
column1 = int(sys.argv[2])
column2 = int(sys.argv[3])

infile = open(filename)
lines = infile.read().split('\n')
x = []
y = []

count = 0
for aline in lines:
    if aline == "":
        continue
    if count == 0:
        print(len(aline.split()))
        if len(aline.split()) > column2:
            ylabel = aline.split()[column2]
        else:
            continue
        if len(aline.split()) > column1:
            xlabel = aline.split()[column1]
        else:
            continue
        count += 1
        continue
    if len(aline.split()) > column2 and len(aline.split()) > column1:
        pass
    else:
        continue

    x.append(float(aline.split()[column1]))
    y.append(float(aline.split()[column2]))
    count += 1

print(len(x))
X = np.array([i for i in x])
Y = np.array([i for i in y])
    
#
plt.scatter(X, Y)
plt.show()
