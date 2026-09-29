"""Social-preview cards (1280x640) with a small, project-specific motif."""
from __future__ import annotations

import math
import random

from svgkit import (DARK, LIGHT, rect, line, text, measure, wrap, svg_doc, polyline,
                    circle, _fmt, ticks_corner)

W, H = 1280, 640


def _bg(T, cx="74%", cy="46%"):
    g = []
    for x in range(0, W + 1, 40):
        g.append(line(x, 0, x, H, T.line, 1))
    for y in range(0, H + 1, 40):
        g.append(line(0, y, W, y, T.line, 1))
    return (f'<defs><radialGradient id="fade" cx="{cx}" cy="{cy}" r="60%">'
            f'<stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
            f'</radialGradient><mask id="m"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask></defs>'
            + rect(0, 0, W, H, T.bg) + f'<g mask="url(#m)" opacity="0.6">{"".join(g)}</g>')


# ---------------------------------------------------------------- motifs ----
# Each motif draws inside the box (x, y, w, h).

def motif_fan(T, x, y, w, h, seed=3):
    rng = random.Random(seed)
    n, k = 80, 40
    sx, yc = w / n, y + h / 2
    sig = h / 38
    out = []
    ends = []
    for _ in range(k):
        v, pts = 0.0, []
        for i in range(n + 1):
            pts.append((x + i * sx, yc - v))
            v += rng.gauss(0, sig)
        ends.append(v)
        out.append(polyline(pts, T.text3, 0.9, opacity=0.3))
    rng2 = random.Random(seed + 11)
    v, pts = 0.0, []
    for i in range(n + 1):
        pts.append((x + i * sx, yc - v))
        v += rng2.gauss(0.18 * sig, sig * 0.9)
    out.append(line(x, yc, x + w, yc, T.text3, 1, dash="2 4", opacity=0.7))
    out.append(polyline(pts, T.accent, 2.2))
    out.append(circle(pts[-1][0], pts[-1][1], 4, T.accent))
    return "".join(out)


def motif_orderbook(T, x, y, w, h, seed=5):
    rng = random.Random(seed)
    levels = 9
    rowh = h / (levels * 2 + 1)
    mid = x + w / 2
    out = []
    for i in range(levels):
        sz_a = (0.25 + 0.75 * rng.random()) * (0.35 + i / levels * 0.65)
        sz_b = (0.25 + 0.75 * rng.random()) * (0.35 + i / levels * 0.65)
        ya = y + (levels - 1 - i) * rowh
        yb = y + (levels + 1 + i) * rowh
        out.append(rect(mid - 6 - sz_a * (w / 2 - 70), ya + 3, sz_a * (w / 2 - 70), rowh - 6,
                        T.down, opacity=0.22 + 0.5 * (1 - i / levels), rx=2))
        out.append(rect(mid + 6, yb + 3, sz_b * (w / 2 - 70), rowh - 6,
                        T.up, opacity=0.22 + 0.5 * (1 - i / levels), rx=2))
        pa = f"{100.05 + i * 0.05:.2f}"
        pb = f"{99.95 - i * 0.05:.2f}"
        out.append(text(pa, x + w, ya + rowh * 0.68, 12, T.text3, family="mono", anchor="end"))
        out.append(text(pb, x, yb + rowh * 0.68, 12, T.text3, family="mono"))
    ym = y + levels * rowh
    out.append(line(x, ym + rowh / 2, x + w, ym + rowh / 2, T.accent, 1, dash="3 4"))
    out.append(text("MID 100.00", mid, ym + rowh * 0.72, 12, T.accent, weight=500, family="mono",
                    anchor="middle", tracking=0.08))
    return "".join(out)


