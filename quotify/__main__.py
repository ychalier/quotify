import subprocess
import argparse
import tempfile
import os

from quotify.config import YOUTUBE_DL_EXECUTABLE
from quotify.caption import export_captions
from quotify.webvtt import retrieve_captions
from quotify.search import filter_captions_for_word, find_captions_for_sentence
from quotify.video import get_video_stream, extract_captions, merge_video_files


def main_parse(vtt_source, captions_output):
    captions = retrieve_captions(vtt_source)
    export_captions(captions, captions_output)


def main_compile_word(vtt_source, video_source, word, video_output, parts_directory, padding_prev, padding_next, no_merge):
    if word is None:
        raise ValueError("Target word is None")
    captions = retrieve_captions(vtt_source)
    selection = filter_captions_for_word(captions, video_source, word, padding_prev, padding_next)
    if video_source is None:
        video_source = get_video_stream(vtt_source)
    files = extract_captions(selection, parts_directory)
    if not no_merge:
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


def main_build_sentence(raw_inputs, sentence, video_output, part_directory, padding_prev, padding_next, no_merge):
    if sentence is None:
        raise ValueError("Target sentence is None")
    if os.path.isfile(sentence):
        with open(sentence, "r", encoding="utf8") as file:
            sentence = file.read()
    inputs = []
    for vtt_source, video_source in zip(raw_inputs[::2], raw_inputs[1::2]):
        captions = retrieve_captions(vtt_source)
        if not os.path.isfile(video_source):
            video_source = get_video_stream(video_source)
        inputs.append((captions, video_source))
    selection = find_captions_for_sentence(inputs, sentence, padding_prev, padding_next)
    files = extract_captions(selection, part_directory)
    if not no_merge:
        merge_video_files(files, video_output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", type=str, choices={"parse", "word", "download", "sentence"})
    parser.add_argument("input", type=str, nargs="+")
    parser.add_argument("output", type=str)
    parser.add_argument("-d", "--parts-directory", type=str, default=tempfile.gettempdir())
    parser.add_argument("-w", "--word", type=str)
    parser.add_argument("-s", "--sentence", type=str)
    parser.add_argument("-pp", "--padding-prev", type=int, default=0)
    parser.add_argument("-pn", "--padding-next", type=int, default=1)
    parser.add_argument("-n", "--no-merge", action="store_true")
    args = parser.parse_args()
    for i in range(0, len(args.input), 2):
        if i + 1 < len(args.input) and args.input[i + 1] == "_":
            args.input[i + 1] = args.input[i]
    if args.action == "parse":
        main_parse(args.input[0], args.output)
    elif args.action == "word":
        main_compile_word(args.input[0], args.input[1], args.word, args.output, args.parts_directory, args.padding_prev, args.padding_next, args.no_merge)
    elif args.action == "download":
        download_video(args.input[0], args.output)
    elif args.action == "sentence":
        main_build_sentence(args.input, args.sentence, args.output, args.parts_directory, args.padding_prev, args.padding_next, args.no_merge)


main()