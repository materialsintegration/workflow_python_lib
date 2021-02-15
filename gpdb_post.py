#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
GPDBの登録動作の監視
例
[2021-01-27 16:49:47] Fuseki     INFO  [2614] POST http://localhost:8030/fuseki/GPDB/upload
[2021-01-27 16:49:47] Fuseki     INFO  [2614] POST /GPDB :: 'upload' :: [multipart/form-data] ? 
[2021-01-27 16:49:47] Fuseki     INFO  [2614] Upload: Filename: by_memory.ttl, Content-Type=application/octet-stream, Charset=null => Turtle
[2021-01-27 16:49:47] Fuseki     INFO  [2614] Upload: Graph: default, 22 triple(s)
[2021-01-27 16:49:54] Fuseki     INFO  [2614] 200 OK (6.863 s)
この組み合わせの整合性を調査する。
'''

import sys, os

fuseki_log_file = sys.argv[1]

infile = open(fuseki_log_file)
lines = infile.read().split("\n")

post_table = {}
for item in lines:
    items = item.split()
    if len(items) <= 3:
        continue
    #print(item)
    if items[2] != "Fuseki":
        continue
    if (items[4] in post_table) is False:
        #print(str(items))
        if items[5] != "POST":
            continue
        endpoint = items[6].split("/")[-1]
        #print(endpoint)
        if endpoint != "upload" and endpoint != "sparql":
            continue
        post_table[items[4]] = {"start time":"%s %s"%(items[0], items[1]), "end time":"", "type":endpoint, "post":"OK", "RETURN":"NO"}
    else:
        if items[6] == "OK":
            post_table[items[4]]["RETURN"] = "OK"
            post_table[items[4]]["end time"] = "%s %s"%(items[0], items[1])

for item in post_table:
    print("%s to %21s %s %s : %s - %s"%(post_table[item]["start time"], post_table[item]["end time"], item, post_table[item]["type"], post_table[item]["post"], post_table[item]["RETURN"]))
