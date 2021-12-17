import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from ass_parser import AssEvent, AssFile
from ass_renderer import AssRenderer
from ass_tag_parser import ass_to_plaintext

from ass_lint.video import VideoSource


@dataclass
class CheckContext:
    subs_path: Path
    ass_file: AssFile
    renderer: AssRenderer
    video_resolution: tuple[int, int]
    video: Optional[VideoSource]

    default_language: str = "en_US"
    fonts_dir = Path("~/.config/oc-fonts").expanduser()

    @property
    def language(self) -> str:
        return (
            self.ass_file.script_info.get("Language") or self.default_language
        )


class LogLevel:
    debug = 1
    info = 2
    warning = 3


class BaseResult:
    def __init__(
        self, text: str, events: Optional[list[AssEvent]] = None
    ) -> None:
        self.events = events
        self.text = text

    def __repr__(self) -> str:
        if not self.events:
            return self.text
        ids = "+".join([f'#{event.number or "?"}' for event in self.events])
        return f"{ids}: {self.text}"


class DebugInformation(BaseResult):
    log_level = LogLevel.debug


class Information(BaseResult):
    log_level = LogLevel.info


class Violation(BaseResult):
    log_level = LogLevel.warning


class BaseCheck:
    def __init__(self, context: CheckContext) -> None:
        self.ctx = context

    async def run(self) -> Iterable[BaseResult]:
        raise NotImplementedError("not implemented")


class BaseEventCheck(BaseCheck):
    def __init__(self, context: CheckContext) -> None:
        super().__init__(context)
        self.construct_event_map()

    async def run(self) -> Iterable[BaseResult]:
        for event in self.ctx.ass_file.events:
            logging.debug(f"{self}: running for event #{event.number}")
            async for violation in self.run_for_event(event):
                yield violation

    async def run_for_event(self, event: AssEvent) -> Iterable[BaseResult]:
        raise NotImplementedError("not implemented")

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
