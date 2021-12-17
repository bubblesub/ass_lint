import asyncio
import logging
from pathlib import Path
from threading import Lock
from typing import Union

import numpy as np

try:
    import ffms2
except ImportError:
    ffms2 = None

_SAMPLER_LOCK = Lock()


class VideoError(Exception):
    pass


class VideoSource:
    def __init__(self, path: Path) -> None:
        if not ffms2:
            raise VideoError("ffms2 not installed")

        self.path = path

        logging.debug(f"Loading video {path}")
        try:
            self._source = ffms2.VideoSource(str(path))
        except ffms2.Error as ex:
            raise VideoError(f"error loading video ({ex})")
        logging.debug(f"Finished loading video {path}")

        self.timecodes = sorted(
            [int(round(pts)) for pts in self._source.track.timecodes]
        )
        self.keyframes = sorted(self._source.track.keyframes[:])

        self._last_output_fmt: Any = None

    def frame_idx_from_pts(
        self, pts: Union[float, int, np.ndarray]
    ) -> Union[int, np.ndarray]:
        """Get index of a frame that contains given PTS.

        :param pts: PTS to search for
        :return: frame index, -1 if not found
        """
        ret = np.searchsorted(self.timecodes, pts, "right").astype(np.int32)
        ret = np.clip(ret - 1, a_min=0 if self.timecodes else -1, a_max=None)
        return ret

    def get_frame(self, frame_idx: int, width: int, height: int) -> np.ndarray:
        """Get raw video data from the currently loaded video source.

        :param frame_idx: frame number
        :param width: output image width
        :param height: output image height
        :return: numpy image
        """
        with _SAMPLER_LOCK:
            if frame_idx < 0 or frame_idx >= len(self.timecodes):
                raise ValueError("bad frame")
            assert self._source

            new_output_fmt = (
                [ffms2.get_pix_fmt("rgb24")],
                width,
                height,
                ffms2.FFMS_RESIZER_AREA,
            )
            if self._last_output_fmt != new_output_fmt:
                self._source.set_output_format(*new_output_fmt)
                self._last_output_fmt = new_output_fmt

            frame = self._source.get_frame(frame_idx)
            return (
                frame.planes[0]
                .reshape((height, frame.Linesize[0]))[:, 0 : width * 3]
                .reshape(height, width, 3)
            )

    async def async_get_frame(
        self, frame_idx: int, width: int, height: int
    ) -> np.ndarray:
        """Get raw video data from the currently loaded video source
        asynchronously.

        :param frame_idx: frame number
        :param width: output image width
        :param height: output image height
        :return: numpy image
        """
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        def _worker() -> None:
            result = self.get_frame(frame_idx, width, height)
            loop.call_soon_threadsafe(future.set_result, result)

        asyncio.get_event_loop().run_in_executor(None, _worker)
        return await future
