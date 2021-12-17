import argparse
import asyncio
import logging
from collections.abc import Iterable
from pathlib import Path

import colorama
from ass_parser import read_ass
from ass_renderer import AssRenderer

from ass_lint.checks import get_checks
from ass_lint.common import BaseCheck, BaseResult, CheckContext, LogLevel
from ass_lint.util import benchmark, get_video_height, get_video_width
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


def print_result(result: BaseResult) -> None:
    color = {
        LogLevel.warning: colorama.Fore.RED,
        LogLevel.info: colorama.Fore.RESET,
        LogLevel.debug: colorama.Fore.BLUE,
    }[result.log_level]
    print(color + repr(result) + colorama.Fore.RESET)


async def main() -> None:
    colorama.init()

    args = parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

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
                    print_result(result)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
