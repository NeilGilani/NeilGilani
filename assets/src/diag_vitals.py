"""Vitals (repo: aquaai): camera-only livestock monitoring pipeline, from src/vitals."""
import sys
from diagram import Diagram
from svgkit import DARK, LIGHT, text, rect, line, measure


def tag(d, x, y, label, measured):
    T = d.T
    col = T.accent if measured else T.text3
    w = measure(label, 10.5, 500, "mono", 0.06) + 18
    d.raw("label", rect(x, y, w, 18, "none", col, 1, rx=9))
    d.raw("label", text(label, x + 8, y + 12.6, 10.5, col, weight=500, family="mono", tracking=0.06))


def build(T):
    d = Diagram(T, 1200, 560, title="Vitals pipeline",
                desc="Ordinary camera to YOLO11 detection, custom tracking, optional coat-pattern identity, "
                     "rule-based behaviour, daily per-animal features, a per-animal baseline, and explained alerts. "
                     "Perception is measured on small public datasets; illness detection is validated in simulation only.")
    d.background()
    d.heading("VITALS · CAMERA-ONLY LIVESTOCK MONITORING · src/vitals",
              "From pixels to an explained alert, with each stage marked measured or simulated.")

    W, H, gap, x0 = 252, 138, 30, 36
    xs = [x0 + i * (W + gap) for i in range(4)]
    y1, y2 = 140, 356
    d.group(24, y1 - 16, 1152, H + 32, "Perception")
    d.group(24, y2 - 16, 1152, H + 32, "Decision")

    cam = d.node(xs[0], y1, W, H, "Camera", ["webcam · phone · RTSP", "sampled at 4 fps", "reconnects with backoff"])
    det = d.node(xs[1], y1, W, H, "Detect", ["YOLO11 segmentation", "fine-tuned pig + broiler", "tiled crops for flocks"], accent=True)
    trk = d.node(xs[2], y1, W, H, "Track", ["IoU + constant velocity", "centroid fallback", "speed in body-lengths/s"])
    ide = d.node(xs[3], y1, W, H, "Identify", ["cattle coat descriptor", "one-to-one assignment", "opt-in; pigs use tags"], accent=True)

    beh = d.node(xs[0], y2, W, H, "Behaviour", ["lying · standing · moving", "feeding · drinking (zones)", "3-sample hysteresis"])
    fea = d.node(xs[1], y2, W, H, "Daily features", ["12 per animal per day", "8 behavioural", "4 clinical signs"])
    brn = d.node(xs[2], y2, W, H, "Baseline", ["own 14-day median / MAD", "Mahalanobis + CUSUM drift", "herd-relative check"], accent=True)
    alr = d.node(xs[3], y2, W, H, "Explained alert", ["which signs moved, how far", "webhook · shell · console", "differential: 6 conditions"])

    for a, b in ((cam, det), (det, trk), (trk, ide), (beh, fea), (fea, brn), (brn, alr)):
        d.edge([a["r"], b["l"]])
    # snake from Identify down to Behaviour
    my = (y1 + H + y2) / 2 + 2
    d.edge([(ide["b"][0], ide["b"][1]), (ide["b"][0], my), (beh["t"][0], my), (beh["t"][0], beh["t"][1])])

    tag(d, det["x"] + 16, y1 + H - 32, "MEASURED · 85.5% / 80.6% RECALL", True)
    tag(d, ide["x"] + 16, y1 + H - 32, "MEASURED · 78% RANK-1, 46 COWS", True)
    tag(d, brn["x"] + 16, y2 + H - 32, "SIMULATION ONLY", False)
    d.note(36, 538, "Held-out recall on small public datasets (pigs 47/55, broilers 660/819). 15 fps on a 4-vCPU box without a GPU. Never run on a farm.", 11.5)
    return d.render()


if __name__ == "__main__":
    out = sys.argv[1]
    for T in (DARK, LIGHT):
        open(f"{out}/vitals-pipeline-{T.name}.svg", "w").write(build(T))
    print("ok")
