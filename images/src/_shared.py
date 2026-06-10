"""Shared formation composers used by multiple diagram scripts."""

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from svg_formation import Model, RIDER_SEP, LANE_WIDTH  # noqa: E402


def rotation_snapshot(model: Model, x0: float, y0: float, n: int = 4):
    """Belgisk-kedja front-transition snapshot, "correct" base layout.

    - lane1 = fast lane (shifted forward by 80% of a rider-separation)
    - lane2 = slow lane
    - lane1[0] = mid-glide rightward to merge with slow lane front (50%)
    - lane1[1] = drafting slightly right (30%) behind the rotating rider —
      the "correct" placement; img01 wrong-variant overrides this.

    Returns (lane1, lane2) lists with index 0 = front.
    """
    y_rotate = 0.8 * RIDER_SEP
    x_rotate = 0.5 * LANE_WIDTH
    draft_right = 0.3 * LANE_WIDTH
    lane1_x = x0
    lane2_x = x0 + LANE_WIDTH

    lane1 = [model.create_rider(color="blue",
                                x=lane1_x,
                                y=y0 + i * RIDER_SEP - y_rotate)
             for i in range(n)]
    lane2 = [model.create_rider(color="blue",
                                x=lane2_x,
                                y=y0 + i * RIDER_SEP)
             for i in range(n)]
    lane1[0].x += x_rotate     # mid-glide
    lane1[1].x += draft_right  # correct draft
    return lane1, lane2


def subfigure_bounds(x0: float, y0: float, *,
                     extra_left: float = 0.7 * LANE_WIDTH,
                     extra_top: float = 1.4 * RIDER_SEP,
                     extra_right: float = 0.3 * LANE_WIDTH,
                     extra_bottom: float = 0.4 * RIDER_SEP,
                     n_rows: int = 4):
    """Rectangle covering a rotation_snapshot subfigure (for cross_box etc.)."""
    return (
        x0 - extra_left,
        y0 - extra_top,
        x0 + LANE_WIDTH + extra_right,
        y0 + (n_rows - 1) * RIDER_SEP + extra_bottom,
    )
