import os
import re
import subprocess
from .config import YOUTUBE_DL_EXECUTABLE, CAPTIONS_FOLDER
from .timestamp import Timestamp
from .caption import Caption, CaptionSource
from .utils import extract_video_id


LINE_TIMESTAMP_PATTERN = re.compile(r"^(\d\d:\d\d:\d\d\.\d\d\d) --> (\d\d:\d\d:\d\d\.\d\d\d)")
SPLIT_LINE_TIMESTAMP_PATTERN = re.compile(r"<(\d\d:\d\d:\d\d\.\d\d\d)>")


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