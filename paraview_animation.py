#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
'''
paraviewライブラリを使用したanimation lib
'''

import os, sys

if ("LD_LIBRARY_PATH" in os.environ) is False:
    os.environ["LD_LIBRARY_PATH"] = "/usr/local/paraview_python3/lib/paraview-5.4"
else:
    path = os.environ["LD_LIBRARY_PATH"]
    os.environ["LD_LIBRARY_PATH"] = path + ":/usr/local/paraview_python3/lib/paraview-5.4"

sys.path.append("/home/misystem/assets/modules/P67_manaka")
sys.path.append("/usr/local/paraview_python3/lib/paraview-5.4/site-packages")
sys.path.append("/usr/local/paraview_python3/lib/paraview-5.4/site-packages/vtk")

from paraview.simple import *
from glob import glob
import subprocess
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import time

def divide_vtk(file_pattern="*_to_*.vtk", time_temp=True, represent=None, filename_pattern=None, save_step=1, amount=None):
    '''
    vtkファイルをSCALAR毎に分解する
    '''

    files = []
    if file_pattern == "nstep_time.dat" or file_pattern == "nstep.dat":
        stepfile = open(file_pattern, "r")
        lines = stepfile.read().split("\n")
        for item in lines:
            if item == "":
                continue

            if file_pattern == "nstep.dat":
                filenameformat = "map-a%05d.vtk:%s"
            else:
                filenameformat = "map-a%06d.vtk:%s"
            filename = filenameformat%(int(item.split()[0]), item.split()[1])
            files.append(filename)

    else:
        files = glob(file_pattern)

    file_num = len(files)
    if file_num == 0:
        return

    count = 0
    last_num = int(os.path.basename(files[-1]).split("_")[1].split(".")[0])
    vtk_count = -1
    font = PIL.ImageFont.truetype("/usr/share/fonts/vlgothic/VL-Gothic-Regular.ttf", 18)
    scalar_names = {}
    #for infilename in files:
    if amount is None:                  # 間引きなし
        count_step = save_step
    else:
        try:
            amount = int(amount)
        except:
            amount = 10
        count_step = int(int(last_num / amount) / save_step) * save_step
        if count_step == 0:
            count_step = 1

    infilenames = []
    for vtk_count in range(0, last_num, count_step):
        infilenames.append(filename_pattern%vtk_count)

    infilenames.append(filename_pattern%last_num)

    for infilename in infilenames:
        #vtk_count += 1
        #vtk_count = file_count
        #infilename = filename_pattern%vtk_count
        if os.path.exists(infilename) is False:
            continue
        print("processing vtk file(%s)"%infilename)
        infile = open(infilename.split(":")[0], "r")
        if time_temp is True:
            ptime = int(infilename.split("_")[3]) / 1000.0
            ptemp = float(infilename.split("_")[4].split(".")[0])
        elif time_temp == "niht":
            ptime = int(os.path.basename(infilename).split("_")[1].split(".")[0])
            #ptime = ""
            ptemp = ""
        else:
            #ptime = infilename.split("-")[1].split(".")[0]
            ptime = "%2.4f"%float(infilename.split(":")[1])
            ptemp = ""
        lines = infile.read().split("\n")
        scalar_name = None
        scalar_unit = None
        scalar_table = None
        headers = []
        scalars = {}
        scalars_unit = {}
        lookup_tables = {}
        for aline in lines:
            item = aline.split()
            if len(item) == 0:
                continue
            if time_temp == "niht":
                if len(item) == 2 and item[1] == "sec":
                    ptime = item[1]
            if item[0] == "SCALARS" or item[0] == "scalars":
                print("found SCALARS name %s"%item[1])
                scalar_name = item[1]
                if (scalar_name in scalar_names) is False:
                    scalar_names[scalar_name] = True
                scalars[scalar_name] = []
                scalars_unit[scalar_name] = item[2]
                continue
            if item[0] == "LOOKUP_TABLE":
                lookup_tables[scalar_name] = item[1]
                continue
            if scalar_name is None:
                headers.append(aline)
            else:
                scalars[scalar_name].append(aline)
        infile.close()
 
        for key in scalars:
            outfile = open(key + ".vtk", "w")
            for item in headers:
                outfile.write("%s\n"%item)
            outfile.write("SCALARS %s %s\n"%(key, scalars_unit[key]))
            outfile.write("LOOKUP_TABLE %s\n"%lookup_tables[key])
            for item in scalars[key]:
                outfile.write("%s\n"%item)
            outfile.close()
    
            vtkfilename = key + ".vtk"
            reader = OpenDataFile(vtkfilename)
            points = reader.PointData
    
            view = GetActiveView()    # 出力画像のアングル等の指定の準備
            if not view:
                view = CreateRenderView()
    
            xmin, xmax, ymin, ymax, zmin, zmax = reader.GetDataInformation().GetBounds()    # 対象物の大きさを取得
    
            ox = (xmax + xmin) / 2.0    # 対象物のX軸の中心点
            oy = (ymax + ymin) / 2.0    # 対象物のY軸の中心点
            oz = (zmax + zmin) / 2.0    # 対象物のZ軸の中心点
    
            camera_distance = max((xmax - xmin), (ymax - ymin), (zmax - zmin)) * 2.5    # 対象物からカメラの位置
            camera_position_front = [ox, oy, oz + camera_distance]    # 正面からのカメラの位置座標
            #camera_position_side = [ox + camera_distance, oy, oz]    # 横からのカメラの位置座標
            #camera_position_top = [ox, oy + camera_distance, oz]    # 上からのカメラの位置座標
            #camera_position_diagonal = [ox + (camera_distance / 2.0), oy + (camera_distance / 2.0), oz + (camera_distance / 2.0)]    # 斜めからのカメラの位置座標
            view.CameraPosition = camera_position_front    # 正面からのカメラの位置座標の設定
            view.CameraFocalPoint = [ox, oy, oz]    # カメラの焦点座標の設定
            view.CameraViewUp = [0, 1, 0]    # 出力画像の縦軸の設定
            view.CameraViewAngle = 30    # カメラの画角の設定
            view.ViewSize = [600, 400]
            viewobject = Show()    # オブジェクトの描画
            if represent is not None:
                viewobject.SetRepresentationType("Volume")
            viewobject.SetScalarBarVisibility(view, True)
            Render()
    
            WriteImage("%s-%08d.jpg"%(key, count))
            time.sleep(2.0)
            img = PIL.Image.open("%s-%08d.jpg"%(key, count))
            draw = PIL.ImageDraw.Draw(img)
            if time_temp is True:
                draw.text((30, 350), u'%08d(K)'%ptemp, fill=(255, 255, 255), font=font)
            else:
                draw.text((30, 350), u'%s'%ptime, fill=(255, 255, 255), font=font)
            img.save("%s-%08d.jpg"%(key, count))
            Delete()
            Delete(view)
        count += 1

    for item in scalar_names:
        subprocess.call("convert -delay 200 -loop 0 %s*.jpg %s.gif > convert.log 2>&1"%(item, item), shell=True, executable='/bin/bash')

    files = glob("*.jpg")
    for item in files:
        os.remove(item)

