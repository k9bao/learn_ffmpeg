# 常用命令

- [常用命令](#常用命令)
  - [素材说明](#素材说明)
  - [视频剪切截图](#视频剪切截图)
  - [视频拼接](#视频拼接)
  - [视频编码格式转换](#视频编码格式转换)
  - [素材旋转](#素材旋转)
  - [素材缩放](#素材缩放)
  - [素材透明度调整](#素材透明度调整)
  - [素材位置调整](#素材位置调整)
  - [背景纯色填充](#背景纯色填充)
  - [背景图片填充](#背景图片填充)
  - [背景模糊](#背景模糊)
  - [视频镜像](#视频镜像)
  - [蒙版](#蒙版)
  - [花字贴纸](#花字贴纸)
  - [视频画中画](#视频画中画)
  - [素材亮度调整，素材对比度调整，素材饱和度调整](#素材亮度调整素材对比度调整素材饱和度调整)
  - [视频变速](#视频变速)
  - [视频裁切](#视频裁切)
  - [视频倒放](#视频倒放)
  - [绿幕抠图](#绿幕抠图)
  - [音频变声](#音频变声)
  - [音量调节](#音量调节)
  - [音频变速](#音频变速)
  - [音频淡入淡出](#音频淡入淡出)
  - [音频拼接](#音频拼接)
  - [多音轨混音](#多音轨混音)
  - [lut滤镜](#lut滤镜)
  - [shader特效](#shader特效)
  - [shader转场](#shader转场)
  - [视频定格](#视频定格)
  - [提取音频或视频](#提取音频或视频)
  - [桌面分享推流](#桌面分享推流)
  - [推流桌面+麦克风](#推流桌面麦克风)
  - [推流桌面+摄像头+麦克风](#推流桌面摄像头麦克风)
  - [视频解封装](#视频解封装)
  - [视频转码](#视频转码)
  - [视频改封装](#视频改封装)
  - [直播转录](#直播转录)
  - [播放yuv文件](#播放yuv文件)
  - [双声道合并单声道](#双声道合并单声道)
  - [提取两个声道](#提取两个声道)
  - [将两个音频源合并为双声道](#将两个音频源合并为双声道)
  - [音频音量探测](#音频音量探测)
  - [绘制音频波形图  （多声道混合）](#绘制音频波形图--多声道混合)
  - [绘制不同声道的波形图](#绘制不同声道的波形图)
  - [调整音量](#调整音量)
  - [删除其中一个音频流](#删除其中一个音频流)
  - [只保留其中一个声道](#只保留其中一个声道)
  - [将声音放大](#将声音放大)
  - [视频转gif](#视频转gif)
  - [合并视频和字幕](#合并视频和字幕)

## 素材说明

- [源素材](http://clips.vorwaerts-gmbh.de/big_buck_bunny.mp4)
  - Audio: aac (LC) (mp4a / 0x6134706D), 22050 Hz, stereo, fltp, 65 kb/s
  - Video: h264 (Constrained Baseline) (avc1 / 0x31637661), yuv420p(tv, smpte170m/smpte170m/bt709), 640x360, 612 kb/s, 23.96 fps, 24 tbr, 600 tbn, 1200 tbc (default)

- 通过三条命令分别得到 1.mp4, 2.mp4, 3.mp4
  - ffmpeg -y -ss 0 -to 8 -i big_buck_bunny.mp4 -codec copy 1.mp4
  - ffmpeg -y -ss 15 -to 23 -i big_buck_bunny.mp4 -codec copy 2.mp4
  - ffmpeg -y -ss 46 -to 54 -i big_buck_bunny.mp4 -codec copy 3.mp4

## 视频剪切截图

- 4.5秒位置截图一张
  - ffmpeg -i 1.mp4  -ss 4.5 -vframes 1 output.png
- 固定开始时间，连续10张图
  - ffmpeg  -i 1.mp4  -ss 4.500 -vframes 10 output_%3d.png
- 视频每秒截一张图片，保存为png图片，通过滤镜vf指定fps(如果每2秒截一张图，把fps改为0.5即可)，fps就表示每秒几张图
  - ffmpeg -i 1.mp4 -vf fps=1  output_%3d.png
- 视频每秒截一张图片，保存为png图片，通过 -r 指定fps
  - ffmpeg -i 1.mp4 -r 1 output_%3d.jpeg
- 剪切视频
  - ffmpeg -ss 0:1:30 -t 0:0:20 -i 1.mp4 -vcodec copy -acodec copy output.mp4

## 视频拼接

方法一

```filelist.txt
file '1.mp4'
file '2.mp4'
file '3.mp4'
```

`ffmpeg -f concat -i filelist.txt -c copy -y ./output.mp4`

说明：其中 filelist.txt 里每行写一个文件，要求格式参数一致

方法二

`ffmpeg -v debug -i 1.mp4 -i 2.mp4 -i 3.mp4 -t 3 -filter_complex "[0]scale=1920:1080[0v];[1]scale=1920:1080[1v];[2]scale=1920:1080[2v];[0:a]asplit=1[0a];[1:a]asplit=1[1a];[2:a]asplit=1[2a];[0v][0a][1v][1a][2v][2a]concat=n=3:v=1:a=1[v][a]" -vsync 0 -map "[v]" -map "[a]" -vcodec libx264 -pix_fmt yuv420p -y output.mp4`

- `-v debug` 等价于 -loglevel debug 设置日志级别为 debug，支持的日志级别："quiet","panic","fatal","error","warning","info","verbose","debug","trace"
- `-i ./1.mp4 -i ./2.mp4 -i ./3.mp4` 指定输入视频，后边通过[0][1][2]来引用
- `-t 15` 输出持续15s，-t和-to互斥(-t的优先级高于-to)
- `-vsync 0` 时间戳直传，时间戳不会被修改，demux -> mux [deprecated]
- `-map [v] -map [a]` 将[v]和[a]二路流作为输出操作流
- `-vcodec libx264` 编码为 h264
- `-pix_fmt yuv420p` 编码格式为 yuv420p
- `-y` 如果输出文件存在，这覆盖文件
- `./output.mp4` 输出视频文件

- `-filter_complex` 复杂滤波
  - `[0]scale=1920:1080[0v]` 将第0个视频进行缩放为1920*1080，命名为 0v
  - `[0:a]asplit=1[0a]` 取第0个流的音频，命名为 0a
  - `[0v][0a][1v][1a][2v][2a]concat=n=3:v=1:a=1[v][a]` 输入3组音视频，输出1组视频，一组音频。[0v][1v][2v]组合成[v];[0a][1a][2a]组合成[a]

## 视频编码格式转换

`ffmpeg -i 1.mp4 -vcodec libx264 -pix_fmt yuv420p -y output.mp4`

## 素材旋转

ffmpeg -i 1.mp4 -itsoffset 0 -i 2.mp4 -itsoffset 2.1 -i 3.mp4 -t 4.1 -filter_complex "[0]split=1[0v];[1]rotate=0*PI/180:c=0x00000000,format=rgba,colorchannelmixer=aa=1,fade=in:st=0:d=0.1:alpha=1,fade=out:st=1507.8:d=0.01:alpha=1[1v]; [0v][1v]overlay=(W-w)/2:(H-h)/2[overlay1]; [2]rotate=44*PI/180:c=0x00FF00:ow='hypot(iw,ih)':oh=ow
,chromakey=0x00FF00:0.32:0,format=rgba,colorchannelmixer=aa=1[alpha]; [overlay1][alpha]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay2]" -map "[overlay2]" -vcodec libx264 -an -pix_fmt yuv420p -y output.mp4

- `-filter_complex` 复杂滤波
  - `[0]split=1[0v]`  取第0个流的视频，命名为 0v
  - `[1]...[1v]` 取第1个流的视频，命名为 1v, 中间经过一系列操作
    - `rotate=0*PI/180:c=0x00000000` 顺时针旋转0度，超出区域填充透明色
    - `format=rgba` 数据格式为rgba，带alpha通道
    - `colorchannelmixer=aa=1`
    - `fade=in:st=0:d=0.1:alpha=1`
    - `fade=out:st=1507.8:d=0.01:alpha=1`
  - `[0v][0a][1v][1a][2v][2a]concat=n=3:v=1:a=1[v][a]` 输入3组音视频，输出1组视频，一组音频。[0v][1v][2v]组合成[v];[0a][1a][2a]组合成[a]

ffmpeg -i ../../media/video/5hVideo.mp4 -itsoffset 0 -i ./video/aivideo/2b6649148deb924c9bb65766041662c8_transition.mp4 -itsoffset 10.2 -i ./video/aivideo/a24d21088c88c4d1af78d54978199b88.mp4 -t 19.66666 -filter_complex " [0]scale=1920:1080[0v];[1]rotate=0*PI/180:c=0x00000000,format=rgba,colorchannelmixer=aa=1,fade=in:st=0:d=0.1:alpha=1,fade=out:st=1507.8:d=0.01:alpha=1[1v]; [0v][1v]overlay=(W-w)/2:(H-h)/2[overlay1]; [2]rotate=44*PI/180:c=0x00FF00:ow='hypot(iw,ih)':oh=ow
,chromakey=0x00FF00:0.32:0,format=rgba,colorchannelmixer=aa=1[alpha]; [overlay1][alpha]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay2]" -map [overlay2] -vcodec libx264 -an -pix_fmt yuv420p -y ./yodoxuTest3_video.mp4

## 素材缩放

filter_complex " [0]scale=1920:1080[0v] “

## 素材透明度调整

ffmpeg -v debug -threads 6 -i ./video/aivideo/2b6649148deb924c9bb65766041662c8.mp4 -itsoffset 0 -i ./video/aivideo/a24d21088c88c4d1af78d54978199b88_transition.mp4 -t 19.66666 -filter_complex " [0]scale=1920:1080[0v];[1]rotate=PI/3:c=0x00000000[rotate1];[rotate1]format=rgba,colorchannelmixer=aa=0.5[1v]; [0v][1v]overlay=0:0[overlay1]" -map [overlay1] -vcodec libx264 -an -pix_fmt yuv420p -y ./yodoxuTest3_video.mp4

## 素材位置调整

[overlay5][6v]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay6]

## 背景纯色填充

pad="1920:1080:(ow-iw)/2:(oh-ih)/2:blue"

## 背景图片填充

[overlay5][6v]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay6]

## 背景模糊

ffmpeg -v debug -threads 6 -i ../../media/video/5hVideo.mp4 -itsoffset 0 -i ./video/aivideo/2b6649148deb924c9bb65766041662c8_transition.mp4 -itsoffset 10.2 -i ./video/aivideo/a24d21088c88c4d1af78d54978199b88.mp4 -t 19.66666 -filter_complex " [0]scale=1920:1080[0v];[1]rotate=0*PI/180:c=0x00000000[rotate];[rotate]format=rgba,colorchannelmixer=aa=1[alpha];[alpha]fade=in:st=0:d=0.1:alpha=1,fade=out:st=1507.8:d=0.01:alpha=1[1v]; [0v][1v]overlay=(W-w)/2:(H-h)/2[overlay1]; [2]split=2[2split1][2split2];[2split1]scale=1920:1080[scale];[scale]boxblur=10:10[blur];[2split2]rotate=44*PI/180:c=0x00FF00,chromakey=0x00FF00:0.32:0[rotate];[rotate]format=rgba,colorchannelmixer=aa=1[alpha];[blur][alpha]overlay=(W-w)/2:(H-h)/2:eof_action=pass[handled]; [overlay1][handled]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay2]" -map [overlay2] -vcodec libx264 -an -pix_fmt yuv420p -y ./yodoxuTest3_video.mp4

## 视频镜像

xvfb-run -a --server-args="-screen 0 1920x1080x24 -ac -nolisten tcp -dpi 72 +extension RANDR"ffmpeg -v debug -threads 6 -i ../../media/video/5hVideo.mp4 -itsoffset 37 -i ./video/aivideo/1f9025efb50a4e6aaaddcbc2d1e41184.mp4 -itsoffset 21 -i ./video/aivideo/1f9025efb50a4e6aaaddcbc2d1e41184.mp4 -itsoffset 15 -i ./video/aivideo/a24d21088c88c4d1af78d54978199b88.mp4 -itsoffset 8 -i ./video/aivideo/9583473a25ca1bfa54ad01443f8463c0.mp4 -itsoffset 8 -i ./video/aivideo/bg12.jpeg -itsoffset 0 -i ./video/aivideo/2b6649148deb924c9bb65766041662c8.mp4  -t 15 -filter_complex " [0]scale=1920:1080[0v];[1]plusglshader=sdsource=../../media/effect/adjustment.gl:vxsource='../../media/effect/vertex.gl',rotate=0*PI/180:c=0x00FF00:ow='hypot(iw,ih)':oh=ow,chromakey=0x00FF00:0.15:0,format=rgba,colorchannelmixer=aa=1[1v]; [0v][1v]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay1]; [2]rotate=0*PI/180:c=0x00FF00:ow='hypot(iw,ih)':oh=ow,chromakey=0x00FF00:0.25:0,format=rgba,colorchannelmixer=aa=1[2v]; [overlay1][2v]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay2]; [3]split=2[split1][split2];[split2]boxblur=8:8,scale=1920:1080[split2];[split1]rotate=0*PI/180:c=0x00FF00:ow='hypot(iw,ih)':oh=ow,chromakey=0x00FF00:0.25:0,format=rgba,colorchannelmixer=aa=0.5[3v]; [split2][3v]overlay=(W-w)/2:(H-h)/2[3v]; [overlay2][3v]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay3]; [4]split=2[split1][split2];[split2]scale=1920:1080[split2];[split1]plusglshader=sdsource=../../media/effect/mirror_frag.gl:vxsource='../../media/effect/mirror_vertex.gl',rotate=50*PI/180:c=0x00FF00:ow='hypot(iw,ih)':oh=ow,chromakey=0x00FF00:0.25:0,format=rgba,colorchannelmixer=aa=1[5v]; [5]scale=1920:1080[image];[split2][image]overlay=(W-w)/2:(H-h)/2[split2];[split2][5v]overlay=(W-w)/2:(H-h)/2[5v]; [overlay3][5v]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay5]; [6]split=2[split1][split2];[split2]drawbox=0:0:color=#5233c1:t=fill,scale=1920:1080[split2];[split1]plusglshader=sdsource=../../media/effect/mirror_frag.gl:vxsource='../../media/effect/mirror_vertex.gl',rotate=0*PI/180:c=0x00FF00:ow='hypot(iw,ih)':oh=ow,chromakey=0x00FF00:0.25:0,format=rgba,colorchannelmixer=aa=1[6v]; [split2][6v]overlay=(W-w)/2:(H-h)/2[6v]; [overlay5][6v]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay6]" -map [overlay6] -vcodec libx264 -an -pix_fmt yuv420p -y ./yodoxuTest3_video.mp4

## 蒙版

ffmpeg -v debug -threads 6 -i ./yodoxuTest3_gif.mp4 -loop 1 -i ./video/aivideo/mask10.png -t 14 -filter_complex "[1]scale=1920:1080,chromakey=#75fa6b:0.1:0,format=rgba,colorchannelmixer=aa=1[alf];[0][alf]overlay=(W-w)/2:(H-h)/2" -vcodec libx264 -pix_fmt yuv420p -y ./yodoxuTest3_testMaskPng.mp4

## 花字贴纸

ffmpeg -v debug \
-threads 6 \
 -i ./media/FinalCombineTest9.mp4 -itsoffset 7.0 -i ./media/heibaixiantiao1V2.mp4 -i ./media/1.mp4 -i ./media/0.mp4  -ignore_loop 0 -itsoffset 3.0 -i ./media/timesnapimg2/%3d.png \
-t 15 \
-filter_complex " \
[1:v] fade=in:st=6:d=1:alpha=1,fade=out:st=12:d=2:alpha=1 [1vv]; \
[1vv]scale=480:250[1v]; \
[2:v] fade=out:st=1:d=1:alpha=1 [2vv]; \
[2vv]scale=480:250[2v]; \
[3:v] fade=out:st=0.5:d=0.5:alpha=1 [3v]; \
[0][1v]overlay=20:20[out]; \
[out][2v]overlay=200:280[out2]; \
[out2][3v]overlay=500:180[out3]; \
[4]scale=480:250[4v]; \
[4v] fade=out:st=7:d=1.5:alpha=1 [4vv]; \
[out3][4vv]overlay=0:0[trueout]" \
-map [trueout] \
-y ./Lab/giftest5.mp4

## 视频画中画

scale + overlay

## 素材亮度调整，素材对比度调整，素材饱和度调整

xvfb-run -a --server-args="-screen 0 1920x1080x24 -ac -nolisten tcp -dpi 72 +extension RANDR"ffmpeg -v debug -threads 6 -i ../../media/video/5hVideo.mp4 -itsoffset 0 -i ./video/aivideo/2b6649148deb924c9bb65766041662c8_transition.mp4 -itsoffset 10.2 -i ./video/aivideo/a24d21088c88c4d1af78d54978199b88.mp4-itsoffset 18 -i ./video/aivideo/a24d21088c88c4d1af78d54978199b88.mp4 -itsoffset 18 -loop 1 -i ./video/aivideo/bg1.png-t 29.66666 -filter_complex " [0]scale=1920:1080[0v];[1]rotate=0*PI/180:c=0x00000000[rotate];[rotate]format=rgba,colorchannelmixer=aa=1[alpha];[alpha]fade=in:st=0:d=0.1:alpha=1,fade=out:st=1507.8:d=0.01:alpha=1[1v]; [0v][1v]overlay=(W-w)/2:(H-h)/2[overlay1]; [2]split=2[2split1][2split2];[2split1]scale=1920:1080[scale];[scale]boxblur=10:10[blur];[2split2]rotate=44*PI/180:c=0x00FF00,chromakey=0x00FF00:0.32:0,format=rgba,colorchannelmixer=aa=1.0[alpha];[blur][alpha]overlay=(W-w)/2:(H-h)/2:eof_action=pass[handled]; [overlay1][handled]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay2];[4]scale=1920:1080[scale];[scale]fade=in:st=0:d=0.1:alpha=1,fade=out:st=23.7:d=0.1:alpha=1[handled4];[3]rotate=90*PI/180:c=0x00FF00,chromakey=0x00FF00:0.32:0,format=rgba,colorchannelmixer=aa=0.3[alpha];[handled4][alpha]overlay=(W-w)/2:(H-h)/2:eof_action=pass[handled]; [overlay2][handled]overlay=(W-w)/2:(H-h)/2:eof_action=pass[overlay3];[overlay3]plusglshader=sdsource=../../media/effect/adjustment.gl:vxsource='../../media/effect/vertex.gl':start=3.0:duration=5[final] " -map [final] -vcodec libx264 -an -pix_fmt yuv420p -y ./yodoxuTest3_video.mp4

## 视频变速

ffmpeg -v debug -threads 6 -i ./yodoxuTest3_video.mp4 -filter_complex "setpts=2.0*PTS" ./yodoxuTest3_video_speeddown.mp4

## 视频裁切

ffmpeg -v debug -threads 6-i ./video/aivideo/a24d21088c88c4d1af78d54978199b88.mp4 -filter_complex "
[0:a]asplit=3[asplit1][asplit2][asplit3];[0:v]scale=1920:1080,setdar=16/9,split=3[split1][split2][split3];[split2]crop=1920:480:0:300,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setdar=16/9[split2];[split3]crop=920:680:500:200,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black,setdar=16/9[split3];[split1][asplit1][split2][asplit2][split3][asplit3]concat=n=3:v=1:a=1[v][a]" -map [v] -map [a] -vcodec libx264 -pix_fmt yuv420p -y ./yodoxuTest3_testCrop.mp4

## 视频倒放

ffmpeg -v debug -i ./video/aivideo/2b6649148deb924c9bb65766041662c8.mp4  -af areverse -vf reverse -y ./yodoxuTest3_testReverse.mp4

## 绿幕抠图

ffmpeg -v debug -threads 6 -i ./yodoxuTest3_gif.mp4 -loop 1 -i ./video/aivideo/mask20.png -t 14 -filter_complex "[1]scale=1920:1080,chromakey=#0b0101:0.01:0,format=rgba,colorchannelmixer=aa=1[alf];[0][alf]overlay=(W-w)/2:(H-h)/2" -vcodec libx264 -pix_fmt yuv420p -y ./yodoxuTest3_testMaskPng.mp4

## 音频变声

soundstretch ./yodoxuTest3_audio.wav ./soundtouch_down.wav -pitch=-5

## 音量调节

ffmpeg -v debug -threads 6-i ../../media/audio/5hAudio.mp4  -i ./audio/aivideo/sm_p5tzf3u3tjuwsl.mp3-t 29.66666 -filter_complex " [1]adelay=0|0,volume=0.5,afade=in:st=0:d=5,afade=out:st=18:d=2[1a];[0][1a]amix=inputs=2:duration=first"  -vcodec libx264 -vn -pix_fmt yuv420p -y ./yodoxuTest3_testVolume3.mp4

## 音频变速

soundstretch ./audio/aivideo/douyin.wav ./audio/aivideo/douyin_nansheng2_jiasu.wav -tempo=100 -pitch=-4

## 音频淡入淡出

[5]adelay=37000|37000,volume=0.5,afade=in:st=37:d=3,afade=out:st=50:d=3[5a]

## 音频拼接

[1]adelay=0|0,volume=1,afade=in:st=0:d=0,afade=out:st=8:d=0[1a]; [2]adelay=8000|8000,volume=1,afade=in:st=8:d=0,afade=out:st=15:d=0[2a]; 

## 多音轨混音

amix=inputs=6:duration=first

## lut滤镜

ffmpeg -v debug \
-i ./media/videoshort.mp4 \
-filter_complex \
"lutglshader=ext=./lut/tokyo.jpg:ext_type=0:sdsource=./gl/lut_shader.gl:vxsource='./gl/lut_vertex.gl'" \
-vcodec libx264 \
-an \
-f mp4 \
-y ./lab/luttest_tokyo.mp4

## shader特效

ffmpeg -v debug \
-i videoshort.mp4 \
-filter_complex "[0:v]plusglshader=sdsource='./AwesomeFourth.gl':vxsource='./gl/light_vertex2.gl'[1outgl];[1outgl]scale=1280:-2" \
-vcodec libx264 \
-an \
-pix_fmt yuv420p \
-y AwesomeFourth4_anothervideo.mp4

## shader转场

ffmpeg -v debug \
-threads 8 \
-i ./media/pureblack.mov -ignore_loop 0 -i ./media/giftest.gif \
-t 10 \
-filter_complex "
[1]scale=1920:1080[1v]; \
[0][1v]gltransition=duration=1.0:offset=0.0:source=./Lab/huanhuanxiayiV2.glsl[1outgl]; \
[1outgl]scale=1920:-2[final1]" \
-map "[final1]" \
-vcodec libx264 \
-pix_fmt yuv420p \
-y ./Lab/videotransitiontest6.mp4

## 视频定格

中间图片不用变化：
ffmpeg -v debug -threads 6 -ss 0.0 -i ./video/aivideo/a24d21088c88c4d1af78d54978199b88.mp4 -ss 0.0 -i ./video/aivideo/a24d21088c88c4d1af78d54978199b88.mp4 -filter_complex "
[0:a]asetpts='PTS-STARTPTS + gte(T,2)*(3/TB)',aresample=async=1:first_pts=0[a];[1]setpts='PTS-STARTPTS + gte(T,2)*(3/TB)'[v]" -map [v] -map [a] -vcodec libx264 -pix_fmt yuv420p -y ./yodoxuTest3_testSetpts.mp4

中间图片需要变化：
ffmpeg -ss 2.50 -i ./video/aivideo/2b6649148deb924c9bb65766041662c8.mp4 -frames:v 1 -q:v 2 -y ./frame.jpg

ffmpeg -ss 0.00 -t 2.50 -accurate_seek -i ./video/aivideo/2b6649148deb924c9bb65766041662c8.mp4 \
-vcodec libx264 \
-pix_fmt yuv420p \
-avoid_negative_ts "make_zero" -y ./2b6649148deb924c9bb65766041662c8_first.mp4

ffmpeg -ss 2.50-accurate_seek  -i ./video/aivideo/2b6649148deb924c9bb65766041662c8.mp4 \
-vcodec libx264 \
-pix_fmt yuv420p \
-avoid_negative_ts "make_zero" -y ./2b6649148deb924c9bb65766041662c8_second.mp4


ffmpeg -v debug -i ./2b6649148deb924c9bb65766041662c8_first.mp4 -i ./yodoxuTest3_testFrame1.mp4 -i ./2b6649148deb924c9bb65766041662c8_second.mp4  -t 15 -filter_complex "[0:a]asplit=1[0a];[0]scale=1920:1080[0v];[1]fade=out:st=2.9:d=0.01:alpha=1[1v];[2]scale=1920:1080[2v];[1:a]asplit=1[1a];[2:a]asplit=1[2a];[0v][0a][1v][1a][2v][2a]concat=n=3:v=1:a=1[v][a]" -vsync 0  -map [v] -map [a] -vcodec libx264 -pix_fmt yuv420p -y ./yodoxuTest3_testFrameFinal.mp4

## 提取音频或视频

ffmpeg -i input_file -vcodec copy -an output_file_video //分离视频流
ffmpeg -i input_file -acodec copy -vn output_file_audio //分离音频流

## 桌面分享推流

ffmpeg -f avfoundation -i "1" -vcodec libx264 -preset ultrafast -acodec libfaac -f flv rtmp://domain/rtmplive/home 

## 推流桌面+麦克风

ffmpeg -f avfoundation -i "1:0" -vcodec libx264 -preset ultrafast -acodec libmp3lame -ar 44100 -ac 1 -f flv rtmp://domain/rtmplive/home 

## 推流桌面+摄像头+麦克风

ffmpeg -f avfoundation -framerate 30 -i "1:0" \-f avfoundation -framerate 30 -video_size 640x480 -i "0" \-c:v libx264 -preset ultrafast \-filter_complex 'overlay=main_w-overlay_w-10:main_h-overlay_h-10' -acodec libmp3lame -ar 44100 -ac 1  -f flv rtmp://domain/rtmplive/home 

## 视频解封装

ffmpeg –i test.mp4 –vcodec copy –an –f m4v test.264
ffmpeg –i test.avi –vcodec copy –an –f m4v test.264

## 视频转码

ffmpeg –i test.mp4 –vcodec h264 –s 352*278 –an –f m4v test.264 //转码为码流原始文件
ffmpeg –i test.mp4 –vcodec h264 –bf 0 –g 25 –s 352*278 –an –f m4v test.264 //转码为码流原始文件
ffmpeg –i test.avi -vcodec mpeg4 –vtag xvid –qsame test_xvid.avi //转码为封装文件

-bf B帧数目控制
-g 关键帧间隔控制
-s 分辨率控制

## 视频改封装

ffmpeg –i video_file.flv –i audio_file –vcodec copy –acodec copy output_file.mp4

## 直播转录

ffmpeg –i rtsp://192.168.3.205:5555/test –vcodec copy out.avi

## 播放yuv文件

ffplay -f rawvideo -video_size 1920x1080 input.yuv

## 双声道合并单声道

ffmpeg -i music.mp3 -ac 1 music.aac

## 提取两个声道

-map_channel [input_file_id.stream_specifier.channel_id|-1][?][:output_file_id.stream_specifier]

ffmpeg -i music.mp3 -map_channel 0.0.0 letf.aac -map_channel 0.0.1 right.aac

## 将两个音频源合并为双声道

 ffmpeg -i left.aac -i right.aac -filter_complex "[0:a][1:a]amerge=inputs=2[aout]" -map "[aout]" output.mka

## 音频音量探测

 ffmpeg -i test.mp4 -filter_complex volumedetect -c:v copy -f null /dev/null

## 绘制音频波形图  （多声道混合）

ffmpeg -i music.mp3 -filter_complex "showwavespic=s=640*120" -frames:v 1 output.png 

## 绘制不同声道的波形图

ffmpeg -i 1.mp3 -filter_complex "showwavespic=s=640*240:split_channels=1" -frames:v 1 output.png

## 调整音量

声音音量应该仔细调整，以保护我们的耳朵和ffmpeg提供2种方法。第一个使用-vol选项，它接受从0到256的整数值，其中256是最大值

ffmpeg -i music.mp3 -vol 30 sound_low.mp3

另一种方法是使用表中描述的卷过滤器:

音量降低到三分之二

ffmpeg -i music.mp3 -af volume=2/3 quiet_music.mp3

增加10分贝的音量

 ffmpeg -i music.mp3 -af volume=10dB louder_sound.mp3

## 删除其中一个音频流

ffmpeg  -i gf.mkv  -map 0.0 -map 0.2  -vcodec copy -acodec copy out.mkv

## 只保留其中一个声道

ffmpeg.exe -i xiaoetong.mp4 -map_channel 0.1.0 -c:v copy  xiaoetong.single.mp4

## 将声音放大

ffmpeg  -i   input.mp3   -vol   400    output.mp3

## 视频转gif

ffmpeg -i capx.mp4 -t 10 -s 320x240 -pix_fmt rgb24 jidu1.gif
// -t参数表示提取前10秒视频
// -s 表示按照 320x240的像素提取

## 合并视频和字幕

ffmpeg -i webrtc.mp4 -i webrtc.srt -map 0:v -map 0:a -map 1:s -c:v copy -c:a copy -c:s mov_text  webrtc2013.mp4
//mp4不支持srt格式，需要加-c:s mov_text才行，mkv格式则不需要