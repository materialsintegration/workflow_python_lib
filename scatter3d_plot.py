#!python3.6
# -*- coding: utf-8 -*-

'''
matplotlibを使用して３次元散布図を描く
'''

import matplotlib.pyplot as plt
import numpy as np
import sys, os
from mpl_toolkits.mplot3d import Axes3D

def scatter3dGraph(filename, plotspec):
    '''
    ３Ｄグラフ散布図を描画する
    @param filename (string) グラフ描画の対象のファイル名。CSVフォーマット（区切りはplotspecに記載）
    @param plotspec (dict) グラフ描画の設定集。CSVの区切り設定もある
    '''
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
    
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_zlabel(zlabel)
    
    if with_line is True:
        ax.plot(X,Y,Z, marker = "o")
    else:
        ax.plot(X,Y,Z, marker = "o", linestyle="None")
    
    plt.show()

def main():
    '''
    単独実行の開始点
    '''

    if len(sys.argv) < 5:
        print("python %s <data file> <column1 for x> <column2 for y> <column3 for z> [line] [sep]"%sys.argv[0])
        sys.exit(1)
    
    with_line = False
    sep = None
    for i in range(len(sys.argv)):
        if i == 1:
            filename = sys.argv[i]
        if i == 2:
            column1 = int(sys.argv[i])
        if i == 3:
            column2 = int(sys.argv[i])
        if i == 4:
            column3 = int(sys.argv[i])
        if i == 5 or i == 6:
            if sys.argv[i] == "line":
                with_line == True:
            else:
                sep = sys.argv[i]

    print("sep = %s"%sep)
    #print(len(sys.argv))
    if len(sys.argv) > 5:
        if len(sys.argv) == 6 and sys.argv[5] == "line":
            with_line = True

    title = "scatter plot"
    plotspec = {}
    plotspec["xcolumn"] = []
    for item in column1.split(","):
        plotspec["xcolumn"].append(int(item))
    plotspec["ycolumn"] = []
    for item in column2.split(","):
        plotspec["ycolumn"].append(int(item))
    plotspec["zcolumn"] = []
        plotspec["zcolumn"].append(int(item))
    if len(column1.split(",")) > 1 and len(column2.split(",")) > 1 and len(column3.split(",") > 1:
        print("各辺同時に複数のカラムを割り当てることはできません。")
        sys.exit(1)
    if len(column1.split(",")) > 1:
        plotspec["xlegend"] = True
    else:
        plotspec["xlegend"] = False
    if len(column2.split(",")) > 1:
        plotspec["ylegend"] = True
    else:
        plotspec["ylegend"] = False
    if len(column3.split(",")) > 1:
        plotspec["zlegend"] = True
    else:
        plotspec["zlegend"] = False

    plotspec["seperator"] = sep
    plotspec["45line"] = True
    plotspec["withline"] = False
    plotspec["savepng"] = "scatter_plot.png"
    plotspec["title"] = title
    plotspec["grid"] = True
    plotspec["xlabel"] = ""
    plotspec["ylabel"] = ""
    plotspec["zlabel"] = ""
    print(str(plotspec))

    scatter2dGraph(filename, plotspec)

if __name__ == "__main__":

    main()
