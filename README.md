# ワークフロー実行ヘルパープログラム群
ワークフロー内、またはMIntシステム外（例えばWindowsPCやLinux環境など)からワークフローを実行させるためのヘルパーライブラリ、プログラム群。

## 概要
ワークフローAPIを使用するための簡単なスクリプト。APIをプログラムなどから利用するための手間を省き、必要な設定値（APIトークン、URL、サイトID、ワークフローID、ランIDなど）を指定するだけでワークフローAPIで利用可能なAPI呼び出しが使用可能になる。

## 使い方
このリポジトリにはいくつかのスクリプトがある。それぞれについて説明する。
* common_lib.py   ----- API呼び出し用関数のクラス
* erfh5_lib.py          - SYSWELDが作成する、erfh5ファイルをXMLやpython辞書に変換するためのスクリプト
* erfh5_xml_part.py     - 同erfh5ファイルをXMLに変換する際に別pythonスクリプトをthreadingとsubprocessで実行するが、そのためのスクリプト
* workflow_execute.py   - ワークフローを連続または１つだけ動作させるスクリプト
* workflow_extract.py   - ワークフロー情報をjson形式で出力するスクリプト
* workflow_lib.py       - 予測モジュール実行時にmiapiをラップして使いやすくしたスクリプト
* workflow_params.py    - ワークフローのパラメータ一覧を出力するスクリプト
* workflow_rundetail.py - ラン詳細を得るスクリプト
* workflow_runlist.py   - 指定されたワークフローを実行したラン番号のリストを返す。
* workflow_changest.py  - 指定されたランのステータスを実行中止(canceled)へ変更する。
* parent_job_servei.sh  - Torqueジョブ監視スクリプト。１つ目を親のジョブIDとし、２つめ以降はそこから実行された子のジョブとして監視。親ジョブが終了（ワークフローキャンセルなど）した場合は子のジョブを削除する。
* run_clean.py          - ワークフローIDからラン番号、実行時ディレクトリおよびそのサイズを表示する。簡易コマンドも受け付ける（不要なファイルの削除などに）
* workflow_feedbackrun.py - フィードバックラン実行用のスクリプト
~~ pairgraph.py          - タブ区切りのCSVファイルからペアプロットを作成する。
  + Thermo-Calc実行スクリプト専用
  + 要matplotlib、seabornパッケージ~~
* workflow_create.py    - ワークフローを登録する。
* db_operator.py        - MIntシステムのDBを一括で変更する。

## 特記事項
* 対応するpythonのバージョンは3.6以上を想定している。2.6または2.7でも動作可能かもしれないが、保証はしない。
* MIntシステム2106の導入に伴いAPIのバージョンが変わったため、各スクリプトにversionパラメータ指定を追加した。

## 詳細
各プログラム、ライブラリの詳細と使い方。

### 推奨環境
* python : 3.6以上（4.xは未確認）
* パッケージ
  + requests

### 共通の使い方　　
ほぼ全てのプログラムは、以下のパラメータが必要となる。

* URL : nims.mintsys.jpのような使用しているMIntシステムのホスト名＋ドメイン名。
* APIトークン : API使用を利用する権利を持っているユーザーに発行される６４文字のMIntシステムAPIへのアクセストークン。
  + ユーザーIDとパスワードで直接MIntシステムに問い合わせてトークン取得できるように順次改修中。

### erfh5リーダー

ERFH5(拡張子erfh5)フォーマットを読むためのライブラリ
* erfh5_lib.py
* erfh5_xml_part.py

### workflow_lib.py 
予測モジュール実行用スクリプト内でクラスインスタンスを作成して使用する。予測モジュール実行用スクリプトもできればpythonが望ましい。ワークフローの入力と出力に対する定義を用意し、ソルバー実行を行う。定義は以下のとおりの書式のpython辞書を用意（記述）する。

* 使い方
  + 予測モジュールで指定した実行プログラムでimportし、インスタンスを作成して使用する。
  ```
  sys.path.append("/home/misystem/assets/modules/workflow_python_lib")
  from workflow_lib import *
  ```
  + pythonパスを追加し、読み込む。

* inputポート用定義  
  ```
  inputports = {
    "inputポート名":"",
  }
  ```
* outputポート用定義  
  ```
  outputports = {
    "outputポート名":"",
  }
  ```
* inputポート名と実ファイル名との変換用  
  ```
  in_realnames = {
    "inputポート名":"実ファイル名",
  }
  ```
* outputポート名と実ファイル名との変換用  
  ```
  out_realnames = {
    "実ファイル名":"outputポート名",
  }
  ```
