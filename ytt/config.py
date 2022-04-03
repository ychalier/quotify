import os
import tempfile


class Config:

    def __init__(self,
                 youtube_dl="youtube-dl",
                 ffmpeg="ffmpeg",
                 tempdir=tempfile.gettempdir(),
                 lang="fr",
                 padding_prev=0,
                 padding_next=0,
                 lookahead=5,
                 find_first=False):
        self.youtube_dl = youtube_dl
        self.ffmpeg = ffmpeg
        self.tempdir = tempdir
        self.lang = lang
        self.padding_prev = padding_prev
        self.padding_next = padding_next
        self.lookahead = lookahead
        self.find_first = find_first
    
    def add_arguments(self, parser):
        parser.add_argument("-yd", "--youtube-dl", type=str, default=self.youtube_dl, help=f"path to the youtube-dl executable (default: '{ self.youtube_dl }')")
        parser.add_argument("-fm", "--ffmpeg", type=str, default=self.ffmpeg, help=f"path to the FFmpeg executable (default: '{ self.ffmpeg }')")
        parser.add_argument("-td", "--tempdir", type=str, default=self.tempdir, help=f"path to the temporary directory to use (default: '{ self.tempdir }')")
        parser.add_argument("-lg", "--lang", type=str, default=self.lang, help=f"YouTube automatic captions language to work with (default: '{ self.lang }')")
        parser.add_argument("-pp", "--padding-prev", type=int, default=self.padding_prev, help=f"number of captions to include before the first match when using --find or --filter (default: { self.padding_prev })")
        parser.add_argument("-pn", "--padding-next", type=int, default=self.padding_next, help=f"number of captions to include after the last match when using --find or --filter (default: { self.padding_next })")
        parser.add_argument("-la", "--lookahead", type=int, default=self.lookahead, help=f"maximum number of tokens to search for at the same time when using --find (default: { self.lookahead })")
        parser.add_argument("-ff", "--find-first", action="store_true", help=f"if set, --find will stop when the first match is found, otherwise it chooses a random one from all matches")

    def update(self, args):
        self.youtube_dl = args.youtube_dl
        self.ffmpeg = args.ffmpeg
        self.tempdir = args.tempdir
        self.lang = args.lang
        self.padding_prev = args.padding_prev
        self.padding_next = args.padding_next
        self.lookahead = args.lookahead
        self.find_first = args.find_first

    def setup(self):
        os.makedirs(self.tempdir, exist_ok=True)
