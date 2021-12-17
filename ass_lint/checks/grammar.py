import asyncio
from collections.abc import Iterable
from functools import cache
from typing import Any, Optional

from ass_parser import AssEvent
from ass_renderer import AssRenderer
from ass_tag_parser import ass_to_plaintext

from ..common import is_event_karaoke
from .base import BaseEventCheck, BaseResult, CheckContext, Violation

try:
    from gingerit.gingerit import GingerIt

    parser = GingerIt()  # pylint: disable=invalid-name
except ImportError:
    parser = None


@cache
def parse(text) -> Optional[dict[str, Any]]:
    if not parser:
        return None
    return parser.parse(text)


class CheckGrammar(BaseEventCheck):
    def __init__(self, context: CheckContext) -> None:
        super().__init__(context)
        if not parser:
            raise RuntimeError(
                "grammar checker is not available, install gingerit package"
            )

    async def run_for_event(self, event: AssEvent) -> Iterable[BaseResult]:
        text = ass_to_plaintext(event.text).replace("\n", " ")
        if not text or event.is_comment or is_event_karaoke(event):
            return
        if not self.ctx.language.lower().startswith("en"):
            return

        result = await asyncio.get_event_loop().run_in_executor(
            None, parse, text
        )
        if result and result["result"].lower() != text.lower():
            yield Violation(f'suggested change: {result["result"]}', [event])
