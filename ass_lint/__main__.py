import argparse
import asyncio
import logging
from collections.abc import Iterable
from pathlib import Path

from ass_parser import read_ass
from ass_renderer import AssRenderer

from ass_lint.checks import (
    BaseCheck,
    BaseResult,
    CheckActorStats,
    CheckAssTags,
    CheckContext,
    CheckDoubleWords,
    CheckDurations,
    CheckFonts,
    CheckGrammar,
    CheckLineContinuation,
    CheckLongLines,
    CheckPunctuation,
    CheckPunctuationStats,
    CheckQuotes,
    CheckSpelling,
    CheckStyleStats,
    CheckStyleValidity,
    CheckTimes,
    CheckUnnecessaryBreaks,
    CheckVideoResolution,
)
from ass_lint.common import benchmark, get_video_height, get_video_width
from ass_lint.video import VideoError, VideoSource


def make_context(path: Path) -> CheckContext:
    ass_file = read_ass(path)

    video_resolution = (
        get_video_width(ass_file),
        get_video_height(ass_file),
    )

    renderer = AssRenderer()
    renderer.set_source(ass_file=ass_file, video_resolution=video_resolution)

    video = None
    if video_path := ass_file.script_info.get("Video File"):
        video_path = path.parent / video_path
        try:
            video = VideoSource(video_path)
        except VideoError as ex:
            logging.warning(ex)

    return CheckContext(
        subs_path=path,
        ass_file=ass_file,
        video_resolution=video_resolution,
        renderer=renderer,
        video=video,
    )


def get_checks(full: bool) -> Iterable[BaseCheck]:
    if full:
        yield CheckGrammar

    yield CheckStyleValidity
    yield CheckAssTags
    yield CheckDurations
    yield CheckPunctuation
    yield CheckQuotes
    yield CheckLineContinuation
    yield CheckDoubleWords
    yield CheckUnnecessaryBreaks
    yield CheckLongLines

    if full:
        yield CheckTimes

    yield CheckVideoResolution
    yield CheckSpelling
    yield CheckActorStats
    yield CheckStyleStats
    yield CheckFonts
    yield CheckPunctuationStats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="run slower checks",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="show debug information",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    ctx = make_context(args.path)
    checks = list(get_checks(full=args.full))

    for check_cls in checks:
        with benchmark(f"{check_cls}"):
            try:
                check = check_cls(ctx)
            except Exception as ex:
                logging.warning(ex)
            else:
                async for result in check.run():
                    logging.log(result.log_level, repr(result))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
