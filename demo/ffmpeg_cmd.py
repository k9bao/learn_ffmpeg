import os
import shutil
import subprocess
import json
import math
import itertools
import tempfile

FFPROBE_BIN = "ffprobe"
FFMPEG_BIN = "ffmpeg"
DEFAULT_FPS = 25

audio_ext_map = {
    "mp3": "mp3",
    "vorbis": "ogg",
    "opus": "opus",
    "aac": "m4a",
    "wmav2": "wma",
    "wmav1": "wma",
}


def run_sys_command(cmd_arr, extra_env=None):
    my_env = os.environ.copy()
    if extra_env is not None:
        my_env.update(extra_env)

    cmd_arr = list(filter(None, cmd_arr))
    cmd_str = " ".join(cmd_arr)

    proc = subprocess.Popen(cmd_arr, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=my_env)

    ret = proc.communicate()
    ret = [r.decode("utf-8", errors="ignore") if r else r for r in ret]

    if proc.returncode != 0:
        print(f"Running command {cmd_str} with non-zero, return code:{proc.returncode},\
                              STDOUT: {ret[0]}, STDERR: {ret[1]}")
    return ret


class VideoProp:
    def __init__(self, url, probe=None) -> None:
        self.url = url
        self.probe = probe

    def get_probe(self):
        if not self.probe:
            self.probe = VideoProcessor.probe(self.url)

    @property
    def vpx_alpha(self):
        if not hasattr(self, "_vpx_alpha"):
            self.get_probe()
            result = False
            if "streams" in self.probe:
                for s in self.probe["streams"]:
                    if s["codec_type"] == "video" and (s["codec_name"] == "vp8" or s["codec_name"] == "vp9"):
                        tags = s.get("tags", {})
                        if tags.get("alpha_mode") == "1" or tags.get("ALPHA_MODE") == "1":
                            result = True
                            break
            setattr(self, "_vpx_alpha", result)
        return self._vpx_alpha

    @property
    def audio_ext(self):
        if not hasattr(self, "_audio_ext"):
            self.get_probe()
            result = ".m4a"
            streams = self.probe.get("streams") or []
            for s in streams:
                if s["codec_type"] == "audio":
                    result = "." + (audio_ext_map.get(s["codec_name"]) or "mp4")
                    break
            setattr(self, "_audio_ext", result)
        return self._audio_ext

    @property
    def video_ext(self):
        if not hasattr(self, "_video_ext"):
            self.get_probe()
            if self.vpx_alpha:
                setattr(self, "_video_ext", ".webm")
            else:
                setattr(self, "_video_ext", ".mp4")
        return self._video_ext

    def video_code(self):
        self.get_probe()
        if "streams" in self.probe:
            for s in self.probe["streams"]:
                if s["codec_type"] == "video":
                    return s.get("codec_name", None)
        return ""

    def fmt_duration_sec(self):
        self.get_probe()
        if "format" in self.probe:
            if "duration" in self.probe["format"]:
                return float(self.probe["format"]["duration"])
        if "streams" in self.probe:
            for s in self.probe["streams"]:
                if s["codec_type"] == "video" and "duration" in s:
                    return float(s["duration"])
        if "streams" in self.probe:
            for s in self.probe["streams"]:
                if s["codec_type"] == "audio" and "duration" in s:
                    return float(s["duration"])
        return 0.0

    def get_stream_type(self):
        # 0:音视频都没有, 1:只有视频, 2:只有音频, 3:音视频都有
        self.get_probe()
        stream_type = 0
        if "streams" in self.probe:
            for s in self.probe["streams"]:
                if s["codec_type"] == "video":
                    stream_type |= 1
                if s["codec_type"] == "audio":
                    stream_type |= 2
        return stream_type

    @staticmethod
    def is_valid_audio(self):
        self.get_probe()
        stream = [s for s in (self.probe.get("streams") or []) if s["codec_type"] == "audio"]
        return True if stream else False

    @staticmethod
    def get_video_size(self):
        self.get_probe()
        if "streams" in self.probe:
            for s in self.probe["streams"]:
                if s["codec_type"] == "video":
                    sar = s.get("sample_aspect_ratio", "1:1")
                    dar = s.get("display_aspect_ratio", "16:9")
                    return s["width"], s["height"], sar, dar

    @staticmethod
    def ts_offset(self):
        self.get_probe()
        video_s, audio_s = 0, 0
        has_video, has_audio = False, False
        streams = self.probe.get("streams") or []
        for s in streams:
            if s["codec_type"] == "video" and not has_video:
                video_s = float(s["start_time"])
                has_video = True
            elif s["codec_type"] == "audio" and not has_audio:
                audio_s = float(s["start_time"])
                has_audio = True
        return (video_s, audio_s)


