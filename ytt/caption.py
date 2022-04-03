import enum
from .utils import tokenize, remove_tags, normalize


@enum.unique
class CaptionType(enum.Enum):

    RAW = 0
    INNER = 1
    TRAILING = 2


class Caption:

    def __init__(self, text, start, end, type=None, index=None):
        self.index = index
        self.text = text
        self.start = start
        self.end = end
        self.type = type
    
    def clean(self):
        self.text = normalize(remove_tags(self.text))
    
    def __repr__(self):
        prefix = ""
        if self.index is not None:
            prefix = f"{ self.index } "
        return "%s%s-%s %s" % (
            prefix,
            repr(self.start),
            repr(self.end),
            self.text
        )
    
    def __str__(self):
        prefix = ""
        if self.index is not None:
            prefix = f"{ self.index }\t"
        return "%s%s --> %s\t%s" % (
            prefix,
            str(self.start),
            str(self.end),
            self.text
        )
    
    def copy(self):
        return Caption(
            self.text,
            self.start.copy(),
            self.end.copy(),
            self.type,
            self.index)

    def to_dict(self):
        return {
            "index": self.index,
            "text": self.text,
            "start": self.start.to_ffmpeg_timecode(),
            "end": self.end.to_ffmpeg_timecode(),
            "type": self.type.name if self.type is not None else None
        }
    
    def tokens(self):
        return tokenize(self.text)
