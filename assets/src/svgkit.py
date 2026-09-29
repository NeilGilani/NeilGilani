"""svgkit — tiny SVG toolkit that renders text as outlined paths.

GitHub serves README images through a proxy and SVGs are drawn as <img>, so
web fonts never load inside them. Outlining text with the real font (shaped by
HarfBuzz for kerning/ligatures) makes every banner, card and diagram render
identically on every OS, at any zoom, with no font dependency.
"""
from __future__ import annotations

import html
import io
import math
import os
from dataclasses import dataclass

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_DIR = os.environ.get("SVGKIT_FONTS", os.path.join(os.path.dirname(__file__), "..", "fonts"))


class _RoundingSVGPen(SVGPathPen):
    """SVGPathPen that rounds coordinates to keep files small."""

    def __init__(self, glyphSet, ndigits=1):
        super().__init__(glyphSet, ntos=lambda v: _fmt(v, ndigits))


def _fmt(v: float, nd: int = 1) -> str:
    s = f"{v:.{nd}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in ("-0", "", "-") else s


_GLYPHS: dict[str, str] = {}   # id -> path d (font units), collected per document


class Font:
    _cache: dict[str, "Font"] = {}

    def __init__(self, name: str):
        path = os.path.join(FONT_DIR, name + ".woff")
        tt = TTFont(path)
        tt.flavor = None  # WOFF -> SFNT so HarfBuzz can read it
        buf = io.BytesIO()
        tt.save(buf)
        self.tt = TTFont(io.BytesIO(buf.getvalue()))
        self.upem = self.tt["head"].unitsPerEm
        self.glyphset = self.tt.getGlyphSet()
        face = hb.Face(hb.Blob(buf.getvalue()))
        self.hb = hb.Font(face)
        self.order = self.tt.getGlyphOrder()
        self.tag = "".join(c for c in name if c.isalnum()).lower()[:10]
        os2 = self.tt["OS/2"]
        self.cap_height = getattr(os2, "sCapHeight", 0) or int(self.upem * 0.7)
        self.x_height = getattr(os2, "sxHeight", 0) or int(self.upem * 0.5)
        self.ascender = self.tt["hhea"].ascent
        self.descender = self.tt["hhea"].descent

    @classmethod
    def get(cls, name: str) -> "Font":
        if name not in cls._cache:
            cls._cache[name] = Font(name)
        return cls._cache[name]

    def shape(self, text: str, features=None):
        b = hb.Buffer()
        b.add_str(text)
        b.guess_segment_properties()
        hb.shape(self.hb, b, features or {"kern": True, "liga": True, "calt": True})
        return b.glyph_infos, b.glyph_positions

    def measure(self, text: str, size: float, tracking: float = 0.0) -> float:
        """Advance width in px. tracking is in em (e.g. -0.02, 0.12)."""
        if not text:
            return 0.0
        infos, pos = self.shape(text)
        adv = sum(p.x_advance for p in pos) + tracking * self.upem * max(len(pos) - 1, 0)
        return adv * size / self.upem

    def glyph_uses(self, text: str, x: float, y: float, size: float,
                   tracking: float = 0.0, anchor: str = "start") -> tuple[str, float]:
        """Return (<g> of <use> refs, width); glyph outlines go to the shared registry."""
        width = self.measure(text, size, tracking)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        s = size / self.upem
        infos, pos = self.shape(text)
        pen_x, uses = 0.0, []
        for info, p in zip(infos, pos):
            gname = self.order[info.codepoint]
            gid = f"{self.tag}{info.codepoint}"
            if gid not in _GLYPHS:
                pen = _RoundingSVGPen(self.glyphset, 0)
                self.glyphset[gname].draw(pen)
                _GLYPHS[gid] = pen.getCommands()
            if _GLYPHS[gid]:
                ux = _fmt(pen_x + p.x_offset, 0)
                uy = _fmt(p.y_offset, 0)
                uses.append(f'<use href="#{gid}" x="{ux}"' + (f' y="{uy}"' if uy != "0" else "") + "/>")
            pen_x += p.x_advance + tracking * self.upem
        g = (f'<g transform="translate({_fmt(x, 2)} {_fmt(y, 2)}) scale({_fmt(s, 5)} {_fmt(-s, 5)})"'
             f'>{"".join(uses)}</g>')
        return g, width

    def path_d(self, text: str, x: float, y: float, size: float,
               tracking: float = 0.0, anchor: str = "start", nd: int = 1) -> tuple[str, float]:
        """Return (svg path d, width) for text whose baseline starts at (x, y)."""
        width = self.measure(text, size, tracking)
        if anchor == "middle":
            x -= width / 2
        elif anchor == "end":
            x -= width
        s = size / self.upem
        infos, pos = self.shape(text)
        pen_x = 0.0
        cmds = []
        for info, p in zip(infos, pos):
            gname = self.order[info.codepoint]
            ox = x + (pen_x + p.x_offset) * s
            oy = y - p.y_offset * s
            pen = _RoundingSVGPen(self.glyphset, nd)
            tpen = TransformPen(pen, (s, 0, 0, -s, ox, oy))
            self.glyphset[gname].draw(tpen)
            c = pen.getCommands()
            if c:
                cmds.append(c)
            pen_x += p.x_advance + tracking * self.upem
        return "".join(cmds), width


@dataclass
class Theme:
    name: str
    bg: str
    surface: str
    surface2: str
    line: str
    line2: str
    text: str
    text2: str
    text3: str
    accent: str
    accent_dim: str
    up: str
    down: str


