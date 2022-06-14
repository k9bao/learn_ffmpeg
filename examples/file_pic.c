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


static AVFormatContext *fmt_ctx;
static AVCodecContext *dec_ctx;
static int video_stream_index = -1;
static int64_t last_pts = AV_NOPTS_VALUE;
static int64_t pkt_count = 0;

#define LOGE(TAG, format, ...) av_log(NULL, AV_LOG_ERROR, "%d:%s" TAG format "\n", __LINE__, __FUNCTION__, ##__VA_ARGS__)
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
  av_log(NULL, AV_LOG_DEBUG, "open video decoder ok\n");
  return 0;
}

int main(int argc, char **argv) {
  int ret;
  AVPacket packet;
  AVFrame *frame;
  char buf[1024];
  const char *filename, *outpath;

  if (argc <= 1) {
    LOGE(TAG,
            "Usage: %s <input file>\n"
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
  }

// ........

  avcodec_free_context(&dec_ctx);
  avformat_close_input(&fmt_ctx);
  av_frame_free(&frame);

  if (ret < 0 && ret != AVERROR_EOF) {
    LOGE(TAG, "Error occurred: %s\n", av_err2str(ret));
    exit(1);
  }

  exit(0);
}
