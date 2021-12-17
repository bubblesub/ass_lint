from collections.abc import Iterable

from ass_lint.checks.actor_stats import CheckActorStats
from ass_lint.checks.ass_tags import CheckAssTags
from ass_lint.checks.double_words import CheckDoubleWords
from ass_lint.checks.durations import CheckDurations
from ass_lint.checks.fonts import CheckFonts
from ass_lint.checks.grammar import CheckGrammar
from ass_lint.checks.line_continuation import CheckLineContinuation
from ass_lint.checks.long_lines import CheckLongLines
from ass_lint.checks.punctuation import CheckPunctuation
from ass_lint.checks.punctuation_stats import CheckPunctuationStats
from ass_lint.checks.quotes import CheckQuotes
from ass_lint.checks.spelling import CheckSpelling
from ass_lint.checks.style_stats import CheckStyleStats
from ass_lint.checks.style_validity import CheckStyleValidity
from ass_lint.checks.times import CheckTimes
from ass_lint.checks.unnecessary_breaks import CheckUnnecessaryBreaks
from ass_lint.checks.video_resolution import CheckVideoResolution
from ass_lint.common import BaseCheck


def get_checks(full: bool) -> Iterable[BaseCheck]:
    if full:
        yield CheckGrammar

    yield CheckStyleValidity
    yield CheckAssTags
    yield CheckDurations
    yield CheckPunctuation
    yield CheckQuotes
    yield CheckLineContinuation
    yield CheckDoubleWords
    yield CheckUnnecessaryBreaks
    yield CheckLongLines

    if full:
        yield CheckTimes

    yield CheckVideoResolution
    yield CheckSpelling
    yield CheckActorStats
    yield CheckStyleStats
    yield CheckFonts
    yield CheckPunctuationStats


__all__ = [
    "get_checks",
]
