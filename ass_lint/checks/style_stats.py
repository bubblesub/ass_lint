import logging
from collections import defaultdict

from .base import BaseCheck


class CheckStyleStats(BaseCheck):
    async def run(self) -> None:
        logging.info("Styles summary:")
        styles = defaultdict(int)

        for event in self.ctx.ass_file.events:
            styles[event.style_name] += 1

        for style, occurrences in sorted(
            styles.items(), key=lambda kv: -kv[1]
        ):
            logging.info(f"– {occurrences} time(s): {style}")
