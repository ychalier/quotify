# ytt - Youtube Transcript Toolkit

YouTube [automatic captioning](https://support.google.com/youtube/answer/6373554) is a very neat feature as it a provides summarized and static ressources for exploiting the content of videos by generating precisely timed transcripts. For instance, with audio book or audio theatre videos, it can help [extracting the script of fictional works](https://github.com/ychalier/les-mysteres-perces) without having to run (and pay for) a state-of-the-art [STT](https://en.wikipedia.org/wiki/Speech_recognition) software.

Captions for a given YouTube video can be downloaded with [youtube-dl](https://youtube-dl.org/) as [WebVTT](https://en.wikipedia.org/wiki/WebVTT) files:

```console
youtube-dl --write-auto-sub --sub-lang fr --skip-download [URL]
```

Yet, there is a gap between the raw VTT file and the actual transcript: sentences are often duplicated, words can be duplicated too, timecodes are fuzzy around words, etc. 
So the first thing this module does is parsing those VTT files and generating clean transcripts. Then, it provides tools for exploiting those transcripts in fun ways: creating a montage of a given word or re-creating a given script from video extracts:

| **Word montage**                                                        | **Script re-creation**                                                  |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| [![](https://i.imgur.com/DpIapHB.png)](https://i.imgur.com/DpIapHB.mp4) | [![](https://i.imgur.com/PwTXebX.png)](https://i.imgur.com/PwTXebX.mp4) |
| [Source : Monsieur Phi](https://www.youtube.com/watch?v=GuTgfnkILGs)                   | [Source : Thinkerview](https://www.youtube.com/watch?v=YFhV_SkhZyc)                   |

## Getting Started

### Prerequisites

You must have a working installation of [youtube-dl](https://youtube-dl.org/) (any fork should work) and [FFmpeg](https://ffmpeg.org/). Better if they are in `PATH`.

### Installation

Simply clone this repository:

```console
git clone https://github.com/ychalier/ytt.git
```

### Usage

```console
python ytt.py [-h] -i INPUT [-ft FILTER] [-fd FIND] [-o OUTPUT] [-x EXTRACT]
              [-yd YOUTUBE_DL] [-fm FFMPEG] [-td TEMPDIR] [-lg LANG]
              [-pp PADDING_PREV] [-pn PADDING_NEXT] [-la LOOKAHEAD] [-ff]
```

Use `-h` or `--help` to get details. For example, here's how to get the first word montage:

```console
python ytt.py -i https://www.youtube.com/watch?v=GuTgfnkILGs -ft boule -x . -pp 1 -pn 1
```