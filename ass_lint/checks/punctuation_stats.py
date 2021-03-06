from collections import defaultdict

from ass_tag_parser import ass_to_plaintext

from ass_lint.common import BaseCheck, Information
from ass_lint.util import is_event_karaoke, is_event_title


class CheckPunctuationStats(BaseCheck):
    CHARS = "!…"

    async def run(self) -> None:
        stats = defaultdict(int)
        for event in self.ctx.ass_file.events:
            if is_event_title(event) or is_event_karaoke(event):
                continue
            for char in self.CHARS:
                stats[char] += ass_to_plaintext(event.text).count(char)

        yield Information(
            "Punctuation stats: "
            + ", ".join(f"{char}: {count}" for char, count in stats.items())
        )
