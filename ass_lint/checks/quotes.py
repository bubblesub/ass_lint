import re
from collections.abc import Iterable

from ass_parser import AssEvent
from ass_tag_parser import ass_to_plaintext

from ass_lint.common import (
    BaseEventCheck,
    BaseResult,
    DebugInformation,
    Information,
    Violation,
)


class CheckQuotes(BaseEventCheck):
    async def run_for_event(self, event: AssEvent) -> Iterable[BaseResult]:
        text = ass_to_plaintext(event.text)

        if text.count('"'):
            yield Information("plain quotation mark", [event])

        if (
            (text.count("„") + text.count("“")) != text.count("”")
        ) or text.count('"') % 2 == 1:
            yield Information("partial quote", [event])
            return

        if re.search(r'[:,]["”]', text):
            yield Violation("punctuation inside quotation marks", [event])

        if re.search(r'["”][\.,…?!]', text, flags=re.M):
            yield DebugInformation(
                "punctuation outside quotation marks", [event]
            )

        if re.search(r'[a-z]\s[„“"].+[\.…?!]["”]', text, flags=re.M):
            yield Violation("punctuation inside quotation marks", [event])
        elif re.search(r'[„“"].+[\.…?!]["”]', text, flags=re.M):
            yield DebugInformation(
                "punctuation inside quotation marks", [event]
            )
