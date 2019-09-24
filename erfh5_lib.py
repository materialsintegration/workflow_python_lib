#!python3.6
# -*- coding: utf-8 -*-

'''
erfh5(HDF5u準拠のファイルフォーマット)用のライブラリ
'''

import h5py
import sys, os
import numpy
import xml.etree.ElementTree as ET

debug_print = True

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
                else:
                    hdf_dict[item] = self.erfh5ToXMLFile(ffile[item], item, spc, erfh5_xml_object)
                    #for value in hdf_dict[item]:
                    #    erfh5_xml_object.write('%s%s\n'%(spc, value))
            if erfh5_xml is not None:
                erfh5_xml_object.write('</%s>\n'%item)
                if self.tag_print is True:
                    print('</%s>'%item)
    
        if erfh5_xml is not None:
            erfh5_xml_object.close()
            return True
        else:
            return hdf_dict

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
        state = self.elems.find(".//singlestate")
    
        # 値の収集
        # 温度
        if state[0].find(".//entityresults/NODE/TEMPERATURE_NOD/ZONE1_set0/erfblock/res") is not None:
            for item in state:
                node = item.find(".//entityresults/NODE/TEMPERATURE_NOD/ZONE1_set0/erfblock/res")
                if node is None:
                    continue
                data = node.text.split(", ")
                if self.debug_print is True:
                    sys.stderr.write("tag = %s in %d\n"%(item.tag, len(data)))
                count = 1
                for value in data:
                    key = "%s:%05d"%(item.tag, count)
                    self.state_node_temperatures[key] = value
                    count += 1
        # STRAINS on LINE2
        if state[0].find(".//entityresults/LINE2/STRAINS_ELE/ZONE1_set0/erfblock/res") is not None:
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
        if state[0].find(".//entityresults/LINE2/STRESSES_ELE/ZONE1_set0/erfblock/res") is not None:
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
        if state[0].find(".//entityresults/QUAD4/STRAINS_ELE/ZONE1_set0/erfblock/res") is not None:
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
        if state[0].find(".//entityresults/QUAD4/STRESSES_ELE/ZONE1_set0/erfblock/res") is not None:
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
            if max_temp < float(self.state_node_temperatures[item]):
                max_temp = float(self.state_node_temperatures[item])
                max_key = item

        if max_key is None:
            return False, "There is no NODE/TEMPARETURE_NOD elements"

        index = int(max_key.split(":")[1]) - 1
        print("max is at %s(%s)"%(max_key, self.coordinate[index]))
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

def main():
    '''
    テスト用開始点
    '''

    print_help = False
    if len(sys.argv) == 1:
        print_help = True
        print("please define <erfh5 file>")

    erfh5_file = sys.argv[1]
    erfh5_xml = None
    param = None
    if len(sys.argv) == 3:
        param = sys.argv[2]
        if param == "--help":
            print_help = True

    if print_help is True:
        sys.stderr.write("Usage:\n")
        sys.stderr.write("python %s <erfh5 file> [--xml|--xml-with-tag|--dict|--help]\n"%sys.argv[0])
        sys.stderr.write("     --xml : create xml file\n")
        sys.stderr.write("     --xml-with-tag : create xml file and print all tag without text contents\n")
        sys.stderr.write("     --dict : create python dict\n")
        sys.stderr.write("     --help : this message\n")
        sys.exit(1)

    if os.path.exists(erfh5_file) is False:
        sys.stderr.write("cannot read erfh5 file(%s)"%erfh5_file)
        sys.exit(1)

    if param == "--xml-with-tag":
        erfh5 = erfh5Object(tag_print=True)
    else:
        erfh5 = erfh5Object()

    if param == "--xml" or param == "--xml-with-tag":
        erfh5_xml = os.path.basename(erfh5_file).split(".")[0] + ".xml"
        erfh5.readErfh5FileToXML(erfh5_file, erfh5_xml)
    elif param == "--dict":
        ffile = h5py.File(erfh5_file, "r")
        hdf_dict = {}
        spc = ""
        for item in ffile:
            if item == "post":
                continue
            hdf_dict = erfh5.erfh5ToDict(item, "", spc)

    ret, max_value = erfh5.getMaxTempFromerfh5XML(erfh5_xml)
    if ret is True:
        print("MAX Temperature is %f"%max_value)

    #print(hdf_dict)
if __name__ == '__main__':
    main()
