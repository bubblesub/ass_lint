import re
from collections.abc import Iterable

from ass_parser import AssEvent
from ass_tag_parser import ass_to_plaintext

from ..common import is_event_karaoke
from .base import BaseEventCheck, BaseResult, Violation

MIN_DURATION = 250  # milliseconds
MIN_DURATION_LONG = 500  # milliseconds
MIN_GAP = 250  # milliseconds


def character_count(text: str) -> int:
    """Count how many characters an ASS line contains.

    Doesn't take into account effects such as text invisibility etc.

    :param text: input ASS line
    :return: number of characters
    """
    return len(re.sub(r"\W+", "", ass_to_plaintext(text), flags=re.I | re.U))


class CheckDurations(BaseEventCheck):
    async def run_for_event(self, event: AssEvent) -> Iterable[BaseResult]:
        text = ass_to_plaintext(event.text)
        if not text or event.is_comment:
            return

        if event.duration < MIN_DURATION_LONG and character_count(text) >= 8:
            yield Violation(
                event, f"duration shorter than {MIN_DURATION_LONG} ms"
            )

        elif event.duration < MIN_DURATION:
            yield Violation(event, f"duration shorter than {MIN_DURATION} ms")

        next_event = self.get_next_non_empty_event(event)

        if next_event and not (
            is_event_karaoke(next_event) and is_event_karaoke(event)
        ):
            gap = next_event.start - event.end
            if 0 < gap < MIN_GAP:
                yield Violation(
                    [event, next_event],
                    f"gap shorter than {MIN_GAP} ms ({gap} ms)",
                )
