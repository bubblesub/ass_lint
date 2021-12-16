import logging
import re
from unittest.mock import Mock

import pytest
from ass_parser import AssEvent

from ass_lint.checks.quotes import CheckQuotes


@pytest.fixture(name="check_quotes")
def fixture_check_quotes(context: Mock) -> CheckQuotes:
    return CheckQuotes(context=context)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, expected_violations",
    [
        ("„What…", [("partial quote", logging.INFO)]),
        ("…what.”", [("partial quote", logging.INFO)]),
        ("„What.”", [(".*inside.*marks", logging.DEBUG)]),
        ("„What”.", [(".*outside.*", logging.DEBUG)]),
        ("„What”, he said.", [(".*outside.*", logging.DEBUG)]),
        ("„What.” he said.", [(".*inside.*", logging.DEBUG)]),
        ("„What!” he said.", [(".*inside.*", logging.DEBUG)]),
        ("„What?” he said.", [(".*inside.*", logging.DEBUG)]),
        ("„What…” he said.", [(".*inside.*", logging.DEBUG)]),
        ("„What,” he said.", [(".*inside.*", logging.WARNING)]),
        ("He said „what.”", [(".*inside.*", logging.WARNING)]),
        ("He said „what!”", [(".*inside.*", logging.WARNING)]),
        ("He said „what?”", [(".*inside.*", logging.WARNING)]),
        ("He said „what…”", [(".*inside.*", logging.WARNING)]),
        ('"What"', [("plain quotation mark", logging.INFO)]),
        (
            '"What…',
            [
                ("plain quotation mark", logging.INFO),
                ("partial quote", logging.INFO),
            ],
        ),
        (
            '…what."',
            [
                ("plain quotation mark", logging.INFO),
                ("partial quote", logging.INFO),
            ],
        ),
        (
            '"What."',
            [
                ("plain quotation mark", logging.INFO),
                (".*inside.*marks", logging.DEBUG),
            ],
        ),
        (
            '"What".',
            [
                ("plain quotation mark", logging.INFO),
                (".*outside.*", logging.DEBUG),
            ],
        ),
        (
            '"What", he said.',
            [
                ("plain quotation mark", logging.INFO),
                (".*outside.*", logging.DEBUG),
            ],
        ),
        (
            '"What." he said.',
            [
                ("plain quotation mark", logging.INFO),
                (".*inside.*", logging.DEBUG),
            ],
        ),
        (
            '"What!" he said.',
            [
                ("plain quotation mark", logging.INFO),
                (".*inside.*", logging.DEBUG),
            ],
        ),
        (
            '"What?" he said.',
            [
                ("plain quotation mark", logging.INFO),
                (".*inside.*", logging.DEBUG),
            ],
        ),
        (
            '"What…" he said.',
            [
                ("plain quotation mark", logging.INFO),
                (".*inside.*", logging.DEBUG),
            ],
        ),
        (
            '"What," he said.',
            [
                ("plain quotation mark", logging.INFO),
                (".*inside.*", logging.WARNING),
            ],
        ),
        (
            'He said "what."',
            [
                ("plain quotation mark", logging.INFO),
                (".*inside.*", logging.WARNING),
            ],
        ),
        (
            'He said "what!"',
            [
                ("plain quotation mark", logging.INFO),
                (".*inside.*", logging.WARNING),
            ],
        ),
        (
            'He said "what?"',
            [
                ("plain quotation mark", logging.INFO),
                (".*inside.*", logging.WARNING),
            ],
        ),
        (
            'He said "what…"',
            [
                ("plain quotation mark", logging.INFO),
                (".*inside.*", logging.WARNING),
            ],
        ),
    ],
)
async def test_check_quotes(
    text: str,
    expected_violations: list[tuple[str, int]],
    check_quotes: CheckQuotes,
) -> None:
    event = AssEvent(text=text)
    check_quotes.ctx.ass_file.events.append(event)
    check_quotes.construct_event_map()
    results = [result async for result in check_quotes.run_for_event(event)]
    assert len(results) == len(expected_violations)
    for expected_violation, result in zip(expected_violations, results):
        violation_text_re, log_level = expected_violation
        assert re.match(violation_text_re, result.text)
        assert result.log_level == log_level
