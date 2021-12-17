from collections.abc import Iterable
from typing import Any

from ass_parser import AssEvent
from ass_tag_parser import (
    AssTagAlignment,
    AssTagComment,
    AssTagKaraoke,
    AssTagListEnding,
    AssTagListOpening,
    ParseError,
    parse_ass,
)

from ass_lint.common import BaseEventCheck, BaseResult, Violation


def get(source: list[Any], idx: int) -> Any:
    if idx < 0 or idx >= len(source):
        return None
    return source[idx]


class CheckAssTags(BaseEventCheck):
    async def run_for_event(self, event: AssEvent) -> Iterable[BaseResult]:
        try:
            ass_line = parse_ass(event.text)
        except ParseError as ex:
            yield Violation(f"invalid syntax ({ex})", [event])
            return

        for i, item in enumerate(ass_line):
            if (
                isinstance(item, AssTagListOpening)
                and isinstance(get(ass_line, i - 1), AssTagListEnding)
                and not isinstance(get(ass_line, i - 2), AssTagKaraoke)
            ):
                yield Violation("disjointed tags", [event])

            if isinstance(item, AssTagListEnding) and isinstance(
                get(ass_line, i - 1), AssTagListOpening
            ):
                yield Violation("pointless tag", [event])

        for item in ass_line:
            if isinstance(item, AssTagAlignment) and item.legacy:
                yield Violation("using legacy alignment tag", [event])

            elif isinstance(item, AssTagComment):
                yield Violation("use notes to make comments", [event])
