"""High-level DSL for klung-handboken formation diagrams.

Concepts:
    Rider — a bike, with mutable x, y, color
    Text  — annotation with target riders and a side hint
    Model — a scene; holds riders, texts, optional cross-overlay

The DSL exposes a few scale constants (RIDER_SEP, LANE_WIDTH) so a
diagram script can reason in formation-relative units instead of pixels.

Coords are screen coords (top-left origin). Forward = up (-y).

Each subfigure is a function of (x0, y0) — compose multiple by
calling them with different offsets in the same Model.
"""

from dataclasses import dataclass, field
from html import escape
from typing import List, Optional, Tuple


# ---- scale ----
# Rider glyph: a small chevron head + a thin trailing line (the "bike"
# is taller than wide — long, thin, with an arrowhead pointing forward).
RIDER_LENGTH = 50      # head tip to body bottom
RIDER_WIDTH = 12       # chevron head base width
RIDER_HEAD_H = 10      # height of chevron head
RIDER_GAP = 12         # vertical gap between consecutive riders in lane
RIDER_SEP = RIDER_LENGTH + RIDER_GAP    # 62
LANE_WIDTH = 30        # center-to-center distance between lanes


# ---- color palette ----
# Logical color names from the DSL map to actual hex values (RoH-style
# colored highlights on white). Each role is visually distinguishable.
_COLOR = {
    "blue":   "#2563eb",   # neutral, default
    "black":  "#000000",   # DU / reader
    "green":  "#16a34a",   # correct example
    "red":    "#dc2626",   # wrong example
    "orange": "#ea580c",   # focus / annotated rider
    "white":  "#ffffff",
}
_X_COLOR = "#dc2626"       # red cross overlay (matches RoH)

FONT = 'font-family="Helvetica, Arial, sans-serif"'


@dataclass
class Rider:
    x: float
    y: float
    color: str = "blue"
    crossed: bool = False


@dataclass
class Text:
    text: str
    targets: List[Rider] = field(default_factory=list)
    pos: str = "right"     # left | right | above | below


@dataclass
class Arrow:
    """A line or quadratic-bezier arrow with a triangle head at the end.

    start, end: (x, y) tuples in screen coords.
    via: (x, y) control point for a quadratic Bezier curve, or None
         for a straight line.
    color: logical color name (mapped to hex via _COLOR).
    """
    start: Tuple[float, float]
    end: Tuple[float, float]
    via: Optional[Tuple[float, float]] = None
    color: str = "black"


class Model:
    def __init__(self):
        self.riders: List[Rider] = []
        self.texts: List[Text] = []
        self.arrows: List[Arrow] = []
        self.crosses: List[Tuple[float, float, float, float]] = []

    def create_rider(self, color="blue", x=0.0, y=0.0) -> Rider:
        r = Rider(x=x, y=y, color=color)
        self.riders.append(r)
        return r

    def create_text(self, text, targets=None, pos="right") -> Text:
        t = Text(text=text, targets=list(targets or []), pos=pos)
        self.texts.append(t)
        return t

    def create_arrow(self, start, end, via=None, color="black") -> Arrow:
        a = Arrow(start=tuple(start), end=tuple(end),
                  via=tuple(via) if via else None, color=color)
        self.arrows.append(a)
        return a

    def cross_box(self, x1, y1, x2, y2):
        """Overlay a big X across the given rectangle."""
        self.crosses.append((x1, y1, x2, y2))

    def rider_bbox(self) -> Tuple[float, float, float, float]:
        if not self.riders:
            return (0, 0, 0, 0)
        xs = [r.x for r in self.riders]
        ys = [r.y for r in self.riders]
        return (
            min(xs) - RIDER_WIDTH,
            min(ys) - RIDER_LENGTH / 2,
            max(xs) + RIDER_WIDTH,
            max(ys) + RIDER_LENGTH / 2,
        )


# ---- rendering ----

def _rider_svg(r: Rider) -> str:
    color = _COLOR.get(r.color, _COLOR["blue"])
    hw = RIDER_WIDTH / 2
    hl = RIDER_LENGTH / 2
    head_h = RIDER_HEAD_H
    # Chevron head (open V) + thin trailing line for the body. No fill.
    p = (
        f"M{-hw},{-hl + head_h} "
        f"L0,{-hl} "
        f"L{hw},{-hl + head_h} "
        f"M0,{-hl + 1} "
        f"L0,{hl}"
    )
    parts = [f'<g transform="translate({r.x},{r.y})">',
             f'<path d="{p}" fill="none" stroke="{color}" stroke-width="2.5"'
             f' stroke-linecap="round" stroke-linejoin="round"/>']
    if r.crossed:
        sx = RIDER_WIDTH * 0.45
        sy = RIDER_LENGTH * 0.21
        parts.append(
            f'<g stroke="{_X_COLOR}" stroke-width="1.5" stroke-linecap="round">'
            f'<line x1="{-sx}" y1="{-sy}" x2="{sx}" y2="{sy}"/>'
            f'<line x1="{-sx}" y1="{sy}" x2="{sx}" y2="{-sy}"/>'
            f'</g>'
        )
    parts.append('</g>')
    return "\n".join(parts)


def _wrap(text: str, max_chars: int) -> List[str]:
    words = text.split()
    out, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_chars:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    if cur:
        out.append(cur)
    return out


FONT_SIZE = 13
LINE_H = 16
TEXT_MARGIN = 42       # gap from bbox edge to text column
TEXT_GAP = 6           # minimum gap between stacked text blocks
MAX_CHARS = 26


