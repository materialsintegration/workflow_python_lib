#!python3.6
# -*- coding: utf-8 -*-

'''
erfh5(HDF5u準拠のファイルフォーマット)用のライブラリ
'''

import h5py
import sys, os
import numpy
import xml.etree.ElementTree as ET
import threading
import multiprocessing
import subprocess
import time
import copy

debug_print = True

class shell_thread(threading.Thread):
    '''
    シェルスクリプトスレッド実行用クラス
    '''
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        '''
        '''
        threading.Thread.__init__(self, group=group, target=target, name=name, daemon=daemon)

        self.item_chain = args[0]       # ここまでのタグをリストで渡す
        self.spc = args[1]              # インデントスペース
        self.xmlfilename = args[2]      # 出力ファイル名
        self.tag_print = args[3]        # タグのみ出力するか
        self.headname = "headdev-cl"
        if ("MISYSTEM_HEADNODE_HOSTNAME" in os.environ):
            self.headname = os.environ["MISYSTEM_HEADNODE_HOSTNAME"]

    def run(self):
        '''
        スクリプト実行用関数
        '''

        current_dir = os.getcwd()
        #print("%s:%2d exec start in %s"%(datetime.datetime.now(), self.thread_num, current_dir))
        sys.stderr.write("<%s><%s>mutilprocessing class type start\n"%(self.item_chain[0], self.item_chain[1]))
        sys.stderr.flush()
        item_chain = "%s:%s"%(self.item_chain[0], self.item_chain[1])
        cmd = 'python3.6 /home/misystem/assets/modules/workflow_python_lib/erfh5_xml_part.py %s "%s" %s %s'%(item_chain, self.spc, self.xmlfilename, self.tag_print)
        #sys.stderr.write("Command = %s"%cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        stdout_data = p.stdout.read()
        stderr_data = p.stderr.read()
        #sys.stderr.write("Error? %s"%stderr_data)