def motif_memory(T, x, y, w, h, seed=9):
    """Episodes on a timeline consolidating into durable lessons (fading = aging)."""
    rng = random.Random(seed)
    out = []
    ty = y + h * 0.78
    out.append(line(x, ty, x + w, ty, T.line2, 1))
    eps = []
    for i in range(22):
        ex = x + 10 + i * (w - 20) / 21
        fail = rng.random() < 0.35
        eps.append((ex, fail))
        out.append(circle(ex, ty, 3.2, T.down if fail else T.text3, opacity=0.35 + 0.65 * i / 21))
    lessons = [(x + w * 0.28, y + h * 0.3), (x + w * 0.58, y + h * 0.18), (x + w * 0.86, y + h * 0.36)]
    for lx, ly in lessons:
        for ex, fail in eps:
            if fail and abs(ex - lx) < w * 0.22:
                out.append(line(ex, ty - 4, lx, ly + 9, T.accent, 1, opacity=0.35))
        out.append(circle(lx, ly, 9, T.bg, T.accent, 1.6))
        out.append(circle(lx, ly, 3.4, T.accent))
    out.append(line(lessons[0][0], lessons[0][1], lessons[1][0], lessons[1][1], T.accent, 1, dash="2 4", opacity=0.7))
    out.append(line(lessons[1][0], lessons[1][1], lessons[2][0], lessons[2][1], T.accent, 1, dash="2 4", opacity=0.7))
    out.append(text("SESSIONS", x, ty + 28, 11, T.text3, weight=500, family="mono", tracking=0.14))
    out.append(text("LESSONS", x, y + 4, 11, T.accent, weight=500, family="mono", tracking=0.14))
    return "".join(out)


def motif_payoff(T, x, y, w, h, seed=2):
    """Call payoff at expiry vs. model value before expiry."""
    out = []
    x0, x1 = x, x + w
    yb = y + h * 0.82
    K = x + w * 0.45
    out.append(line(x0, yb, x1, yb, T.line2, 1))
    out.append(line(K, y + 10, K, yb + 8, T.text3, 1, dash="2 4"))
    out.append(polyline([(x0, yb), (K, yb), (x1, y + 20)], T.text3, 1.4))
    pts = []
    for i in range(101):
        s = x0 + i * w / 100
        z = (s - K) / (w * 0.16)
        # smooth call value ~ softplus shape
        v = (w * 0.16) * math.log1p(math.exp(z)) * ((yb - (y + 20)) / (x1 - K))
        pts.append((s, yb - v))
    out.append(polyline(pts, T.accent, 2.2))
    out.append(text("K", K + 6, yb + 20, 12, T.text3, family="mono"))
    out.append(text("PAYOFF", x1, yb + 20, 11, T.text3, weight=500, family="mono", anchor="end", tracking=0.14))
    out.append(text("MODEL VALUE", x0, y + 24, 11, T.accent, weight=500, family="mono", tracking=0.14))
    return "".join(out)


def motif_code(T, x, y, w, h, lines_):
    out = [rect(x, y, w, h, T.surface, T.line2, 1, rx=10)]
    out.append(circle(x + 20, y + 20, 4.5, T.line2))
    out.append(circle(x + 36, y + 20, 4.5, T.line2))
    out.append(circle(x + 52, y + 20, 4.5, T.line2))
    ly = y + 64
    for ln in lines_:
        cx = x + 26
        for tok, kind in ln:
            col = {"kw": T.accent, "id": T.text, "num": T.up, "cm": T.text3, "op": T.text2}[kind]
            out.append(text(tok, cx, ly, 17, col, family="mono"))
            cx += measure(tok, 17, 400, "mono")
        ly += 30
    return "".join(out)


