from ..common import get_video_aspect_ratio, get_video_height, get_video_width
from .base import BaseCheck, Violation


class CheckVideoResolution(BaseCheck):
    async def run(self) -> None:
        width = get_video_width(self.ctx.ass_file)
        height = get_video_height(self.ctx.ass_file)
        aspect_ratio = get_video_aspect_ratio(self.ctx.ass_file)
        if not width:
            yield Violation("Unknown video width.")
        if not height:
            yield Violation("Unknown video height.")
        if not aspect_ratio:
            yield Violation("Unknown aspect ratio.")
