import os
import re
import csv
import json
import enum
import tempfile
import argparse
import subprocess
import tqdm


YOUTUBE_DL_EXECUTABLE = "yt-dlp"
FFMPEG_EXECUTABLE = "ffmpeg"
CAPTIONS_FOLDER = "captions"


YOUTUBE_VIDEO_ID_PATTERN = re.compile(r".*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]{11}).*", re.MULTILINE)
LINE_TIMESTAMP_PATTERN = re.compile(r"^(\d\d:\d\d:\d\d\.\d\d\d) --> (\d\d:\d\d:\d\d\.\d\d\d)")
SPLIT_LINE_TIMESTAMP_PATTERN = re.compile(r"<(\d\d:\d\d:\d\d\.\d\d\d)>")


def remove_tags(string):
    """Remove any HTML tag from a string.
    """
    return re.sub(r"\[\w+?\]", "", re.sub(r"<[^>]+?>", "", string)).strip()


def extract_video_id(url):
    """Extract a YouTube video ID from a URL.
    """
    match = YOUTUBE_VIDEO_ID_PATTERN.match(url)
    if match is not None:
        return match.group(1)
    raise ValueError(f"Could not extract video id from { url }")


@enum.unique
class CaptionSource(enum.Enum):

    INNER = 0
    TRAILING = 1


class Timestamp:

    STRING_PATTERN = re.compile(r"(\d\d):(\d\d):(\d\d)\.(\d\d\d)")

    def __init__(self, total_seconds):
        self.total_seconds = total_seconds
        self._hours = int(self.total_seconds) // 3600
        self._minutes = (int(self.total_seconds) % 3600) // 60
        self._seconds = int(self.total_seconds) % 60
        self._milliseconds = int(self.total_seconds * 1000) % 1000

    def __eq__(self, other):
        return self.total_seconds == other.total_seconds
    
    def __hash__(self):
        return hash(self.total_seconds)

    def __add__(self, other):
        return Timestamp(self.total_seconds + other.total_seconds)

    def __sub__(self, other):
        return Timestamp(self.total_seconds - other.total_seconds)

    def __repr__(self):
        return str(self.total_seconds)

    def __str__(self):
        return "%02d:%02d:%02d.%03d" % (
            self._hours,
            self._minutes,
            self._seconds,
            self._milliseconds
        )
    
    def copy(self):
        return Timestamp(self.total_seconds)
    
    def to_ffmpeg_timecode(self):
        return "%02d:%02d:%02d.%02d" % (
            self._hours,
            self._minutes,
            self._seconds,
            round(self._milliseconds * 0.1)
        )
    
    def to_premiere_timecode(self, ips=25):
        return "%02d:%02d:%02d:%02d" % (
            self._hours,
            self._minutes,
            self._seconds,
            round(self._milliseconds * 0.001 * ips)
        )
    
    @classmethod
    def from_string(cls, string):
        match = cls.STRING_PATTERN.match(string)
        return cls(
            3600 * int(match.group(1))\
            + 60 * int(match.group(2))\
            + int(match.group(3))\
            + .001 * int(match.group(4))
        )


class Caption:

    def __init__(self, text, start, end, source=None):
        self.text = remove_tags(text)
        self.start = start
        self.end = end
        self.source = source
    
    def __repr__(self):
        return "%s --> %s\t%s" % (
            str(self.start),
            str(self.end),
            self.text
        )
    
    def __str__(self):
        return "%s --> %s\t%s" % (
            str(self.start),
            str(self.end),
            self.text
        )
    
    def copy(self):
        return Caption(
            self.text,
            self.start.copy(),
            self.end.copy(),
            self.source)

    def to_dict(self):
        return {
            "text": self.text,
            # "start": repr(self.start),
            # "end": repr(self.end),
            "start": self.start.to_ffmpeg_timecode(),
            "end": self.end.to_ffmpeg_timecode(),
            # "start_premiere_timecode": self.start.to_premiere_timecode(),
            # "end_premiere_timecode": self.end.to_premiere_timecode(),
            "source": self.source.name if self.source is not None else None
        }


def download_subtitles(url, lang="fr"):
    """Download WebVTT subtitles from a YouTube video.
    """
    video_id = extract_video_id(url)
    output_path = os.path.join(CAPTIONS_FOLDER, f"{ video_id }.{ lang }.vtt")
    if os.path.isfile(output_path):
        return output_path
    os.makedirs(CAPTIONS_FOLDER, exist_ok=True)
    subprocess.Popen(
        [
            YOUTUBE_DL_EXECUTABLE,
            "--write-auto-sub",
            "--sub-lang",
            lang,
            "--sub-format",
            "vtt",
            "--skip-download",
            "--output",
            os.path.join(CAPTIONS_FOLDER, f"{ video_id }"),
            f"https://www.youtube.com/watch?v={ video_id }",
        ]
    ).wait()
    return output_path if os.path.isfile(output_path) else None


