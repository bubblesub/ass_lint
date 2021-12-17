from collections import defaultdict

from ass_lint.common import BaseCheck, Information


class CheckActorStats(BaseCheck):
    async def run(self) -> None:
        result = ["Actors summary:"]
        actors = defaultdict(int)

        for event in self.ctx.ass_file.events:
            actors[event.actor] += 1

        for actor, occurrences in sorted(
            actors.items(), key=lambda kv: -kv[1]
        ):
            result.append(f"– {occurrences} time(s): {actor}")

        yield Information("\n".join(result))
