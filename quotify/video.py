from lib2to3.pgen2 import token
import os
import json
import tempfile
import subprocess
import tqdm
from .config import FFPROBE_EXECUTABLE, YOUTUBE_DL_EXECUTABLE, FFMPEG_EXECUTABLE


def get_video_size(video_path):
    process = subprocess.Popen(
        [
            FFPROBE_EXECUTABLE,
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            video_path
        ],
        stdout=subprocess.PIPE
    )
    process.wait()
    data = json.loads(process.stdout.read().decode("utf8"))
    for stream in data["streams"]:
        if "width" in stream and "height" in stream:
            return stream["width"], stream["height"]
    raise RuntimeError(f"Could not retrieve the size of { video_path }")


def get_video_stream(url):
    process = subprocess.Popen(
        [
            YOUTUBE_DL_EXECUTABLE,
            "-g",
            url
        ],
        stdout=subprocess.PIPE
    )
    process.wait()
    split = process.stdout.read().decode("utf8").strip().split("\n")
    if len(split) != 2:
        raise RuntimeError(f"Could not find a stream for { url }")
    return split


def slugify(*captions):
    return "-".join(
        token
        for caption in captions
        for token in caption.tokens()
    )


def extract_captions(selection, parts_directory):
    files = []
    for i, (video_source, captions) in enumerate(tqdm.tqdm(selection)):
        outpath = os.path.join(parts_directory, "%04d-%s.mp4" % (i, slugify(*captions)))
        files.append(os.path.realpath(outpath))
        if isinstance(video_source, str):
            subprocess.Popen(
                [
                    FFMPEG_EXECUTABLE,
                    "-loglevel",
                    "quiet",
                    "-hide_banner",
                    "-ss",
                    captions[0].start.to_ffmpeg_timecode(),
                    "-i",
                    video_source,
                    "-t",
                    (captions[-1].end - captions[0].start).to_ffmpeg_timecode(),
                    outpath,
                    "-y"
                ]
            ).wait()
        else:
            subprocess.Popen(
                [
                    FFMPEG_EXECUTABLE,
                    "-loglevel",
                    "quiet",
                    "-hide_banner",
                    "-ss",
                    captions[0].start.to_ffmpeg_timecode(),
                    "-i",
                    video_source[0],
                    "-t",
                    (captions[-1].end - captions[0].start).to_ffmpeg_timecode(),
                    "-ss",
                    captions[0].start.to_ffmpeg_timecode(),
                    "-i",
                    video_source[1],
                    "-t",
                    (captions[-1].end - captions[0].start).to_ffmpeg_timecode(),
                    "-map",
                    "0:v",
                    "-map",
                    "1:a",
                    "-c:v",
                    "libx264",
                    "-c:a",
                    "aac",
                    outpath,
                    "-y"
                ]
            ).wait()
    return files


def merge_video_files(files, video_output):
    tempdir = tempfile.gettempdir()
    with open(os.path.join(tempdir, "concat.txt"), "w", encoding="utf8") as outfile:
        for file in files:
            outfile.write("file '%s'\n" % file)
    width, height = get_video_size(files[0])
    subprocess.Popen(
        [
            FFMPEG_EXECUTABLE,
            "-loglevel",
            "quiet",
            "-stats",
            "-hide_banner",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            os.path.join(tempdir, "concat.txt"),
            "-vf",
            f"scale={ width }:{ height }",
            video_output,
            "-y"
        ]
    ).wait()

