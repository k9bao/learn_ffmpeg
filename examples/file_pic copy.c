#define _XOPEN_SOURCE 600 /* for usleep */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <libavcodec/avcodec.h>
#include <libavfilter/buffersink.h>
#include <libavfilter/buffersrc.h>
#include <libavformat/avformat.h>
#include <libavutil/opt.h>


void ascii2hex(unsigned char* chs,int len) {  
	//用于接收到的串转换成要用的十六进制串返回主窗口调用
	char hex[16] = {'0', '1', '2', '3', '4', '5', '6', '7', '8','9', 'A', 'B', 'C', 'D', 'E', 'F'};
  int i = 0;
  while(i < len){
    int b= chs[i] & 0x000000ff;
    printf("%c%c",hex[b/16],hex[b%16]);
    if (i != 0 && i%16 == 0){
      printf("\n");
    }else{
      printf(" ");
    }
    i++;
  }
} 


static AVFormatContext *fmt_ctx;
static AVCodecContext *dec_ctx;
static int video_stream_index = -1;
static int64_t last_pts = AV_NOPTS_VALUE;
static int64_t pkt_count = 0;

#define LOGE(TAG, format, ...) av_log(NULL, AV_LOG_ERROR, "%d:%s" TAG format "\n", __LINE__, __FUNCTION__, ##__VA_ARGS__)
// #define LOGE(TAG, format, ...) av_log(NULL, AV_LOG_ERROR, "%s:%d:%s" TAG format "\n", __FILE__, __LINE__, __FUNCTION__, ##__VA_ARGS__)
#define TAG "[FILE_PIC]"

static int open_input_file(const char *filename) {
  int ret;
  AVCodec *dec;

  if ((ret = avformat_open_input(&fmt_ctx, filename, NULL, NULL)) < 0) {
    av_log(NULL, AV_LOG_ERROR, "Cannot open input file\n");
    return ret;
  }

  if ((ret = avformat_find_stream_info(fmt_ctx, NULL)) < 0) {
    av_log(NULL, AV_LOG_ERROR, "Cannot find stream information\n");
    return ret;
  }

  /* select the video stream */
  ret = av_find_best_stream(fmt_ctx, AVMEDIA_TYPE_AUDIO, -1, -1, &dec, 0);
  if (ret < 0) {
    av_log(NULL, AV_LOG_ERROR, "Cannot find a video stream in the input file\n");
    return ret;
  }
  av_log(NULL, AV_LOG_ERROR, "%s, fmt_dur:%lld, stream_dur:%lld, str_time.base=%d,%d", 
    filename, fmt_ctx->duration,fmt_ctx->streams[0]->duration, fmt_ctx->streams[0]->time_base.den,fmt_ctx->streams[0]->time_base.num);

  video_stream_index = ret;

  /* create decoding context */
  dec_ctx = avcodec_alloc_context3(dec);
  if (!dec_ctx) return AVERROR(ENOMEM);
  avcodec_parameters_to_context(dec_ctx, fmt_ctx->streams[video_stream_index]->codecpar);

  /* init the video decoder */
  if ((ret = avcodec_open2(dec_ctx, dec, NULL)) < 0) {
    av_log(NULL, AV_LOG_ERROR, "Cannot open video decoder\n");
    return ret;
  }
  av_seek_frame(fmt_ctx, video_stream_index, 1, 0);

  return 0;
}

static void pgm_save(unsigned char *buf, int wrap, int xsize, int ysize, char *filename) {
  FILE *f;
  int i;

  f = fopen(filename, "wb");
  fprintf(f, "P5\n%d %d\n%d\n", xsize, ysize, 255);
  for (i = 0; i < ysize; i++) fwrite(buf + i * wrap, 1, xsize, f);
  fclose(f);
}

static void write_data(unsigned char *buf, int size, char *filename) {
  FILE *f;
  f = fopen(filename, "wb");
  fwrite(buf, 1, size, f);
  fclose(f);
}