* インスタンス作成と定義の読み込み  
定義を作成したら、クラスをインスタンス化し、定義を読み込ませ、インスタンスの初期化を行う。クラス名は「MIApiCommandClass」
  ```
  wf_tool = MIApiCommandClass()
  wf_tool.setInportNames(inputports)
  wf_tool.setOutportNames(outputports)
  wf_tool.setRealName(in_realnames, out_realnames)
  wf_tool.Initialize(translate_input=True, translate_output=True)
  ```
  + インスタンス化はパラメータ不要。  
  + パラメータのtranslate_inputおよびtranslate_outputはポート名から実ファイル名へのシンボリックリンク作成を行うかどうかのフラグである。Trueを設定すれば、行う。  
  + Initializeメンバー関数はmiapiの初期化を行う。実行時、translate_inputがTrueの場合、inputポートのポート名と実ファイル名の変換（コピー動作、シンボリックリンクではない）を行う。

* ソルバー実行
ソルバー実行のために、ソルバー名（Zabbixなどで定期的に情報集約して使用率を計測する用）の設定を行い、ソルバーを実行する。ExecSolverメンバー関数内で、ソルバーログに実行開始、終了が日時と共に記録される。
  ```
  cmd = "ソルバー実行行"
  wf_tool.solver_name = "ソルバー名"
  wf_tool.ExecSolver(cmd)
  ```
  + ソルバー実行行はコマンド名とパラメータ  
  + ソルバーログは、~/assets/workflow/[サイト番号]/solver_logs以下である。  
  + ExecSolverメンバー関数実行後、translate_outputがTrueの場合に、各ポート名と実ファイル名の変換（コピー動作、シンボリックリンクではない）を行う。このメンバー関数を使用しない場合はoutputポートのポート名と実ファイルの変換は行われない。行いたい場合は次の実行後の処理にある、PostProcessメンバー関数を実行する。
  + ソルバー実行ログ例
    ```
    2020/03/19 10:16:12: start: sysWeld: 200000100000001: 9cc0f5c1-da33-4e2b-b87e-a26884f08e48: None: W000020000000268
    2020/03/19 10:20:32: normal end: sysWeld: 200000100000001: 9cc0f5c1-da33-4e2b-b87e-a26884f08e48: None: W000020000000268
    ```
    - 日時、状況、ソルバー名、ランの実行者ID、ソルバー実行用個別ID、ラン番号（未対応）、ワークフローIDが記録されている。
    - 状況は、start(開始)/normal end(正常終了)/abnormal end(異常終了)のどれかである。
    - ソルバー実行用個別IDはExecSolver毎に発行されるUUIDである。

* 実行後の処理いくつか
  + ExecSolverを実行し無かった場合に実行して、outputポートのポート名と実ファイル名の変換を行う。
    ```
    wf_tool.PostProcess()
    ```
  + いくつかあるファイルの最後のファイルをoutputポートのポート名にする。
    ```
    wf_tool.copyLastTimeStampfile("Ni-Al_*.vtk", "ニッケル熱処理計算の結果ファイル")
    ```
    ※ 簡単なファイルパターンを入れて、マッチするファイル群から作成日時の最後のものをポート名にコピーする。

### workflow_params.py
ワークフロー実行用パラメータ（ポート名）取得プログラム。  
このプログラムを利用して、実行したいワークフローのパラメータ（ポート名）を取得する。後述の実行用プログラムで必要なパラメータ（ポート名）と対応するファイルを指定するのに使用する。

* パラメータ一覧取得   
  実行に必要なパラメータ
  + 共通パラメータ
  + ワークフローID
  以下のコマンドラインで一覧を取得する。
  ```
  python3.6 /home/misystem/assets/modules/workflow_python_lib/workflow_params.py workflow_id:W000020000000219 token:64文字のトークンを指定する misystem:dev-u-tokyo.mintsys.jp
  ```
  これを実行すると、以下のような返信がある。  
  ```
  input parameters
  port = weld_shape_pf_param_py_01(True)
  port = クランプ終了時間_01(True)
  port = クランプ開始時間_01(True)
  port = 入熱量_01(True)
  port = 冷却終了温度_01(True)
  port = 冷却開始時間_01(True)
  port = 初期温度_01(True)
  port = 初期組織の相分率_01(True)
  port = 効率_01(True)
  port = 溶接幅_01(True)
  port = 溶接終了時間_01(True)
  port = 溶接長さ_01(True)
  port = 溶接開始時間_01(True)
  port = 熱源移動速度_01(True)
  port = 環境温度_01(True)
  port = 貫通_01(True)
  output for results
  port = 作成したメッシュ先端_01(file)
  port = 作成したメッシュ全体_01(file)
  port = 最大温度分布画像_01(file)
  port = 最高温度_01(file)
  port = 残留応力_01(file)
  port = 残留応力画像_01(file)
  port = 溶接画像_01(file)
  port = 硬さ分布_01(file)
  port = 硬さ分布画像_01(file)
  port = 粒径情報_01(file)
  port = 結果ファイル_01(file)
  ```

