#!python3.6
# -*- coding: utf-8 -*-

'''
さまざまな乱数発生関数で、所定の数の生成した乱数を返す。
'''

import random
import os, sys
import time

def random_with_num(random_type, random_val1, random_val2, random_num, random_seed, disporlist=True):
    '''
    '''

    random_list = []
    random.seed(random_seed)

    for i in range(random_num):
        if random_type == "uniform": 
            value = random.uniform(random_val1, random_val2)
        elif random_type == "gauss": 
            value = random.gauss(random_val1, random_val2)
        elif random_type == "gamma": 
            value = random.gamma(random_val1, random_val2)
        elif random_type == "log": 
            value = random.lognormvariate(random_val1, random_val2)
        elif random_type == "normal": 
            value = random.normalvariate(random_val1, random_val2)
        else:
            value = random.random()
        if disporlist is True:
            print("%f"%value)
        else:
            random_list.append(value)
    
    if disporlist is True:
        sys.stderr.write("%s\n"%random_seed)
    else:
        return random_list, random_seed

def main():
    '''
    開始点
    '''

    if len(sys.argv) < 5:
        print("Usage")
        print("$ python %s <type [uniform|gauss|gamma|log|normal]> <value1> <value2> <num of generate> <seed>"%sys.argv[0])
        print("         uniform:一様乱数。value1 <= N <= value2")
        print("          gauss :ガウス分布。value1は平均をvalue2は標準偏差。")
        print("          gamma :ガンマ分布。value1はalphaをvalue2はbeta。")
        print("            log :対数正規分布。value1は平均をvalue2は標準偏差。")
        print("          normal:正規分布。value1は平均をvalue2は標準偏差。")
        print("")
        print("標準出力に乱数リストを標準エラーに使用したseedをそれぞれ返します。")

    random_type = sys.argv[1]
    random_val1 = float(sys.argv[2])
    random_val2 = float(sys.argv[3])
    random_num = int(sys.argv[4])
    if len(sys.argv) == 6:
        random_seed = sys.argv[5]
    else:
        random_seed = time.time()

    random_with_num(random_type, random_val1, random_val2, random_num, random_seed)

if __name__ == '__main__':
    main()

