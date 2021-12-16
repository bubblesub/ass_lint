from unittest.mock import Mock

import pytest
from ass_parser import AssEventList


@pytest.fixture
def context() -> Mock:
    return Mock(
        ass_file=Mock(
            events=AssEventList(),
            script_info={
                "PlayResX": 1280,
                "PlayResY": 720,
            },
        ),
        renderer=Mock(),
        video_resolution=(1280, 720),
    )
