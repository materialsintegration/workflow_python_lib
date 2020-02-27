#!python3.6
# -*- coding: utf-8 -*-

'''
matplotlibを使用して３次元散布図を描く
'''

import matplotlib.pyplot as plt
import numpy as np
import sys, os
from mpl_toolkits.mplot3d import Axes3D

if len(sys.argv) < 5:
    print("python scatter3d_plot.py <data file> <column1> <column2> <column3> [line]")
    sys.exit(1)

filename = sys.argv[1]
column1 = int(sys.argv[2])
column2 = int(sys.argv[3])
column3 = int(sys.argv[4])
with_line = False
#print(len(sys.argv))
if len(sys.argv) > 5:
    if len(sys.argv) == 6:
        with_line = True
infile = open(filename)
lines = infile.read().split('\n')
x = []
y = []
z = []
count = 0
for aline in lines:
    if aline == "":
        continue
    if count == 0:
        xlabel = aline.split()[column1]
        ylabel = aline.split()[column2]
        zlabel = aline.split()[column3]
        count += 1
        continue
    print(aline)
    x.append(float(aline.split()[column1]))
    y.append(float(aline.split()[column2]))
    z.append(float(aline.split()[column3]))
    count += 1

X = np.array([i for i in x])
Y = np.array([i for i in y])
Z = np.array([i for i in z])
    
#
fig = plt.figure()
ax = Axes3D(fig)

#ax.set_xlabel("Energy(MJ/mm)")
#ax.set_ylabel("Weld End Time(sec)")
#ax.set_zlabel("obj_fnc(Vs 1000C)")
ax.set_xlabel(xlabel)
ax.set_ylabel(ylabel)
ax.set_zlabel(zlabel)

if with_line is True:
    ax.plot(X,Y,Z, marker = "o")
else:
    ax.plot(X,Y,Z, marker = "o", linestyle="None")

plt.show()
