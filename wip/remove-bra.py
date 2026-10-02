"""Remove the bra from a step illustration, keeping the artist's own lines.

Work in progress. Run on images/step-1.webp it produces wip/step-1-bare-wip.png,
which Nicky judged "ok but not great" on 2026-10-01 -- good enough to keep, not
good enough to publish. Parked here so the method is not lost.

What it does, and why it works at all: the illustrator drew the bra cups
following the breast, so the garment's own boundary is the anatomy. Nothing is
invented.

  - the cup's lower edge, detected as the darker stroke inside the fabric,
    becomes the inframammary fold
  - the cup's outer edge becomes the line separating breast from arm
  - the areola goes at the centroid of the mound, which is the fabric above the
    fold with the strap excluded -- placing it by eye put both nipples too far
    toward the middle
  - the areola tone (224,165,155) and line colour (188,138,131) are sampled
    from step-3.jpg, the one topless illustration in the set, so the palette is
    this illustrator's rather than a guess

Lessons that cost a pass each:
  - masking by colour alone catches every dark outline in the picture: lips,
    eyes, hair. Restrict to the garment's region.
  - masking by hue catches the body's own contour line, which erases parts of
    the silhouette. Mask the fabric FILL, then grow it to swallow its outline.
  - "background" must be flood-filled from the corners. Testing pixels for
    paleness misreads skin-adjacent pixels and leaves pale wedges where the
    band met the torso.

Still wrong at 3x: faint strap stubs at the shoulder line, and the two outer
contours read slightly broken. Steps 2, 4 and 5 are harder -- raised arms make
the cup edge a poorer guide to the fold, a hand crosses one breast, and callout
lines land on the fabric.
"""
from PIL import Image, ImageFilter, ImageDraw, ImageChops
from collections import deque
import statistics, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "images/step-1.webp"
OUT = sys.argv[2] if len(sys.argv) > 2 else "wip/step-1-bare-wip.png"

SKIN = (242, 196, 185)
AREOLA = (224, 165, 155)      # sampled from step-3.jpg
LINE = (188, 138, 131)        # ditto
BRA = (201, 150, 153)

im = Image.open(SRC).convert("RGB")
W, H = im.size
px = im.load()

# --- true background, flood-filled from the corners -------------------------
bg = Image.new("L", (W, H), 0)
bgp = bg.load()
seed = px[2, 2]
q = deque([(0, 0), (W - 1, 0), (0, H - 1), (W - 1, H - 1)])
seen = set()
while q:
    x, y = q.popleft()
    if (x, y) in seen or not (0 <= x < W and 0 <= y < H):
        continue
    seen.add((x, y))
    if sum(abs(px[x, y][i] - seed[i]) for i in range(3)) > 26:
        continue
    bgp[x, y] = 255
    q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
body = ImageChops.invert(bg)


def fabric(x0, x1, y0, y1):
    f = Image.new("L", (W, H), 0)
    fp = f.load()
    for x in range(x0, min(x1, W)):
        for y in range(y0, min(y1, H)):
            c = px[x, y]
            if sum((c[i] - BRA[i]) ** 2 for i in range(3)) < 44 ** 2:
                fp[x, y] = 255
    return f.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))


front = fabric(210, 402, 238, 414)
fp = front.load()
back = fabric(410, W, 300, H)

# --- the artist's cup edge becomes the fold ---------------------------------
raw = {}
for x in range(238, 384):
    ys = [y for y in range(330, 400) if sum(px[x, y]) < 430 and px[x, y][0] < 195]
    if ys:
        raw[x] = statistics.median(ys)
known = sorted(raw)
fold = {}
for x in range(known[0], known[-1] + 1):
    if x in raw:
        fold[x] = raw[x]
    else:
        lo = max(k for k in known if k <= x)
        hi = min(k for k in known if k >= x)
        fold[x] = raw[lo] if lo == hi else raw[lo] + (raw[hi] - raw[lo]) * (x - lo) / (hi - lo)
xs = sorted(fold)
sm = {x: sum(fold[xs[j]] for j in range(max(0, i - 5), min(len(xs), i + 6)))
         / len(range(max(0, i - 5), min(len(xs), i + 6)))
      for i, x in enumerate(xs)}


def outer(lo, hi, side):
    pts = []
    for y in range(332, 377):
        row = [x for x in range(lo, hi) if fp[x, y] and y < fold.get(x, 1e9) - 1]
        if row:
            pts.append((min(row) if side == "L" else max(row), y))
    return [(sum(pts[j][0] for j in range(max(0, i - 4), min(len(pts), i + 5)))
             / len(range(max(0, i - 4), min(len(pts), i + 5))), y)
            for i, (x, y) in enumerate(pts)]


def centre(lo, hi):
    pts = [(x, y) for x in range(lo, hi) for y in range(322, 414)
           if fp[x, y] and y < fold.get(x, 1e9) - 1]
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


L_edge, R_edge = outer(210, 308, "L"), outer(310, 402, "R")
centres = (centre(210, 308), centre(310, 402))

# --- fill the garment, clipped to the body ---------------------------------
out = im.copy()
op = out.load()
for msk, (x0, x1, y0, y1) in ((front, (208, 404, 236, 416)), (back, (408, W, 298, H))):
    g = ImageChops.multiply(msk.filter(ImageFilter.MaxFilter(9)), body)
    gp = g.load()
    for x in range(x0, min(x1, W)):
        for y in range(y0, min(y1, H)):
            if gp[x, y]:
                op[x, y] = SKIN

# --- redraw fold and outer contours, supersampled so they antialias ---------
big = out.resize((W * 3, H * 3), Image.LANCZOS)
d = ImageDraw.Draw(big)
pts = [(x * 3, sm[x] * 3) for x in xs]
for seg in ([p for p in pts if p[0] <= 306 * 3], [p for p in pts if p[0] >= 316 * 3]):
    if len(seg) > 3:
        d.line(seg, fill=LINE, width=3, joint="curve")
for e in (L_edge, R_edge):
    if len(e) > 3:
        d.line([(x * 3, y * 3) for x, y in e], fill=LINE, width=3, joint="curve")
out = big.resize((W, H), Image.LANCZOS)

# --- areolae, concentric passes for a soft edge -----------------------------
lay = Image.new("RGBA", (W * 4, H * 4), (0, 0, 0, 0))
dl = ImageDraw.Draw(lay)
for cx, cy in centres:
    for s, a in ((1.00, 70), (0.82, 110), (0.64, 150), (0.46, 185)):
        w, h = 23 * s, 20 * s
        dl.ellipse([(cx - w / 2) * 4, (cy - h / 2) * 4,
                    (cx + w / 2) * 4, (cy + h / 2) * 4], fill=AREOLA + (a,))
lay = lay.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.6))
out = out.convert("RGBA")
out.alpha_composite(lay)
out.convert("RGB").save(OUT)
print("written %s   areolae at %s" % (OUT, [(round(c[0]), round(c[1])) for c in centres]))