※　input parametersからoutput for resultsの間にリストされたのが、入力ポート名である。これを「ポート名:対応するファイル名」として、必要なだけ、実行プログラムのコマンドラインパラメータとして構成する。
※　ポート名に(True)となっているのは必須であり、省略できないことを示している。

### workflow_execute.py
ワークフロー実行用API呼び出しプログラム。
あらかじめトークンを用意するか、認証プログラムで前もってログイン処理を行いトークンを入手しておく。パラメータ一覧を入手し、実行スクリプトで「パラメータ:対応するファイル名」という実行時引数を必要な数だけ構成し実行する。「SYSWELD最適化ワークフロー」を例に説明する。

```mermaid
sequenceDiagram;

participant A as user
participant B as このプログラム
participant C as MInt System

A->>B:execute
alt ラン実行成功の確認
  B->>C:ステータス確認(WF-API)
  C->>B:ラン番号の返信(WF-API)
  B->>A:ラン番号(stderr)、実行時ディレクトリ、ラン詳細ページURLの表示(stdout)
else faild
  C->>B:エラー情報の返信(WF-API)
  B->>A:エラー情報の表示後終了
end
alt 実行状況の確認
  B->>C:ラン詳細の確認(WF-API)
  C->>B:ラン詳細の返信(WF-API)
  B->>B:loop
else faild
  C->>B:エラー情報の返信(WF-API)
  B->>A:エラー情報の表示後終了
end
alt ワークフローの終了時
  B->>C:ラン詳細の確認(WF-API)
  C->>B:ラン詳細の返信(WF-API)
  B->>A:終了が確認されたので、出力ポートのダウンロード（もし指定があれば）して終了。
else faild
  C->>B:エラー情報の返信(WF-API)
  B->>A:エラー情報の表示後、各モジュールのstdoutを取得、保存して終了
end
```
* 準備  
  必要なパラメータ（ポート名）をworkflow_params.pyを実行して取得しておく。

* 実行  
  実行に必要なパラメータ
  + 共通パラメータ
  + ワークフローID
  + 必要なポート名と対応するファイル名
  上記workflow_params.pyの実行結果を参考にすると以下のようになる。
  ```
  python3.6 /home/misystem/assets/modules/workflow_python_lib/workflow_execute.py workflow_id:W000020000000219 token:64文字のトークンを指定する misystem:dev-u-tokyo.mintsys.jp weld_shape_pf_param_py_01:weld_shape_pf_param.py クランプ終了時間_01:Clamping_End_Time.dat クランプ開始時間_01:Clamping_Initial_Time.dat 入熱量_01:Energy.dat 冷却終了温度_01:Cooling_End_Time.dat 冷却開始時間_01:Cooling_Initial_Time.dat 初期温度_01:Initial_Temperature.dat 初期組織の相分率_01:init_microstructure.txt 効率_01:Efficiency.dat 溶接幅_01:Width.dat 溶接終了時間_01:Welding_End_Time.dat 溶接長さ_01:Length.dat 溶接開始時間_01:Welding_Initial_Time.dat 熱源移動速度_01:Velocity.dat 環境温度_01:Amient_Temp.dat
  ```
  + 構成ファイルの書式
    - JSON準拠である(inputsは2021年9月13日現在実装中で使用不可である)
      ```
      {
      "workflow_id":"Wxxxxxyyyyyyyyyy",
      "token":"64文字の文字列",
      "misystem":"MIntシステムのURL",
      "timeout":"タイムアウト１,タイムアウト２",
      "siteid":"sitexxxxx",
      "description":"任意の長さの文字列",
      "downloaddir":"出力ポート値保存場所",
      "inputs":{
         "クランプ終了時間_01":["file", "Clamping_End_Time.dat"],
         "溶接終了時間_01":["value", 10.04],
         "初期組織の相分率_01":["AssetID", "A0012300000000000123"],
         "weld_shape_pf_param_py_01":["value", "weld_shape_pf_param.py"],
         }
      }
      ```

