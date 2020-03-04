#!/usr/bin/python3.6
# -*- coding: utf-8 -*-

from miapi.system.command_line_interpreter import CommandLineInterpreter
from miapi.system import runinfo
import subprocess
import shutil
import os, sys
import datetime
import uuid
import signal
import io
from glob import glob

# ソルバー起動ログ格納ディレクトリ
SOLVER_LOGFILE = "/home/misystem/assets/workflow/site00002/solver_logs/solver_execute.log"

'''
MI-APIを使用したツールの補助ライブラリ
'''

class MIApiCommandClass(object):
    '''
    MI-APIを使用した
    '''

    def __init__(self, uid=None, token=None):
        '''
        コンストラクタ
        '''

        if uid is not True:
            pass

        if token is not True:
            pass

        self.input_port_names = {}
        self.input_filenames = {}
        self.input_realnames = {}
        self.input_realname_tables = {}	
        self.output_port_names = {}
        self.output_filenames = {}
        self.output_realnames = {}
        #self.output_realname_tables = {}
        self.tool_directory = None
        self.RunInfo = {}
        self.translate_output = False
        self.solver_logfile = None
        self.solver_name = None
        self.solver_id = str(uuid.uuid4())
        # このパッケージを使用した上位プログラムが
        # Torqueに直にジョブを流した時に
        # MIシステムのラン終了でそのジョブが終了出きるように、
        # ここにリストを作っておく。
        self.torque_job_list = []

        # signal定義（ワークフロー停止、Torquによるjob削除対応
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGHUP, self.signal_handler)
        signal.signal(signal.SIGQUIT, self.signal_handler)
        signal.signal(signal.SIGILL, self.signal_handler)
        signal.signal(signal.SIGTRAP, self.signal_handler)
        signal.signal(signal.SIGIOT, self.signal_handler)
        #signal.signal(signal.SIGEMT, self.signal_handler)
        signal.signal(signal.SIGFPE, self.signal_handler)
        signal.signal(signal.SIGBUS, self.signal_handler)
        signal.signal(signal.SIGSEGV, self.signal_handler)
        signal.signal(signal.SIGSYS, self.signal_handler)
        signal.signal(signal.SIGPIPE, self.signal_handler)
        signal.signal(signal.SIGALRM, self.signal_handler)

    def logwrite(self, mess, output_dir):
        '''
        ログ出力用関数。output_dirに出力先をセットする。
        @param mess(string)
        @param output_dir(ファイルディスクリプタ)
        @retval なし
        '''

        if isinstance(output_dir, io.TextIOWrapper) is False:
            output_dir = sys.stderr

        output_dir.write("%s %s\n"%((datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), mess)))
        output_dir.flush()

    def signal_handler(self, signum, frame):
        '''
        シグナル受け取り処理
        多くの場合、Torqu（またはMIntシステム）からの終了処理（のはず）
        残念ながらkill -9 は受け取れないらしい
        '''

        sys.stderr.write("%s catch end process signal(%d)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), signum))
        sys.stderr.flush()
        # 独自登録のTorqueジョブがあったら、停止する。
        if len(self.torque_job_list) != 0:
            for job in self.torque_job_list:
                sys.stderr.write("%s deleting job(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), job))
                sys.stderr.flush()
                p = subprocess("ssh headdev-cl qdel %s"%job, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.wait()

        sys.stderr.write("%s 終了\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), signum))
        sys.stderr.flush()
        sys.exit(0)

    def __del__(self):
        '''
        終了処理
        '''

        sys.stderr.write("%s 終了処理中...\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
        sys.stderr.flush()
        if self.solver_logfile is not None:
            self.solver_logfile.close()
        # 独自登録のTorqueジョブがあったら、停止する。
        if len(self.torque_job_list) != 0:
            for job in self.torque_job_list:
                sys.stderr.write("%s deleting job(%s)\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), job))
                sys.stderr.flush()
                p = subprocess("ssh headdev-cl qdel %s"%job, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                p.wait()

        sys.stderr.write("%s 終了\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")))
        sys.stderr.flush()

    def addTorqueJob(self, job_id):
        '''
        Torqueのジョブ番号の登録
        '''

        self.torque_job_list.append(job_id)

    def delTorqueJob(self, job_id):
        '''
        Torqueの登録してあるジョブリストから、job_idを削除する
        '''

        self.torque_job_list.remove(job_id)

    def log_solver_start(self):
        '''
        ソルバー実行開始記録
        '''

        if self.solver_logfile is not None:
            self.solver_logfile.write("%s: start: %s: %s: %s\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), self.solver_name, self.RunInfo["miwf_userid"], self.solver_id))

    def log_solver_emend(self):
        '''
        ソルバー実行異常終了記録
        '''

        if self.solver_logfile is not None:
            self.solver_logfile.write("%s: abnormal end: %s: %s: %s\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), self.solver_name, self.RunInfo["miwf_userid"], self.solver_id))

    def log_solver_normalend(self):
        '''
        ソルバー実行正常終了記録

        '''

        if self.solver_logfile is not None:
            self.solver_logfile.write("%s: normal end: %s: %s: %s\n"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), self.solver_name, self.RunInfo["miwf_userid"], self.solver_id))

    def setInportNames(self, inports):
        '''
        inputポートの辞書をセットする
        @param inports(dict)
        @retval セットした辞書の数
        '''

        if inports == None or len(inports) == 0:
            raise Exception("There are no inport names")

        self.input_port_names = inports

        print("%s set input port names"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), flush=True)
        return len(self.input_port_names)

    def setOutportNames(self, outports):
        '''
        outputポートの辞書をセットする
        @param outports(dict)
        @retval セットした辞書の数
        '''

        if outports == None or len(outports) == 0:
            raise Exception("There are no outport names")

        self.output_port_names = outports

        print("%s set output port names"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), flush=True)
        return len(self.output_port_names)

    def setRealName(self, input_realnames=None, output_realnames=None):
        '''
        ソルバー実行後の正確なファイル名をポートのファイル名に変更する
        @param realnames (dict)
        @retval なし
        '''

        #if input_realnames is None or len(input_realnames) == 0:
        #    raise Exception("There is no relaname and port name list")
        #if output_realnames is None or len(output_realnames) == 0:
        #    raise Exception("There is no relaname and port name list")

        self.input_realname_tables = input_realnames
        #self.output_realname_tables = output_realnames
        self.output_realnames = output_realnames

        print("%s set realname table"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), flush=True)

    def getFilenameAsPort(self, portname):
        '''
        初期化後にパラメータ列から、port名に対応するファイル名テーブルが作られている。
        port名から対応するファイル名を返す。
        ただし、必須でないものはNoneになっている。
        また存在しないポート名を指定した場合は、Falseが返る
        '''

        if (portname in self.input_filenames) is True:
            return self.input_filenames[portname]
        else:
            return False

    def Initialize(self, translate_input=False, translate_output=False, solver="", version="1.0.0"):
        '''
        MI-APIの初期化
        ポートに設定されたファイル名の取得
        ツールのディレクトリへの移動
        @param version(string)
        @retval なし
        '''

        if solver == "":
            self.solver_name = "unknown"
        else:
            self.solver_name = solver

        self.translate_output = translate_output
        if len(self.input_port_names) == 0:
            raise Exception("not set input port name(s)")

        for item in self.input_port_names:
            CommandLineInterpreter.define_inputport(item, self.input_port_names[item])

        for item in self.output_port_names:
            CommandLineInterpreter.define_outputport(item, self.output_port_names[item])

        CommandLineInterpreter.initialize()

        self.RunInfo["main_module_name"] = runinfo.main_module_name
        self.RunInfo["miwf_userid"] = runinfo.miwf_userid
        self.RunInfo["miwf_workflowid"] = runinfo.miwf_workflowid
        self.RunInfo["miwf_runid"] = runinfo.miwf_runid
        self.RunInfo["miwf_api_token"] = runinfo.miwf_api_token
        self.RunInfo["miwf_randomseed"] = runinfo.miwf_randomseed
        self.RunInfo["miwf_workdir"] = runinfo.miwf_workdir
        self.RunInfo["miwf_currentdir"] = runinfo.miwf_currentdir
        self.RunInfo["version"] = runinfo.version

        '''
        入力ポートのファイル名を取得し、ポート名:ファイル名 の辞書にする。
        '''

        for item in self.input_port_names:
            try:
                inputfile = CommandLineInterpreter.get_input_port_as_filepath(item)
                print("%s port name = %s is %s"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), item, inputfile), flush=True)
                self.input_filenames[item] = os.path.abspath(inputfile)

            except (FileNotFoundError):
                print('%s 入力ポートに指定したファイルが存在しません。(port名:%s)'%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), item), flush=True)
                self.input_filenames[item] = item   # 存在しない場合ポート名を格納する
                #sys.exit(1)

        '''
        出力ポートのファイル名を取得し、ポート名:ファイル名 の辞書にする。
        ツールのディレクトリ名も取得する
        '''

        tooldir = None
        for item in self.output_port_names:
            try:
                outputfile = CommandLineInterpreter.get_output_port_as_filepath(item)
            except (FileExistsError):
                print('%s 出力ポートに指定したファイルは既に存在します。(port名:%s)'%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), item), flush=True)
                #sys.exit()

            self.output_filenames[item] = outputfile
            tooldir = os.path.dirname(outputfile)

        if tooldir is not None:
            self.tool_directory = tooldir

        '''
        realname tableからそれぞれの_relanames辞書を作成する。(_01対策)
        '''
        # 入力側
        for item in self.input_port_names:
            filename = os.path.basename(self.input_filenames[item])
            #if (item in self.input_realname_tables) is True:
            for real_name in self.input_realname_tables:
                if filename.startswith(real_name) is True:
            #if (filename in self.input_realname_tables) is True:
                #self.input_realnames[filename] = self.input_realname_tables[item]
                    self.input_realnames[filename] = self.input_realname_tables[real_name]
                elif filename == "value":
                    self.input_realnames[item] = self.input_realname_tables[real_name]
                #print("%s input_port_name = %s / filename = %s / realname = %s"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), item, filename, self.input_realname_tables[real_name]))
        # 出力側
        #for item in self.output_port_names:
        #    filename = os.path.basename(self.output_filenames[item])
        #    if (item in self.output_realname_tables) is True:
        #        self.output_realnames[filename] = self.output_realname_tables[item]
        #        print("%s output_port_name = %s / filename = %s / realname = %s"%(item, filename, self.output_realname_tables[item]))

        '''
        ディレクトリ名が取得できていれば、移動する
        '''

        if self.tool_directory is not None:
            print("%s change current dir from %s to %s"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), os.getcwd(), tooldir), flush=True)
            os.chdir(self.tool_directory)

        # 入力ファイルのリンクをリアル名で作成する。
        if translate_input is True:
            for item in self.input_port_names:
                filename = os.path.basename(self.input_filenames[item])
                #print("key = %s(%s)"%(filename, self.input_port_names[item]))
                #if filename == "value":         # ループの場合スキップする
                #    continue
    
                if filename == "value":
                    filename = item
                input_dir = os.path.dirname(self.input_realnames[filename])
                real_name = os.path.basename(self.input_realnames[filename])
                current_dir = os.getcwd()
                if input_dir != "":
                    if os.path.exists(input_dir) is False:
                        os.mkdir(input_dir)
                    os.chdir(input_dir)
                #os.symlink(self.input_filenames[item], self.input_realnames[filename])
                print("create cymlink from %s -> %s"%(filename, real_name))
                os.symlink(self.input_filenames[item], real_name)
                os.chdir(current_dir)

        print("%s successfully intialized"%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), flush=True)
        print('%s host(%s) / user(%s)'%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), subprocess.getoutput('hostname'), subprocess.getoutput('whoami')), flush=True)
        print('%s ulimit -s(%s)'%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), subprocess.getoutput('ulimit -s')), flush=True)
        print('%s solver execute log (%s)'%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), SOLVER_LOGFILE), flush=True)
        args = " ".join(sys.argv)
        print('%s args : %s'%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), args))
        self.solver_logfile = open(SOLVER_LOGFILE, "a")

    def ExecSolver(self, cmd=None, not_errors=None, do_postprocess=True):
        '''
        ソルバーを実行します。
        @param cmd(string) 実行したいプログラムのパス、他。
        @param not_errors(bool) True:指定したコマンドが異常終了でもモジュール実行プログラムとして正常終了する Falseまたは指定し無い場合異常終了する。
        @param do_postprocess(bool) False:コマンド終了後出力ファイルとポート名のシンボリックリンクを作成しない
        @retval
        '''

        if cmd is None:
            raise Exception("There is no execute command.")

        print('%s exec command bellow'%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), flush=True)
        print(cmd, flush=True)
        self.log_solver_start()
        #ret = subprocess.call(cmd, shell=True, executable='/bin/bash')
        ret = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdouts = ""
        stderrs = ""
        # 実行中の標準出力と標準エラー出力を貯める
        while True:
            temp1 = ret.stdout.read()
            stdout = "%s\n"%temp1.decode('utf-8')
            temp2 = ret.stderr.read()
            stderr = "%s\n"%temp2.decode('utf-8')
            if temp1:
                stdouts += stdout
                sys.stdout.write("%s\n"%stdout)
                sys.stdout.flush()
            if temp2:
                stderrs += stderr
                sys.stderr.write("%s\n"%stderr)
                sys.stderr.flush()

            if not temp1 and ret.poll() is not None:
                break

        if ret.poll() != 0:
            print('%s failed execute program'%datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), flush=True)
            self.log_solver_emend()
            if not_errors is None:
                sys.exit(1)
            else:
                is_error = True
                for item in not_errors:
                    if ret == item:
                        is_error = False 
                if is_error is True:
                    sys.exit(1)

        self.log_solver_normalend()

        if do_postprocess is True:
            self.PostProcessing()

        return stdouts, stderrs

    def PreProcessing(self):
        '''
        ソルバー実行前の処理
        '''

        #if self.translate_output is True:
        #    for item in self.output_realnames:
        #        if os.path.exists(item) is True:
        #            shutil.copyfile(item, self.output_realnames[item])
        #        else:
        #            print("%s file %s is not exists in here(%s)"%(datetime.datetime.now(), item, os.getcwd()), flush=True)

    def PostProcessing(self):
        '''
        ソルバー実行後の処理
        '''

        if self.translate_output is True:
            for item in self.output_realnames:
                if os.path.exists(item) is True:
                    shutil.copyfile(item, self.output_realnames[item])
                else:
                    print("%s file %s is not exists in here(%s)"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), item, os.getcwd()), flush=True)

    def getSortedFileList(self, key):
        '''
        keyで取得できる（ワイルドカードなど）ファイルのならびを日付の古い純に並べて返す
        @param key(string)
        @retval list
        '''

        files = glob("./%s"%key)

        file_dict = {}
        for item in files:
            file_dict[item] = os.path.getctime(item)

        file_sort = sorted(file_dict.items(), key=lambda x:x[1])

        new_list = []
        for item in file_sort:
            new_list.append(item[0])

        return new_list
 
    def copyLastTimeStampfile(self, key, newfile):
        '''
        keyで取得できる（ワイルドカードなど）ファイルで最後に作成されたファイルをnewfile名にコピーする
        @param key(string)
        @param newfile(string)
        @retval なし
        '''

        file_sort = self.getSortedFileList("./%s"%key)
        #oldfile = files[-1]
        oldfile = file_sort[-1]
        print("%s copy from the last created file(%s) to the newfile name(%s)"%(datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), oldfile ,newfile), flush=True)
        shutil.copyfile(oldfile, newfile)

