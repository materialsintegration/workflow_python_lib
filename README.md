# erfh5リーダー 
ERFH5(拡張子erfh5)フォーマットを読むためのライブラリ

## 概要
SYSWELD (VisualEnvironment)から出力されるいくつかのファイルフォーマットのうち、erfh5が最終的に同Viewerなどで読み込むためのファイルとなる。これの内容を読み、データなどを一部抜き出すことが可能ならeffh5が作成された段階で、データ作成が終了する。GUIを起動すること無くデータがまたGUIで出せるデータはJPGなどの画像データなので、もっと粒度の細かいデータを得ることができる。

## 使い方
このリポジトリにはいくつかのスクリプトがある。それぞれについて説明する。
* common_lib.py   ----- API呼び出し用関数のクラス
* erfh5_lib.py        - SYSWELDが作成する、erfh5ファイルをXMLやpython辞書に変換するためのスクリプト
* erfh5_xml_part.py   - 同erfh5ファイルをXMLに変換する際に別pythonスクリプトをthreadingとsubprocessで実行するが、そのためのスクリプト
* workflow_execute.py - ワークフローを連続または１つだけ動作させるスクリプト
* workflow_extract.py - ワークフロー情報をjson形式で出力するスクリプト
* workflow_lib.py     - 予測モジュール実行時にmiapiをラップして使いやすくしたスクリプト
* workflow_params.py  - ワークフローのパラメータ一覧を出力するスクリプト

### 予測モジュール実行用
予測モジュール実行用スクリプト内でクラスインスタンスを作成して使用する。予測モジュール実行用スクリプトもできればpythonが望ましい。ワークフローの入力と出力に対する定義を用意し、ソルバー実行を行う。定義は以下のとおりの書式のpython辞書を用意（記述）する。

* import
  ```
  sys.path.append("/home/misystem/assets/modules/workflow_python_lib")
  from workflow_lib import *
  ```
  pythonパスを追加し、読み込む。

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
  インスタンス化はパラメータ不要。  
  パラメータのtranslate_inputおよびtranslate_outputはポート名から実ファイル名へのシンボリックリンク作成を行うかどうかのフラグである。Trueを設定すれば、行う。  
※ Initializeメンバー関数はmiapiの初期化を行う。実行時、translate_inputがTrueの場合、inputポートのポート名と実ファイル名の変換（コピー動作、シンボリックリンクではない）を行う。

* ソルバー実行
ソルバー実行のために、ソルバー名（定期的に情報集約して使用率を計測する）の設定を行い、ソルバーを実行する。
  ```
  cmd = "ソルバー実行行"
  wf_tool.solver_name = "ソルバー名"
  wf_tool.ExecSolver(cmd)
  ```
※ ソルバー実行行はコマンド名とパラメータ  
※ 情報集約場所は、~/assets/workflow/[サイト番号]/solver_logs以下である。  
※ ExecSolverメンバー関数実行後、translate_outputがTrueの場合に、各ポート名と実ファイル名の変換（コピー動作、シンボリックリンクではない）を行う。このメンバー関数を使用しない場合はoutputポートのポート名と実ファイルの変換は行われない。行いたい場合は次の実行後の処理にある、PostProcessメンバー関数を実行する。

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

### ワークフロー実行
あらかじめトークンを用意するか、認証プログラムで前もってログイン処理を行いトークンを入手しておく。パラメータ一覧を入手し、実行スクリプトで「パラメータ:対応するファイル名」という実行時引数を必要な数だけ構成し実行する。「SYSWELD最適化ワークフロー」を例に説明する。

* パラメータ一覧取得  
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

inpt parametersからoutput for resultsの間にリストされたのが、入力ポート名である。これを「ポート名:対応するファイル名」として、必要なだけ、実行プログラムのコマンドラインパラメータとして構成する。

* 実行
  ```
python3.6 /home/misystem/assets/modules/workflow_python_lib/workflow_execute.py workflow_id:W000020000000219 token:64文字のトー>クンを指定する misystem:dev-u-tokyo.mintsys.jp weld_shape_pf_param_py_01:weld_shape_pf_param.py クランプ終了時間_01:Clamping_End_Time.dat クランプ開始時間_01:Clamping_Initial_Time.dat 入熱量_01:Energy.dat 冷却終了温度_01:Cooling_End_Time.dat 冷却開始時間_01:Cooling_Initial_Time.dat 初期温度_01:Initial_Temperature.dat 初期組織の相分率_01:init_microstructure.txt 効率_01:Efficiency.dat 溶接幅_01:Width.dat 溶接終了時間_01:Welding_End_Time.dat 溶接長さ_01:Length.dat 溶接開始時間_01:Welding_Initial_Time.dat 熱源移動速度_01:Velocity.dat 環境温度_01:Amient_Temp.dat 貫通_01:Penetration.dat number:-1
  ```

  ※ number:-1 なのはこのプログラムはnumberに1以上の整数を指定すると、同時実行中のランが指定した数以下のうちは連続してランを実行する。-1の場合は1つ実行し、終了したら、実行プログラムを終了する。

* その他
  + 実行終了時、outputポート名のファイルを/tmp以下に出力し、そのファイル名を一覧として出力する。
    終了時の一例
    ```
    2019/10/09 09:23:27 - ワークフロー実行中（R000020000204903）
    2019/10/09 09:28:25 - ラン実行ステータスがcompletedに変化したのを確認しました
    2019/10/09 09:28:25 - ワークフロー実行終了
    作成したメッシュ先端:/tmp/作成したメッシュ先端
    作成したメッシュ全体:/tmp/作成したメッシュ全体
    最大温度分布画像:/tmp/最大温度分布画像
    最高温度:/tmp/最高温度
    残留応力:/tmp/残留応力
    残留応力画像:/tmp/残留応力画像
    溶接画像:/tmp/溶接画像
    硬さ分布:/tmp/硬さ分布
    硬さ分布画像:/tmp/硬さ分布画像
    粒径情報:/tmp/粒径情報
    結果ファイル:/tmp/結果ファイル
    ```
  + 異常終了した場合は、各ツールのstdoutとラン詳細のJSONファイルを保存する。前者は「ツール名.log」。後者は「run_ラン番号_detail.log」という名前になる。
