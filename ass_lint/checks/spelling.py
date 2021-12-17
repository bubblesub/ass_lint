import logging
from collections import defaultdict
from collections.abc import Iterable
from functools import cache

import ass_tag_parser
import regex

from ..common import is_event_karaoke, suppress_stderr
from .base import BaseCheck, Violation

try:
    with suppress_stderr():
        import enchant
except ImportError:
    enchant = None


class SpellCheckerError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)


class DictNotFound(SpellCheckerError):
    def __init__(self, language: str) -> None:
        super().__init__(f"dictionary {language} not installed")


class WordList:
    def __init__(self) -> None:
        self.case_insensitive: list[str] = []
        self.case_sensitive: list[str] = []

    def add_word(self, word: str) -> None:
        if word.islower():
            self.case_insensitive.append(word.lower())
        else:
            self.case_sensitive.append(word)

    def __contains__(self, word: str) -> None:
        return (
            word in self.case_sensitive
            or word.lower() in self.case_insensitive
        )


class SpellChecker:
    def __init__(
        self, language: str, whitelist: WordList, blacklist: WordList
    ) -> None:
        super().__init__()
        self.whitelist = whitelist
        self.blacklist = blacklist

        if not enchant:
            raise SpellCheckError("Enchant not installed")

        try:
            self._dict = enchant.Dict(language)
        except enchant.errors.DictNotFoundError as ex:
            raise DictNotFound(language) from ex

    def check(self, word: str) -> bool:
        return word not in self.blacklist and (
            word in self.whitelist or self._dict.check(word)
        )


def iter_words_ass_line(text: str) -> Iterable[tuple[int, int, str]]:
    """Iterate over words within an ASS line.

    Doesn't take into account effects such as text invisibility etc.

    :param text: input ASS line
    :return: iterator over tuples with start, end and word
    """
    try:
        ass_line = ass_tag_parser.parse_ass(text)
    except ass_tag_parser.ParseError:
        return

    for item in ass_line:
        if not isinstance(item, ass_tag_parser.AssText):
            continue

        # expand whitespace characters
        text = regex.sub(
            r"\\[Nnh]",
            "  ",  # two spaces to preserve match positions
            text,
        )

        for match in regex.finditer(
            r"[\p{L}\p{S}\p{N}][\p{L}\p{S}\p{N}\p{P}]*\p{L}|\p{L}", text
        ):
            yield (
                item.meta.start + match.start(),
                item.meta.start + match.end(),
                match.group(0),
            )


@cache
def spell_check_ass_line(
    spell_checker: SpellChecker, text: str
) -> Iterable[tuple[int, int, str]]:
    """Iterate over badly spelled words within an ASS line.

    Doesn't take into account effects such as text invisibility etc.

    :param spell_checker: spell checker to validate the words with
    :param text: input ASS line
    :return: iterator over tuples with start, end and text
    """
    for start, end, word in iter_words_ass_line(text):
        if not spell_checker.check(word):
            yield (start, end, word)


class CheckSpelling(BaseCheck):
    async def run(self) -> None:
        whitelist = WordList()
        blacklist = WordList()
        lang = self.ctx.language
        lang_short = regex.sub("[-_].*", "", lang)

        dict_names = [
            f"dict-{lang}.txt",
            f"dict-{lang_short}.txt",
            f"{lang}-dict.txt",
            f"{lang_short}-dict.txt",
            "dict.txt",
        ]

        for dict_name in dict_names:
            dict_path = self.ctx.subs_path.with_name(dict_name)
            if dict_path.exists():
                for line in dict_path.read_text().splitlines():
                    if line.startswith("!"):
                        blacklist.add_word(line[1:])
                    else:
                        whitelist.add_word(line)
                break

        spell_checker = SpellChecker(lang, whitelist, blacklist)

        misspelling_map = defaultdict(set)
        for event in self.ctx.ass_file.events:
            if is_event_karaoke(event):
                continue
            text = ass_tag_parser.ass_to_plaintext(event.text)
            for _start, _end, word in spell_check_ass_line(
                spell_checker, text
            ):
                misspelling_map[word].add(event.number)

        result = []
        if misspelling_map:
            for word, line_numbers in sorted(
                misspelling_map.items(),
                key=lambda item: len(item[1]),
                reverse=True,
            ):
                yield Violation(
                    f"Misspelled {word}: "
                    + ", ".join(f"#{num}" for num in line_numbers)
                )
