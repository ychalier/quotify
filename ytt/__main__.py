import argparse
from ytt.config import Config
from ytt.source import Source
from ytt.transcript_pool import TranscriptPool


def main():
    config = Config()
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, required=True, action="append", help="path to a VTT file, path to a video file or URL to a YouTube video, separated by commas; several sources can be passed; each source must provide either a path to a VTT file or a YouTube video URL")
    parser.add_argument("-ft", "--filter", type=str, default=None, help="regular expression pattern applied to each caption (default: None)")
    parser.add_argument("-fd", "--find", type=str, default=None, help="sentence to find as a subsequence of captions (default: None)")
    parser.add_argument("-o", "--output", type=str, default=None, help="file path to export transcripts to, as JSON or CSV (default: None)")
    parser.add_argument("-x", "--extract", type=str, default=None, help="directory path to export video extracts (default: None)")
    config.add_arguments(parser)
    args = parser.parse_args()
    config.update(args)
    config.setup()
    transcript_pool = TranscriptPool.from_sources(
        config,
        [
            Source.from_arg(config, source_arg)
            for source_arg in args.input
        ]
    )
    if args.filter is not None:
        transcript_pool = transcript_pool.filter(args.filter)
    if args.find is not None:
        transcript_pool = transcript_pool.find(args.find)
    if args.output is not None:
        transcript_pool.export(args.output)
    if args.extract is not None:
        transcript_pool.extract(args.extract)
    if args.output is None and args.extract is None:
        print(transcript_pool)


main()