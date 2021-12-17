from collections.abc import Iterable

from ass_parser import AssEvent

from .base import BaseEventCheck, BaseResult, Violation


class CheckStyleValidity(BaseEventCheck):
    async def run_for_event(self, event: AssEvent) -> Iterable[BaseResult]:
        if (
            event.style_name.startswith("[")
            and event.style_name.endswith("]")
            and event.is_comment
        ):
            return

        style = self.ctx.ass_file.styles.get_by_name(event.style_name)
        if style is None:
            yield Violation(event, "using non-existing style")