def _layout_texts(texts: List[Text], bbox) -> dict:
    """Return {id(text): (tx, ty_first_baseline, anchor, lines)} placements.

    On each side, sort by target avg y (or x), stack so blocks don't
    overlap. Each block's first-baseline y is computed so its center is
    at the target average — pushed down if it would overlap the previous.
    """
    x1, y1, x2, y2 = bbox
    by_side: dict = {"left": [], "right": [], "above": [], "below": []}
    for t in texts:
        if t.targets:
            by_side.setdefault(t.pos, by_side["right"]).append(t)

    placements = {}

    for side in ("left", "right"):
        side_texts = sorted(
            by_side.get(side, []),
            key=lambda t: sum(r.y for r in t.targets) / len(t.targets),
        )
        prev_bottom = -1e9
        tx = (x2 + TEXT_MARGIN) if side == "right" else (x1 - TEXT_MARGIN)
        anchor = "start" if side == "right" else "end"
        for t in side_texts:
            avg_y = sum(r.y for r in t.targets) / len(t.targets)
            lines = _wrap(t.text, MAX_CHARS)
            block_h = len(lines) * LINE_H
            desired_top = avg_y - block_h / 2
            top = max(desired_top, prev_bottom + TEXT_GAP)
            prev_bottom = top + block_h
            first_baseline = top + FONT_SIZE
            placements[id(t)] = (tx, first_baseline, anchor, lines)

    for side in ("above", "below"):
        side_texts = sorted(
            by_side.get(side, []),
            key=lambda t: sum(r.x for r in t.targets) / len(t.targets),
        )
        for t in side_texts:
            avg_x = sum(r.x for r in t.targets) / len(t.targets)
            lines = _wrap(t.text, MAX_CHARS)
            block_h = len(lines) * LINE_H
            if side == "above":
                top = y1 - TEXT_MARGIN - block_h
            else:
                top = y2 + TEXT_MARGIN
            first_baseline = top + FONT_SIZE
            placements[id(t)] = (avg_x, first_baseline, "middle", lines)

    return placements


def _text_svg(t: Text, placement) -> str:
    tx, first_baseline, anchor, lines = placement
    text_block = "\n".join(
        f'<text x="{tx}" y="{first_baseline + i * LINE_H}"'
        f' text-anchor="{anchor}" font-size="{FONT_SIZE}" {FONT}>'
        f'{escape(line)}</text>'
        for i, line in enumerate(lines)
    )

    # Leader source: edge of text block nearest the targets, mid-height
    block_h = len(lines) * LINE_H
    mid_y = first_baseline - FONT_SIZE + block_h / 2
    if anchor == "start":
        lx = tx - 4
    elif anchor == "end":
        lx = tx + 4
    else:
        lx = tx
    ly = mid_y

    leaders = []
    for r in t.targets:
        if r.x < lx:
            ex = r.x + RIDER_WIDTH / 2 + 2
        elif r.x > lx:
            ex = r.x - RIDER_WIDTH / 2 - 2
        else:
            ex = r.x
        leaders.append(
            f'<line x1="{lx}" y1="{ly}" x2="{ex}" y2="{r.y}"'
            f' stroke="#000" stroke-width="1"/>'
        )
    return text_block + "\n" + "\n".join(leaders)


def _cross_svg(x1, y1, x2, y2) -> str:
    return (
        f'<g stroke="{_X_COLOR}" stroke-width="2" stroke-linecap="round" fill="none">'
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'
        f'<line x1="{x1}" y1="{y2}" x2="{x2}" y2="{y1}"/>'
        f'</g>'
    )


def _arrow_svg(a: Arrow) -> str:
    color = _COLOR.get(a.color, _COLOR["black"])
    sx, sy = a.start
    ex, ey = a.end
    if a.via:
        vx, vy = a.via
        d = f"M{sx},{sy} Q{vx},{vy} {ex},{ey}"
    else:
        d = f"M{sx},{sy} L{ex},{ey}"
    return (
        f'<path d="{d}" stroke="{color}" stroke-width="2" fill="none"'
        f' stroke-linecap="round" marker-end="url(#arrowhead)"/>'
    )


_ARROW_MARKER_DEF = (
    '<defs>'
    '<marker id="arrowhead" viewBox="0 0 10 10" refX="9" refY="5"'
    ' markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
    '<path d="M0,0 L10,5 L0,10 Z" fill="#000"/>'
    '</marker>'
    '</defs>'
)


def render(*models: Model, width: int, height: int, title: str = "",
           output: Optional[str] = None) -> str:
    body_parts = []
    for m in models:
        bbox = m.rider_bbox()
        placements = _layout_texts(m.texts, bbox)
        for a in m.arrows:
            body_parts.append(_arrow_svg(a))
        for r in m.riders:
            body_parts.append(_rider_svg(r))
        for t in m.texts:
            p = placements.get(id(t))
            if p:
                body_parts.append(_text_svg(t, p))
        for c in m.crosses:
            body_parts.append(_cross_svg(*c))

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg"'
        f' viewBox="0 0 {width} {height}" width="{width}" height="{height}"'
        f' role="img" aria-label="{escape(title)}">\n'
        f'<title>{escape(title)}</title>\n'
        f'{_ARROW_MARKER_DEF}\n'
        f'<rect width="{width}" height="{height}" fill="white"/>\n'
        + "\n".join(body_parts) +
        '\n</svg>\n'
    )
    if output:
        import pathlib
        pathlib.Path(output).write_text(svg, encoding="utf-8")
    return svg
