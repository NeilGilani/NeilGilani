"""Architecture-diagram primitives in the same visual language as the banner."""
from __future__ import annotations

from svgkit import (DARK, LIGHT, rect, line, text, measure, wrap, svg_doc, polyline,
                    circle, arrow, elbow, _fmt)


class Diagram:
    def __init__(self, T, w, h, title="", desc=""):
        self.T, self.w, self.h = T, w, h
        self.title, self.desc = title, desc
        self.layers = {"bg": [], "group": [], "edge": [], "node": [], "label": []}

    # -- primitives -----------------------------------------------------------
    def background(self, grid=True):
        T = self.T
        self.layers["bg"].append(rect(0, 0, self.w, self.h, T.bg, rx=14))
        if grid:
            g = []
            for x in range(0, self.w + 1, 32):
                g.append(line(x, 0, x, self.h, T.line, 1))
            for y in range(0, self.h + 1, 32):
                g.append(line(0, y, self.w, y, T.line, 1))
            self.layers["bg"].append(f'<g opacity="0.35">{"".join(g)}</g>')

    def heading(self, kicker, title, x=36, y=48):
        T = self.T
        self.layers["label"].append(text(kicker.upper(), x, y, 12, T.accent, weight=500, family="mono", tracking=0.16))
        if title:
            self.layers["label"].append(text(title, x, y + 30, 22, T.text, weight=600, tracking=-0.02))

    def group(self, x, y, w, h, label, accent=False):
        T = self.T
        col = T.accent if accent else T.line2
        self.layers["group"].append(rect(x, y, w, h, "none", col, 1, rx=12,
                                         extra=' stroke-dasharray="4 5"'))
        lw = measure(label.upper(), 11, 500, "mono", 0.14)
        self.layers["group"].append(rect(x + 14, y - 8, lw + 14, 16, T.bg))
        self.layers["group"].append(text(label.upper(), x + 21, y + 4, 11, T.accent if accent else T.text3,
                                         weight=500, family="mono", tracking=0.14))

    def node(self, x, y, w, h, title, sub=None, accent=False, muted=False, sub2=None):
        """Box with a title (sans) and optional mono subtitle lines. Returns anchor dict."""
        T = self.T
        stroke = T.accent if accent else T.line2
        fill = T.surface2 if accent else T.surface
        self.layers["node"].append(rect(x, y, w, h, fill, stroke, 1.25 if accent else 1, rx=10))
        tcol = T.text3 if muted else T.text
        lines = [title]
        ty = y + (h / 2) + 6 if not sub else y + 26
        self.layers["node"].append(text(title, x + 16, ty, 16.5, tcol, weight=500, tracking=-0.01))
        if sub:
            sy = ty + 22
            for s in ([sub] if isinstance(sub, str) else sub):
                self.layers["node"].append(text(s, x + 16, sy, 12, T.text3, family="mono"))
                sy += 18
        return {"l": (x, y + h / 2), "r": (x + w, y + h / 2), "t": (x + w / 2, y),
                "b": (x + w / 2, y + h), "x": x, "y": y, "w": w, "h": h}

    def edge(self, pts, label=None, accent=False, dash=None, lpos=None, lanchor="middle"):
        T = self.T
        col = T.accent if accent else T.text3
        if len(pts) == 2:
            self.layers["edge"].append(arrow(*pts[0], *pts[1], col, 1.3, 6, dash))
        else:
            self.layers["edge"].append(elbow(pts, col, 1.3, 6, dash))
        if label:
            if lpos is None:
                (x1, y1), (x2, y2) = pts[len(pts) // 2 - 1], pts[len(pts) // 2]
                lpos = ((x1 + x2) / 2, (y1 + y2) / 2)
            self.pill(lpos[0], lpos[1], label, accent, lanchor)

    def pill(self, x, y, label, accent=False, anchor="middle"):
        T = self.T
        lw = measure(label, 11.5, 400, "mono")
        lx = x - lw / 2 if anchor == "middle" else x if anchor == "start" else x - lw
        self.layers["label"].append(rect(lx - 7, y - 11, lw + 14, 20, T.bg, rx=4))
        self.layers["label"].append(text(label, lx, y + 3.5, 11.5, T.accent if accent else T.text2, family="mono"))

    def note(self, x, y, s, size=12, color=None, anchor="start", mono=True, weight=400, maxw=None):
        T = self.T
        fam = "mono" if mono else "sans"
        rows = wrap(s, size, maxw, weight, fam) if maxw else [s]
        for i, r in enumerate(rows):
            self.layers["label"].append(text(r, x, y + i * (size * 1.45), size, color or T.text3,
                                             weight=weight, family=fam, anchor=anchor))

    def raw(self, layer, svg):
        self.layers[layer].append(svg)

    def render(self):
        body = "".join("".join(self.layers[k]) for k in ("bg", "group", "edge", "node", "label"))
        return svg_doc(self.w, self.h, body, self.title, self.desc)