def parse_webvtt(text):
    """Parse a WebVTT string a return a list of captions.
    """
    header_line = True
    captions = []
    current_caption_start = None
    current_caption_end = None
    current_caption_end_whole = None
    current_caption_text = ""
    for line in text.split("\n"):
        line = line.strip()
        if line == "":
            continue
        if header_line:
            if re.match(r"^(WEBVTT|\w+: \w+)$", line):
                continue
            header_line = False
        if not header_line:
            match = LINE_TIMESTAMP_PATTERN.match(line)
            if match is not None:
                current_caption_start = Timestamp.from_string(match.group(1))
                current_caption_end = Timestamp.from_string(match.group(2))
                current_caption_end_whole = current_caption_end
                current_caption_text = ""
            else:
                is_a_timestamp = False
                for bit in SPLIT_LINE_TIMESTAMP_PATTERN.split(line):
                    if is_a_timestamp:
                        current_caption_end = Timestamp.from_string(bit)
                        captions.append(Caption(
                            current_caption_text.strip(),
                            current_caption_start,
                            current_caption_end,
                            CaptionSource.INNER))
                        current_caption_text = ""
                        current_caption_start = current_caption_end
                    else:
                        current_caption_text += " " + bit.strip()
                    is_a_timestamp = not is_a_timestamp
                captions.append(Caption(
                    current_caption_text.strip(),
                    current_caption_start,
                    current_caption_end_whole,
                    CaptionSource.TRAILING))
    buffer_size = 50
    buffer = ""
    for caption in captions:
        if caption.text == "":
            continue
        for i in range(len(buffer) - 1):
            if caption.text.startswith(buffer[i:])\
                and (caption.text == buffer[i:]
                    or caption.text[len(buffer) - i] in " ")\
                and (i == 0
                    or buffer[i - 1] in " "):
                caption.text = caption.text[len(buffer) - i:]
        if caption.text != "":
            buffer = re.sub(" +", " ", buffer + " " + caption.text)
        if len(buffer) > buffer_size:
            buffer = buffer[len(buffer) - buffer_size - 1:]
        
    for caption in captions:
        caption.text = caption.text.strip()
    return [
        caption
        for caption in captions
        if caption.text != ""
    ]


def retrieve_captions(vtt_source):
    if os.path.isfile(vtt_source):
        with open(vtt_source, "r", encoding="utf8") as file:
            text = file.read()
    else:
        source_path = download_subtitles(vtt_source)
        if source_path is None:
            raise ValueError(f"Could not download subtitles from { vtt_source }")
        with open(source_path, "r", encoding="utf8") as file:
            text = file.read()
    return parse_webvtt(text)


def export_captions(captions, captions_output):
    if captions_output.endswith(".json"):
        with open(captions_output, "w", encoding="utf8") as file:
            json.dump({
                "captions": [
                    caption.to_dict()
                    for caption in captions
                ]
            }, file, indent=4)
    elif captions_output.endswith(".csv"):
        with open(captions_output, "w", encoding="utf8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=captions[0].to_dict().keys())
            writer.writeheader()
            writer.writerows([caption.to_dict() for caption in captions])
    else:
        raise ValueError(f"Output format not supported (only .json or .csv)")


def main_parse(vtt_source, captions_output):
    captions = retrieve_captions(vtt_source)
    export_captions(captions, captions_output)


def filter_captions_for_word(captions, word):
    selection = []
    for i, caption in enumerate(captions):
        if word in caption.text:
            copy_ = caption.copy()
            if i < len(captions) - 1:
                copy_.end = captions[i + 1].end.copy()
            selection.append(copy_)
    return selection


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


def extract_captions(video_source, captions, parts_directory):
    files = []
    for i, caption in enumerate(tqdm.tqdm(captions)):
        outpath = os.path.join(parts_directory, "%04d.mp4" % i)
        files.append(outpath)
        if isinstance(video_source, str):
            subprocess.Popen(
                [
                    FFMPEG_EXECUTABLE,
                    "-loglevel",
                    "quiet",
                    "-hide_banner",
                    "-ss",
                    caption.start.to_ffmpeg_timecode(),
                    "-i",
                    video_source,
                    "-t",
                    (caption.end - caption.start).to_ffmpeg_timecode(),
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
                    caption.start.to_ffmpeg_timecode(),
                    "-i",
                    video_source[0],
                    "-t",
                    (caption.end - caption.start).to_ffmpeg_timecode(),
                    "-ss",
                    caption.start.to_ffmpeg_timecode(),
                    "-i",
                    video_source[1],
                    "-t",
                    (caption.end - caption.start).to_ffmpeg_timecode(),
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
            "-c",
            "copy",
            video_output,
            "-y"
        ]
    ).wait()


def main_compile_word(vtt_source, video_source, word, video_output, parts_directory):
    if word is None:
        raise ValueError("Target word is None")
    captions = retrieve_captions(vtt_source)
    selection = filter_captions_for_word(captions, word)
    if video_source is None:
        video_source = get_video_stream(vtt_source)
    files = extract_captions(video_source, selection, parts_directory)
    merge_video_files(files, video_output)


def download_video(url, output):
    subprocess.Popen(
        [
            YOUTUBE_DL_EXECUTABLE,
            "--write-auto-sub",
            "--sub-lang",
            "fr",
            "--sub-format",
            "vtt",
            "--output",
            output,
            url,
        ]
    ).wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", type=str, choices={"parse", "word", "download"})
    parser.add_argument("input", type=str, nargs="+")
    parser.add_argument("output", type=str)
    parser.add_argument("-d", "--parts-directory", type=str, default=tempfile.gettempdir())
    parser.add_argument("-w", "--word", type=str)    
    args = parser.parse_args()
    for i in range(0, len(args.input), 2):
        if i + 1 < len(args.input) and args.input[i + 1] == "_":
            args.input[i + 1] = args.input[i]
    if args.action == "parse":
        main_parse(args.input[0], args.output)
    elif args.action == "word":
        main_compile_word(args.input[0], args.input[1], args.word, args.output, args.parts_directory)
    elif args.action == "download":
        download_video(args.input[0], args.output)


if __name__ == "__main__":
    main()