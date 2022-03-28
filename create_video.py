import subprocess
import argparse
import re
import os
import glob
import webvtt as webvtt


def merge_captions(captions):
    """
    Merge the text content of a list of webvtt.Caption into a single string,
    where repetitions are pruned out.
    """
    text = ""
    for caption in captions:
        caption_text = caption.text.strip()
        longest_prefix_length = 0
        for i in range(1, len(caption_text) + 1):
            if text.endswith(caption_text[:i]):
                longest_prefix_length = i
        if longest_prefix_length == 0:
            text += " "
        text += caption_text[longest_prefix_length:]
    return re.sub(" +", " ", text)


def tokenize(sentence):
    return list(filter(lambda x: len(x) > 0, re.sub(" +", " ", re.sub("[^a-z0-9]", " ", sentence.lower())).strip().split(" ")))
    

def sanitize(sentence):
    return " ".join(tokenize(sentence))


def load_script(path_script):
    with open(path_script, "r", encoding="utf8") as file:
        text = file.read()
    return list(map(tokenize, text.split("\n")))


def load_captions(path_caption):
    return webvtt.read(path_caption)


def find_in_captions(tokens, captions):
    i = 0
    match_start = None
    for caption in captions:
        for caption_token in tokenize(caption.text):
            if tokens[i] == caption_token:
                if i == 0:
                    match_start = caption.start
                i += 1
                if i == len(tokens):
                    return match_start, caption.end
            else:
                match_start = None
                i = 0
    return None, None


def build_video(path_script, captions_folders="captions"):
    script = load_script(path_script)
    for path in glob.glob(os.path.join(captions_folders, "*.fr.vtt")):
        captions = load_captions(path)
    for line in script:
        i = 0
        while i < len(line):
            j = len(line)
            while j > i:
                match_start, match_end = find_in_captions(line[i:j], captions)
                if match_start is not None and match_end is not None:
                    print(i, j, line[i:j], match_start, match_end)
                    i = j - 1
                    break
                j -= 1
            i += 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path_script", type=str)
    args = parser.parse_args()
    build_video(args.path_script)


if __name__ == "__main__":
    main()
