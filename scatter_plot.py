#!python3.6
# -*- coding: utf-8 -*-

'''
matplotlibを使用して３次元散布図を描く
'''

import matplotlib.pyplot as plt
import numpy as np
import sys, os
from mpl_toolkits.mplot3d import Axes3D

if len(sys.argv) < 2:
    sys.exit(1)

filename = sys.argv[1]
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
        xlabel = aline.split()[2]
        ylabel = aline.split()[3]
        zlabel = aline.split()[4]
        count += 1
        continue
    print(aline)
    x.append(float(aline.split()[2]))
    y.append(float(aline.split()[3]))
    z.append(float(aline.split()[4]))
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

#ax.plot(X,Y,Z, marker = "o", linestyle="None")
ax.plot(X,Y,Z, marker = "o")

plt.show()
