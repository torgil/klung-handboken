"""Rotation back-transition: rätt vs fel position.

Valid for both tvåpar and belgisk — in belgisk the back-transition flows
continuously (chain); in tvåpar you ride alongside for a moment before
rotating. Same geometry, same rätt/fel principle.

Colors:
  - Red arrow + red X    = wrong slot (broken out, accelerated ahead)
  - Orange arrow         = the correct slot
  - Green arrow          = the rider-pair forming behind you
  - Black arrow          = DU (your perspective)

Per RoH 2017: "Memorera de två eller tre cyklisterna du har bakom dig
(orange och grön pil)... då vet du precis när det är din tur."
"""

from _shared import ROOT, rotation_snapshot
from svg_formation import Model, RIDER_SEP, LANE_WIDTH, render


def scene(model, x0, y0):
    lane1, lane2 = rotation_snapshot(model, x0, y0)

    # DU — black, reader perspective
    lane2[2].color = "black"
    model.create_text(text="DU", targets=[lane2[2]], pos="right")

    # right_pos = correct slot for the next-to-transition rider
    right_pos = lane2[3]
    right_pos.color = "orange"
    model.create_text(text="Rätt position",
                      targets=[right_pos], pos="right")

    # wrong_pos = ghost rider showing off-position fault
    wrong_pos = model.create_rider(color="red",
                                   x=right_pos.x, y=right_pos.y)
    wrong_pos.crossed = True
    model.create_text(
        text="Helt fel position vid växling till snabba ledet.",
        targets=[wrong_pos], pos="right")

    # Watch these two (orange + green per RoH 2017)
    lane1[3].color = "green"
    model.create_text(
        text="Ha koll på dessa två och var beredd när det är din tur!",
        targets=[right_pos, lane1[3]], pos="left")

    # Maybe also this one (when kuperat/kurvigt)
    model.create_text(
        text="Kanske även denna när det är kuperat och kurvigt!",
        targets=[lane1[2]], pos="left")

    # Final mutations: right_pos glides inward, wrong_pos drifts outward
    # and forward.
    right_pos.x -= 0.2 * LANE_WIDTH
    wrong_pos.x += 0.5 * LANE_WIDTH
    wrong_pos.y -= 0.3 * RIDER_SEP


if __name__ == "__main__":
    m = Model()
    scene(m, x0=340, y0=130)
    out = ROOT / "images" / "rotation_back.svg"
    render(m, width=680, height=480,
           title="Rätt vs fel position vid rotation bak",
           output=str(out))
    print(f"Wrote {out.relative_to(ROOT)}")
