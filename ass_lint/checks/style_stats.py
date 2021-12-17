from collections import defaultdict

from .base import BaseCheck, Information


class CheckStyleStats(BaseCheck):
    async def run(self) -> None:
        results = ["Styles summary:"]
        styles = defaultdict(int)

        for event in self.ctx.ass_file.events:
            styles[event.style_name] += 1

        for style, occurrences in sorted(
            styles.items(), key=lambda kv: -kv[1]
        ):
            results.append(f"– {occurrences} time(s): {style}")

        yield Information("\n".join(results))
