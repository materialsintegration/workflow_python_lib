# -*- coding: utf-8 -*-

## @file MBLogger.py
#  @brief MBLoggerのpython本体
#
# @author   H.Tomita(Penguin System Co.,Ltd.)
#
#- このpython codeはpython 3.6で開発しています。
#- このライブラリはclassとして実装しています。

# revision note:
#2019.01.07 H.Tomita first release
#2021/05/12 Y.Manaka
#  このスクリプトは他のスクリプトのためにworkflow_python_libに移しました。
#  /home/misystem/assets/modules/phase_transformation/scriptには後方互換性のためにシンボリックリンクとしました。
#  /home/misystem/assets/modules/phase_transformation/script/MBLogger.pyを編集した場合は、
#  /home/misystem/assets/modules/workflow_python_libでのcommit/pushをお願いします。

import sys
import datetime
import os
#c.f. http://qiita.com/amedama/items/b856b2f30c2f38665701
#c.f. http://symfoware.blog68.fc2.com/blog-entry-885.html
from logging import getLogger, StreamHandler, DEBUG, FileHandler

## @brief MBLoggerのpython本体(class)
class MBLogger(object):
    #------------------------------
    # 定数(class変数)
    #------------------------------
    ## @brief プログラム名
    PRG_NAME = "MBLogger.py"
    ## @brief バージョン
    VERSION = "1.0.0.0"
    ## @brief 終了ステータス OK
    MB_FILEIO_STATUS_OK = 0
    ## @brief 終了ステータス NG
    MB_FILEIO_STATUS_NG = 1
    ## @{
    # ステータスファイルに用いる拡張子部分
    # この文字列はステータスファイルの中にも出力させる。
    STATUS_SUFFIX_START = "0start"
    STATUS_SUFFIX_NORMAL_END = "1end"
    STATUS_SUFFIX_ERROR_END = "9error"
    ## @}

    ## @constructor
    def __init__(self):
        #------------------------------
        # private member変数(instance変数)
        #------------------------------
        ## @brief (private)対象プログラムのID
        self._TargetNameId = ""
        ## @brief (private)対象プログラムの作業ディレクトリの基準となるパス
        self._WorkingBaseDir = "."
        ## @brief (private)ログファイルのポインタ
        self._LogFilePtr = None
        ## @brief (private)起動処理時点のタイムスタンプ
        self._OverallStartTimespec = ""
        ## @brief (private)デバッグ用ログ
        self._Logger = getLogger(MBLogger.PRG_NAME)
        ## @brief (private)デバッグ用ログハンドラ
        # self._Handler = StreamHandler()
        # self._Handler = FileHandler(filename='/home/mimb/mi-mb/logs/MBLogger.log')
        self._Handler = FileHandler(filename='/dev/null')
        #続いて初期化処理
        self._Handler.setLevel(DEBUG)
        self._Logger.setLevel(DEBUG)
        self._Logger.addHandler(self._Handler)
        self._Logger.debug("checkpoint done constructor")

    ## @brief (public)起動処理
    def MB_fileio_start(self, name_id, working_base_dir, note=None):

        #起動時刻、対象プログラムのID、作業ディレクトリの基準パスを設定
        self._OverallStartTimespec = self._get_timestamp_string()
        self._TargetNameId = name_id
        self._WorkingBaseDir = working_base_dir
        self._Logger.debug("checkpoint _OverallStartTimespec=|{0:s}|".format(self._OverallStartTimespec))
        self._Logger.debug("checkpoint _TargetNameId=|{0:s}|".format(self._TargetNameId))
        self._Logger.debug("checkpoint _WorkingBaseDir=|{0:s}|".format(self._WorkingBaseDir))

        #起動ステータスファイルおよびログファイルを作成
        _ret = self._write_logfile(self.STATUS_SUFFIX_START, note)
        return(_ret)

    ## @brief (public)正常終了処理
    def MB_fileio_normal_end(self, note=None):
        #正常終了ステータスファイルおよびログファイルを作成
        _ret = self._write_logfile(self.STATUS_SUFFIX_NORMAL_END, note)
        return(_ret)

    ## @brief (public)エラー終了処理
    def MB_fileio_error_end(self, note=None):
        #エラー終了ステータスファイルおよびログファイルを作成
        _ret = self._write_logfile(self.STATUS_SUFFIX_ERROR_END, note)
        return(_ret)

    ## @brief (public)ログ出力
    #- ログファイルが開かれていない場合は何も出力しない。
    def MB_fileio_logging(self, note=None):
        #ログファイルを作成
        _ret = self._write_logfile("", note)
        return(_ret)

    ## @brief (private)ファイル出力を実行
    def _write_logfile(self, suffix, note=None):
        try:
            #まずはdirectoryをcheckし、無ければ作る
            _log_dir_path = "{0:s}/log".format(self._WorkingBaseDir)
            self._Logger.debug("checkpoint _log_dir_path=|{0:s}|".format(_log_dir_path))
            if not os.access(_log_dir_path, os.F_OK):
                os.mkdir(_log_dir_path, 0o777)

            #日時文字列取得
            _timestamp_string = self._get_timestamp_string()
            self._Logger.debug("checkpoint _timestamp_string=|{0:s}|".format(_timestamp_string))

            #ステータスファイル作成
            _status_file_path = "{0:s}/{1:s}.{2:s}".format(_log_dir_path, self._TargetNameId, suffix)
            self._Logger.debug("checkpoint _status_file_path=|{0:s}|".format(_status_file_path))
            if suffix == self.STATUS_SUFFIX_START:
                _logstr = "START of program {0:s}(timestamp)".format(self._OverallStartTimespec)
                with open(_status_file_path, "w", encoding="utf-8") as _fp:
                    _fp.write("[{0:s}] {1:s}({2:d}) {3:s}\n".format(_timestamp_string, self._TargetNameId, os.getpid(), _logstr))
                _logtype = 'info'
            elif suffix == self.STATUS_SUFFIX_NORMAL_END:
                _logstr = "END of program " + "{0:s}(timestamp)".format(_timestamp_string) + ", {0:s}(start)".format(self._OverallStartTimespec)
                with open(_status_file_path, "w", encoding="utf-8") as _fp:
                    _fp.write("[{0:s}] {1:s}({2:d}) {3:s}\n".format(_timestamp_string, self._TargetNameId, os.getpid(), _logstr))
                _logtype = 'info'
            elif suffix == self.STATUS_SUFFIX_ERROR_END:
                _logstr = "ERROR of program " + "{0:s}(timestamp)".format(_timestamp_string) + ", {0:s}(start)".format(self._OverallStartTimespec)
                with open(_status_file_path, "w", encoding="utf-8") as _fp:
                    _fp.write("[{0:s}] {1:s}({2:d}) {3:s}\n".format(_timestamp_string, self._TargetNameId, os.getpid(), _logstr))
                _logtype = 'error'

            #ログファイル作成
            _log_file_path = "{0:s}/{1:s}.log".format(_log_dir_path, self._TargetNameId)
            self._Logger.debug("checkpoint _log_file_path=|{0:s}|".format(_log_file_path))
            if note is not None:
                with open(_log_file_path, "a", encoding="utf-8") as _fp:
                    _fp.write("[{0:s}][debug] {1:s}({2:d}) {3:s}\n".format(_timestamp_string, self._TargetNameId, os.getpid(), note))
            if _logstr is not None:
                with open(_log_file_path, "a", encoding="utf-8") as _fp:
                    _fp.write("[{0:s}][{1:s}] {2:s}({3:d}) {4:s}\n".format(_timestamp_string, _logtype, self._TargetNameId, os.getpid(), _logstr))
            return self.MB_FILEIO_STATUS_OK
        except IOError as e:
            self._Logger.debug("IOError[{0:d}]:{1:s}".format(e.errno, e.strerror))
            return self.MB_FILEIO_STATUS_NG
        except OSError as e:
            self._Logger.debug("OSError[{0:d}]:{1:s}".format(e.errno, e.strerror))
            return self.MB_FILEIO_STATUS_NG
        except Exception as e:
            self._Logger.debug("UnexpectedError:{0:s}".format(str(e)))
            return self.MB_FILEIO_STATUS_NG

    ## @brief (private class method)現在時刻を整形した文字列に取得する。
    # 整形＝"mmm dd HH:MM:SS"（syslog出力に合わせている）
    #@return 整形した時刻文字列
    @classmethod
    def _get_timestamp_string(self):
        _current_datetime = datetime.datetime.today()
        _buffer = _current_datetime.strftime("%Y/%m/%d %H:%M:%S")
        return _buffer

