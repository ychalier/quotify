import os
import subprocess
from .utils import extract_video_id


class Source:

    def __init__(self,
                 config,
                 vtt_path=None,
                 video_path=None,
                 youtube_url=None):
        self.config = config
        self.vtt_path = vtt_path
        self.video_path = video_path
        self.youtube_url = youtube_url
        self.video_stream = None
        self.audio_stream = None
    
    def __str__(self):
        string = ""
        if self.vtt_path is not None:
            string += self.vtt_path + " "
        if self.video_path is not None:
            string += self.video_path + " "
        if self.youtube_url is not None:
            string += self.youtube_url
        return f"Source: { string.strip() }"
    
    @classmethod
    def from_arg(cls, config, arg):
        source = cls(config)
        for part in arg.split(","):
            if os.path.isfile(part):
                if part.endswith(".vtt"):
                    source.vtt_path = part.strip()
                else:
                    source.video_path = part.strip()
            elif part.startswith("http"):
                source.youtube_url = part.strip()
            else:
                raise RuntimeError(f"Source is neither an existing file or a URL: '{ part }'")
        if source.vtt_path is None and source.youtube_url is None:
            raise RuntimeError(f"Source must provide either a path to a VTT or a URL to a YouTube video")
        return source 

    def _download_vtt(self):
        if self.youtube_url is None:
            raise ValueError(f"No YouTube URL given")
        video_id = extract_video_id(self.youtube_url)
        self.vtt_path = os.path.join(
            self.config.tempdir,
            f"{ video_id }.{ self.config.lang }.vtt"
        )
        subprocess.Popen(
            [
                self.config.youtube_dl,
                "--write-auto-sub",
                "--sub-lang",
                self.config.lang,
                "--sub-format",
                "vtt",
                "--skip-download",
                "--output",
                os.path.join(self.config.tempdir, f"{ video_id }"),
                self.youtube_url
            ]
        ).wait()
        if not os.path.isfile(self.vtt_path):
            raise ValueError(f"Could not download subtitles from { self.youtube_url }")

    def to_dict(self):
        return {
            "vtt_path": os.path.realpath(self.vtt_path) if self.vtt_path is not None else None,
            "video_path": os.path.realpath(self.video_path) if self.video_path is not None else None,
            "youtube_url": self.youtube_url
        }

    def vtt(self):
        if self.vtt_path is None or not os.path.isfile(self.vtt_path):
            self._download_vtt()
        with open(self.vtt_path, "r", encoding="utf8") as file:
            text = file.read()
        return text
    
    def name(self):
        if self.youtube_url is not None:
            return extract_video_id(self.youtube_url)
        if self.vtt_path is not None:
            return os.path.splitext(os.path.basename(self.vtt_path))[0]
        if self.video_path is not None:
            return os.path.splitext(os.path.basename(self.video_path))[0]
        return None
    
    def fetch_stream(self):
        if self.youtube_url is None:
            raise ValueError("Missing YouTube URL")
        process = subprocess.Popen(
            [
                self.config.youtube_dl,
                "-g",
                self.youtube_url
            ],
            stdout=subprocess.PIPE
        )
        process.wait()
        split = process.stdout.read().decode("utf8").strip().split("\n")
        if len(split) != 2:
            raise RuntimeError(f"Could not find a stream for { self.youtube_url }")
        self.video_stream = split[0]
        self.audio_stream = split[1]

    def create_ffmpeg_input(self, ss=None, t=None):
        cmd = []
        if self.video_path is not None and os.path.isfile(self.video_path):
            if ss is not None:
                cmd += ["-ss", ss.to_ffmpeg_timecode()]
            cmd += ["-i", self.video_path]
            if t is not None:
                cmd += ["-t", t.to_ffmpeg_timecode()]
        else:
            if self.video_stream is None or self.audio_stream is None:
                self.fetch_stream()
            if ss is not None:
                cmd += ["-ss", ss.to_ffmpeg_timecode()]
            cmd += ["-i", self.video_stream]
            if t is not None:
                cmd += ["-t", t.to_ffmpeg_timecode()]
            if ss is not None:
                cmd += ["-ss", ss.to_ffmpeg_timecode()]
            cmd += ["-i", self.audio_stream]
            if t is not None:
                cmd += ["-t", t.to_ffmpeg_timecode()]
            cmd += [
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
            ]
        return cmd
    
    def extract(self, start, end, path):
        cmd = [
                self.config.ffmpeg,
                "-loglevel",
                "quiet",
                "-hide_banner",
            ]\
            + self.create_ffmpeg_input(ss=start, t=end - start)\
            + [
                path,
                "-y"
            ]
        subprocess.Popen(cmd).wait()