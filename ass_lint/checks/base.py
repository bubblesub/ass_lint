import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from ass_parser import AssEvent, AssFile
from ass_renderer import AssRenderer
from ass_tag_parser import ass_to_plaintext


@dataclass
class CheckContext:
    subs_path: Path
    ass_file: AssFile
    renderer: AssRenderer
    video_resolution: tuple[int, int]
    default_language: str = "en_US"
    fonts_dir = Path("~/.config/oc-fonts").expanduser()


class BaseCheck:
    def __init__(self, context: CheckContext) -> None:
        self.ctx = context

    async def run(self) -> None:
        raise NotImplementedError("not implemented")

    @property
    def spell_check_lang(self) -> str:
        return (
            self.ctx.ass_file.script_info.get("Language")
            or self.ctx.default_language
        )


class BaseResult:
    def __init__(
        self, event: Union[AssEvent, list[AssEvent]], text: str
    ) -> None:
        if isinstance(event, list):
            self.event = event[0]
            self.additional_events = event[1:]
        else:
            self.event = event
            self.additional_events = []
        self.text = text

    @property
    def events(self) -> Iterable[AssEvent]:
        yield self.event
        yield from self.additional_events

    def __repr__(self) -> str:
        ids = "+".join([f'#{event.number or "?"}' for event in self.events])
        return f"{ids}: {self.text}"


class DebugInformation(BaseResult):
    log_level = logging.DEBUG


class Information(BaseResult):
    log_level = logging.INFO


class Violation(BaseResult):
    log_level = logging.WARNING


class BaseEventCheck(BaseCheck):
    def __init__(self, context: CheckContext) -> None:
        super().__init__(context)
        self.construct_event_map()

    async def run(self) -> None:
        async for result in self.get_violations():
            logging.log(result.log_level, repr(result))

    async def run_for_event(self, event: AssEvent) -> Iterable[BaseResult]:
        raise NotImplementedError("not implemented")

    async def get_violations(self) -> Iterable[BaseResult]:
        for event in self.ctx.ass_file.events:
            async for violation in self.run_for_event(event):
                yield violation

    def construct_event_map(self) -> None:
        non_empty_events = [
            event
            for event in self.ctx.ass_file.events
            if ass_to_plaintext(event.text) and not event.is_comment
        ]

        self.forwards_event_map = {}
        self.backwards_event_map = {}
        last: Optional[AssEvent] = None
        for event in non_empty_events:
            if last:
                self.forwards_event_map[last.index] = event
                self.backwards_event_map[event.index] = last
            last = event

    def get_prev_non_empty_event(self, event: AssEvent) -> Optional[AssEvent]:
        return self.backwards_event_map.get(event.index)

    def get_next_non_empty_event(self, event: AssEvent) -> Optional[AssEvent]:
        return self.forwards_event_map.get(event.index)