* 実行開始後
  
  + 実行開始から終了まで  
    ```
    2020/07/28 13:24:02 - ワークフロー実行中（R000110000606859）
    2020/07/28 13:24:02 - ラン詳細ページ  https://nims.mintsys.jp/workflow/runs/110000606859
    2020/07/28 13:24:02 - 実行ディレクトリ /home/misystem/assets/workflow/site00011/calculation/94/da/28/d4/00/26/44/c8/80/ef/a9/cd/c2/87/74/f1
    2020/07/28 13:24:13 - ラン実行ステータスがcompletedに変化したのを確認しました
    2020/07/28 13:24:13 - ワークフロー実行終了
    ```
    という表示が行われる。

  + 実行終了時、outputポート名のファイルを/tmp/ラン番号ディレクトリ以下に出力し、そのファイル名を一覧として出力する。
    終了時の一例
    ```
    2020/07/28 13:24:13 - フェライトとパーライトの硬さ 取得中...
    フェライトとパーライトの硬さ:/tmp/R000110000606859/フェライトとパーライトの硬さ
    2020/07/28 13:24:14 - ベイナイトの硬さ 取得中...
    ベイナイトの硬さ:/tmp/R000110000606859/ベイナイトの硬さ
    2020/07/28 13:24:14 - マルテンサイトの硬さ 取得中...
    マルテンサイトの硬さ:/tmp/R000110000606859/マルテンサイトの硬さ
    2020/07/28 13:24:14 - 硬さ 取得中...
    硬さ:/tmp/R000110000606859/硬さ
    ```
    ※ /tmp以下はシステムにもよるが30日前後でクリーンアップされ、一般ファイルは削除されるので、注意。

  + 実行停止  
    途中ctrl+Cでスクリプトの処理自体は停止させられるが、実行中だったり、待ち合わせ中などの場合は、前者ならステータスの変化、後者なら待ち合わせ終了後の実行タイミングまでスクリプトは終了しません。またワークフロー自体の停止も行いません。signal処理しているので、ctrl+Cのみこの様な挙動になる。
    + 強制停止したい場合は ctrl+Zで停止させ、
    ```
    $ kill -9 %1
    ```
    で強制終了させる。
　  + この場合でもワークフロー実行は停止、終了はしません。 
  + 異常終了  
    ワークフローが異常終了した場合は、各ツールのstdoutとラン詳細のJSONファイルをMIntシステムより取得し保存する。前者は「ツール名.log」。後者は「run_ラン番号_detail.log」という名前になる。
  + その他  
    ワークフローAPIプログラムの異常など異常終了以外の異常応答は５分後リトライを５回まで行う。回復しない場合は終了する。

### workflow_runlist.py
ライブラリとしては、ワークフローIDから対応するランのラン番号リストなどの辞書を返すプログラムである。単体実行した時は実行時ディレクトリやラン詳細のURLを表示する。

件数が多い場合の処理は含まれていないので、注意すること。

* 実行  
  実行に必要なパラメータ
  + 共通パラメータ
  + ワークフローID
  + サイトID
  + トークン（無い場合はユーザーIDとパスワードによるログイン処理を実行する）
  ```
  python3.6 workflow_runlist.py [token:<APIトークン>] misystem:dev-u-tokyo.mintsys.jp workflow_id:W000020000000217 siteid:site00002
  ```
* 単体実行すると以下のような表示が行われる。  
  ```
  $ python3.6 workflow_runlist.py workflow_id:W000020000000283 misystem:dev-u-tokyo.mintsys.jp siteid:site00002 result:true
  processing parameter workflow_id
  workflow_id is W000020000000283
  processing parameter misystem
  url for misystem is dev-u-tokyo.mintsys.jp
  processing parameter siteid
  siteid is site00002
  processing parameter result
  ログインID: utadmin01
  パスワード: 
  RunID : R000020000531497
                 開始 : 2020/07/21 09:24:00
                 終了 : 2020/07/21 11:39:38
           ステータス : canceled
          ラン詳細URL : https://dev-u-tokyo.mintsys.jp/workflow/runs/20000531497
    実行時ディレクトリ: /home/misystem/assets/workflow/site00002/calculation/3d/38/65/5d/11/ad/4f/9d/a6/1d/3c/a2/d0/65/51/84
  RunID : R000020000531496
                 開始 : 2020/07/21 09:17:41
                 終了 : 2020/07/21 09:19:36
           ステータス : abend
          ラン詳細URL : https://dev-u-tokyo.mintsys.jp/workflow/runs/20000531496
    実行時ディレクトリ: /home/misystem/assets/workflow/site00002/calculation/6c/e9/0e/ed/96/a7/4a/f0/bb/78/8a/ba/0e/50/71/e8
  RunID : R000020000531495
                 開始 : 2020/07/21 09:13:22
                 終了 : 2020/07/21 09:13:36
           ステータス : abend
          ラン詳細URL : https://dev-u-tokyo.mintsys.jp/workflow/runs/20000531495
    実行時ディレクトリ: /home/misystem/assets/workflow/site00002/calculation/ec/fa/29/71/2a/f1/47/91/8c/45/86/41/20/66/32/8a
  ```
  内部の関数では上記結果はリストで返る。

