import re
from collections.abc import Iterable

from ass_parser import AssEvent
from ass_tag_parser import ass_to_plaintext

from ..common import (
    NON_STUTTER_PREFIXES,
    NON_STUTTER_SUFFIXES,
    NON_STUTTER_WORDS,
    WORDS_WITH_PERIOD,
    is_event_title,
)
from .base import BaseEventCheck, BaseResult, Violation


class CheckPunctuation(BaseEventCheck):
    async def run_for_event(self, event: AssEvent) -> Iterable[BaseResult]:
        text = ass_to_plaintext(event.text)

        if text.startswith("\n") or text.endswith("\n"):
            yield Violation("extra line break", [event])
        elif re.search(r"^\s|\s$", text):
            yield Violation("extra whitespace", [event])

        if text.count("\n") >= 2:
            yield Violation("three or more lines", [event])

        if re.search(r"\n[ \t]|[ \t]\n", text):
            yield Violation("whitespace around line break", [event])

        if re.search(r"\n[.,?!:;…]", text):
            yield Violation("line break before punctuation", [event])
        elif re.search(r"\s[.,?!:;…]", text):
            yield Violation("whitespace before punctuation", [event])

        if "  " in text:
            yield Violation("double space", [event])

        if "..." in text:
            yield Violation("bad ellipsis (expected …)", [event])
        elif re.search("[…,.!?:;][,.]", text):
            yield Violation("extra comma or dot", [event])
        elif re.search(r"!!|\?\?", text):
            yield Violation("double punctuation mark", [event])
        elif re.search(r"…[!?]|[!?]…", text):
            yield Violation("ellipsis around punctuation mark", [event])
        elif re.search(r"[!?\.] …", text):
            yield Violation("ellipsis in the middle of sentence", [event])

        context = re.split(r"\W+", re.sub('[.,?!"]', "", text.lower()))
        if self.ctx.language.lower().startswith("en"):
            for word in [
                "im",
                "youre",
                "hes",
                "shes",
                "theyre",
                "isnt",
                "arent",
                "wasnt",
                "werent",
                "didnt",
                "thats",
                "heres",
                "theres",
                "wheres",
                "cant",
                "dont",
                "wouldnt",
                "couldnt",
                "shouldnt",
                "hasnt",
                "havent",
                "ive",
                "wouldve",
                "youve",
                "ive",
            ]:
                if word in context:
                    yield Violation("missing apostrophe", [event])

        if "’" in text:
            yield Violation("bad apostrophe", [event])

        if re.search("^– .* –$", text, flags=re.M):
            yield Violation("bad dash (expected —)", [event])
        elif not re.search("^—.*—$", text, flags=re.M):
            if len(re.findall(r"^–|[\.…!?] –", text, flags=re.M)) == 1:
                yield Violation("dialog with just one person", [event])

            if re.search(r"[-–]$", text, flags=re.M):
                yield Violation("bad dash (expected —)", [event])

            if re.search(r"^- |^—", text, flags=re.M):
                yield Violation("bad dash (expected –)", [event])

            if re.search(r" - ", text, flags=re.M):
                yield Violation("bad dash (expected –)", [event])

        if re.search(r"\s+'(t|re|s)\b", text):
            yield Violation("whitespace before apostrophe", [event])

        if re.search(r" —|— (?![A-Z])", text) and not is_event_title(event):
            yield Violation("whitespace around —", [event])

        match = re.search(r"(\w+[\.!?])\s+[a-z]", text, flags=re.M)
        if match:
            if match.group(1) not in WORDS_WITH_PERIOD:
                yield Violation("lowercase letter after sentence end", [event])

        match = re.search(r"^([A-Z][a-z]{,3})(-([a-z]+))+", text, flags=re.M)
        if match:
            if (
                match.group(0).lower() not in NON_STUTTER_WORDS
                and match.group(1).lower() not in NON_STUTTER_PREFIXES
                and match.group(2).lower() not in NON_STUTTER_SUFFIXES
            ):
                yield Violation(
                    "possibly wrong stutter capitalization", [event]
                )

        if re.search(r"[\.,?!:;][A-Za-z]|[a-zA-Z]…[A-Za-z]", text):
            yield Violation(
                "missing whitespace after punctuation mark", [event]
            )

        if re.search(
            "\\s|\N{ZERO WIDTH SPACE}", text.replace(" ", "").replace("\n", "")
        ):
            yield Violation("unrecognized whitespace", [event])
