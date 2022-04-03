import re


class Timecode:

    PATTERN = re.compile(r"(\d\d):(\d\d):(\d\d)\.(\d\d\d)")

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
        return Timecode(self.total_seconds + other.total_seconds)

    def __sub__(self, other):
        return Timecode(self.total_seconds - other.total_seconds)
    
    def __gt__(self, other):
        if isinstance(other, Timecode):
            return self.total_seconds > other.total_seconds
        elif isinstance(other, float) or isinstance(other, int):
            return self.total_seconds > other
        else:
            raise TypeError("'>' not supported between instances of 'Timecode' and '%s'" % type(other))

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
        return Timecode(self.total_seconds)
    
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
        match = cls.PATTERN.match(string)
        return cls(
            3600 * int(match.group(1))\
            + 60 * int(match.group(2))\
            + int(match.group(3))\
            + .001 * int(match.group(4))
        )
