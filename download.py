import os
import argparse
import subprocess


def download_file(url, output, lang="fr", youtube_dl="youtube-dl"):
    os.makedirs(output, exist_ok=True)
    subprocess.Popen(
        [
            youtube_dl,
            "--write-auto-sub",
            "--sub-lang",
            lang,
            "--sub-format",
            "vtt",
            "--restrict-filenames",
            "--output",
            os.path.join(output, "%(title)s-%(id)s.%(ext)s"),
            url,
        ]
    ).wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", type=str, help="a YouTube video URL")
    parser.add_argument("output", type=str, help="path to the ouptut folder")
    parser.add_argument("-lg", "--lang", type=str, default="fr", help="YouTube automatic captions language to work with (default: 'fr')")
    parser.add_argument("-yd", "--youtube-dl", type=str, default="youtube-dl", help=f"path to the youtube-dl executable (default: 'youtube-dl')")
    args = parser.parse_args()
    download_file(args.url, args.output, args.lang, args.youtube_dl)


if __name__ == "__main__":
    main()