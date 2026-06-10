"""Rotation front-transition: "tredje led"-felet (fel vs rätt).

Valid for both tvåpar and belgisk — in belgisk the front-transition
flows continuously, in tvåpar you ride alongside a beat first. The
"don't make a third column" principle is identical in both.

Two subfigures side by side. Both start from rotation_snapshot.

Left subfigure ("Fel"):
  lane1[1] breaks out left (red) — creating a third column.
  lane1[2] (black) suffers behind, exposed to wind for longer.
  A big X is drawn across the whole subfigure.

Right subfigure ("Rätt"):
  lane1[1] stays in the drafting position (green).

Per RoH 2017: "Gå inte ut och skapa ett 'tredje' led (röd pil). Om du
gör det kommer det att bli en liten lucka till bakomvarande cyklist
(svart pil)... Ligg istället kvar bakom i väntan på din tur (grön pil)."
"""

import pathlib

from _shared import ROOT, rotation_snapshot, subfigure_bounds
from svg_formation import Model, RIDER_SEP, LANE_WIDTH, render


def wrong_subfigure(model, x0, y0):
    lane1, lane2 = rotation_snapshot(model, x0, y0)
    # Undo the correct draft and break out into the "third column" left
    lane1[1].x -= 0.3 * LANE_WIDTH    # cancel base draft
    lane1[1].x -= 0.6 * LANE_WIDTH    # third column
    lane1[1].y -= 0.5 * RIDER_SEP     # accelerated ahead of position
    lane1[1].color = "red"
    lane1[2].color = "black"          # the suffering rider behind
    model.cross_box(*subfigure_bounds(x0, y0))


def right_subfigure(model, x0, y0):
    lane1, lane2 = rotation_snapshot(model, x0, y0)
    lane1[1].color = "green"


if __name__ == "__main__":
    m = Model()
    GAP = 4 * LANE_WIDTH
    LEFT_X = 130
    wrong_subfigure(m, x0=LEFT_X, y0=170)
    right_subfigure(m, x0=LEFT_X + LANE_WIDTH + GAP, y0=170)
    out = ROOT / "images" / "rotation_front.svg"
    render(m, width=520, height=380,
           title="Fel vs rätt position vid rotation fram — tredje led",
           output=str(out))
    print(f"Wrote {out.relative_to(ROOT)}")
