import re
from unittest.mock import Mock

import pytest
from ass_parser import AssEvent

from ass_lint.checks.base import LogLevel
from ass_lint.checks.quotes import CheckQuotes


@pytest.fixture(name="check_quotes")
def fixture_check_quotes(context: Mock) -> CheckQuotes:
    return CheckQuotes(context=context)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "text, expected_violations",
    [
        ("„What…", [("partial quote", LogLevel.info)]),
        ("…what.”", [("partial quote", LogLevel.info)]),
        ("„What.”", [(".*inside.*marks", LogLevel.debug)]),
        ("„What”.", [(".*outside.*", LogLevel.debug)]),
        ("„What”, he said.", [(".*outside.*", LogLevel.debug)]),
        ("„What.” he said.", [(".*inside.*", LogLevel.debug)]),
        ("„What!” he said.", [(".*inside.*", LogLevel.debug)]),
        ("„What?” he said.", [(".*inside.*", LogLevel.debug)]),
        ("„What…” he said.", [(".*inside.*", LogLevel.debug)]),
        ("„What,” he said.", [(".*inside.*", LogLevel.warning)]),
        ("He said „what.”", [(".*inside.*", LogLevel.warning)]),
        ("He said „what!”", [(".*inside.*", LogLevel.warning)]),
        ("He said „what?”", [(".*inside.*", LogLevel.warning)]),
        ("He said „what…”", [(".*inside.*", LogLevel.warning)]),
        ('"What"', [("plain quotation mark", LogLevel.info)]),
        (
            '"What…',
            [
                ("plain quotation mark", LogLevel.info),
                ("partial quote", LogLevel.info),
            ],
        ),
        (
            '…what."',
            [
                ("plain quotation mark", LogLevel.info),
                ("partial quote", LogLevel.info),
            ],
        ),
        (
            '"What."',
            [
                ("plain quotation mark", LogLevel.info),
                (".*inside.*marks", LogLevel.debug),
            ],
        ),
        (
            '"What".',
            [
                ("plain quotation mark", LogLevel.info),
                (".*outside.*", LogLevel.debug),
            ],
        ),
        (
            '"What", he said.',
            [
                ("plain quotation mark", LogLevel.info),
                (".*outside.*", LogLevel.debug),
            ],
        ),
        (
            '"What." he said.',
            [
                ("plain quotation mark", LogLevel.info),
                (".*inside.*", LogLevel.debug),
            ],
        ),
        (
            '"What!" he said.',
            [
                ("plain quotation mark", LogLevel.info),
                (".*inside.*", LogLevel.debug),
            ],
        ),
        (
            '"What?" he said.',
            [
                ("plain quotation mark", LogLevel.info),
                (".*inside.*", LogLevel.debug),
            ],
        ),
        (
            '"What…" he said.',
            [
                ("plain quotation mark", LogLevel.info),
                (".*inside.*", LogLevel.debug),
            ],
        ),
        (
            '"What," he said.',
            [
                ("plain quotation mark", LogLevel.info),
                (".*inside.*", LogLevel.warning),
            ],
        ),
        (
            'He said "what."',
            [
                ("plain quotation mark", LogLevel.info),
                (".*inside.*", LogLevel.warning),
            ],
        ),
        (
            'He said "what!"',
            [
                ("plain quotation mark", LogLevel.info),
                (".*inside.*", LogLevel.warning),
            ],
        ),
        (
            'He said "what?"',
            [
                ("plain quotation mark", LogLevel.info),
                (".*inside.*", LogLevel.warning),
            ],
        ),
        (
            'He said "what…"',
            [
                ("plain quotation mark", LogLevel.info),
                (".*inside.*", LogLevel.warning),
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
