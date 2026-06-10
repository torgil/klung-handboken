"""Lagtempo formation — ett led, rotation runt utsidan.

Single column. Front rider glides off to one side, drifts back along
the outside of the column, rejoins at the back. The rotation arc is
drawn as a single quadratic curve sweeping from front-outside-right
back to bottom-into-column-from-right, arrowhead pointing inward at
the rejoin slot.
"""

import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from svg_formation import (Model, RIDER_SEP, RIDER_WIDTH, render)


def scene(model, x0, y0, n=5):
    cx = x0
    riders = [model.create_rider(color="blue", x=cx, y=y0 + i * RIDER_SEP)
              for i in range(n)]

    top_y = riders[0].y
    bot_y = riders[-1].y
    mid_y = (top_y + bot_y) / 2

    # Rotation arc: from just outside top-right of front rider, bows
    # out to the right, ends pointing back into the column at the
    # bottom-right of the back rider.
    edge = RIDER_WIDTH / 2 + 2
    arc_reach = 4.5 * RIDER_WIDTH        # how far outward the arc bows
    model.create_arrow(
        start=(cx + edge, top_y),
        via=(cx + arc_reach, mid_y),
        end=(cx + edge, bot_y),
        color="black",
    )

    return riders


if __name__ == "__main__":
    m = Model()
    scene(m, x0=140, y0=60)
    out = ROOT / "images" / "lagtempo.svg"
    render(m, width=240, height=400,
           title="Lagtempo — rotation runt utsidan",
           output=str(out))
    print(f"Wrote {out.relative_to(ROOT)}")
