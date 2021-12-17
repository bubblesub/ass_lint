from collections.abc import Iterable

from ass_parser import AssEvent

from ass_lint.common import BaseEventCheck, BaseResult, Violation


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
            yield Violation("using non-existing style", [event])