def motif_candles(T, x, y, w, h, seed=11):
    rng = random.Random(seed)
    n = 34
    cw = w / n
    p = 100.0
    cs = []
    for _ in range(n):
        o = p
        hi = lo = p
        for _ in range(5):
            p *= math.exp(rng.gauss(0.001, 0.012))
            hi, lo = max(hi, p), min(lo, p)
        cs.append((o, hi, lo, p))
    mn = min(c[2] for c in cs)
    mx = max(c[1] for c in cs)
    sy = lambda v: y + h * 0.72 - (v - mn) / (mx - mn) * h * 0.68
    out = []
    for i, (o, hi, lo, c) in enumerate(cs):
        cx = x + i * cw + cw / 2
        col = T.up if c >= o else T.down
        out.append(line(cx, sy(hi), cx, sy(lo), col, 1.2, opacity=0.9))
        top, bot = sy(max(o, c)), sy(min(o, c))
        out.append(rect(cx - cw * 0.32, top, cw * 0.64, max(bot - top, 1.5), col, rx=1, opacity=0.9))
        vol = rng.random()
        out.append(rect(cx - cw * 0.32, y + h - vol * h * 0.16, cw * 0.64, vol * h * 0.16, T.text3, opacity=0.35))
    # moving average
    closes = [c[3] for c in cs]
    ma = []
    for i in range(n):
        if i >= 6:
            ma.append((x + i * cw + cw / 2, sy(sum(closes[i - 6:i + 1]) / 7)))
    out.append(polyline(ma, T.accent, 1.8))
    return "".join(out)


def motif_detect(T, x, y, w, h, seed=4):
    """Top-down pen: tracked animals with ID boxes and motion trails."""
    rng = random.Random(seed)
    out = [rect(x, y, w, h, "none", T.line2, 1, rx=8)]
    ids = []
    for k in range(6):
        cx = x + 50 + rng.random() * (w - 100)
        cy = y + 50 + rng.random() * (h - 100)
        trail = [(cx, cy)]
        ang = rng.random() * math.tau
        for _ in range(14):
            ang += rng.gauss(0, 0.45)
            cx = min(max(cx + 9 * math.cos(ang), x + 40), x + w - 40)
            cy = min(max(cy + 9 * math.sin(ang), y + 40), y + h - 40)
            trail.append((cx, cy))
        ids.append(trail)
        flagged = k == 2
        col = T.accent if flagged else T.text2
        out.append(polyline(trail, col, 1.2, opacity=0.45))
        bw, bh = 58, 40
        ex, ey = trail[-1]
        out.append(ticks_corner(ex - bw / 2, ey - bh / 2, bw, bh, col, 8, 1.4))
        out.append(text(f"ID {k + 1:02d}", ex - bw / 2, ey - bh / 2 - 7, 11, col, weight=500, family="mono"))
        if flagged:
            out.append(text("BELOW BASELINE", ex + bw / 2 + 8, ey + 4, 11, T.accent, weight=500,
                            family="mono", tracking=0.1))
    return "".join(out)


# ------------------------------------------------------------------ card ----

def card(T, repo: str, title: str, subtitle: str, chips: list[str], motif: str,
         kicker: str = "") -> str:
    b = [_bg(T)]
    b.append(text(f"NEILGILANI / {repo.upper()}", 72, 86, 14, T.text3, weight=500, family="mono", tracking=0.16))
    if kicker:
        b.append(text(kicker.upper(), W - 72, 86, 14, T.accent, weight=500, family="mono",
                      tracking=0.16, anchor="end"))
    b.append(line(72, 106, W - 72, 106, T.line2, 1))
    # title (auto-size to fit ~560px)
    size = 84
    while measure(title, size, 600, tracking=-0.04) > 600 and size > 48:
        size -= 2
    b.append(text(title, 68, 250, size, T.text, weight=600, tracking=-0.04))
    ly = 250 + 62
    for ln in wrap(subtitle, 28, 560, 400, tracking=-0.01)[:3]:
        b.append(text(ln, 72, ly, 28, T.text2, tracking=-0.01))
        ly += 40
    # chips
    cx = 72
    for c in chips:
        cw = measure(c.upper(), 13, 500, "mono", 0.12) + 28
        b.append(rect(cx, 530, cw, 36, "none", T.line2, 1, rx=18))
        b.append(text(c.upper(), cx + 14, 553, 13, T.text2, weight=500, family="mono", tracking=0.12))
        cx += cw + 10
    b.append(motif)
    return svg_doc(W, H, "".join(b), title=title, desc=subtitle)
