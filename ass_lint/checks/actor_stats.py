import logging
from collections import defaultdict

from ass_lint.checks.base import BaseCheck


class CheckActorStats(BaseCheck):
    async def run(self) -> None:
        logging.info("Actors summary:")
        actors = defaultdict(int)

        for event in self.ctx.ass_file.events:
            actors[event.actor] += 1

        for actor, occurrences in sorted(
            actors.items(), key=lambda kv: -kv[1]
        ):
            logging.info(f"– {occurrences} time(s): {actor}")
