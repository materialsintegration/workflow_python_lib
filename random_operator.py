#!python3.6
# -*- coding: utf-8 -*-

'''
さまざまな乱数発生関数で、所定の数の生成した乱数を返す。
'''

import random
import os, sys
import time

def rand(num, random_val1, random_val2):

    n_iter = num
    segSize = 1/float(n_iter)
    print("segSize = %f"%segSize)

    random_list = []
    point_list = []
    for i in range(n_iter):
        segMin = float(i) * segSize
        print("segMin = %f"%segMin)
        #point = segMin + (random.normalvariate(random_val1, random_val1 * random_val2) * segSize)
        point = segMin + (random.normalvariate(7.5, 1) * segSize)
        #point = segMin + (random.gauss(random_val1, random_val1 * random_val2) * segSize)
        #point = segMin + (random.gauss(7.6, 1) * segSize)
        pointValue = (point * ((random_val1 * (1 + random_val2)) - (random_val1 * (1 - random_val2)))) + random_val1
        #print(point)
        #print(pointValue)
        point_list.append(point)
        random_list.append(pointValue)

    return point_list, random_list

def random_with_num_with_lhypercube(random_type, random_val1, random_val2, random_num, random_seed, disporlist=True):
    '''
    各乱数生成法を使用して個数分の乱数をラテンハイパーキューブ法を使用して抽出する
    @param random_type (string)
    @param random_val1 (value)
    @param random_val2 (value)
    @param random_seed (string)
    @param disporlist (bool)
    @retval disporlist is True: only print, False: returen dict
    '''

    random_list = []
    random.seed(random_seed)

    for i in range(random_num):
        if random_type == "uniform": 
            min_value = random_val1 * (1.0 - random_val2)
            max_value = random_val1 * (1.0 + random_val2)
            value = random.uniform(min_value, max_value)
        elif random_type == "gauss": 
            value = random.gauss(random_val1, random_val1 * random_val2)
        elif random_type == "gamma": 
            value = random.gamma(random_val1, random_val2)
        elif random_type == "log": 
            value = random.lognormvariate(random_val1, random_val1 * random_val2)
        elif random_type == "normal": 
            value = random.normalvariate(random_val1, random_val1 * random_val2)
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
def random_with_num(random_type, random_val1, random_val2, random_num, random_seed, disporlist=True):
    '''
    各乱数生成法を使用して個数分の乱数を生成する
    @param random_type (string)
    @param random_val1 (value)
    @param random_val2 (value)
    @param random_seed (string)
    @param disporlist (bool)
    @retval disporlist is True: only print, False: returen dict
    '''

    random_list = []
    random.seed(random_seed)

    for i in range(random_num):
        if random_type == "uniform": 
            min_value = random_val1 * (1.0 - random_val2)
            max_value = random_val1 * (1.0 + random_val2)
            value = random.uniform(min_value, max_value)
        elif random_type == "gauss": 
            value = random.gauss(random_val1, random_val1 * random_val2)
        elif random_type == "gamma": 
            value = random.gamma(random_val1, random_val2)
        elif random_type == "log": 
            value = random.lognormvariate(random_val1, random_val1 * random_val2)
        elif random_type == "normal": 
            value = random.normalvariate(random_val1, random_val1 * random_val2)
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

