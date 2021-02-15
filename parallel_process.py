#!/usr/local/python2.7/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) The University of Tokyo and
# National Institute for Materials Science (NIMS). All rights reserved.
# This document may not be reproduced or transmitted in any form,
# in whole or in part, without the express written permission of
# the copyright owners.

'''
並列実行のサポート
'''

import sys, os
import multiprocessing
import threading
import subprocess
import time

class job_thread(threading.Thread):
    '''
    スレッド処理用クラス
    '''

    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        '''
        コンストラクタ
        実行したい関数はargs[0]にセットしておくこと
        引数は、辞書型(kwargs)にセットしておくこと
        '''

        threading.Thread.__init__(self, group=group, target=target, name=name, daemon=daemon)

        self.thread_args = args
        self.thread_kwargs = kwargs
        self.thread_function = args[0]
        self.function_returns = None

    def run(self):
        '''
        スレッド実行用関数
        '''

        self.function_returns = self.thread_function(self.thread_kwargs)

    def getReturn(self):
        '''
        処理後の関数戻り値の返却
        '''

        return self.function_returns

class parallelSupport(object):
    '''
    並列実行サポート
    '''

    def __init__(self, process_type="subprocess", max_parallel=None, fail_then_end=True):
        '''
        初期化
        @param process_type (string) subprocess/threading/multiprocessing
        @param max_parallel (int) Max Parallel number. None=same as core number
        @param fail_then_end (bool) True:エラーの際、これ以上新規に実行しない。実行中のものは終了まで待つ。
        '''

        self.core_num = multiprocessing.cpu_count()
        self.process_type = process_type
        self.process_table = []
        self.count = -1
        self.noContinue = fail_then_end
        if max_parallel is None:
            self.max_parallel = self.core_num
        else:
            try:
                self.max_parallel = int(max_parallel)
            except:
                self.max_parallel = self.core_num
        print("最大実行数は %d です。"%self.max_parallel)
        print("並列タイプは %s です。"%self.process_type)

    def clear(self):
        '''
        再利用のためのクリア
        '''

        self.count = -1
        self.process_table = []

    def add_process(self, cmd, *args, **kargs):
        '''
        並列処理の追加
        @param cmd (string) コマンド列または関数
        '''

        self.count += 1
        if cmd == "threading":          # threadingなのに関数名が無い場合は例外発生
            if len(args) == 0:
                raise ValueError("no function name for threading type")

        self.process_table.append({"cmd":cmd, "args":args, "kargs":kargs, "instance":None, "No":self.count, "status":"not_exec", "stdout":None, "stderr":None})
        return self.count

    def get_processes(self):
        '''
        プロセステーブルの返却
        @retval リスト
        '''

        return self.process_table

    def exec_parallel(self):
        '''
        '''

        if len(self.process_table) == 0:
            return False, "並列処理したいプロセス登録がありません。"

        print("全実行数は %d です。"%len(self.process_table))
        if self.process_type == "subprocess":
            # subprocessタイプの並列処理
            return self._exec_parallel_subprocess()
        elif self.process_type == "threading":
            # theadingタイプの並列処理
            return self._exec_parallel_threading()
        elif self.process_type == "multiprocessing":
            # multiprocessingタイプの並列処理
            pass

        return False, "並列処理タイプ(subprocess/threading/multiprocess)が指定されていません。"

    def _exec_parallel_threading(self):
        '''
        threading版並列処理の実行
        '''

        all_num = len(self.process_table)
        exec_num = 0
        noNewExec = False                           # True:これ以上の新規実行を行わない
        while True:
            if exec_num <= self.max_parallel:        # 実行中の数と最大希望実行数との比較
                # 未実行があれば実行する
                isExec = False
                for item in self.process_table:
                    if item["status"] == "not_exec" and noNewExec is False:
                        print("No.%d のスレッドを実行します。"%item["No"])
                        item["instance"] = job_thread(args=item["args"], kargs=["kargs"])
                        item["instance"].start()
                        item["status"] = "executing"
                        exec_num += 1
                        isExec = True
                        break
                if isExec is True:
                    continue
            # 全部実行済みなら終了する
            isAllEnd = True
            for item in self.process_table:
                if item["status"] != "end":
                    isAllEnd = False
            if isAllEnd is True:
                #print("%d終了"%all_num)
                break
            # 終了したものがあるか確認する。
            for item in self.process_table:
                if item["status"] != "executing":
                    continue
                if item["instance"].is_alive() is False:
                    print("No.%d のスレッドが終了しました。"%item["No"])
                    # 終了！
                    item["status"] = "end"
                    item["stdout"] = item["instance"].getReturn()
                    exec_num -= 1
            time.sleep(2.0)

        return True, ""

    def _exec_parallel_subprocess(self):
        '''
        subprocess版並列処理の実行
        '''

        all_num = len(self.process_table)            # 全プロセス数
        exec_num = 0                                 # 実行中のプロセス数
        isExecOk = True
        noNewExec = False                           # True:これ以上の新規実行を行わない
        while True:
            if exec_num <= self.max_parallel:        # 実行中の数と最大希望実行数との比較
                # 未実行があれば実行する
                isExec = False
                for item in self.process_table:
                    if item["status"] == "not_exec" and noNewExec is False:
                        print("No.%d のsubprocessを開始します。"%item["No"])
                        item["instance"] = subprocess.Popen(item["cmd"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        item["status"] = "executing"
                        exec_num += 1
                        isExec = True
                        break
                if isExec is True:
                    time.sleep(2.0)
                    continue
            # 実行中がなければ終了する。
            isAllEnd = True
            for item in self.process_table:
                if item["status"] == "executing":
                    isAllEnd = False
            if isAllEnd is True:
                #print("%d終了"%all_num)
                break
            # 終了したものがあるか確認する。
            for item in self.process_table:
                if item["status"] != "executing":
                    continue
                if item["instance"].poll() is not None:
                    print("No.%d のsubprocessが終了しました。"%item["No"])
                    item["status"] = "end"
                    exec_num -= 1
                    outputs = item["instance"].communicate()
                    item["stdout"] = outputs[0]
                    item["stderr"] = outputs[1]
                    if item["instance"].returncode != 0:
                        isExecOk = False
                        message = item["cmd"]
                        break
            #print("waiting 2s")
            if isExecOk is not True:                # 実行が失敗したものあった。
                if self.noContinue is True:         # 新規実行どうするか
                    noNewExec = True                # 新規実行はしない
                    #return False, message
            time.sleep(2.0)
    
        return True, ""
