from typing import Optional
from unittest.mock import Mock

import pytest
from ass_parser import AssEvent

from ass_lint.checks.double_words import CheckDoubleWords


@pytest.fixture(name="check_double_words")
def fixture_check_double_words(context: Mock) -> CheckDoubleWords:
    return CheckDoubleWords(context=context)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, violation_text",
    [
        ("text", None),
        ("text text", "double word (text)"),
        ("text{} text", "double word (text)"),
        ("text{}\\Ntext", "double word (text)"),
        ("text{}text", None),
    ],
)
async def test_check_double_words(
    text: str,
    violation_text: Optional[str],
    check_double_words: CheckDoubleWords,
):
    event = AssEvent(text=text)
    check_double_words.ctx.ass_file.events.append(event)
    check_double_words.construct_event_map()
    results = [
        result async for result in check_double_words.run_for_event(event)
    ]
    if violation_text is None:
        assert len(results) == 0
    else:
        assert len(results) == 1
        assert results[0].text == violation_text
