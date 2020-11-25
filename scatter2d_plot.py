#!python3.6
# -*- coding: utf-8 -*-

'''
matplotlibを使用して二次元ガウス分布図を作成する
'''

import matplotlib.pyplot as plt
import japanize_matplotlib
import numpy as np
import sys, os
from mpl_toolkits.mplot3d import Axes3D


def scatter2dGraph(filename, plotspec):
    '''
    ２Ｄグラフを描画する
    @param filename (string) グラフ描画の対象のファイル名。CSVフォーマット（区切りはplotspecに記載）
    @param plotspec (dict) グラフ描画の設定集。CSVの区切り設定もある
    '''

    infile = open(filename)
    lines = infile.read().split('\n')
    x = {}
    y = {}
    for item in plotspec["xcolumn"]:
        x[item] = []
    for item in plotspec["ycolumn"]:
        y[item] = []
    
    count = 0
    for aline in lines:
        if aline == "":
            continue
        if plotspec["seperator"] is None:
            items = aline.split()
        else:
            items = aline.split(plotspec["seperator"])
        #print(len(items))
        xlabel = []
        ylabel = []
        if count == 0:
            if plotspec["ylegend"] is True:
                for item in plotspec["ycolumn"]:
                    ylabel.append(items[item])
            else:
                if plotspec["ylabel"] == "":
                    if len(items) > plotspec["ycolumn"][0]:
                        #ylabel.append(items[plotspec["ycolumn"][0]])
                        plotspec["ylabel"] = items[plotspec["ycolumn"][0]]
                    else:
                        continue
            if plotspec["xlegend"] is True:
                for item in plotspec["xcolumn"]:
                    xlabel.append(items[item])
            else:
                if plotspec["xlabel"] == "":
                    if len(items) > plotspec["xcolumn"][0]:
                        #xlabel.append(items[plotspec["xcolumn"][0]])
                        plotspec["xlabel"] = items[plotspec["xcolumn"][0]]
                    else:
                        continue
            count += 1
            print("xlabel(%s) / ylabel(%s)"%(xlabel, ylabel))
            continue
        # カラム指定と各行の数の確認。カラム番号より少ない場合、その行は無視
        for item in plotspec["xcolumn"]:
            if len(items) < item:
                continue
        for item in plotspec["ycolumn"]:
            if len(items) < item:
                continue
    
        # nanとか数値化できないカラムの確認。
        isnan = False
        for item in plotspec["xcolumn"]:
            if items[item] == "nan" or items[item] == "":
                isnan = True
            #x[item].append(float(items[item]))
        for item in plotspec["ycolumn"]:
            if items[item] == "nan" or items[item] == "":
                isnan = True
            #y[item].append(float(items[item]))
        if isnan is False:
            for item in plotspec["xcolumn"]:
                x[item].append(float(items[item]))
            for item in plotspec["ycolumn"]:
                y[item].append(float(items[item]))
    
        count += 1

    # 45度線描画の確認
    print("45線描画")
    if plotspec["45line"] is True:
        xMax = xMin = x[plotspec["xcolumn"][0]][0]
        print(str(xMax))
        for item in plotspec["xcolumn"]:
            for value in x[item]:
                if xMax < value:
                    xMax = value
                if xMin > value:
                    xMin = value
        yMax = yMin = y[plotspec["ycolumn"][0]][0]
        for item in plotspec["ycolumn"]:
            for value in y[item]:
                if yMax < value:
                    yMax = value
                if yMin > value:
                    yMin = value

    print(len(x))
    X = {}
    Y = {}
    for item in plotspec["xcolumn"]:
        X[item] = np.array([i for i in x[item]])
    for item in plotspec["ycolumn"]:
        Y[item] = np.array([i for i in y[item]])
        
    #
    #plt.scatter(X, Y, linewidths=1, xlabel=xlabel, ylabel=ylabel)
    #igfont = {'family':'ipa-pgothic'}
    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    
    if len(plotspec["xcolumn"]) == 1:
        xitem = plotspec["xcolumn"][0]
        for yitem in plotspec["ycolumn"]:
            ax.scatter(X[xitem], Y[yitem], marker='.')
    else:
        yitem = plotspec["ycolumn"][0]
        for xitem in plotspec["xcolumn"]:
            ax.scatter(X[xitem], Y[yitem], marker='.')

    # タイトル
    ax.set_title(plotspec["title"])
    # 凡例
    if plotspec["xlegend"] is True:
        ax.legend(xlabel)
    if plotspec["ylegend"] is True:
        ax.legend(ylabel)

    # 軸ラベル
    ax.set_xlabel(plotspec["xlabel"])
    ax.set_ylabel(plotspec["ylabel"])

    # グリッド線
    ax.grid(plotspec["grid"])
    if plotspec["45line"] is True:
        if yMin < xMin:
            coodMin = yMin
        else:
            coodMin = xMin
        if yMax > xMax:
            coodMax = yMax
        else:
            coodMax = xMax
        line45x = np.array([coodMin, coodMax])
        line45y = np.array([coodMin, coodMax])
        ax.plot(line45x, line45y, color="red")

    # 保存
    if ("savepng" in plotspec) is True:
        if plotspec["savepng"] != "":
            fig.savefig(plotspec["savepng"])

    plt.show()

def main():
    '''
    単独実行の開始点
    '''

    if len(sys.argv) < 4:
        print("python %s <input csv> <for x axis column,,,> <for y axis column,,,> [seperate char] [title]"%sys.argv[0])
        sys.exit(1)

    filename = sys.argv[1]
    column1 = sys.argv[2]
    column2 = sys.argv[3]
    sep = None
    if len(sys.argv) >= 5:
        sep = sys.argv[4]
    title = "scatter plot"
    if len(sys.argv) == 6:
        title = sys.argv[5]

    print("sep = %s"%sep)
    plotspec = {}
    plotspec["xcolumn"] = []
    for item in column1.split(","):
        plotspec["xcolumn"].append(int(item))
    plotspec["ycolumn"] = []
    for item in column2.split(","):
        plotspec["ycolumn"].append(int(item))
    if len(column1.split(",")) > 1 and len(column2.split(",")) > 1:
        print("縦横同時に複数のカラムを割り当てることはできません。")
        sys.exit(1)
    if len(column1.split(",")) > 1:
        plotspec["xlegend"] = True
    else:
        plotspec["xlegend"] = False
    if len(column2.split(",")) > 1:
        plotspec["ylegend"] = True
    else:
        plotspec["ylegend"] = False
    #if sep == "space":
    #    plotspec["seperator"] = None
    #elif sep == "conma":
    #    plotspec["seperator"] = ","
    #else:
    #    plotspec["seperator"] = None
    plotspec["seperator"] = sep
    plotspec["45line"] = True
    plotspec["withline"] = False
    plotspec["savepng"] = "scatter_plot.png"
    plotspec["title"] = title
    plotspec["grid"] = True
    plotspec["xlabel"] = ""
    plotspec["ylabel"] = ""
    print(str(plotspec))

    scatter2dGraph(filename, plotspec)

if __name__ == "__main__":

    main()