class xml_thread(threading.Thread):
    '''
    erfh5ファイルから内容を分割してXMLに書き込むためのスレッドオブジェクト
    '''

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        '''
        コンストラクタ
        '''

        threading.Thread.__init__(self, group=group, target=target, name=name, daemon=daemon)
        # args= hdf_items, item_chain, spc, xmlfilename, tag_print
        self.hdf_items = args[0]        # hdfコンテンツ
        self.item_chain = args[1]       # ここまでのタグをリストで渡す
        self.spc = args[2]              # インデントスペース
        self.xmlfilename = args[3]      # 出力ファイル名
        self.tag_print = args[4]        # タグのみ出力するか

    def run(self):
        '''
        スレッド実行開始
        '''

        xmlfileobject = open(self.xmlfilename, "w")
        spc = self.spc
        for tag in self.item_chain:
            xmlfileobject.write("%s<%s>\n"%(spc, tag))
            spc += "  "

        spc = spc[0:-2]
        self.erfh5ToXMLFile(self.hdf_items, spc, xmlfileobject)

        for tag in self.item_chain[::-1]:
            xmlfileobject.write("%s</%s>\n"%(spc, tag))
            spc = spc[0:-2]

    def erfh5ToXMLFile(self, hdf_items, spc, xmlfileobject):
        '''
        HDF5の内容を再帰的に読んで、XMLファイルを作成する。
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
            print("error in %s"%str(self.item_chain))

        for item in hdf_items:
            if isinstance(hdf_items[item], h5py.Dataset) is True:
                hdf_dict[item] = []
                if len(hdf_items[item].shape) == 0:
                    if self.tag_print is True:
                        print('%s<%s shape="0" type="%s">'%(spc, item, hdf_items[item][()].dtype))
                    xmlfileobject.write('%s<%s shape="0" type="%s">'%(spc, item, hdf_items[item][()].dtype))
                    xmlfileobject.write('%s'%hdf_items[item][()])
                elif len(hdf_items[item].shape) == 1:
                    if self.tag_print is True:
                        print('%s<%s shape="%s" type="%s">'%(spc, item, hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    xmlfileobject.write('%s<%s shape="%s" type="%s">'%(spc, item, hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    n = 0
                    for value in hdf_items[item][()]:
                        if n == 0:
                            xmlfileobject.write('%s'%value)
                        else:
                            xmlfileobject.write(', %s'%value)
                        n += 1
                elif len(hdf_items[item].shape) == 2:
                    if self.tag_print is True:
                        print('%s<%s shape="%s x %s" type="%s">'%(spc, item, hdf_items[item].shape[1], hdf_items[item].shape[0], hdf_items[item][()].dtype))
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
                    if self.tag_print is True:
                        print('%s<%s shape="%s x %s x %s" type="%s">'%(spc, item, hdf_items[item].shape[2], hdf_items[item].shape[1], hdf_items[item].shape[0], hdf_items[item][()].dtype))
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
                if self.tag_print is True:
                    print('%s</%s>'%(spc, item))
            elif len(hdf_items[item]) != 0:
                if self.tag_print is True:
                    print('%s<%s type="HDF5 Group Tag">'%(spc, item))
                #xmlfileobject.write('%s<%s type="%s">\n'%(spc, item, type(hdf_items[item])))
                xmlfileobject.write('%s<%s type="HDF5 Group Tag">\n'%(spc, item))
                if self.erfh5ToXMLFile(hdf_items[item], spc, xmlfileobject) is False:
                    pass
                if self.tag_print is True:
                    print('%s</%s>'%(spc, item))
                xmlfileobject.write('%s</%s>\n'%(spc, item))
    
        return True
    
class xml_multiprocess(multiprocessing.Process):
    '''
    erfh5ファイルから内容を分割してXMLに書き込むためのマルチプロセスオブジェクト
    hd5pyオブジェクトを複数扱うと壊れる？ので、ファイル名と必要なタグりすと(findで使う)だけを渡す。
    '''

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        '''
        コンストラクタ
        '''

        multiprocessing.Process.__init__(self, group=None, target=target, name=name)
        #self.hdf_items = args[0]        # hdfコンテンツ
        self.item_chain = args[0]       # ここまでのタグをリストで渡す
        self.spc = args[1]              # インデントスペース
        self.hdffilename = args[2]      # 入力ファイル名
        self.tag_print = args[3]        # タグのみ出力するか

    def run(self):
        '''
        スレッド実行開始
        '''

        sys.stderr.write("<%s><%s>mutilprocessing class type start\n"%(self.item_chain[0], self.item_chain[1]))
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
    
class erfh5Object(object):
    '''
    erfh5ファイルを読み、XMLや辞書に書き出す
    '''

    def __init__(self, tag_print=None):
        '''
        コンストラクタ
        '''

        self.elems = None
        self.coordinate = None
        self.tag_print = tag_print
        self.debug_print = False
        self.state_line2_strains = {}
        self.state_line2_stresses = {}
        self.state_node_temperatures = {}
        self.state_quad4_strains = {}
        self.state_quad4_stresses = {}

    def readErfh5FileToXML(self, erfh5_file, erfh5_xml=None):
        '''
        erfh5ファイルを読み込みXMLファイルへ書き出す
        erfh5_xmlがNoneの場合（ファイル名を指定しない場合）python辞書を作成し、返す
        @param erfh5_file (string)
        @param erfh5_xml (string)

        '''
        ffile = h5py.File(erfh5_file, "r")
        spc = ""
        hdf_dict = {}
        if erfh5_xml is not None:
            erfh5_xml_object = open(erfh5_xml, "w")
            if self.tag_print is True:
                print('<?xml version="1.0" encoding="UTF-8"?>')
            erfh5_xml_object.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        for item in ffile:
            #print("%s | %s : %s"%(spc, item, ffile[item]))
            if item == "post":
                continue
            if erfh5_xml is not None:
                if self.tag_print is True:
                    print('<%s>'%item)
                erfh5_xml_object.write('<%s>\n'%item)
            if isinstance(ffile[item], h5py.Dataset) is True:
                pass
            elif len(ffile[item]) != 0:
                if erfh5_xml is None:
                    hdf_dict[item] = self.erfh5ToDict(ffile[item], item, spc)
                elif self.tag_print is True:
                    hdf_dict[item], valueid = self.erfh5ToXMLFileOnlyTags(ffile[item], item, spc)
                else:
                    hdf_dict[item], valueid = self.erfh5ToXMLFileOnlyTags(ffile[item], item, spc)
                    #hdf_dict[item] = self.erfh5ToXMLFile(ffile[item], item, spc, erfh5_xml_object)
                    #for value in hdf_dict[item]:
                    #    erfh5_xml_object.write('%s%s\n'%(spc, value))
            if erfh5_xml is not None:
                erfh5_xml_object.write('</%s>\n'%item)
                if self.tag_print is True:
                    print('</%s>'%item)
    
        if erfh5_xml is not None:
            erfh5_xml_object.close()

        return hdf_dict

    def erfh5ToXMLFileMultiprocess(self, item_chain, spc, hdffilename, tag_print):
        '''
        マルチプロセス実行開始
        @param ffile                      # hdf_object
        @param item_chain = args[0]       # ここまでのタグをリストで渡す
        @param spc = args[1]              # インデントスペース
        @param hdffilename = args[2]      # 入力ファイル名
        @param tag_print = args[3]        # タグのみ出力するか
        '''

        self.item_chain = item_chain
        self.spc = spc
        self.hdffilename = hdffilename
        self.tag_print = tag_print

        sys.stderr.write("<%s><%s>mutilprocessing start\n"%(self.item_chain[0], self.item_chain[1]))
        sys.stderr.flush()

        # erhf5ファイル開く
        #hdf_object = h5py.File(self.hdffilename, "r")

        # xmlファイル開く
        erfh5_xml = "%s_%s.xml"%(self.item_chain[0], self.item_chain[1])
        xmlfileobject = open(erfh5_xml, "w")

        spc = self.spc
        for tag in self.item_chain:
            xmlfileobject.write("%s<%s>\n"%(spc, tag))
            spc += "  "
    
        for item in self.hdf_object:
            if item == "post":
                continue
            for tag2 in self.hdf_object[item]:
                if tag2 == self.item_chain[0]:
                    for tag3 in self.hdf_object[item][tag2]:
                        if tag3 == self.item_chain[1]:
                            self.erfh5ToXMLFileMultiprocessRecursive(self.hdf_object[item][tag2][tag3], self.item_chain, spc, xmlfileobject, self.tag_print)

        spc = spc[0:-2]

        for tag in self.item_chain[::-1]:
            xmlfileobject.write("%s</%s>\n"%(spc, tag))
            spc = spc[0:-2]

        xmlfileobject.close()

    def erfh5ToXMLFileMultiprocessRecursive(self, hdf_items, item_chain, spc, xmlfileobject, tag_print):
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
                if self.erfh5ToXMLFileMultiprocessRecursive(next_hdf_item, item_chain, spc, xmlfileobject, tag_print) is False:
                    pass
                #if tag_print is True:
                #    print('%s</%s>'%(spc, item))
                xmlfileobject.write('%s</%s>\n'%(spc, item))
    
        return True

    def readErfh5FileToXMLByMulti(self, erfh5_file, multi_type="thread"):
        '''
        erfh5ファイルを読み込みXMLファイルへスレッドを使用して並列または並行に書き出す
        erfh5_xmlがNoneの場合（ファイル名を指定しない場合）python辞書を作成し、返す
        @param erfh5_file (string)
        @param erfh5_xml (string)
        @param multi_type (string)

        '''
        self.hdf_object = h5py.File(erfh5_file, "r")
        spc = ""
        hdf_dict = {}
        erfh5_xml = os.path.basename(erfh5_file).split(".")[0] + ".xml"
        erfh5_xml_object = open(erfh5_xml, "w")
        if self.tag_print is True:
            print('<?xml version="1.0" encoding="UTF-8"?>')
        erfh5_xml_object.write('<?xml version="1.0" encoding="UTF-8"?>\n')

        ths = {}
        th_dicts = []
        root_tag = ""
        for item in self.hdf_object:
            #print("%s | %s : %s"%(spc, item, self.hdf_object[item]))
            if item == "post":
                continue
            if erfh5_xml is not None:
                if self.tag_print is True:
                    print('<%s>'%item)
                erfh5_xml_object.write('<%s>\n'%item)
                root_tag = item
            if isinstance(self.hdf_object[item], h5py.Dataset) is True:
                pass
            elif len(self.hdf_object[item]) != 0:             # 2段階目のタグ以下
                for tag2 in self.hdf_object[item]:
                    if tag2 == "erfheader":
                        continue
                    for tag3 in self.hdf_object[item][tag2]:
                        #if tag3 != "state000000000009" and tag3 != "state000000000006":
                        #    continue
                        tag3xmlfile = "%s_%s.xml"%(tag2, tag3)
                        tags = []
                        tags.append(tag2)
                        tags.append(tag3)
                        #hdf_item = self.hdf_object[item][tag2][tag3]
                        #th_dicts.append(hdf_item)
                        if multi_type == "multiprocess":
                            #t = multiprocessing.Process(target=xml_multiprocess, args=(self.hdf_object[item][tag2][tag3], tags, "  ", tag3xmlfile, False,))
                            #t = xml_multiprocess(args=(tags, "  ", erfh5_file, False,))
                            #ths["%s:%s"%(tag2, tag3)] = xml_multiprocess(args=(tags, "  ", erfh5_file, False,))
                            #ths["%s:%s"%(tag2, tag3)] = multiprocessing.Process(target=self.erfh5ToXMLFileMultiprocess, args=(tags, "  ", erfh5_file, False,))
                            ths["%s:%s"%(tag2, tag3)] = shell_thread(args=(tags, "  ", erfh5_file, False,))
                        else:
                            ths["%s:%s"%(tag2, tag3)] = xml_thread(args=(self.hdf_object[item][tag2][tag3], tags, "  ", tag3xmlfile, False,))
                        ths["%s:%s"%(tag2, tag3)].start()
                        #ths.append(t)
                        time.sleep(2.0)

            if self.tag_print is True:
                print('</%s>'%item)
    
        # スレッドの待ち合わせ
        sys.stderr.write("waiting thread process\n")
        sys.stderr.flush()
        for th in ths:
            ths[th].join()

        sys.stderr.write("all thread process ended.\n")
        sys.stderr.flush()

        # ファイルの取り出しと、本体への合流
        for th in ths:
            xml_file_name = "%s_%s.xml"%(th.split(":")[0], th.split(":")[1])
            infile = open(xml_file_name, "r")
            erfh5_xml_object.write(infile.read())
            infile.close()

        erfh5_xml_object.write('</%s>\n'%root_tag)
        erfh5_xml_object.close()

        # 本体作成後部分ファイルは削除
        for th in ths:
            xml_file_name = "%s_%s.xml"%(th.split(":")[0], th.split(":")[1])
            os.remove(xml_file_name)

        sys.stderr.write("xml file created.\n")
        sys.stderr.flush()

        return erfh5_xml

    def readXML(self, xmlfile):
        '''
        erfh5を変換したXMLを読み込み、内部に保持する。
        @param xmlfile (string)
        '''

        if os.path.exists(xmlfile) is False:
            return False, "cannot find xml file(%s)"%xmlfile
    
        tree = ET.parse(xmlfile)
        self.elems = tree.getroot()

        coordinate = self.elems.find(".//constant/entityresults/NODE/COORDINATE/ZONE1_set0/erfblock/res").text.split("], [")
        self.coordinate = []
        for item in coordinate:
            self.coordinate.append(item)

        return True, "read xml contents"
        
    def getStateElementFromerfh5XML(self, xmlfile):
        '''
        HDF5をXMLに変換したXMLを読んで、signlestate:state00000000000?（複数アリ？）の辞書を返す。
        多分対象は
        * .//signlestate/state00000000000?/entityresults/NODE/TEMPERATURE_NOD/ZONE1_set0/erfblock/res
        * .//signlestate/state00000000000?/entityresults/NODE/TEMPERATURE_NOD/ZONE1_set0/erfblock/res
        以下のfoat32なリストから最大値を取得する
        @param xmlfile (string) XMLファイル名
        '''
    
        ret, mess = self.readXML(xmlfile)
        state_items = self.elems.findall(".//singlestate")
    
        # 値の収集
        for state in state_items:
            # 温度
            if state.find(".//entityresults/NODE/TEMPERATURE_NOD/ZONE1_set0/erfblock/res") is not None:
                for item in state:
                    node = item.find(".//entityresults/NODE/TEMPERATURE_NOD/ZONE1_set0/erfblock/res")
                    if node is None:
                        continue
                    data = node.text.split(", ")
                    if self.debug_print is True:
                        sys.stderr.write("tag = %s in %d\n"%(item.tag, len(data)))
                    count = 1
                    #print("reading temerature data in tag(%s)"%item.tag)
                    for value in data:
                        key = "%s:%05d"%(item.tag, count)
                        self.state_node_temperatures[key] = value
                        count += 1
            # STRAINS on LINE2
            if state.find(".//entityresults/LINE2/STRAINS_ELE/ZONE1_set0/erfblock/res") is not None:
                for item in state:
                    node = item.find(".//entityresults/LINE2/STRAINS_ELE/ZONE1_set0/erfblock/res")
                    if node is None:
                        continue
                    data = node.text.split("], [")
                    if data[0][0] == "[":
                        data[0] = data[0][1:]
                    if data[-1][-1] == "]":
                        data[-1] = data[-1][0:-1]
                    if self.debug_print is True:
                        sys.stderr.write("tag = %s in %d\n"%(item.tag, len(data)))
                    count = 1
                    for value in data:
                        key = "%s:%05d"%(item.tag, count)
                        self.state_line2_strains[key] = value
                        count += 1
            # STRESSES on LINE2
            if state.find(".//entityresults/LINE2/STRESSES_ELE/ZONE1_set0/erfblock/res") is not None:
                for item in state:
                    node = item.find(".//entityresults/LINE2/STRESSES_ELE/ZONE1_set0/erfblock/res")
                    if node is None:
                        continue
                    data = node.text.split("], [")
                    if data[0][0] == "[":
                        data[0] = data[0][1:]
                    if data[-1][-1] == "]":
                        data[-1] = data[-1][0:-1]
                    if self.debug_print is True:
                        sys.stderr.write("tag = %s in %d\n"%(item.tag, len(data)))
                    count = 1
                    for value in data:
                        key = "%s:%05d"%(item.tag, count)
                        self.state_line2_stresses[key] = value
                        count += 1
            # STRAINS on QUAD4
            if state.find(".//entityresults/QUAD4/STRAINS_ELE/ZONE1_set0/erfblock/res") is not None:
                for item in state:
                    node = item.find(".//entityresults/QUAD4/STRAINS_ELE/ZONE1_set0/erfblock/res")
                    if node is None:
                        continue
                    data = node.text.split("], [")
                    if data[0][0] == "[":
                        data[0] = data[0][1:]
                    if data[-1][-1] == "]":
                        data[-1] = data[-1][0:-1]
                    if self.debug_print is True:
                        sys.stderr.write("tag = %s in %d\n"%(item.tag, len(data)))
                    count = 1
                    for value in data:
                        key = "%s:%05d"%(item.tag, count)
                        self.state_quad4_strains[key] = value
                        count += 1
            # STRESSES on QUAD4
            if state.find(".//entityresults/QUAD4/STRESSES_ELE/ZONE1_set0/erfblock/res") is not None:
                for item in state:
                    node = item.find(".//entityresults/QUAD4/STRESSES_ELE/ZONE1_set0/erfblock/res")
                    if node is None:
                        continue
                    data = node.text.split("], [")
                    if data[0][0] == "[":
                        data[0] = data[0][1:]
                    if data[-1][-1] == "]":
                        data[-1] = data[-1][0:-1]
                    if self.debug_print is True:
                        sys.stderr.write("tag = %s in %d\n"%(item.tag, len(data)))
                    count = 1
                    for value in data:
                        key = "%s:%05d"%(item.tag, count)
                        self.state_quad4_stresses[key] = value
                        count += 1

    def getMaxTempFromerfh5XML(self, xmlfile):
        '''
        HDF5をXMLに変換し、そのXMLを読んで、signlestate:state00000000000?（複数アリ？）の
        .//signlestate/state00000000000?/entityresults/NODE/TEMPERATURE_NOD/ZONE1_set0/erfblock/res
        以下のfoat32なリストから最大値を取得する
        @param xmlfile (string) XMLファイル名
        '''
    
        self.getStateElementFromerfh5XML(xmlfile)
    
        # 最大値取得
        max_temp = 0
        max_key = None
        for item in self.state_node_temperatures:
            #print("比べています  対象: %s"%item)
            if max_temp < float(self.state_node_temperatures[item]):
                max_temp = float(self.state_node_temperatures[item])
                max_key = item

        if max_key is None:
            return False, "There is no NODE/TEMPARETURE_NOD elements"

        index = int(max_key.split(":")[1]) - 1
        sys.stderr.write("max is at %s(%s)\n"%(max_key, self.coordinate[index]))
        return True, max_temp
    
    def erfh5ToXMLFile(self, hdf_items, item_chain, spc, xmlfileobject):
        '''
        HDF5の内容を再帰的に読んで、XMLファイルを作成する。
        @param hdf_items (object)
        @param item_chain (string)
        @param spc (string)
        @param xmlfileobject (object)
        @retval (bool)
        '''
    
        spc += "  "
    
        hdf_dict = {}
        for item in hdf_items:
            item_chain_new = item_chain + "/" + item
            if isinstance(hdf_items[item], h5py.Dataset) is True:
                hdf_dict[item] = []
                if len(hdf_items[item].shape) == 0:
                    #xmlfileobject.write('%s<%s shape="0" type="%s">\n'%(spc, item, hdf_items[item].value.dtype))
                    if self.tag_print is True:
                        print('%s<%s shape="0" type="%s">'%(spc, item, hdf_items[item][()].dtype))
                    xmlfileobject.write('%s<%s shape="0" type="%s">'%(spc, item, hdf_items[item][()].dtype))
                    xmlfileobject.write('%s'%hdf_items[item][()])
                elif len(hdf_items[item].shape) == 1:
                    #hdf_dict[item] = hdf_items[item].value.tolist()
                    #xmlfileobject.write('%s<%s shape="%s" type="%s">\n'%(spc, item, hdf_items[item].shape[0], hdf_items[item].value.dtype))
                    if self.tag_print is True:
                        print('%s<%s shape="%s" type="%s">'%(spc, item, hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    xmlfileobject.write('%s<%s shape="%s" type="%s">'%(spc, item, hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    #xmlfileobject.write('%s'%spc)
                    #for value in hdf_items[item].value:
                    n = 0
                    for value in hdf_items[item][()]:
                        if n == 0:
                            xmlfileobject.write('%s'%value)
                        else:
                            xmlfileobject.write(', %s'%value)
                        n += 1
                    #xmlfileobject.write('\n')
                elif len(hdf_items[item].shape) == 2:
                    if self.tag_print is True:
                        print('%s<%s shape="%s x %s" type="%s">'%(spc, item, hdf_items[item].shape[1], hdf_items[item].shape[0], hdf_items[item][()].dtype))
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
                    if self.tag_print is True:
                        print('%s<%s shape="%s x %s x %s" type="%s">'%(spc, item, hdf_items[item].shape[2], hdf_items[item].shape[1], hdf_items[item].shape[0], hdf_items[item][()].dtype))
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
                if self.tag_print is True:
                    print('%s</%s>'%(spc, item))
            elif len(hdf_items[item]) != 0:
                #print("%s | %s : "%(spc, item))
                #print('%s<%s type="%s">'%(spc, item, type(hdf_items[item])))
                if self.tag_print is True:
                    print('%s<%s type="HDF5 Group Tag">'%(spc, item))
                #xmlfileobject.write('%s<%s type="%s">\n'%(spc, item, type(hdf_items[item])))
                xmlfileobject.write('%s<%s type="HDF5 Group Tag">\n'%(spc, item))
                if self.erfh5ToXMLFile(hdf_items[item], item_chain_new, spc, xmlfileobject) is False:
                    pass
                if self.tag_print is True:
                    print('%s</%s>'%(spc, item))
                xmlfileobject.write('%s</%s>\n'%(spc, item))
    
        return True

    def erfh5ToXMLFileOnlyTags(self, hdf_items, item_chain, spc, valueId=0):
        '''
        HDF5の内容を再帰的に読んで、XMLファイルのタグのみを出力する
        @param hdf_items (object)   HDF5クラスインスタンス
        @param item_chain (string)　ここまでのタグツリー
        @param spc (string)         XMLの整形用空白文字列
        @param valueId (int)        辞書の位置を表すID（０から
        @retval (bool)
        '''
    
        spc += "  "
    
        hdf_dict = {}
        for item in hdf_items:
            item_chain_new = item_chain + "/" + item
            if isinstance(hdf_items[item], h5py.Dataset) is True:
                hdf_dict[item] = {}
                if self.tag_print is True:
                    if len(hdf_items[item].shape) == 0:
                        print('%s<%s shape="0" type="%s">'%(spc, item, hdf_items[item][()].dtype))
                    elif len(hdf_items[item].shape) == 1:
                        print('%s<%s shape="%s" type="%s">'%(spc, item, hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    elif len(hdf_items[item].shape) == 2:
                        print('%s<%s shape="%s x %s" type="%s">'%(spc, item, hdf_items[item].shape[1], hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    elif len(hdf_items[item].shape) == 3: 
                        print('%s<%s shape="%s x %s x %s" type="%s">'%(spc, item, hdf_items[item].shape[2], hdf_items[item].shape[1], hdf_items[item].shape[0], hdf_items[item][()].dtype))
                    else:
                        sys.stderr.write("%s shape = %s type=%s\n"%(item, str(hdf_items[item].shape), hdf_items[item].dtype)) 
                hdf_dict[item]["contents"] = ""
                hdf_dict[item]["TAG_ID"] = "TAG%015d"%valueId
                valueId += 1
                if self.tag_print is True:
                    print('%s</%s>'%(spc, item))
            elif len(hdf_items[item]) != 0:
                if self.tag_print is True:
                    print('%s<%s type="HDF5 Group Tag">'%(spc, item))
                hdf_dict[item] = {}
                hdf_dict[item]["TAG_ID"] = "TAG%015d"%valueId
                valueId += 1
                hdf_dict[item]["contents"], valueId = self.erfh5ToXMLFileOnlyTags(hdf_items[item], item_chain_new, spc, valueId)
                if self.tag_print is True:
                    print('%s</%s>'%(spc, item))
            else:
                #sys.stderr.write('%s type="%s"\n'%(item, str(hdf_items[item][()].dtype)))
                sys.stderr.write('%s type="%s"\n'%(item, type(hdf_items[item])))
    
        return hdf_dict, valueId
    
    def erfh5ToDict(self, hdf_items, item_chain, spc):
        '''
        HDF5の内容を再帰的に読んで、辞書を構築して返す
        @param hdf_items (object)
        @param item_chain (string)
        @param spc (string)
        @retval (dict)
        '''
    
        spc += " "
    
        hdf_dict = {}
        for item in hdf_items:
            item_chain_new = item_chain + "/" + item
            if isinstance(hdf_items[item], h5py.Dataset) is True:
                #print("%s | ----- %s ----"%(spc, item_chain_new))
                #print("%s | ----- %s / shape = %s / type = %s ----"%(spc, item, hdf_items[item].shape, type(hdf_items[item].value)))
                #print("%s | type = %s"%(spc, type(hdf_items[item])))
                #print("%s |    : "%spc, hdf_items[item].value)
                hdf_dict[item] = []
                if len(hdf_items[item].shape) == 0:
                    hdf_dict[item].append(hdf_items[item].value)
                elif len(hdf_items[item].shape) == 1:
                    hdf_dict[item] = hdf_items[item].value.tolist()
                else:
                    for ndarray in hdf_items[item]:
                        hdf_dict[item].append(ndarray.tolist())
                    #for num in range(hdf_items[item].shape[0]):
                    #    if isinstance(hdf_items[item][num], numpy.int32) is True:
                    #        hdf_dict[item].append(int(hdf_items[item][num]))
                    #    elif isinstance(hdf_items[item][num], numpy.float32) is True:
                    #        hdf_dict[item].append(int(hdf_items[item][num]))
                    #    else:
                    #        hdf_dict[item].append(hdf_items[item][num].tolist())
            elif len(hdf_items[item]) != 0:
                #print("%s | %s : "%(spc, item))
                hdf_dict[item] = self.erfh5ToDict(hdf_items[item], item_chain_new, spc)
    
        return hdf_dict

def print_help():
    '''
    '''

    sys.stderr.write("Usage:\n")
    sys.stderr.write("python %s <erfh5 file> [--xml|--xml-with-tag|--xml-by-thread|--xml-by-multiprocess|--dict|--help]\n"%sys.argv[0])
    sys.stderr.write("     --xml : create xml file\n")
    sys.stderr.write("     --xml-by-thread : create xml file using by multi-thread.\n")
    sys.stderr.write("     --xml-by-multiprocess : create xml file using by multi-process.\n")
    sys.stderr.write("     --xml-with-tag : create xml file and print all tag without text contents\n")
    sys.stderr.write("     --dict : create python dict\n")
    sys.stderr.write("     --help : this message\n")
    sys.exit(1)

def main():
    '''
    テスト用開始点
    '''

    if len(sys.argv) < 2:
        print_help()
        print("please define <erfh5 file>")

    erfh5_file = sys.argv[1]
    erfh5_xml = None
    if sys.argv == "--help":
        print_help()

    if os.path.exists(erfh5_file) is False:
        sys.stderr.write("cannot read erfh5 file(%s) in current directory(./%s)"%(erfh5_file, os.path.basename(os.getcwd())))
        sys.exit(1)

    if ("--xml-with-tag" in sys.argv) is True:
        erfh5 = erfh5Object(tag_print=True)
    else:
        erfh5 = erfh5Object()

    if ("--xml" in sys.argv) is True or ("--xml-with-tag" in sys.argv) is True:
        erfh5_xml = os.path.basename(erfh5_file).split(".")[0] + ".xml"
        erfh5.readErfh5FileToXML(erfh5_file, erfh5_xml)
    elif ("--xml-by-thread" in sys.argv) is True:
        print("xml write using by threading process\n")
        erfh5_xml = erfh5.readErfh5FileToXMLByMulti(erfh5_file)
    elif ("--xml-by-multiprocess" in sys.argv) is True:
        print("xml write using by multi-processing\n")
        erfh5_xml = erfh5.readErfh5FileToXMLByMulti(erfh5_file, "multiprocess")
    elif ("--dict" in sys.argv) is True:
        ffile = h5py.File(erfh5_file, "r")
        hdf_dict = {}
        spc = ""
        for item in ffile:
            if item == "post":
                continue
            hdf_dict = erfh5.erfh5ToDict(item, "", spc)

    elif ("--max-temp" in sys.argv) is True:
        erfh5_xml = os.path.basename(erfh5_file).split(".")[0] + ".xml"
        if os.path.exists(erfh5_xml) is False:
            print("not found xml file(%s)"%erfh5_xml)
            sys.exit(1)
        ret, max_value = erfh5.getMaxTempFromerfh5XML(erfh5_xml)
        if ret is True:
            #print("MAX Temperature is %f"%max_value)
            print("%f"%max_value)
    else:
        print(str(sys.argv))

    #print(hdf_dict)
if __name__ == '__main__':
    main()
