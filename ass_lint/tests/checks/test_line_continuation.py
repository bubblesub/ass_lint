from typing import Optional
from unittest.mock import Mock

import pytest
from ass_parser import AssEvent

from ass_lint.checks.line_continuation import CheckLineContinuation


@pytest.fixture(name="check_line_continuation")
def fixutre_check_line_continuation(context: Mock) -> CheckLineContinuation:
    return CheckLineContinuation(context=context)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "texts, violation_text",
    [
        (["Whatever…"], None),
        (["Whatever…", "I don't care."], None),
        (["…okay."], None),
        (["Whatever…", "…you say."], "old-style line continuation"),
        (["Whatever", "you say."], None),
        (["Whatever,", "we don't care."], None),
        (["Whatever:", "we don't care."], None),
        (["whatever."], "sentence begins with a lowercase letter"),
        (
            ["Whatever.", "whatever."],
            "sentence begins with a lowercase letter",
        ),
        (["Whatever,", "whatever."], None),
        (["Whatever i18n ąćę", "whatever."], None),
        (["Whatever"], "possibly unended sentence"),
        (["Whatever", "Whatever."], "possibly unended sentence"),
        (["Whatever,", "I have."], None),
        (["Whatever,", "I'm going."], None),
        (["Whatever,", "I'd go."], None),
        (["Whatever,", "I'll go."], None),
        (["Whatever,", "Not."], "possibly unended sentence"),
        (["Whatever,", "żółć."], None),
        (["Whatever,", '"Not."'], None),
        (["Whatever,", "„Not.”"], None),
        (["Whatever,", "“Not.”"], None),
        (["Japan vs.", "the rest."], None),
        (
            ["Japan vss.", "the rest."],
            "sentence begins with a lowercase letter",
        ),
    ],
)
async def test_check_line_continuation(
    texts: list[str],
    violation_text: Optional[str],
    check_line_continuation: CheckLineContinuation,
) -> None:
    for text in texts:
        check_line_continuation.ctx.ass_file.events.append(AssEvent(text=text))
    check_line_continuation.construct_event_map()

    results = []
    for event in check_line_continuation.ctx.ass_file.events:
        async for result in check_line_continuation.run_for_event(event):
            results.append(result)

    if violation_text is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        assert results[0].text == violation_text
