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
)
from ass_lint.common import benchmark, get_video_height, get_video_width


def make_context(path: Path) -> CheckContext:
    ass_file = read_ass(path)

    video_resolution = (
        get_video_width(ass_file),
        get_video_height(ass_file),
    )

    renderer = AssRenderer()
    renderer.set_source(ass_file=ass_file, video_resolution=video_resolution)

    return CheckContext(
        subs_path=path,
        ass_file=ass_file,
        video_resolution=video_resolution,
        renderer=renderer,
    )


def get_event_checks(full: bool) -> Iterable[BaseCheck]:
    if full:
        yield CheckGrammar

    yield CheckAssTags
    yield CheckDurations
    yield CheckPunctuation
    yield CheckQuotes
    yield CheckLineContinuation
    yield CheckDoubleWords
    yield CheckLongLines


def get_global_checks(full: bool) -> Iterable[BaseCheck]:
    yield CheckSpelling
    yield CheckActorStats
    yield CheckFonts
    yield CheckPunctuationStats


async def list_violations(
    ctx: CheckContext, checks: list[BaseCheck]
) -> Iterable[BaseResult]:

    for check_cls in checks:
        with benchmark(f"{check_cls}"):
            check = check_cls(ctx)
            async for violation in check.get_violations():
                yield violation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument(
        "-f",
        "--full",
        action="store_true",
        help="run slower checks",
    )
    return parser.parse_args()


async def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO)

    ctx = make_context(args.path)
    event_checks = list(get_event_checks(full=args.full))
    global_checks = list(get_global_checks(full=args.full))

    async for result in list_violations(ctx, checks=event_checks):
        logging.log(result.log_level, repr(result))

    for check_cls in global_checks:
        with benchmark(f"{check_cls}"):
            check = check_cls(ctx)
            await check.run()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
