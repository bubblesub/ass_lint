import re
from collections.abc import Iterable
from copy import copy

from ass_parser import AssEvent
from ass_renderer import AssRenderer

from ass_lint.common import (
    BaseEventCheck,
    BaseResult,
    CheckContext,
    Information,
)
from ass_lint.util import (
    WIDTH_MULTIPLIERS,
    get_video_aspect_ratio,
    get_video_width,
    is_event_karaoke,
    is_event_title,
    measure_frame_size,
)


class CheckUnnecessaryBreaks(BaseEventCheck):
    def __init__(self, context: CheckContext) -> None:
        super().__init__(context)
        self.optimal_width: Optional[float] = None
        aspect_ratio = get_video_aspect_ratio(context.ass_file)
        if aspect_ratio:
            self.optimal_width = (
                get_video_width(context.ass_file)
                * WIDTH_MULTIPLIERS[aspect_ratio][1]
            )

    async def run_for_event(self, event: AssEvent) -> Iterable[BaseResult]:
        if self.optimal_width is None:
            # AR information unavailable, covered by a separate check
            return

        if r"\N" not in event.text:
            return

        if is_event_title(event) or is_event_karaoke(event):
            return

        event_copy = copy(event)
        event_copy.text = event.text.replace(r"\N", " ")
        many_sentences = (
            len(re.split(r"[\.!?…—] ", event_copy.text)) > 1
            or event_copy.text.count("–") >= 2
        )
        if many_sentences:
            return

        width, _height = measure_frame_size(
            renderer=self.ctx.renderer,
            video_resolution=self.ctx.video_resolution,
            event=event_copy,
        )

        if width < self.optimal_width:
            yield Information(
                f"possibly unnecessary break "
                f"({self.optimal_width - width:.02f} until "
                f"{self.optimal_width:.02f})",
                [event],
            )
