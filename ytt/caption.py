import re
import csv
import enum
import json
from .utils import tokenize


def remove_tags(string):
    """Remove any HTML tag from a string.
    """
    return re.sub(r"\[\w+?\]", "", re.sub(r"<[^>]+?>", "", string)).strip()


@enum.unique
class CaptionSource(enum.Enum):

    INNER = 0
    TRAILING = 1


class Caption:

    def __init__(self, text, start, end, source=None):
        self.text = remove_tags(text)
        self.start = start
        self.end = end
        self.source = source
    
    def __repr__(self):
        return "%s-%s %s" % (
            repr(self.start),
            repr(self.end),
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
    
    def tokens(self):
        return tokenize(self.text)


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