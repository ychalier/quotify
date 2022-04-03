import os
import glob
import json
import argparse
import tempfile
import subprocess


def get_video_size(video_path, ffprobe="ffprobe"):
    process = subprocess.Popen(
        [
            ffprobe,
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


def merge_video_files(files, video_output, ffmpeg="ffmpeg", ffprobe="ffprobe"):
    tempdir = tempfile.gettempdir()
    with open(os.path.join(tempdir, "concat.txt"), "w", encoding="utf8") as outfile:
        for file in files:
            outfile.write("file '%s'\n" % os.path.realpath(file))
    width, height = get_video_size(files[0], ffprobe)
    subprocess.Popen(
        [
            ffmpeg,
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str, help="path to the directory containing video extracts")
    parser.add_argument("output", type=str, help="path to the ouptut video")
    parser.add_argument("-fm", "--ffmpeg", type=str, default="ffmpeg", help=f"path to the FFmpeg executable (default: 'ffmpeg')")
    parser.add_argument("-fp", "--ffprobe", type=str, default="ffprobe", help=f"path to the FFprobe executable (default: 'ffprobe')")
    args = parser.parse_args()
    files = glob.glob(os.path.join(args.input, "*"))
    merge_video_files(files, args.output, args.ffmpeg, args.ffprobe)


if __name__ == "__main__":
    main()