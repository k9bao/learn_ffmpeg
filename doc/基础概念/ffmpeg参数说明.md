# ffmpeg 参数说明

- [ffmpeg的命令](https://ffmpeg.org/ffmpeg.html)

- 时间单位(偏移量)：默认是秒,可以是正数，可以是小数
  - [时间单位说明](https://ffmpeg.org/ffmpeg-utils.html#time-duration-syntax)
  - [-][HH:]MM:SS[.m...] or [-]S+[.m...][s|ms|us]
  - 55 表示55秒
  - 23.189 表示23.189秒
  - 12:03:45 表示12小数3分钟45秒
  - 200ms 表示0.2秒(200毫秒)
  - 200000us 也是表示0.2秒(200000微妙)

- [颜色单位](https://ffmpeg.org/ffmpeg-utils.html#Color)
  - `Black` `0x000000` `#000000` `#000000FF` 黑色
  - `Green` `0x008000` `#008000` `#008000FF` 绿色
  - `#00000000` `#000000@0.0` 黑色+背景色透明
  - `#00000080` `#000000@0.5` 黑色+背景色半透明
  - `#000000FF` `#000000@1.0` 黑色+背景色不透明,这也是默认缺省值

- `-vf` `-filter:v` 视频滤镜

- `-b:v` 视频码率，比如 4096k
- `-b:a` 音频码率, 比如 128k

- `-codec` `-c` 编码，比如 -c copy 保存于是编码格式
  - `-vcodec` `-codec:v` `-c:v` 视频编码 比如 h264
  - `-acodec` `-codec:a` `-c:a` 音频编码 比如 aac

- `-f` 指定fmt格式
  - 比如 image2,rawvideo,avi等
  - 一般无需指定，通过后缀或者源猜测容器。
  - 比如要把 vp8 封装到 mp4中，则需要指定
- `-frames:v` `-vframes` 设置输出视频帧数

- `-itsoffset` 偏移量，时间单位

- `-pix_fmt` 数据格式，比如 yuv420p

- `-r` fps,整数或分数3000/1001
  - 作为输入参数，会忽略文件中的时间戳，重新打时间戳。
  - 作为输出参数，会根据实际个数丢弃或者拷贝帧
  - 可以通过滤镜的 fps 指定，比如 -vf fps=1

- `-s` 指定输入或输出视频尺寸
  - 比如 1920x1080，一般情况下输入无需指定，除非是裸流。
  - 输出大小一般建议使用 scale 滤镜， 比如 -vf scale=1920:1080

- `-t` 输出的duration时间，-t和-to互斥(-t的优先级高于-to)

- `-v` -loglevel 的缩写，设置日志级别
  - 支持的日志级别："quiet","panic","fatal","error","warning","info","verbose","debug","trace"

- `-y` 如果输出文件存在，则覆盖文件

## [滤镜的命令](https://ffmpeg.org/ffmpeg-filters.html)

- [split/asplit 分割](http://underpop.online.fr/f/ffmpeg/help/split_002c-asplit.htm.gz)
  - `[0:a]asplit=1[0a]` 取第0个流的音频，命名为 0a
  - `[0]split=1[0v]` 取第0个流的视频，命名为 0v
- [scale 缩放](https://ffmpeg.org/ffmpeg-filters.html#scale-1)
  - `[0]scale=1920:1080[0v]` 将第0个视频进行缩放为1920*1080，命名为 0v
- [fade 淡入淡出](https://ffmpeg.org/ffmpeg-filters.html#fade)
  - `[1]fade=out:st=2.9:d=0.01:alpha=1[1v]` 第1个视频在2.9秒位置淡出，持续0.01秒。仅针对alpha通道，如果没有alpha通道，则淡入淡出不生效
- [concat 拼接](https://ffmpeg.org/ffmpeg-filters.html#concat)
  - `[0v][0a][1v][1a][2v][2a]concat=n=3:v=1:a=1[v][a]` 输入3组音视频，输出1组视频，一组音频。[0v][1v][2v]组合成[v];[0a][1a][2a]组合成[a]
- [rotate 旋转](https://ffmpeg.org/ffmpeg-filters.html#rotate)
  - `rotate=0*PI/180:c=0x00000000` 顺时针旋转0度，超出区域填充透明色
- [colorchannelmixer 颜色混合](https://ffmpeg.org/ffmpeg-filters.html#colorchannelmixer)
  - red=red*rr + blue*rb + green*rg + alpha*ra 调整红色
  - blue=red*br + blue*bb + green*bg + alpha*ba 调整红色
  - green=red*gr + blue*gb + green*gg + alpha*ga 调整红色
  - alpha=red*ar + blue*ab + green*ag + alpha*aa 调整透明通道
  