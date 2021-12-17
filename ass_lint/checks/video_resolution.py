import logging

from ..common import get_video_aspect_ratio, get_video_height, get_video_width
from .base import BaseCheck


class CheckVideoResolution(BaseCheck):
    async def run(self) -> None:
        width = get_video_width(self.ctx.ass_file)
        height = get_video_height(self.ctx.ass_file)
        aspect_ratio = get_video_aspect_ratio(self.ctx.ass_file)
        if not width:
            logging.error("Unknown video width.")
        if not height:
            logging.error("Unknown video height.")
        if not aspect_ratio:
            logging.error("Unknown aspect ratio.")