* 関数呼び出し  
  importして関数として呼び出すことも可能である。

  ```python
  def get_runlist(token, url, siteid, workflow_id):
    '''
    ラン詳細の取得
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param siteid (string) サイトID。e.g. site00002
    @param workflow_id (string) ワークフローID。e.g. W000020000000197
    @retcal (list) {"runid":ランID, "status":ステータス, "description":説明} と言う辞書のリスト
    '''
  ```
* 辞書は以下のような内容
  ```python
  {"run_id":"Rxxxxxyyyyyyyyyy", "status":"completed", "description":"", "uuid":"", "start":"<creation_time>", "end":"<modification_time>"}
  ```
  日時はJSTである。

### workflow_rundetail.py
ラン詳細を取得するプログラムである。
* 実行  
  実行に必要なパラメータ
  + 共通パラメータ
  + ランID
  + サイトID
  ```
  python3.6 workflow_rundetail.py token:<APIトークン>  misystem:dev-u-tokyo.mintsys.jp run_id:R000020000365301 siteid:site00002
  ```
  実行すると以下のような表示が行われる。  
  ```
  {
    "completion_time": "2019-11-28T02:27:11Z",
    "creation_time": "2019-11-28T02:09:16Z",
    "creator_id": "200000100000001",
    "creator_name": "東大システム管理者０１",
    "description": "API経由ワークフロー実行 2019-11-28 11:09:14.415349\n\nparameter\n等温時効                :888.93\n析出相の体積分率            :0.177\n",
    "downloaded": false,
    "gpdb_url": "https://dev-u-tokyo.mintsys.jp:50443/gpdb-api/v2/runs/54a70a47-2029-4737-8d8b-0be00d162073",
    "is_interactive": false,
    "log_size": 911,
    "loop_count": 0,
    "modified_by_id": "200000100000001",
    "modified_by_name": "東大システム管理者０１",
    "modified_time": "2019-11-28T02:27:22Z",
    "run_id": "http://dev-u-tokyo.mintsys.jp/workflow/runs/R000020000365301",
    "status": "completed",
    "workflow_id": "http://dev-u-tokyo.mintsys.jp/workflow/workflows/W000020000000197",
    "workflow_name": "Ni-Al熱処理シミュレーション",
    "workflow_revision": 4
  }

  /home/misystem/assets/workflow/site00002/calculation/54/a7/0a/47/20/29/47/37/8d/8b/0b/e0/0d/16/20/73
  ```
  内部の関数を呼ぶと詳細情報のJSONデータのみが返される。

* 関数呼び出し  
  importして関数として呼び出すことも可能である。
  ```
  def get_rundetail(token, url, siteid, runid, with_result=False, debug=False):
    '''
    ラン詳細の取得
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param siteid (string) サイトID。e.g. site00002
    @param run_id (string) ランID。e.g. R000020000365545
    @retval (dict)
    '''
  ```

### workflow_iourl.py
指定したラン番号の入出力ファイルURLの一覧を取得します。
* 実行  
  実行に必要なパラメータ。
  実行に必要なパラメータ
  + 共通パラメータ
  + ランID
  + サイトID
  ```
  python3.6 workflow_iourl.py token:<APIトークン>  misystem:dev-u-tokyo.mintsys.jp run_id:R000020000365301 siteid:site00002
  ```
  実行すると以下のような表示が行われる。  
  ```
  {
    "R000020000464367": {
      "loop": 0,
      "pyin": [
        "https://dev-u-tokyo.mintsys.jp:50443/gpdb-api/v2/runs/",
        1
      ],
      "pysaveto": [
        "https://dev-u-tokyo.mintsys.jp:50443/gpdb-api/v2/runs/",
        4
      ],
      "pyout": [
        null,
        null
      ]
    }
  }
  ```

* 関数呼び出し  
  importして関数として呼び出すことも可能である。
  ```
  def get_runiofile(token, url, siteid, runid, with_result=False, thread_num=0):
    '''
    入出力ファイルURL一覧の取得
    @param token (string) APIトークン
    @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
    @param siteid (string) サイトID。e.g. site00002
    @param runid (string) ランID。e.g. R000020000365545
    @param with_result (bool) この関数を実行時、情報を標準エラーに出力するか
    @retval (dict) {"runID":{"ポート名":[ファイルURL, ファイルサイズ]}}
    '''
  ```

### extract_io_ports.py
予測モジュールファイルから、common_libを使用して作成した予測モジュール用実行ファイル画必要とする入力ポートおよび出力ポートのエントリ部分を作成する。

