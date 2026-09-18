"""Compose the side-trail strip from the watercolour bouquet.

The trail is one tall image, mirrored for the other side. Pieces are placed
along a density curve: large and overlapping at the top, shrinking as it
descends, with the vertical step shrinking too so the density stays even and
the trail thins rather than breaking into gaps.
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

ART = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
master = Image.open(os.path.join(ART, "bouquet.png")).convert("RGBA")

W, H = 380, 2600          # tall enough to cover the hero at desktop widths
TOP_SCALE, END_SCALE = 0.78, 0.13


def feather(im, strength=0.15):
    """Dissolve the crop boundary so a box that slices a petal doesn't leave a
    straight edge, and so overlapping pieces blend into each other."""
    w, h = im.size
    f = max(8, int(min(w, h) * strength))
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle([f, f, w - f, h - f], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(f * 0.6))
    im = im.copy()
    im.putalpha(ImageChops.multiply(im.getchannel("A"), mask))
    return im


PIECES = {
    "bloom_big":   (178,   0, 470, 235),
    "bloom_left":  ( 18, 172, 338, 424),
    "bloom_bud":   (436, 168, 626, 336),
    "leaf_top":    ( 58,  26, 196, 146),
    "leaf_lower":  ( 14, 316, 128, 414),
    "leaf_mid":    (330, 236, 486, 366),
    "greenery":    (470,  16, 628, 158),
    "berry_left":  (  4, 118, 126, 240),
    "berry_right": (396, 262, 528, 352),
    "ribbon_curl": (250, 556, 470, 720),
    "ribbon_loop": (128, 396, 306, 502),
    "stem":        (296, 404, 404, 566),
}
cut = {}
for name, box in PIECES.items():
    p = master.crop(box)
    bb = p.getbbox()
    cut[name] = feather(p.crop(bb) if bb else p)


def cubic(p0, p1, p2, p3, steps=14):
    out = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        out.append((u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
                    u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]))
    return out


def heart_triangle(size, colour=(201, 106, 133, 255)):
    """Nicky's motif, the same shape as the nav bar and modal headers."""
    S = 8
    img = Image.new("RGBA", (40*S, 50*S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(20, 22)]
    pts += cubic((20, 22), (8, 14), (6, 2), (14, 2))
    pts += cubic((14, 2), (20, 2), (20, 12), (20, 22))
    pts += cubic((20, 22), (20, 12), (20, 2), (26, 2))
    pts += cubic((26, 2), (34, 2), (32, 14), (20, 22))
    d.polygon([(x*S, y*S) for x, y in pts], fill=colour)
    d.polygon([(x*S, y*S) for x, y in
               ((20, 22), (10, 48), (16, 44), (20, 48), (24, 44), (30, 48))], fill=colour)
    img = img.crop(img.getbbox())
    return img.resize((size, int(img.height * size / img.width)), Image.LANCZOS)


canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))


def place(key, cx, cy, scale, rot=0, alpha=1.0):
    im = key if isinstance(key, Image.Image) else cut[key]
    im = im.resize((max(1, int(im.width*scale)), max(1, int(im.height*scale))), Image.LANCZOS)
    if rot:
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1.0:
        im.putalpha(im.getchannel("A").point(lambda v: int(v*alpha)))
    canvas.alpha_composite(im, (int(cx - im.width/2), int(cy - im.height/2)))


rng = random.Random(7)          # fixed seed: the arrangement is reproducible

BLOOMS = ["bloom_big", "bloom_left", "bloom_bud"]
FILLERS = ["leaf_top", "leaf_mid", "leaf_lower", "greenery", "berry_left", "berry_right"]

# The densest part of the arrangement, placed by hand so the top reads as a
# full cluster rather than a sequence.
place("stem",       168,  150, 0.90, -14, 0.85)
place("bloom_big",  150,  118, 0.76, -12)
place("leaf_top",   258,   74, 0.84,  28)
place("greenery",    74,  182, 0.76, -24)
place("berry_left", 236,  196, 0.68,  14)
place("leaf_mid",   136,  236, 0.64, -32)

y = 236
i = 0
while y < H - 40:
    t = min(1.0, max(0.0, (y - 236) / (H - 286)))
    # ease the shrink so it stays generous for longer before tailing away
    scale = TOP_SCALE + (END_SCALE - TOP_SCALE) * (t ** 0.78)

    x = 190 + math.sin(y / 190.0) * 66 + rng.uniform(-26, 26)
    x = max(80, min(300, x))
    rot = rng.uniform(-34, 34)

    if i % 3 == 0:
        place(rng.choice(BLOOMS), x, y, scale, rot)
    else:
        place(rng.choice(FILLERS), x, y, scale * rng.uniform(0.86, 1.12), rot)

    # a stem every so often, threading the clusters together
    if i % 7 == 3:
        place("stem", x + rng.uniform(-30, 30), y + 44, scale * 1.1, rot * 0.5, 0.7)

    # the motif and a ribbon curl, thinning out as the trail descends
    if i % 11 == 5:
        place(heart_triangle(max(16, int(52 * scale / TOP_SCALE))),
              x + rng.uniform(-60, 60), y + 60, 1.0, rng.uniform(-14, 14), 0.5)
    if i % 13 == 9:
        place("ribbon_curl", x + rng.uniform(-40, 40), y + 70, scale * 0.85,
              rng.uniform(-18, 18), 0.72)

    # Step must stay smaller than the pieces are tall, or the trail breaks
    # into separate objects. It shrinks with the artwork so the density
    # holds steady while the flowers taper.
    y += 16 + scale * 54
    i += 1

canvas.save(os.path.join(ART, "trail.png"))
canvas.save(os.path.join(ART, "trail.webp"), "WEBP", quality=86, method=6)
print("trail: {}x{}  |  {} placements  |  {:.0f} KB".format(
    W, H, i + 6, os.path.getsize(os.path.join(ART, "trail.webp")) / 1024))