DARK = Theme(
    name="dark",
    bg="#0A0A0B", surface="#111113", surface2="#17171A",
    line="#232327", line2="#2E2E33",
    text="#EDEDEF", text2="#A1A1AA", text3="#6B6B74",
    accent="#F5A524", accent_dim="#7A5314",
    up="#4ADE80", down="#F87171",
)
LIGHT = Theme(
    name="light",
    bg="#FAFAF9", surface="#F2F2F0", surface2="#EAEAE7",
    line="#E0E0DC", line2="#D0D0CB",
    text="#0A0A0B", text2="#52525B", text3="#8A8A92",
    accent="#B45309", accent_dim="#F3D7A8",
    up="#15803D", down="#B91C1C",
)

SANS = "Geist-{w}"
MONO = "GeistMono-{w}"


def text(s: str, x: float, y: float, size: float, fill: str, weight: int = 400,
         family: str = "sans", tracking: float = 0.0, anchor: str = "start",
         opacity: float | None = None, upper: bool = False, extra: str = "") -> str:
    fam = SANS if family == "sans" else MONO if family == "mono" else family
    f = Font.get(fam.format(w=weight))
    if not s.strip():
        return ""
    if upper:
        s = s.upper()
    g, _ = f.glyph_uses(s, x, y, size, tracking, anchor)
    op = f' fill-opacity="{opacity}"' if opacity is not None else ""
    return g.replace("<g ", f'<g fill="{fill}"{op}{extra} ', 1)


def measure(s: str, size: float, weight: int = 400, family: str = "sans",
            tracking: float = 0.0, upper: bool = False) -> float:
    fam = SANS if family == "sans" else MONO if family == "mono" else family
    return Font.get(fam.format(w=weight)).measure(s.upper() if upper else s, size, tracking)


def wrap(s: str, size: float, max_w: float, weight: int = 400, family: str = "sans",
         tracking: float = 0.0) -> list[str]:
    words, lines, cur = s.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if measure(trial, size, weight, family, tracking) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def svg_doc(w: int, h: int, body: str, title: str = "", desc: str = "") -> str:
    t = f"<title>{html.escape(title)}</title>" if title else ""
    d = f"<desc>{html.escape(desc)}</desc>" if desc else ""
    defs = "".join(f'<path id="{k}" d="{v}"/>' for k, v in _GLYPHS.items() if v)
    _GLYPHS.clear()
    defs = f"<defs>{defs}</defs>" if defs else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}" role="img" fill="none">{t}{d}{defs}{body}</svg>\n')


def rect(x, y, w, h, fill="none", stroke=None, sw=1, rx=0, opacity=None, extra=""):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<rect x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(w)}" height="{_fmt(h)}" rx="{rx}" fill="{fill}"{s}{o}{extra}/>'


def line(x1, y1, x2, y2, stroke, sw=1, dash=None, opacity=None, extra=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<line x1="{_fmt(x1)}" y1="{_fmt(y1)}" x2="{_fmt(x2)}" y2="{_fmt(y2)}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}{o}{extra}/>')


def polyline(pts, stroke, sw=1.5, opacity=None, extra="", fill="none"):
    p = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in pts)
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return (f'<polyline points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round" stroke-linecap="round"{o}{extra}/>')


def circle(cx, cy, r, fill="none", stroke=None, sw=1, opacity=None, extra=""):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    o = f' opacity="{opacity}"' if opacity is not None else ""
    return f'<circle cx="{_fmt(cx)}" cy="{_fmt(cy)}" r="{_fmt(r)}" fill="{fill}"{s}{o}{extra}/>'


def arrow(x1, y1, x2, y2, stroke, sw=1.25, head=6, dash=None, opacity=None):
    """Straight arrow with an open chevron head."""
    ang = math.atan2(y2 - y1, x2 - x1)
    a1, a2 = ang + math.radians(150), ang - math.radians(150)
    hx1, hy1 = x2 + head * math.cos(a1), y2 + head * math.sin(a1)
    hx2, hy2 = x2 + head * math.cos(a2), y2 + head * math.sin(a2)
    return (line(x1, y1, x2, y2, stroke, sw, dash, opacity) +
            polyline([(hx1, hy1), (x2, y2), (hx2, hy2)], stroke, sw, opacity))


def elbow(pts, stroke, sw=1.25, head=6, dash=None, opacity=None):
    """Orthogonal polyline arrow through pts, head at the last point."""
    body = ""
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        body += line(x1, y1, x2, y2, stroke, sw, dash, opacity)
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    a1, a2 = ang + math.radians(150), ang - math.radians(150)
    body += polyline([(x2 + head * math.cos(a1), y2 + head * math.sin(a1)), (x2, y2),
                      (x2 + head * math.cos(a2), y2 + head * math.sin(a2))], stroke, sw, opacity)
    return body


def grid(x0, y0, w, h, step, stroke, sw=1, opacity=0.5):
    out = []
    x = x0
    while x <= x0 + w + 0.01:
        out.append(line(x, y0, x, y0 + h, stroke, sw, opacity=opacity))
        x += step
    y = y0
    while y <= y0 + h + 0.01:
        out.append(line(x0, y, x0 + w, y, stroke, sw, opacity=opacity))
        y += step
    return "".join(out)


def ticks_corner(x, y, w, h, stroke, L=10, sw=1.25):
    """Registration-mark corners around a box (the 'viewfinder' motif)."""
    return "".join([
        polyline([(x, y + L), (x, y), (x + L, y)], stroke, sw),
        polyline([(x + w - L, y), (x + w, y), (x + w, y + L)], stroke, sw),
        polyline([(x, y + h - L), (x, y + h), (x + L, y + h)], stroke, sw),
        polyline([(x + w - L, y + h), (x + w, y + h), (x + w, y + h - L)], stroke, sw),
    ])