* Usage
```
Usage python3.6 extract_io_ports.py <prediction_id> <modules.xml> [-c[:前段のモジュール名]]

    バージョン番号は、最新（各数字が最大）のもの

    prediction_id : Pで始まる予測モジュール番号。assetでinport後、exportしたあとのmodules.xmlを使う
    modules.xml   : assetで、exportしたXMLファイル。
        -c        : チェックオンリー。パラメータの長さのみ計算
  :前段のモジュール名 : 一つ前の予測モジュール名を一つ
                  : Wxxxxxyyyyyyyyyy_予測モジュール名_02 という形式
```

* 出力
  + ```<objectPathに記述されたプログラム名>_import.py```というファイル名のファイルを作成する。

### parent_job_survai.sh
自らもTorqueのバッチジョブとして実行中のプログラム(予測もジュール我実行したプログラム。親ジョブとする）が、さらに子プログラムをTorqueのバッチジョブ実行する時に、その子プログラム（子ジョブとする）を親ジョブが先にいなくなった場合（ワークフローキャンセルや、親ジョブが途中で異常終了した場合など）に連動して親ジョブが投入したバッチジョブを削除(qdel)できるようにするスクリプトである。
このスクリプトをTorqueバッチジョブとして実行することで実現する。

* 使い方
  ```
  $ sh parent_job_survai.sh <親ジョブID> <ログファイル> <子ジョブ１> <子ジョブ２> ...
  ```
* 特徴
  + 予測モジュールから実行したプログラムが実行したバッチジョブプログラムはワークフローをキャンセルした時に連動してキャンセルされない。
  + このプログラムを別途バッチジョブ登録して実行して、親ジョブを監視することで、対応できる。

* なぜこのプログラムが必要か。
  + 親ジョブがTorque登録を削除されるとkill -15に続いてわずかな時間、１秒あるかないかでkill -9されるため、15をシグナルキャッチできても対応できない。
  + そもそも現在のワークフロー実行用ジョブスクリプトはシグナルキャッチ処理をおこなっていない。

* リソースの詳細
  + queueはex_queueを指定
  + nodesは１とnon-calc-nodeを指定

### workflow_create.py
ワークフローを登録する。
* 実行

  実行に必要なパラメータ。
  + 共通パラメータ
  + 登録するワークフロー名

  任意指定のパラメータ。
  + 登録するワークフローの説明
  + 登録するワークフローに設定する予測モデルID。URI形式
  + 登録するワークフローに関連付けたいワークフローID。URI形式
  + 関連付けたいワークフローのリビジョン番号
  + ワークフロー定義(miwf)ファイル名
  + ワークフローAPIバージョン(vを付けること)。未指定時のデフォルト値はv4

  実行方法
  ```
  python3.6 workflow_create.py token:<APIトークン> misystem:dev-u-tokyo.mintsys.jp name:<ワークフロー名> description:<ワークフロー説明> prediction_model_id:http://mintsys.jp/inventory/prediction-models/M000020000004476 reference_workflow_id:http://mintsys.jp/workflow/workflows/W000020000000324 reference_workflow_revision:1 miwf_file:W000020000000324.miwf wf_api_version:v4
  ```
  実行すると以下のような表示が行われる。  
  ```
    2021/04/27 11:16:28 - ワークフロー登録終了 - <ワークフローID>
  ```

* 関数呼び出し  
  importして関数として呼び出すことも可能である。
  ```
    def workflow_create(token, url, name, description, prediction_model_id, reference_workflow_id, reference_workflow_revision, miwf, version):
        '''
        ワークフロー登録
        @param token (string) APIトークン
        @param url (string) URLのうちホスト名＋ドメイン名。e.g. dev-u-tokyo.mintsys.jp
        @param name (string) 登録するワークフロー名
        @param description (string) 登録するワークフローの説明
        @param prediction_model_id (string) 登録するワークフローに設定する予測モデルID。URI形式
        @param reference_workflow_id (string) 登録するワークフローに関連付けたいワークフローID。URI形式
        @param reference_workflow_revision (int) 関連付けたいワークフローのリビジョン番号
        @param miwf (json) 登録するワークフローに設定する、ワークフロー定義 ※ファイル名ではない
        @param version (string) ワークフローAPIのバージョン。vを付けること
        @retval ワークフローID（W+15桁の数値）(string)
        '''
  ```

### run_clean.py
MIntシステムでは基本的に、ランディレクトリのファイルは実行終了後は触らない方針である。異常終了やキャンセルした場合でもそのデータに何らかの意味があるという思想からである。他方、プログラムの不備で、削除されるべき中間ファイルが残ってしまうこともある。こういったファイルは実行終了後にのこっていてもGPDB経由で取り出すこともない。このプログラムはそのような時に使用するものである。

* 必要な情報
このプログラムを実行するのに必要な情報は以下の通りである。
  + ワークフロー番号
    - 必須
    - 指定されたワークフローすべてについて調査する。
    - 現状日時やその範囲の指定は実装されていない。（予定は有る）
  + トップURL
    - 必須
    - NIMS運用環境ならnims.mintsys.jp。NIMS開発環境ならdev-u-tokyo.mintsys.jpなどとなる。
  + siteID
    - 必須
    - NIMS運用環境ならsite00011。NIMS開発環境ならsite00002などとなる。
  + excomd
    - オプション
    - 実行中または待機中でないランに対して実行したいシェルコマンドを指定する

* ログイン情報
API実行するのでトークンが必要である。しかしトークン指定はヒストリに残る。また構成ファイルにも対応してないので、毎度ログインプロンプトで取得する方式となっている。

* ログインID
実行に必要なトークンを得るためのログインIDはどのユーザーでも構わない。ただし権限が狭いユーザーだと、他のユーザーのランが操作対象から外れる可能性がある。指定したワークフローの全ランを対象にしたい場合はmiadminなどの管理者ユーザーIDを利用するべきである。

* 使用方法
ランのデータディレクトリに直接アクセスするためネットワーク越し（ヘッドノード以外の計算機から操作する場合など）は余計なパケットおよびヘッドノードのNFSデーモンなどに余計な負荷がかかるので推奨しない。ヘッドノードで実行する方法を推奨する。なおユーザーはmisystemが推奨であるが、ここのところ報告されているNFSデーモン異常動作時はmisystemでの作業は不可能なので、その時は注意してrootで実行する。

* 実行手順
手順の前提条件は以下の通りである。
  + ワークフローID：W000110000000402
  + トップURL：nims.mintsys.jp
  + サイトID：site00011

* 実行時ディレクトリの容量の表示
実行時ディレクトリの容量を表示するための実行手順は以下の通りである。
```
$ cd ~/assets/modules/workflow_python_lib
$ python3.6 run_clean.py workflow_id:W000110000000402 misystem:nims.mintsys.jp siteid:site00011
```

実行中の表示
```
run(R000110000621000) 情報：2021-02-22 19:14:05 - ランは完了しています。
  ディレクトリサイズは 707M .
  /home/misystem/assets/workflow/site00011/calculation/9b/0c/b8/f6/62/06/4c/1f/a6/25/e2/48/7f/59/6d/2a

run(R000110000621001) 情報：2021-02-22 19:19:04 - ランは完了しています。
  ディレクトリサイズは 709M .
  /home/misystem/assets/workflow/site00011/calculation/0d/09/79/eb/bc/00/4e/d8/be/bf/c6/a3/ed/b5/3a/9d
```

* 実行時ディレクトリに対してなにかしら実行する場合
実行時ディレクトリに対して、指定したコマンドの実行が可能である。以下のように実行する。
```
$ cd ~/assets/modules/workflow_python_lib
$ python3.6 run_clean.py workflow_id:W000110000000402 misystem:nims.mintsys.jp siteid:site00011 excmd:'rm W000110000000xxx/W000110000000xxx_とある計算_0?/hogehoge.dat'
```

コマンドを指定する場合、注意点がある。
* excmd:につづけて、コマンド全体をシングルクオート```'```またはダブルクオート```"```でくくる。
* パイプ処理は使えない。

* 実行中の表示
```
run(R000110000620133) 情報：2021-01-04 21:11:31 - ランは完了しています。
  ディレクトリサイズは 4.3G .
  /home/misystem/assets/workflow/site00011/calculation/4c/40/97/d4/ed/71/47/7f/b7/5f/98/28/f3/21/39/f4
  コマンド(rm W000110000000xxx/W000110000000xxx_とある計算_0?/hogehoge.dat)実行中

  CompletedProcess(args='rm W000110000000xxx/W000110000000xxx_とある計算_0?/hogehoge.dat', returncode=0)
run(R000110000620134) 情報：2021-01-04 19:50:06 - ランは完了しています。
  ディレクトリサイズは 4.3G .
  /home/misystem/assets/workflow/site00011/calculation/61/1e/66/74/a0/1a/4a/d4/a4/7e/82/33/bb/2a/51/5a
  コマンド(rm W000110000000xxx/W000110000000xxx_とある計算_0?/hogehoge.dat)実行中

  CompletedProcess(args='rm W000110000000xxx/W000110000000xxx_とある計算_0?/hogehoge.dat', returncode=0)
```

### workflow_feedbackrun.py
フィードバックランAPIに対応したスクリプトである。
* 特徴
通常のworkflow_execute.pyと同じであるが、フィードバックランのAPIにしたがい、mode(start/run/stop)でフィードバックランを制御する。
* ヘルプの表示  
引数無で実行するとヘルプが表示される。
```
Usage
   $ python /home/misystem/assets/modules/workflow_python_lib/workflow_feedbackrun.py workflow_id:Mxxxx token:yyyy misystem:URL <port-name>:<filename for port> [OPTIONS]...
               token  : 非必須 64文字のAPIトークン。指定しなければログインから取得。
             misystem : 必須 dev-u-tokyo.mintsys.jpのようなMIntシステムのURL
    <port-name>:<filename for port> : ポート名とそれに対応するファイル名を必要な数だけ。
                      : 必要なポート名はworkflow_params.pyで取得する。
              timeout : 連続実行でない場合に、実行中のままこの時間（秒指定）を越えた場合に、キャンセルして終了する。
          description : ランの説明に記入する文章。
                 mode : 必須 start/run/stopのどれかを指定する。
                      : start フィードバックラン開始。正常開始できればstdoutにIDが表示される。
                      : run フィードバックラン１回開始。実行完了で戻ってくる。
                      : stop フィードバックラン終了。statusで終了状態を指定する。
          workflow_id : mode:startの時に必要 Rで始まる15桁のランID
          feedback_id : mode:runまたはstopの時に必要な操作対象のランID
                 conf : 構成ファイルの指定
    OPTIONS
        --download    : 実行終了後の出力ポートのダウンロードを行う。
                      : デフォルトダウンロードは行わない。
                      : mode:stop時に有効。
          downloaddir : 実行完了後の出力ポートファイルのダウンロード場所の指定（指定はカレントディレクトリ基準）
                        downloaddir/<RUN番号>/ポート名
                        デフォルトは/tmp/<RUN番号>ディレクトリ
                      : mode:stop時に有効。
                satus : mode:stop時に指定する。complete、abend、cancelを指定する。
                      : 無指定はcompleteとなる。
            max_count : 起動したランが実行できる最大回数。無指定は暫定100回。
```
* ポート名の取得
入力ポート名はworkflow_params.pyで取得した``` _0? ```までの名前を使用する。

* 実行方法
  + mode:startで実行する
    - 戻り値のランIDを控えておく
  + mode:run と feedback_idに控えておいたランIDを指定して、1回loopを実行する。
  + max_count(無指定時は９９)以内で終了する場合は、mode:stop status:(complete/abend/cancel)で終了する。

### db_operator.py
MIntシステムのDBをCSVファイルの書かれたDB、カラム名、変更する値、where句に従って変更する。
* 特徴
CSVファイルに記述されたカラムの値を一括で変換する。
* ヘルプの表示
パラメータ無しで実行するとヘルプが表示される。
```
DB一括変更スクリプト

Usage:
        $ python3.6 %s <mode> <hostid> <password> <db name> <table> [<csv_name>]

        mode       : change->変更、dryrun->テスト、view->取得と表示（標準出力）
        hostid     : 対象DBのホストID（IPアドレス）
        password   : 対象DBへのログイン方法
        db name    : 対象DBの名前
        target     : 変更対象のテーブル名
        csv_name   : パラメータを記述したCSVファイルの名前
                   : modeがchangeの時は定義一覧のCSV化したファイル
                   : modeがviewの時は確認用IDとバージョンのリストファイル
        mode が dryrunの時はmysqlのコマンドを表示するのみ
```
* csvのフォーマット
  + change/dryrun用
  ```
  update_column,update_value,where_column
  pbs_node_group,calc-node,prediction_module_id=119040000056:version=1.0.0
  ```
    - update_column : 変更対象のカラム名
    - update_value  : 変更値
    - where_column  : where句で絞りたいカラムと値を```:```で複数設定する。
  + view用
  ```
  prediction_module_id,version
  ```
    - これはprediction_module_id確認専用
* 使い方
  + CSVを同梱の```workflow_prediction_csv.py```を利用して作成するか、上記フォーマットの説明にしたがって作成する。
  + dryrunでCSVに対応したsql文を表示させて確認する
  + changeで実際の変更を実施する。
  + viewは予測モジュールのpbs_queueとpbs_node_groupカラム確認せんようとなっている。

# 参考文献
* pairgraph
  + [seaborn.pariplot](https://seaborn.pydata.org/generated/seaborn.pairplot.html#seaborn.pairplot)
  + [Python, pandas, seabornでペアプロット図（散布図行列）を作成](https://note.nkmk.me/python-seaborn-pandas-pairplot/)

