import re
import csv
import json
from .timecode import Timecode
from .caption import Caption, CaptionType


def parse_webvtt(text):
    """Read WebVTT text and returns a raw list of captions
    """
    HEADER_PATTERN = re.compile(r"^(WEBVTT|\w+: \w+)$")
    LINE_TIMECODE_PATTERN = re.compile(r"^([\d:\.]{12}) --> ([\d:\.]{12})")
    header_line = True
    captions = []
    current_caption = None
    for line in text.split("\n"):
        line += "\n"
        if line.strip() == "":
            continue
        if header_line:
            if HEADER_PATTERN.match(line):
                continue
            header_line = False
        if not header_line:
            match = LINE_TIMECODE_PATTERN.match(line)
            if match is not None:
                if current_caption is not None:
                    captions.append(current_caption.copy())
                current_caption = Caption(
                    "",
                    Timecode.from_string(match.group(1)),
                    Timecode.from_string(match.group(2)),
                    CaptionType.RAW)
            else:
                current_caption.text += line
    return captions


def split_inner_timecodes(captions):
    TAG_TIMECODE_PATTERN = re.compile(r"<([\d:\.]{12})>")
    captions_split = []
    for caption in captions:
        is_timecode = False
        current_caption = caption.copy()
        current_caption.text = ""
        for bit in TAG_TIMECODE_PATTERN.split(caption.text):
            if is_timecode:
                current_caption.type = CaptionType.INNER
                current_caption.end = Timecode.from_string(bit)
                captions_split.append(current_caption.copy())
                current_caption = caption.copy()
                current_caption.text = ""
                current_caption.start = Timecode.from_string(bit)
            else:
                current_caption.text += bit
            is_timecode = not is_timecode
        current_caption.type = CaptionType.TRAILING
        captions_split.append(current_caption.copy())
    return captions_split


def remove_duplicates(captions, buffer_size=50):
    buffer = ""
    for caption in captions:
        caption.clean()
        for i in range(len(buffer) - 1):
            if caption.text.startswith(buffer[i:])\
                and (caption.text == buffer[i:]
                     or caption.text[len(buffer) - i] == " ")\
                and (i == 0
                     or buffer[i - 1] == " "):
                caption.text = caption.text[len(buffer) - i:].strip()
        if caption.text != "":
            buffer += " " + caption.text
        if len(buffer) > buffer_size:
            buffer = buffer[len(buffer) - buffer_size - 1:]
    return captions


class Transcript:
    """A list of captions.
    """

    def __init__(self, config, captions, source=None):
        self.config = config
        self.captions = captions
        self.source = source
        self.size = len(self.captions)

    def __len__(self):
        return self.size

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.captions[key]
        elif isinstance(key, slice):
            return Transcript(self.config, self.captions[key], self.source)

    def __str__(self):
        prefix = ""
        if self.source is not None:
            prefix = str(self.source) + "\n"
        return (prefix + "\n".join(map(str, self.captions))).strip()

    def __repr__(self):
        return repr(self.captions)
    
    def __iter__(self):
        return iter(self.captions)

    @classmethod
    def from_source(cls, config, source):
        return cls.from_webvtt(config, source.vtt(), source)

    @classmethod
    def from_webvtt(cls, config, text, source=None):
        captions_raw = parse_webvtt(text)
        captions_split = split_inner_timecodes(captions_raw)
        captions_distinct = remove_duplicates(captions_split)
        for i, caption in enumerate(captions_distinct):
            caption.index = i
        return cls(config, captions_distinct, source)

    def _export_json(self, output_path):
        with open(output_path, "w", encoding="utf8") as file:
            json.dump({
                "captions": [
                    caption.to_dict()
                    for caption in self.captions
                ]
            }, file, indent=4)

    def _export_csv(self, output_path):
        with open(output_path, "w", encoding="utf8", newline="") as file:
            fieldnames = []
            if self.size > 0:
                fieldnames = self.captions[0].to_dict().keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows([
                caption.to_dict()
                for caption in self.captions])

    def export(self, output_path):
        if output_path.endswith(".json"):
            self._export_json(output_path)
        elif output_path.endswith(".csv"):
            self._export_csv(output_path)
        else:
            raise NotImplementedError(
                f"Output format not supported (only .json or .csv)")

    def _slice(self, start, stop=None):
        if stop is None:
            stop = start
        return self.captions[start - self.config.padding_prev:
                             stop + self.config.padding_next + 1]

    def filter(self, pattern):
        """Filter captions matching a given pattern.
        """
        selection = []
        for i, caption in enumerate(self.captions):
            if re.match(pattern, caption.text):
                selection += self._slice(i)
        return Transcript(self.config, selection, self.source)

    def find_sequence(self, tokens):
        """Iterate through caption sub-sequences that include a sequence of
        tokens
        """
        i = 0
        index_first = None
        index_last = None
        for k, caption in enumerate(self.captions):
            if caption.text == "":
                continue
            match_whole = True
            for j, token in enumerate(caption.tokens()):
                if token == "":
                    continue
                if i < len(tokens) and token == tokens[i]:
                    if i == 0 or j == 0:
                        match_whole = True
                    i += 1
                elif i < len(tokens):
                    match_whole = False
                    break
            if match_whole:
                if index_first is None:
                    index_first = k
                index_last = k
                if i == len(tokens):
                    yield Transcript(
                        self.config,
                        self._slice(index_first, index_last),
                        self.source)
                    index_first = None
                    i = 0
            else:
                index_first = None
                i = 0
    
    def iter_groups(self):
        """Iterate over groups of sequential captions
        """
        if len(self.captions) > 0:
            group_start = 0
            group_end = 0
            previous_index = None
            for i, caption in enumerate(self.captions):
                if previous_index is not None and (caption.index != previous_index + 1):
                    yield group_start, group_end
                    group_start = i
                else:
                    group_end = i
                previous_index = caption.index
            yield group_start, group_end
