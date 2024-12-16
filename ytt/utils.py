import re
import unicodedata


YOUTUBE_VIDEO_ID_PATTERN = re.compile(r".*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]{11}).*", re.MULTILINE)


def remove_tags(string):
    """Remove any HTML tag from a string.
    """
    return re.sub(r"\[\w+?\]", "", re.sub(r"<[^>]+?>", "", string))


def unicode_normalize(string):
    return "".join((c for c in unicodedata.normalize("NFD", string) if unicodedata.category(c) != "Mn"))


def strip_spaces(string):
    return re.sub(r" +", " ", re.sub("\n", " ", string)).strip()


def normalize(string):
    return strip_spaces(unicode_normalize(string.lower()))


def tokenize(string):
    """Split a string in a list of tokens, after basic normalization
    """
    return list(filter(lambda x: len(x) > 0, re.sub(r" +", " ", normalize(string.replace("'", " "))).strip().split(" ")))


def extract_video_id(url):
    """Extract a YouTube video ID from a URL.
    """
    match = YOUTUBE_VIDEO_ID_PATTERN.match(url)
    if match is not None:
        return match.group(1)
    raise ValueError(f"Could not extract video id from { url }")

