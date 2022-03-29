import re


YOUTUBE_VIDEO_ID_PATTERN = re.compile(r".*(?:youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=)([^#\&\?]{11}).*", re.MULTILINE)


def tokenize(sentence):
    """Split a string in a list of tokens, after basic normalization
    """
    return list(filter(lambda x: len(x) > 0, re.sub(r" +", " ", re.sub(r"[^a-z0-9]", " ", sentence.lower())).strip().split(" ")))


def extract_video_id(url):
    """Extract a YouTube video ID from a URL.
    """
    match = YOUTUBE_VIDEO_ID_PATTERN.match(url)
    if match is not None:
        return match.group(1)
    raise ValueError(f"Could not extract video id from { url }")

