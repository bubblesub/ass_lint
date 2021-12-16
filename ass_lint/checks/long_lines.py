from collections.abc import Iterable

from ass_parser import AssEvent
from ass_renderer import AssRenderer

from ..common import (
    WIDTH_MULTIPLIERS,
    get_optimal_line_heights,
    get_video_aspect_ratio,
    get_video_width,
    is_event_karaoke,
    measure_frame_size,
)
from .base import BaseEventCheck, BaseResult, CheckContext, Violation


class CheckLongLines(BaseEventCheck):
    def __init__(self, context: CheckContext) -> None:
        super().__init__(context)
        self.optimal_line_heights = get_optimal_line_heights(
            ass_file=context.ass_file,
            video_resolution=context.video_resolution,
        )
        self.width_multipliers: dict[int, float] = {}
        aspect_ratio = get_video_aspect_ratio(context.ass_file)
        if aspect_ratio:
            self.width_multipliers = WIDTH_MULTIPLIERS[aspect_ratio]

    async def run_for_event(self, event: AssEvent) -> Iterable[BaseResult]:
        if not self.width_multipliers:
            # AR information unavailable, covered by a separate check
            return

        if is_event_karaoke(event):
            return

        width, height = measure_frame_size(
            renderer=self.ctx.renderer,
            video_resolution=self.ctx.video_resolution,
            event=event,
        )
        average_height = self.optimal_line_heights.get(event.style_name, 0)
        line_count = round(height / average_height) if average_height else 0
        if not line_count:
            return

        try:
            width_multiplier = self.width_multipliers[line_count]
        except LookupError:
            yield Violation(
                event,
                f"too many lines ({height}/{average_height} = {line_count})",
            )
        else:
            optimal_width = (
                get_video_width(self.ctx.ass_file) * width_multiplier
            )
            if width > optimal_width:
                yield Violation(
                    event,
                    f"too long line "
                    f"({width - optimal_width:.02f} beyond {optimal_width:.02f})",
                )
