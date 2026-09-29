"""Profile banner: name, thesis line, and a 'null band' motif.

The motif is the core idea behind the research repos: one observed path drawn
over a fan of paths from a null model (same volatility, no edge). If the
observed line can't leave the band, the "edge" was noise.
"""
from __future__ import annotations

import math
import random
import sys

from svgkit import DARK, LIGHT, rect, line, text, measure, svg_doc, _fmt

W, H = 1280, 440


def walk(rng, n, sigma, drift=0.0):
    y, out = 0.0, [0.0]
    for _ in range(n):
        y += rng.gauss(drift, sigma)
        out.append(y)
    return out


def build(T) -> str:
    rng = random.Random(254)
    b = []
    # --- background + faint grid that fades toward the edges --------------
    b.append(f'<defs>'
             f'<radialGradient id="fade" cx="72%" cy="45%" r="62%">'
             f'<stop offset="0" stop-color="#fff" stop-opacity="1"/>'
             f'<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>'
             f'<mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>'
             f'<clipPath id="plot"><rect x="690" y="70" width="560" height="290"/></clipPath>'
             f'</defs>')
    b.append(rect(0, 0, W, H, T.bg))
    g = []
    for x in range(0, W + 1, 40):
        g.append(line(x, 0, x, H, T.line, 1))
    for y in range(0, H + 1, 40):
        g.append(line(0, y, W, y, T.line, 1))
    b.append(f'<g mask="url(#m)" opacity="0.55">{"".join(g)}</g>')

    # --- top rule: title-block style annotations ---------------------------
    b.append(text("NEIL GILANI", 64, 58, 12.5, T.text3, weight=500, family="mono", tracking=0.18))
    b.append(text("BUILD LOG  ·  2025 → NOW", W - 64, 58, 12.5, T.text3, weight=500,
                  family="mono", tracking=0.18, anchor="end"))
    b.append(line(64, 74, W - 64, 74, T.line2, 1))

    # --- null band motif ----------------------------------------------------
    x0, x1, yc = 700, 1216, 222
    n = 96
    sx = (x1 - x0) / n
    sigma = 4.4
    paths = [walk(rng, n, sigma) for _ in range(46)]
    # percentile envelope (5-95) of the null paths
    lo, hi = [], []
    for i in range(n + 1):
        col = sorted(p[i] for p in paths)
        lo.append(col[int(0.05 * len(col))])
        hi.append(col[int(0.95 * len(col)) - 1])
    env = [(x0 + i * sx, yc - hi[i]) for i in range(n + 1)] + \
          [(x0 + i * sx, yc - lo[i]) for i in range(n, -1, -1)]
    envd = "M" + " L".join(f"{_fmt(x)},{_fmt(y)}" for x, y in env) + "Z"
    motif = [f'<path d="{envd}" fill="{T.text3}" fill-opacity="0.07"/>']
    for p in paths:
        d = "M" + " L".join(f"{_fmt(x0 + i * sx)},{_fmt(yc - v)}" for i, v in enumerate(p))
        motif.append(f'<path d="{d}" stroke="{T.text3}" stroke-opacity="0.26" stroke-width="0.9" fill="none"/>')
    # observed path: a seeded walk with slight drift, kept inside the band late
    obs = walk(random.Random(7), n, sigma * 0.95, drift=0.35)
    obs = [max(min(v, hi[i] * 0.96), lo[i] * 0.96) if i > 48 else v for i, v in enumerate(obs)]
    od = "M" + " L".join(f"{_fmt(x0 + i * sx)},{_fmt(yc - v)}" for i, v in enumerate(obs))
    motif.append(f'<path class="obs" d="{od}" stroke="{T.accent}" stroke-width="2" fill="none" '
                 f'stroke-linejoin="round" stroke-linecap="round" pathLength="1"/>')
    ex, ey = x0 + n * sx, yc - obs[-1]
    motif.append(f'<circle class="dot" cx="{_fmt(ex)}" cy="{_fmt(ey)}" r="3.5" fill="{T.accent}"/>')
    b.append(f'<g clip-path="url(#plot)">{"".join(motif)}</g>')
    # baseline + axis annotations
    b.append(line(x0, yc, x1, yc, T.text3, 1, dash="2 4", opacity=0.6))
    b.append(text("OBSERVED", ex - 10, ey - 14, 10.5, T.accent, weight=500, family="mono",
                  tracking=0.14, anchor="end"))
    b.append(text("NULL MODEL  ·  SAME VOLATILITY, NO EDGE", x0, 356, 10.5, T.text3, weight=500,
                  family="mono", tracking=0.14))
    b.append(text("5–95% BAND", x1, 356, 10.5, T.text3, weight=500, family="mono",
                  tracking=0.14, anchor="end"))

    # --- name + thesis ------------------------------------------------------
    b.append(text("Neil Gilani", 60, 196, 88, T.text, weight=600, tracking=-0.04))
    b.append(text("Most of what I build starts as", 64, 252, 27, T.text2, weight=400, tracking=-0.012))
    b.append(text("a claim I didn’t believe.", 64, 288, 27, T.text2, weight=400, tracking=-0.012))

    # --- domain index -------------------------------------------------------
    y = 380
    b.append(line(64, 344, 600, 344, T.line2, 1))
    labels = ["AI MEMORY", "MARKETS", "VISION", "ROBOTICS"]
    x = 64
    for i, lab in enumerate(labels):
        num = f"0{i + 1}"
        b.append(text(num, x, y, 11, T.accent, weight=500, family="mono", tracking=0.1))
        nx = x + measure(num, 11, 500, "mono", 0.1) + 10
        b.append(text(lab, nx, y, 11, T.text2, weight=500, family="mono", tracking=0.16))
        x = nx + measure(lab, 11, 500, "mono", 0.16) + 30

    style = ('<style>'
             '.obs{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 2.6s cubic-bezier(.4,0,.2,1) .3s forwards}'
             '.dot{opacity:0;animation:pop .4s ease-out 2.8s forwards}'
             '@keyframes draw{to{stroke-dashoffset:0}}'
             '@keyframes pop{to{opacity:1}}'
             '@media (prefers-reduced-motion:reduce){.obs{animation:none;stroke-dashoffset:0}.dot{animation:none;opacity:1}}'
             '</style>')
    return svg_doc(W, H, style + "".join(b), title="Neil Gilani",
                   desc="Most of what I build starts as a claim I didn’t believe. "
                        "AI memory, markets, computer vision, robotics.")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "."
    for T in (DARK, LIGHT):
        open(f"{out}/banner-{T.name}.svg", "w").write(build(T))
    print("ok")
