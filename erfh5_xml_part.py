#!python3.6
# -*- coding: utf-8 -*-

'''
erfh5(HDF5準拠のファイルフォーマット)用のライブラリ
'''

import h5py
import sys, os
import numpy
import xml.etree.ElementTree as ET
import threading
import multiprocessing
import time
import copy
import datetime

debug_print = True

class xml_partprocess(object):
    '''
    erfh5ファイルから内容を分割してXMLに書き込むための部分出力クラス
    hd5pyオブジェクトを複数扱うと壊れる？ので、ファイル名と必要なタグりすと(findで使う)だけを渡し、
    別なpythonプロセスとして実行される。
    '''

    def __init__(self, item_chain, spc, hdffilename, tag_print):
        '''
        コンストラクタ
        '''

        #self.hdf_items = args[0]        # hdfコンテンツ
        self.item_chain = item_chain    # ここで必要なタグをリストで渡す（現在2段階まで）
        self.spc = spc                  # インデントスペース
        self.hdffilename = hdffilename  # 入力ファイル名
        self.tag_print = tag_print      # タグのみ出力するか

    def run(self):
        '''
        実行開始
        '''

        sys.stderr.write("%s:<%s><%s>:mutilprocessing class type start\n"%(datetime.datetime.now(), self.item_chain[0], self.item_chain[1]))
        sys.stderr.flush()

        # erhf5ファイル開く
        hdf_object = h5py.File(self.hdffilename, "r")

        # xmlファイル開く
        erfh5_xml = "%s_%s.xml"%(self.item_chain[0], self.item_chain[1])
        xmlfileobject = open(erfh5_xml, "w")

        spc = self.spc
        for tag in self.item_chain:
            xmlfileobject.write("%s<%s>\n"%(spc, tag))
            spc += "  "
    
        for item in hdf_object:
            if item == "post":
                continue
            for tag2 in hdf_object[item]:
                if tag2 == self.item_chain[0]:
                    for tag3 in hdf_object[item][tag2]:
                        if tag3 == self.item_chain[1]:
                            self.erfh5ToXMLFileMultiprocess(hdf_object[item][tag2][tag3], self.item_chain, spc, xmlfileobject, self.tag_print)

        spc = spc[0:-2]

        for tag in self.item_chain[::-1]:
            xmlfileobject.write("%s</%s>\n"%(spc, tag))
            spc = spc[0:-2]

        xmlfileobject.close()

        sys.stderr.write("%s:<%s><%s>:mutilprocessing class type end\n"%(datetime.datetime.now(), self.item_chain[0], self.item_chain[1]))
        sys.stderr.flush()

    def erfh5ToXMLFileMultiprocess(self, hdf_items, item_chain, spc, xmlfileobject, tag_print):
        '''
        HDF5の内容を再帰的に読んで、XMLファイルを作成する。(multiprocess処理用)
        @param hdf_items (object)
        @param spc (string)
        @param xmlfileobject (object)
        @retval (bool)
        '''
    
        spc += "  "
    
        hdf_dict = {}
        try:
            for item in hdf_items:
                pass
        except:
            print("error in %s"%str(item_chain))
    
        for item in hdf_items:
            if isinstance(hdf_items[item], h5py.Dataset) is True:
                hdf_dict[item] = []
                if len(hdf_items[item].shape) == 0:
                    #if tag_print is True:
                    #    print('%s<%s shape="0" type="%s">'%(spc, item, hdf_items[item][()].dtype))
                    xmlfileobject.write('%s<%s shape="0" type="%s">'%(spc, item, hdf_items[item][()].dtype))
                    xmlfileobject.write('%s'%hdf_items[item][()])
                elif len(hdf_items[item].shape) == 1:
                    #if tag_print is True:
                    #    print('%s<%s shape="%s" type="%s">'%(spc, item, hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    xmlfileobject.write('%s<%s shape="%s" type="%s">'%(spc, item, hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    n = 0
                    for value in hdf_items[item][()]:
                        if n == 0:
                            xmlfileobject.write('%s'%value)
                        else:
                            xmlfileobject.write(', %s'%value)
                        n += 1
                elif len(hdf_items[item].shape) == 2:
                    #if tag_print is True:
                    #    print('%s<%s shape="%s x %s" type="%s">'%(spc, item, hdf_items[item].shape[1], hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    xmlfileobject.write('%s<%s shape="%s x %s" type="%s">'%(spc, item, hdf_items[item].shape[1], hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    n = 0
                    for ndarray in hdf_items[item]:
                        angle_brackets = ""
                        if len(ndarray) != 1:
                            angle_brackets = "["
                        if n == 0:
                            xmlfileobject.write('%s'%angle_brackets)
                        else:
                            xmlfileobject.write(', %s'%angle_brackets)
                        n += 1
                        m = 0
                        for value in ndarray:
                            if m == 0:
                                xmlfileobject.write('%s'%value)
                            else:
                                xmlfileobject.write(', %s'%value)
                            m += 1
                        if len(ndarray) != 1:
                            xmlfileobject.write(']')
                elif len(hdf_items[item].shape) == 3: 
                    #if tag_print is True:
                    #    print('%s<%s shape="%s x %s x %s" type="%s">'%(spc, item, hdf_items[item].shape[2], hdf_items[item].shape[1], hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    xmlfileobject.write('%s<%s shape="%s x %s x %s" type="%s">'%(spc, item, hdf_items[item].shape[2], hdf_items[item].shape[1], hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    s1 = 0
                    for value1 in hdf_items[item]:
                        angle_brackets1 = ""
                        if len(value1) != 1:
                            angle_brackets1 = "["
                        if s1 == 0:
                            xmlfileobject.write('%s'%angle_brackets1)
                        else:
                            xmlfileobject.write(', %s'%angle_brackets1)
                        s1 += 1
                        s2 = 0
                        for value2 in value1:
                            angle_brackets2 = ""
                            if len(value2) != 1:
                                angle_brackets2 = "["
                            if s2 == 0:
                                xmlfileobject.write('%s'%angle_brackets2)
                            else:
                                xmlfileobject.write(', %s'%angle_brackets2)
                            s2 += 1
                            s3 = 0
                            for value in value2:
                                if s3 == 0:
                                    xmlfileobject.write('%s'%value)
                                else:
                                    xmlfileobject.write(', %s'%value)
                                s3 += 1
                            if len(value2) != 1:
                                xmlfileobject.write(']')
                        if len(value1) != 1:
                            xmlfileobject.write(']')
                else:
                    sys.stderr.write("%s shape = %s type=%s\n"%(item, str(hdf_items[item].shape), hdf_items[item].dtype)) 
                xmlfileobject.write('</%s>\n'%item)
                #if tag_print is True:
                #    print('%s</%s>'%(spc, item))
            elif len(hdf_items[item]) != 0:
                #if tag_print is True:
                #    print('%s<%s type="HDF5 Group Tag">'%(spc, item))
                #xmlfileobject.write('%s<%s type="%s">\n'%(spc, item, type(hdf_items[item])))
                xmlfileobject.write('%s<%s type="HDF5 Group Tag">\n'%(spc, item))
                next_hdf_item = hdf_items[item]
                if self.erfh5ToXMLFileMultiprocess(next_hdf_item, item_chain, spc, xmlfileobject, tag_print) is False:
                    pass
                #if tag_print is True:
                #    print('%s</%s>'%(spc, item))
                xmlfileobject.write('%s</%s>\n'%(spc, item))
    
        return True
    
def main():
    '''
    開始点
    '''

    item_chain = []
    for item in sys.argv[1].split(":"):
        item_chain.append(item)
    
    print(item_chain, sys.argv[2], sys.argv[3], sys.argv[4])
    app = xml_partprocess(item_chain, sys.argv[2], sys.argv[3], sys.argv[4])
    app.run()

    sys.exit(0)

if __name__ == '__main__':
    main()
