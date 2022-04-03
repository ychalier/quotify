import os
import csv
import json
import random
import tqdm
from .transcript import Transcript
from .utils import tokenize


class TranscriptPool:

    def __init__(self, config, transcripts):
        self.config = config
        self.transcripts = transcripts

    def __str__(self):
        return "\n".join(map(str, self.transcripts))
    
    @classmethod
    def from_sources(cls, config, sources):
        return cls(
            config,
            [
                Transcript.from_source(config, source)
                for source in sources
            ]
        )
    
    def find(self, text):
        tokens = tokenize(text)
        i = 0
        selection = []
        while i < len(tokens):
            found_i = False
            for j in range(min(len(tokens), i + self.config.lookahead), i, -1):
                candidates = []
                for transcript in self.transcripts:
                    for match in transcript.find_sequence(tokens[i:j]):
                        candidates.append(match)
                        if self.config.find_first:
                            break
                    if self.config.find_first and len(candidates) > 0:
                        break
                if len(candidates) > 0:
                    i = j
                    found_i = True
                    selection.append(random.choice(candidates))
                    break
            if not found_i:
                print(f"Could not find '{ tokens[i] }'")
                i += 1
        return TranscriptPool(self.config, selection)
    
    def filter(self, pattern):
        filtered = []
        for transcript in self.transcripts:
            filtered.append(transcript.filter(pattern))
        return TranscriptPool(self.config, filtered)
    
    def _export_json(self, data, path):
        with open(path, "w", encoding="utf8") as file:
            json.dump({ "captions": data }, file, indent=4)

    def _export_csv(self, data, path):
        with open(path, "w", encoding="utf8", newline="") as file:
            fieldnames = []
            if len(data) > 0:
                fieldnames = data[0].keys()
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    def export(self, path):
        if len(self.transcripts) == 1:
            self.transcripts[0].export(path)
        else:
            data = []
            for transcript in self.transcripts:
                for caption in transcript:
                    entry = {}
                    if transcript.source is not None:
                        entry.update(**transcript.source.to_dict())
                    entry.update(**caption.to_dict())
                    data.append(entry)
            if path.endswith(".json"):
                self._export_json(data, path)
            elif path.endswith(".csv"):
                self._export_csv(data, path)
            else:
                raise NotImplementedError(
                    f"Output format not supported (only .json or .csv)")

    def extract(self, path):
        os.makedirs(path, exist_ok=True)
        queue = []
        index = 0
        for transcript in self.transcripts:
            for group_start, group_end in transcript.iter_groups():
                tokens = []
                for i in range(group_start, group_end + 1):
                    tokens += [token for token in transcript[i].tokens() if token != ""]
                queue.append((
                    transcript.source,
                    transcript[group_start].start,
                    transcript[group_end].end,
                    os.path.join(path, "%04d_%s.mp4" % (index, "_".join(tokens)))
                ))
                index += 1
        for source, start, end, opath in tqdm.tqdm(queue):
            if source is None:
                raise ValueError("Source must be set when extracting, not None")
            source.extract(start, end, opath)