static int recv_frame(AVCodecContext *dec_ctx, AVFrame *frame, const char *out_path) {
  char buf[1024];
  int ret;
  int first_in = 1;
  while (1) {
    ret = avcodec_receive_frame(dec_ctx, frame);
    if (ret == AVERROR(EAGAIN) || ret == AVERROR_EOF) {
      if (1) {
        LOGE(TAG, "----Warn during decoding, %s\n", av_err2str(ret));
        LOGE(TAG, "----%d, %d\n", ret == AVERROR(EAGAIN), ret == AVERROR_EOF);
      }
      return 0;
    } else if (ret < 0) {
      LOGE(TAG, "Error during decoding, %s\n", av_err2str(ret));
      return ret;
    }
    first_in = 0;
    static int64_t last_dts = AV_NOPTS_VALUE;
    static int64_t last_pts = AV_NOPTS_VALUE;
    if (last_dts == AV_NOPTS_VALUE) {
      last_dts = frame->pkt_dts;
    }
    if (last_pts == AV_NOPTS_VALUE) {
      last_pts = frame->pkt_pts;
    }

    if (frame->pkt_dts < last_dts) {
      LOGE(TAG,"dts is not incress.now(%lld) > last(%lld)\n", frame->pkt_dts, last_dts);
    }

    AVStream *s = fmt_ctx->streams[video_stream_index];
    float t = frame->pkt_pts * 1.0 / s->time_base.den;
    LOGE(TAG,
        "saving frame,(%d,%d), \
%3d,pts=%lld,dts=%lld, \
time_base=[%d,%d],%f\n",
        frame->key_frame, frame->pict_type, dec_ctx->frame_number, frame->pkt_pts, frame->pkt_dts, s->time_base.den,
        s->time_base.num, t);
    // LOGE(TAG,"saving frame %d-%d,%d-%d\n",
    // dec_ctx->time_base.den,dec_ctx->time_base.num,dec_ctx->pkt_timebase.den,dec_ctx->pkt_timebase.num);
    fflush(stdout);

    if (dec_ctx->frame_number < 1000) {
      snprintf(buf, sizeof(buf), "%s%d-%lld-%06f.pgm", out_path, dec_ctx->frame_number, frame->pts, t);
      pgm_save(frame->data[0], frame->linesize[0], frame->width, frame->height, buf);
      fflush(stdout);
    }
    last_dts = frame->pkt_dts;
    last_pts = frame->pkt_pts;
  }
}
static int send_package(AVCodecContext *dec_ctx, AVPacket *pkt, const char *out_path) {
  char buf[1024];
  int ret;
  pkt_count++;
  LOGE(TAG,"pkt_count:%lld,pkt:pts:%lld,dts:%lld\n", pkt_count, pkt->pts, pkt->dts);
  if (pkt->pts < pkt->dts) {
    LOGE(TAG,"pts(%lld) < dts(%lld)\n", pkt->pts, pkt->dts);
    exit(0);
  }
  if (pkt->pts == AV_NOPTS_VALUE || pkt->dts == AV_NOPTS_VALUE) {
    LOGE(TAG,"pts or dts is null.pts=%lld,dts=%lld\n", pkt->pts, pkt->dts);
  } else {
  }

  ret = avcodec_send_packet(dec_ctx, pkt);
  if (ret < 0) {
    LOGE(TAG, "Error sending a packet for decoding,ret=%d,%s,%lld\n", ret, av_err2str(ret), pkt->pts);
    LOGE(TAG, "%lld,%lld,%d\n", pkt->pts, pkt->dts, pkt->size);
    // exit(1);
  }
  // if (pkt_count <= 6){
  //     char buf[100] = {0};
  //     snprintf(buf, sizeof(buf), "%s/%lld.pkg", out_path, pkt_count);
  //     write_data(pkt->data, pkt->size, buf);
  // }else{
  //     AVPacket clean_pkt;
  //     clean_pkt.size = 0;
  //     clean_pkt.buf = NULL;
  //     avcodec_send_packet(dec_ctx, &clean_pkt);
  // }
  return ret;
}

int main(int argc, char **argv) {
  int ret;
  AVPacket packet;
  AVFrame *frame;
  char buf[1024];
  const char *filename, *outpath;

  if (argc <= 2) {
    LOGE(TAG,
            "Usage: %s <input file> <output file>\n"
            "And check your input file is encoded by mpeg1video please.\n",
            argv[0]);
    exit(0);
  }
  filename = argv[1];
  outpath = argv[2];

  frame = av_frame_alloc();
  if (!frame) {
    perror("Could not allocate frame");
    exit(1);
  }

  ret = open_input_file(filename);
  if (ret < 0) {
    LOGE(TAG,"open file err %s.", filename);
    goto end;
  }

  LOGE(TAG,"44444\n");
  /* read all packets */
  while (1) {
    if ((ret = av_read_frame(fmt_ctx, &packet)) < 0) {
      LOGE(TAG,"av_read_frame over.\n");
      break;
    }

    if (packet.stream_index == video_stream_index) {
      if (send_package(dec_ctx, &packet, outpath) == 0) {
        recv_frame(dec_ctx, frame, outpath);
      }
    }
    av_packet_unref(&packet);
  }
  avcodec_send_packet(dec_ctx, &packet);
  recv_frame(dec_ctx, frame, outpath);
end:
  avcodec_free_context(&dec_ctx);
  avformat_close_input(&fmt_ctx);
  av_frame_free(&frame);

  if (ret < 0 && ret != AVERROR_EOF) {
    LOGE(TAG, "Error occurred: %s\n", av_err2str(ret));
    exit(1);
  }

  exit(0);
}