def get_avs_animation(file_pattern="*_AVese_*.dat", time_temp=True, represent=None, filename_pattern=None, save_step=1, amount=None):
    '''
    AVS用出力ファイルのアニメーションを作成する。
    '''

    files = glob(file_pattern)

    file_num = len(files)
    if file_num == 0:
        return False

    count = 0
    first_num = int(os.path.basename(files[0]).split("_")[3].split(".")[0])
    last_num = int(os.path.basename(files[-2]).split("_")[3].split(".")[0])
    vtk_count = -1
    font = PIL.ImageFont.truetype("/usr/share/fonts/vlgothic/VL-Gothic-Regular.ttf", 18)
    scalar_names = {}
    #for infilename in files:
    if file_num < 100:                  # 個数が100個以下なら間引き指定あっても無とする。
        amount = None
    if amount is None:                  # 間引きなし
        count_step = save_step
    else:
        try:
            amount = int(amount)
        except:
            amount = 10
        count_step = int(int(last_num / amount) / save_step) * save_step
        if count_step == 0:
            count_step = 1

    infilenames = []
    for avs_count in range(0, last_num, count_step):
        infilenames.append(filename_pattern%avs_count)

    infilenames.append(filename_pattern%last_num)
    jpg_filenames = []

    for infilename in infilenames:
        if os.path.exists(infilename) is False:
            continue
        print("processing avs file(%s)"%infilename)
    
        reader = AVSUCDReader(vtkfilename)
        points = reader.PointData

        view = GetActiveView()    # 出力画像のアングル等の指定の準備
        if not view:
            view = CreateRenderView()

        xmin, xmax, ymin, ymax, zmin, zmax = reader.GetDataInformation().GetBounds()    # 対象物の大きさを取得

        ox = (xmax + xmin) / 2.0    # 対象物のX軸の中心点
        oy = (ymax + ymin) / 2.0    # 対象物のY軸の中心点
        oz = (zmax + zmin) / 2.0    # 対象物のZ軸の中心点

        camera_distance = max((xmax - xmin), (ymax - ymin), (zmax - zmin)) * 2.5    # 対象物からカメラの位置
        camera_position_front = [ox, oy, oz + camera_distance]    # 正面からのカメラの位置座標
        #camera_position_side = [ox + camera_distance, oy, oz]    # 横からのカメラの位置座標
        #camera_position_top = [ox, oy + camera_distance, oz]    # 上からのカメラの位置座標
        #camera_position_diagonal = [ox + (camera_distance / 2.0), oy + (camera_distance / 2.0), oz + (camera_distance / 2.0)]    # 斜めからのカメラの位置座標
        view.CameraPosition = camera_position_front    # 正面からのカメラの位置座標の設定
        view.CameraFocalPoint = [ox, oy, oz]    # カメラの焦点座標の設定
        view.CameraViewUp = [0, 1, 0]    # 出力画像の縦軸の設定
        view.CameraViewAngle = 30    # カメラの画角の設定
        view.ViewSize = [600, 400]
        viewobject = Show()    # オブジェクトの描画
        if represent is not None:
            viewobject.SetRepresentationType("Volume")
        viewobject.SetScalarBarVisibility(view, True)
        Render()

        key = os.path.splitext(infilename)[1]
        WriteImage("%s-%08d.jpg"%(key, count))
        time.sleep(2.0)
        img = PIL.Image.open("%s-%08d.jpg"%(key, count))
        draw = PIL.ImageDraw.Draw(img)
        if time_temp is True:
            draw.text((30, 350), u'%08d(K)'%ptemp, fill=(255, 255, 255), font=font)
        else:
            draw.text((30, 350), u'%s'%ptime, fill=(255, 255, 255), font=font)
        jpg_filename = "%s-%08d.jpg"%(key, count)
        jpg_filenames.append(key)
        img.save(jpg_filename)
        Delete()
        Delete(view)
    count += 1

    for item in jpg_filenames:
        subprocess.call("convert -delay 200 -loop 0 %s*.jpg %s.gif > convert.log 2>&1"%(item, item), shell=True, executable='/bin/bash')

    files = glob("*.jpg")
    for item in files:
        os.remove(item)