class VideoProcessor:
    def __init__(self):
        pass

    @staticmethod
    def download_m3u8(video_url, output_path):
        command = [FFMPEG_BIN, "-y", "-loglevel", "error", "-i", video_url, "-c", "copy", output_path]
        run_sys_command(command)

    @staticmethod
    def dump(video_path, duration=None, start=None):
        command = [
            FFMPEG_BIN,
            *(["-ss", f"{start/1000.}"] if start is not None else []),
            *(["-t", f"{duration/1000.}"] if duration > 0 else []),
            "-i",
            video_path,
            "-dump",
            "-f",
            "null",
            "-",
        ]
        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, err = pipe.communicate()
        if err:
            raise err.decode("utf-8", "ignore")
        out = out.decode("utf-8", "ignore")
        return out

    @staticmethod
    def probe(video_path):
        command = [
            FFPROBE_BIN,
            "-loglevel",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]

        pipe = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        out, __ = pipe.communicate()
        info = json.loads(out)
        if "format" in info and "duration" not in info["format"]:
            info["format"]["duration"] = 0
        return info

    @staticmethod
    def get_project_cover(video_path, cover_path):
        command = [FFMPEG_BIN, "-y", "-loglevel", "error", "-i", video_path, "-vframes", "1", cover_path]
        run_sys_command(command)

    @staticmethod
    def duplicate_first_frame(video_path, frames, new_path):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=True) as tmp:
            command = [FFMPEG_BIN, "-y", "-loglevel", "error", "-i", video_path, "-vframes", "1", tmp.name]
            run_sys_command(command)

            d = frames / DEFAULT_FPS
            command = [
                FFMPEG_BIN,
                "-y",
                "-loglevel",
                "error",
                "-r",
                "25",
                "-loop",
                "1",
                "-i",
                tmp.name,
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                "libx264",
                "-r:v",
                "25",
                "-preset",
                "medium",
                "-vframes",
                f"{frames}",
                "-r",
                "25",
                "-t",
                f"{d}",
                new_path,
            ]
            run_sys_command(command)

    def normalize_video(video_path, target):
        file_info = VideoProcessor.probe(video_path)
        streams = file_info.get("streams") or []
        to_normalize = False
        for s in streams:
            if s["codec_type"] == "video":
                tb = s["time_base"]
                if tb != "1/12800":
                    to_normalize = True
                # only support h264
                if s.get("codec_name") != "h264":
                    to_normalize = True
            elif s["codec_type"] == "audio":
                tb = s["time_base"]
                if tb != "1/44100":
                    to_normalize = True
        if to_normalize:
            command = [FFMPEG_BIN, "-y", "-loglevel", "error", "-i", video_path, "-r", "25", target]
            run_sys_command(command)
        else:
            shutil.copy(video_path, target)
        return to_normalize

    @staticmethod
    def normalize_videos(video_paths):
        # TODO: 如果video_paths的第一个是gap_0.mp4, 则把这个mp4里的mp3 抽调
        # add by zhkun @2019-03-29
        for vf in video_paths:
            if vf.find("gap") > 0:
                tmp_file = vf[0:-4] + "_tmp.mp4"
                command = [FFMPEG_BIN, "-y", "-loglevel", "error", "-i", vf, "-vcodec", "copy", "-an", tmp_file]
                run_sys_command(command)
                shutil.move(tmp_file, vf)

    @staticmethod
    def concat_audios(audio_paths, output_path):
        if len(audio_paths) == 1:
            shutil.copyfile(audio_paths[0], output_path)
            return
        tmp_file = output_path.split(".")
        tmp_file[-2] += "_tmp"
        tmp_file = ".".join(tmp_file)
        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            "-i",
            "concat:{}|{}".format(audio_paths[0], audio_paths[1]),
            tmp_file,
        ]
        run_sys_command(command)
        shutil.move(tmp_file, output_path)

    @staticmethod
    def concat_videos(video_paths, output_path, concat_list):
        """
        Concatenate multiple videos together.
        """
        # TODO: THIS ONLY WORKS WHEN VIDEO AND AUDIO CODECS ARE THE SAME
        if len(video_paths) == 1:
            shutil.copyfile(video_paths[0], output_path)
            return

        VideoProcessor.normalize_videos(video_paths)

        with open(concat_list, "w") as concat:
            lines = ["file '%s'" % filename for filename in video_paths]
            concat.write("\n".join(lines))

        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            "-fflags",
            "+igndts",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_list,
            "-c",
            "copy",
            # '-c:a', 'libmp3lame',
            "-r",
            "25",
            output_path,
        ]
        run_sys_command(command)

    @staticmethod
    def download_silent_audio(url, duration, target_path):
        duration /= 1000
        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            "-i",
            f"{url}",
            "-ss",
            "0",
            "-t",
            f"{duration}",
            "-c",
            "copy",
            "-strict",
            "-2",
            target_path,
        ]
        run_sys_command(command)

    @staticmethod
    def download_black_clip(target_path, dimension, duration, crop):
        # only 16:9 black background
        # 16 : 9
        height = 0
        if int(dimension[0]) * 720 / int(dimension[1]) == 1280:
            height = dimension[1]
        # 9: 16
        elif int(dimension[0]) * 1280 / int(dimension[1]) == 720:
            height = dimension[1]
        url = "{}/assets/{}_background.mp4".format(os.path.dirname(os.path.abspath(__file__)), height)
        duration = ((duration - 22) if duration > 22 else duration) / 1000
        if os.path.exists(url):
            if crop:
                crop = (crop[2] - crop[0], crop[3] - crop[1], crop[0], crop[1])
                command = [
                    FFMPEG_BIN,
                    "-y",
                    "-loglevel",
                    "error",
                    "-t",
                    f"{duration}",
                    "-i",
                    url,
                    "-t",
                    f"{duration}",
                    "-strict",
                    "-2",
                    "-vf",
                    f"crop={crop[0]}:{crop[1]}:{crop[2]}:{crop[3]}, setsar=1:1",
                    target_path,
                ]
            else:
                command = [
                    FFMPEG_BIN,
                    "-y",
                    "-loglevel",
                    "error",
                    "-t",
                    f"{duration}",
                    "-i",
                    url,
                    "-t",
                    f"{duration}",
                    "-strict",
                    "-2",
                    target_path,
                ]
        else:
            url = "{}/assets/720_background.mp4".format(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            if crop:
                width, height = crop[2] - crop[0], crop[3] - crop[1]
            else:
                width, height = dimension
            # 先crop一块图片，后调用scale，可以保证输出一定是偶数宽高的
            if width * 9 > height * 16:
                h = 1280 * height // width
                scale = f"scale={width}:-2"
                crop = f"crop=1280:{h}:0:0"
            else:
                w = 720 * width // height
                scale = f"scale=-2:{height}"
                crop = f"crop={w}:720:0:0"
            command = [
                FFMPEG_BIN,
                "-y",
                "-loglevel",
                "error",
                "-t",
                f"{duration}",
                "-i",
                url,
                "-t",
                f"{duration}",
                "-strict",
                "-2",
                "-vf",
                crop + "," + scale + ", setsar=1:1",
                target_path,
            ]
        run_sys_command(command)

    @staticmethod
    def mix_all_sounds(voices, audios, final_sound, target_video, output_path, duration, pure_edition):
        voice_path = final_sound[:-4] + "_v.mp3"
        audio_path = final_sound[:-4] + "_a.mp3"
        if voices:
            VideoProcessor.amix_all_voice(voices, voice_path)
        if audios:
            VideoProcessor.amix_all_audios(audios, audio_path)
            VideoProcessor.track_replace_audio(target_video, audio_path, pure_edition, duration=duration / 1000)
        else:
            shutil.copyfile(target_video, pure_edition)
        if voices and audios:
            tmp_path = final_sound[:-4] + "_tmp.mp3"
            fc = "[1]volume=0.67[2];[0][2]amix=2:dropout_transition=3600," "volume=2,pan=stereo|c0=c0+c2|c1=c1+c3"
            command = [
                FFMPEG_BIN,
                "-y",
                "-loglevel",
                "error",
                "-i",
                voice_path,
                "-i",
                audio_path,
                "-filter_complex",
                fc,
                tmp_path,
            ]
            run_sys_command(command)
            VideoProcessor.normalize_sound_file(tmp_path, final_sound)
        else:
            source_path = voice_path if voices else audio_path
            shutil.move(source_path, final_sound)
            if audios:
                shutil.copyfile(pure_edition, output_path)
                return

        VideoProcessor.track_replace_audio(target_video, final_sound, output_path, duration=duration / 1000)

    @staticmethod
    def amix_all_voice(all_voices, audio_path):
        all_filename = list(all_voices.keys())
        time_offset = list(all_voices.values())
        all_filename = [file for file, _ in sorted(zip(all_filename, time_offset), key=lambda p: p[1])]
        time_offset = sorted(time_offset)

        amt = len(all_filename)
        if amt == 1:
            offset = time_offset[0]
            command = [
                FFMPEG_BIN,
                "-y",
                "-loglevel",
                "error",
                "-i",
                all_filename[0],
                "-filter_complex",
                f"[0]adelay={offset}|{offset}",
                audio_path,
            ]
            run_sys_command(command)
        else:
            inputs = list(itertools.chain.from_iterable(["-i", f] for f in all_filename))

            delay = ";".join(
                "[{0}]adelay={1}|{1}[{2}]".format(i, start, i + amt) for i, start in enumerate(time_offset)
            )
            amix = "".join("[{}]".format(amt + i) for i in range(amt))
            fc = "{0};{1}amix={2}:" "dropout_transition=3600".format(delay, amix, amt)
            pan = ",pan=stereo|c0=c0+c1|c1=c0+c1"
            fc = fc + pan

            command = [FFMPEG_BIN, "-y", "-loglevel", "error", *inputs, "-filter_complex", fc, audio_path]
            run_sys_command(command)

        tmp_file = audio_path[:-4] + "_nor.mp3"
        VideoProcessor.normalize_sound_file(audio_path, tmp_file)
        shutil.move(tmp_file, audio_path)

    @staticmethod
    def amix_chunk_audios(chunk, offset_chunk, chunk_time_offset_delta, audio_path):
        inputs = list(itertools.chain.from_iterable(["-i", f] for f in chunk))
        chunk_amt = len(chunk)
        delay = ";".join(
            "[{0}]adelay={1}|{1},volume={3:.2f}[{2}]".format(
                i, offset - chunk_time_offset_delta, i + chunk_amt, chunk_amt / (i + chunk_amt)
            )
            for i, offset in enumerate(offset_chunk)
        )
        amix = "".join("[{}]".format(chunk_amt + i) for i in range(chunk_amt))
        fc = "{0};{1}amix={2}:" "dropout_transition=3600,volume={3}".format(delay, amix, chunk_amt, chunk_amt)
        pan = ",pan=stereo|c0=c0+c2|c1=c1+c3"
        fc = fc + pan

        command = [FFMPEG_BIN, "-y", "-loglevel", "error", *inputs, "-filter_complex", fc, audio_path]
        run_sys_command(command)

    @staticmethod
    def amix_all_audios(all_voices, audio_path):
        all_filename = list(all_voices.keys())
        time_offset = list(all_voices.values())
        amt = len(all_filename)
        if amt == 1:
            offset = time_offset[0]
            command = [
                FFMPEG_BIN,
                "-y",
                "-loglevel",
                "error",
                "-i",
                all_filename[0],
                "-filter_complex",
                f"[0]adelay={offset}|{offset}",
                audio_path,
            ]
            run_sys_command(command)
        else:
            chunk_size = 120
            chunk_count = amt // chunk_size
            filename_chunk = []
            time_offset_chunk = []
            item_startoffset = []
            start = 0
            for i in range(chunk_count):
                filename_chunk.append(all_filename[start : start + chunk_size])
                time_offset_chunk.append(time_offset[start : start + chunk_size])
                item_startoffset.append(time_offset[start])
                start += chunk_size

            left_item_len = amt - chunk_count * chunk_size
            if chunk_count == 0 or left_item_len > 1:
                filename_chunk.append(all_filename[start:])
                time_offset_chunk.append(time_offset[start:])
                item_startoffset.append(time_offset[start])
            elif left_item_len == 1:
                # if only one was left, append it to the tail of last chunk
                filename_chunk[-1].append(all_filename[start])
                time_offset_chunk[-1].append(time_offset[start])

            if len(item_startoffset) == 1:
                offset_start = item_startoffset[0]
                print(f"processing {offset_start}")
                VideoProcessor.amix_chunk_audios(filename_chunk[0], time_offset_chunk[0], 0, audio_path)
                print(f"end processing {offset_start} ===> {audio_path}")
            else:
                segment_files = []
                chunk_item_offset = 0
                for j in range(len(item_startoffset)):
                    offset_start = item_startoffset[j]
                    tmp_file = audio_path[:-4] + f"_{j}.mp3"
                    print(f"processing {j}:{offset_start}")
                    VideoProcessor.amix_chunk_audios(filename_chunk[j], time_offset_chunk[j], offset_start, tmp_file)
                    segment_files.append(tmp_file)
                    print(f"end processing {j}:{offset_start} ===> {tmp_file}")
                    chunk_item_offset += len(filename_chunk[j])
                VideoProcessor.amix_chunk_audios(segment_files, item_startoffset, 0, audio_path)

        tmp_file = audio_path[:-4] + "_nor.mp3"
        VideoProcessor.normalize_sound_file(audio_path, tmp_file)
        shutil.move(tmp_file, audio_path)

    @staticmethod
    def normalize_head_and_tail(head_tail_paths, dimension):
        dw, dh = dimension
        screen_width = 0
        if int(dw) * 720 / int(dh) == 1280:
            screen_width = dw
        # 9: 16
        elif int(dw) * 1280 / int(dh) == 720:
            screen_width = dw
        for key in head_tail_paths:
            path = head_tail_paths[key]
            if not path:
                continue
            normalized_path = f"{path[:-4]}_nor.mp4"
            if screen_width:
                command = [
                    FFMPEG_BIN,
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    path,
                    "-vf",
                    f"scale={screen_width}:-1",
                    "-c:a",
                    "copy",
                    normalized_path,
                ]
            else:
                width, height, _, _ = VideoProcessor.get_video_size(path)
                if width * dh > dw * height:
                    pad = f"{dw}:{dw}*ih/iw:(ow-iw)/2:(oh-ih)/2"
                else:
                    pad = f"{dh}*iw/ih:{dh}:(ow-iw)/2:(oh-ih)/2"
                command = [
                    FFMPEG_BIN,
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    path,
                    "-vf",
                    pad,
                    "-c:a",
                    "copy",
                    normalized_path,
                ]
            run_sys_command(command)
            head_tail_paths[key] = normalized_path
        return head_tail_paths

    @staticmethod
    def concat_head_and_tail(video_path, head_tail_paths, output_path):
        head_path = head_tail_paths["head"]
        tail_path = head_tail_paths["tail"]
        inputs = ["-i", head_path, "-i", video_path, "-i", tail_path]
        filter_str = "[0:v] [0:a] [1:v] [1:a] " "[2:v] [2:a] concat=n=3:v=1:a=1 [v] [a]"
        if not head_path:
            inputs = inputs[2:]
            filter_str = "[0:v] [0:a] [1:v] [1:a] concat=n=2:v=1:a=1 [v] [a]"
        if not tail_path:
            inputs = inputs[:-2]
            filter_str = "[0:v] [0:a] [1:v] [1:a] concat=n=2:v=1:a=1 [v] [a]"

        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            *inputs,
            "-filter_complex",
            filter_str,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-q",
            "0",
            output_path,
        ]
        run_sys_command(command)

    @staticmethod
    def replace_audio(video_path, audio_path, output_path, duration):
        """
        Replace video's audio stream with a new stream.
        The original audio stream will be removed.
        """
        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            "-i",
            video_path,
            "-i",
            audio_path,
            "-t",
            f"{duration}",
            "-af",
            "apad",
            "-shortest",
            "-map",
            "0:0?",
            "-map",
            "1:0",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            output_path,
        ]
        run_sys_command(command)

    @staticmethod
    def track_replace_audio(video_path, audio_path, target_path, duration=None):
        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            "-i",
            video_path,
            "-i",
            audio_path,
        ]
        if duration is not None:
            command.extend(["-t", f"{duration-0.022}"])
        command.extend(["-c:v", "copy", "-c:a", "aac", "-map", "0:v:0?", "-map", "1:a:0", target_path])
        run_sys_command(command)

    @staticmethod
    def extract_audio_from_video(video_path):
        number_of_audio_stream = len(
            [s for s in VideoProcessor.probe(video_path).get("streams", []) if s["codec_type"] == "audio"]
        )
        if number_of_audio_stream > 0:
            extract_audio = video_path[:-3] + "mp3"
            command = [
                FFMPEG_BIN,
                "-y",
                "-loglevel",
                "error",
                "-i",
                video_path,
                "-vn",
                "-c:a",
                "libmp3lame",
                # audio quality 2
                # revise project j87kiksdujama4t0bjfktyr
                # to see cut_audio
                "-q:a",
                "2",
                extract_audio,
            ]
            run_sys_command(command)
            return extract_audio
        else:
            return None

    @staticmethod
    def set_volume(audio_path, volume):
        path_array = os.path.splitext(audio_path)
        output_audio = f"{path_array[0]}_volume{path_array[1]}"
        if volume == 1:
            shutil.move(audio_path, output_audio)
            return output_audio
        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            "-i",
            audio_path,
            "-vol",
            f"{int(256 * volume)}",
            output_audio,
        ]
        run_sys_command(command)
        return output_audio

    @staticmethod
    def cut_videos(video_path, offsets, output_paths):
        new_offsets = []
        for offset in offsets:
            start, end = offset
            # ??? why 22.
            end = end - 22 if end - 22 > start else end
            info = VideoProcessor.probe(video_path)
            stream = [s for s in info["streams"] if s["codec_type"] == "video" and "duration" in s]
            duration = float(stream[0]["duration"])
            if duration - 0.04 < start / 1000:
                length = (end + 22 - start) / 1000
                start = duration - length
                new_offsets.append((start, length - 0.022))
            else:
                new_offsets.append((start / 1000, (end - start) / 1000))
        targets = list(
            itertools.chain.from_iterable(
                ["-ss", f"{offset[0]}", "-t", f"{offset[1]}", target]
                for (offset, target) in zip(new_offsets, output_paths)
            )
        )

        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            *VideoProcessor.get_input_video_option(video_path, ignoreSync=True, useGPUMemory=False),
            "-i",
            video_path,
            "-max_muxing_queue_size",
            "400",
            "-q",
            "0",
            "-r",
            "25",
            *VideoProcessor.get_pre_output_options(),
            *targets,
        ]
        run_sys_command(command)

    @staticmethod
    def cut_audio(audio_path, start_ms, end_ms, output_path):
        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            "-i",
            audio_path,
            "-max_muxing_queue_size",
            "400",
            "-ss",
            VideoProcessor.convert_ms_to_ffutils_time_format(start_ms),
            "-t",
            f"{(end_ms-start_ms)/1000}",
            "-q:a",
            "2",
            "-vsync",
            "2",
            "-vn",
            output_path,
        ]
        run_sys_command(command)

    @staticmethod
    def audio_fade_in_out(audio_path, output_path, fade_in, fade_out, start, end):
        if fade_in == 0 and fade_out == 0:
            shutil.move(audio_path, output_path)
        else:

            # added by fulin 2019-7-10
            # if duration less than fadein+fade
            duration = end - start
            if fade_in + fade_out > duration:
                if fade_in == 0:
                    fade_out = duration
                elif fade_out == 0:
                    fade_in = duration
                else:
                    fade_out = duration // 2
                    fade_in = duration - fade_out

            st = (end - fade_out) / 1000
            fade_in_str = f"afade=t=in:ss={start}:d={fade_in/1000}"
            fade_out_str = f"afade=t=out:st={st}:d={fade_out/1000}"
            if fade_in != 0 and fade_out != 0:
                fade_str = ",".join([fade_in_str, fade_out_str])
            else:
                fade_str = fade_in_str if fade_out == 0 else fade_out_str

            command = [FFMPEG_BIN, "-y", "-loglevel", "error", "-i", audio_path, "-af", fade_str, output_path]
            run_sys_command(command)

    @staticmethod
    def change_media_speed(video_path, speed, duration):  # 返回实际的视频秒数，用于真实的渲染
        stream_type = VideoProp(video_path).get_stream_type()
        if stream_type == 0:
            return video_path

        output_path = f"{video_path[:-4]}_s.mp4"
        # duration2 = (duration-22)/1000
        print("-->>origin video_path: {} duration{}, speed{}".format(video_path, duration, speed))
        speed = 1.0 / speed
        """
         ffmpeg -i input.mp4 -filter_complex
         "[0:v]setpts=0.25*PTS[v];[0:a]atempo=2.0,atempo=2.0[a]"
         -map "[v]" -map "[a]" output4.mp4
        """
        ffmpeg_filter = ""
        if stream_type & 1:
            ffmpeg_filter += f"[0:v]setpts={speed}*PTS[v];"
        if stream_type & 2:
            if speed >= 0.5 and speed <= 2:
                ffmpeg_filter += f"[0:a]atempo={1/speed}[a]"
            elif (0.25 <= speed and speed < 0.5) or (2 < speed and speed <= 4):
                aspeed = 1 / math.pow(speed, 1 / 2)
                ffmpeg_filter += f"[0:a]{','.join([f'atempo={aspeed}']*2)}[a]"
            elif speed > 4 and speed <= 8:
                aspeed = 1 / math.pow(speed, 1 / 3)
                ffmpeg_filter += f"[0:a]{','.join([f'atempo={aspeed}']*3)}[a]"
            elif speed > 8 and speed <= 10:
                aspeed = 1 / math.pow(speed, 1 / 4)
                ffmpeg_filter += f"[0:a]{','.join([f'atempo={aspeed}']*4)}[a]"
            else:
                print("not support", speed)

        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            *VideoProcessor.get_input_video_option(video_path),
            "-i",
            video_path,
            # '-vf', f'setpts=PTS*{speed}',
            "-filter_complex",
            ffmpeg_filter,
        ]
        if stream_type & 1:
            command.extend(["-map", "[v]"])
        if stream_type & 2:
            command.extend(["-map", "[a]"])
        command.extend(
            [
                "-t",
                f"{duration}",  # remarked by zhikun@2019-01-14
                *VideoProcessor.get_pre_output_options(),
                output_path,
            ]
        )
        run_sys_command(command)
        shutil.move(output_path, video_path)

    @staticmethod
    def watermark(video_path, watermark_path, output_path):

        ffmpeg_filter = "overlay=(main_w-overlay_w)*0.5:(main_h-overlay_h)*0.5"
        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            *VideoProcessor.get_input_video_option(
                video_path,
                useGPUMemory=False,
            ),
            "-i",
            video_path,
            "-i",
            watermark_path,
            "-filter_complex",
            ffmpeg_filter,
            *VideoProcessor.get_pre_output_options(),
            output_path,
        ]
        run_sys_command(command)

    @staticmethod
    def loop_picture(pic_path, output_path, duration):
        times = int(math.ceil(duration / 1000 / VideoProcessor.duration(pic_path)))
        with tempfile.NamedTemporaryFile(delete=True) as tmp:
            tmp.write(bytes("\n".join(["file '%s'" % pic_path] * times), "utf-8"))
            # flush文件, 否则后续命令加载文件可能会失败
            tmp.flush()
            command = [
                FFMPEG_BIN,
                "-y",
                "-loglevel",
                "error",
                "-safe",
                "0",
                "-f",
                "concat",
                "-i",
                tmp.name,
                "-c",
                "copy",
                "-t",
                VideoProcessor.convert_ms_to_ffutils_time_format(duration),
                output_path,
            ]
            run_sys_command(command)

    @staticmethod
    def extend_audio(audio_path, output_path, duration, repeat=True, fade_out=False):
        repeat_name = output_path[:-4] + "_repeat.mp3"

        if repeat:
            times = int(math.ceil(duration / 1000 / VideoProcessor.duration(audio_path)))
            with tempfile.NamedTemporaryFile(delete=True) as tmp:
                tmp.write("\n".join(["file '%s'" % audio_path] * times))
                tmp.flush()
                cmd_arr = [
                    FFMPEG_BIN,
                    "-y",
                    "-loglevel",
                    "error",
                    "-safe",
                    "0",
                    "-f",
                    "concat",
                    "-i",
                    tmp.name,
                    "-c",
                    "copy",
                    "-t",
                    VideoProcessor.convert_ms_to_ffutils_time_format(duration),
                    repeat_name,
                ]
                run_sys_command(cmd_arr)
        else:
            cmd_arr = [
                FFMPEG_BIN,
                "-y",
                "-loglevel",
                "error",
                "-i",
                audio_path,
                "-t",
                VideoProcessor.convert_ms_to_ffutils_time_format(duration),
                "-filter_complex",
                "[0]apad",
                repeat_name,
            ]
            run_sys_command(cmd_arr)

        bgm_fade_out_path = repeat_name

        shutil.move(bgm_fade_out_path, output_path)
        return output_path

    @staticmethod
    def crop_video(video_path, output_path, x, y, width, height, relative=0):
        """
        when t=0, x, y, width, height is the absolute value,
        when t=1, x, y, width, height is the percentage value to iw, ih
        """
        if relative == 0:
            crop_tpl = "crop={}:{}:{}:{}"
        else:
            crop_tpl = "crop={}*iw:{}*ih:{}*iw:{}*ih"
        cmd_arr = [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            # no support crop output image from decoder
            *VideoProcessor.get_input_video_option(video_path, useGPUMemory=False),
            "-i",
            video_path,
            "-filter:v",
            crop_tpl.format(width, height, x, y),
            *VideoProcessor.get_pre_output_options(),
            output_path,
        ]
        run_sys_command(cmd_arr)
        return output_path

    @staticmethod
    def normalize_sound_file(audio_path, output_path):
        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            "-i",
            audio_path,
            "-map",
            "0:a",
            "-ac",
            "2",
            "-ar",
            "44100",
            "-c:a",
            "libmp3lame",
            "-q:a",
            "2",
            "-map_metadata",
            "-1",
            output_path,
        ]
        run_sys_command(command)

    @staticmethod
    def check_keyframe(video_path: str) -> bool:
        command = [
            FFPROBE_BIN,
            "-loglevel",
            "error",
            "-select_streams",
            "v",
            "-show_frames",
            "-show_entries",
            "frame=key_frame",
            video_path,
        ]
        ret = run_sys_command(command)
        if "key_frame=1" in ret[0]:
            return True
        return True

    @staticmethod
    def get_picture(file: str, time: float, output: str):
        command = [FFMPEG_BIN, "-ss", str(time), "-y", "-loglevel", "error", "-i", file, "-vframes", "1", output]
        run_sys_command(command)

    @staticmethod
    def cut_asset(video_prop, start, end, video_output):
        command = [
            FFMPEG_BIN,
            "-y",
            "-loglevel",
            "error",
            "-ss",
            f"{start/1000}",
            "-t",
            f"{(end-start)/1000}",
            "-i",
            video_prop.url,
            "-an",
            "-c:v",
            "copy",
            video_output,
        ]
        run_sys_command(command)

    # 将一张图片生成指定长度的定格视频
    @staticmethod
    def media_freeze_frame(input_path, output_path, fps, duration):
        command = [
            FFMPEG_BIN,
            "-y",
            "-f",
            "image2",
            "-stream_loop",
            "-1",
            "-i",
            input_path,
            "-r",
            str(fps),
            "-t",
            str(duration),
            output_path,
        ]
        run_sys_command(command)

    # 视频倒放
    @staticmethod
    def media_reverse(input_path):
        output_path = f"{input_path[:-4]}_reverse.mp4"

        command = [FFMPEG_BIN, "-y", "-i", input_path, "-vf", "reverse", "-af", "areverse", output_path]
        run_sys_command(command)
        shutil.move(output_path, input_path)
