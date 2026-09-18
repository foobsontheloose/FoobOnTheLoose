from PIL import Image, ImageDraw, ImageFilter, ImageChops
import os

ART = "/Users/nickymurphy/Desktop/FoobOnTheLoose/images"
master = Image.open(os.path.join(ART, "bouquet.png")).convert("RGBA")


def feather(im, strength=0.15):
    """Dissolve the crop boundary so a box that slices a petal doesn't leave
    a straight edge. Also lets overlapping pieces blend into each other."""
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
    if bb:
        p = p.crop(bb)
    cut[name] = feather(p)


def cubic(p0, p1, p2, p3, steps=14):
    out = []
    for i in range(steps + 1):
        t = i / steps; u = 1 - t
        out.append((u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
                    u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]))
    return out


def heart_triangle(size, colour=(201, 106, 133, 255)):
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


W, H = 380, 1700
canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))


def place(key, cx, cy, scale, rot=0, alpha=1.0):
    im = key if isinstance(key, Image.Image) else cut[key]
    im = im.resize((max(1, int(im.width*scale)), max(1, int(im.height*scale))), Image.LANCZOS)
    if rot:
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1.0:
        im.putalpha(im.getchannel("A").point(lambda v: int(v*alpha)))
    canvas.alpha_composite(im, (int(cx - im.width/2), int(cy - im.height/2)))


# Built as dense clusters joined by runs of greenery and stems, every piece
# overlapping its neighbour, so the eye reads one continuous garland rather
# than a column of separate cut-outs. Scale falls away down the strip.
LAYOUT = [
    # --- cluster A: full and dense at the top
    ("stem",        168,  150, 0.90, -14, 0.85),
    ("bloom_big",   150,  118, 0.74, -12, 1.0),
    ("leaf_top",    258,   74, 0.82,  28, 1.0),
    ("greenery",     74,  182, 0.74, -24, 1.0),
    ("berry_left",  236,  196, 0.66,  14, 1.0),
    ("leaf_mid",    136,  236, 0.62, -32, 1.0),
    # --- bridge
    ("stem",        214,  286, 0.70,  22, 0.8),
    ("leaf_lower",  212,  292, 0.68,  18, 1.0),
    ("greenery",    118,  330, 0.58,  36, 1.0),
    # --- cluster B
    ("bloom_left",  202,  392, 0.54,  14, 1.0),
    ("leaf_top",    104,  418, 0.64, -42, 1.0),
    ("berry_right", 272,  456, 0.62, -12, 1.0),
    (heart_triangle(44), 130, 486, 1.0,  -10, 0.5),
    ("leaf_mid",    214,  512, 0.52,  24, 1.0),
    # --- bridge: stems and greenery keep the chain unbroken
    ("stem",        160,  548, 0.62, -18, 0.78),
    ("greenery",    142,  556, 0.54, -28, 1.0),
    ("leaf_lower",  238,  588, 0.56,  14, 1.0),
    ("berry_left",  150,  614, 0.48,  24, 1.0),
    # --- cluster C
    ("bloom_bud",   176,  652, 0.58,  18, 1.0),
    ("ribbon_loop", 258,  688, 0.54, -10, 0.85),
    ("leaf_top",    108,  700, 0.54,  32, 1.0),
    ("leaf_mid",    216,  736, 0.48, -20, 1.0),
    ("berry_left",  128,  762, 0.46, -16, 1.0),
    ("greenery",    226,  790, 0.46,  26, 1.0),
    # --- cluster D
    ("stem",        160,  838, 0.50,  16, 0.7),
    ("bloom_big",   146,  856, 0.42,  24, 1.0),
    ("leaf_lower",  244,  874, 0.48, -18, 1.0),
    (heart_triangle(36), 116, 912, 1.0, 8, 0.46),
    ("berry_right", 216,  926, 0.46,  10, 1.0),
    ("greenery",    140,  962, 0.44, -30, 1.0),
    ("leaf_top",    232,  996, 0.42,  28, 1.0),
    # --- cluster E
    ("ribbon_curl", 150, 1038, 0.40,  12, 0.72),
    ("bloom_bud",   232, 1066, 0.38, -20, 1.0),
    ("leaf_mid",    134, 1100, 0.38,  22, 1.0),
    ("berry_left",  216, 1132, 0.36,  14, 1.0),
    ("greenery",    146, 1160, 0.36, -24, 1.0),
    ("leaf_lower",  222, 1192, 0.34,  18, 1.0),
    # --- tapering: spacing tightens as the pieces shrink, so the density
    #     stays even and the trail thins rather than breaking up
    ("bloom_bud",   152, 1226, 0.30, -16, 1.0),
    ("leaf_top",    214, 1256, 0.30,  26, 1.0),
    (heart_triangle(28), 146, 1288, 1.0, -8, 0.42),
    ("berry_right", 206, 1312, 0.28,  20, 1.0),
    ("greenery",    152, 1342, 0.28, -18, 1.0),
    ("leaf_mid",    204, 1374, 0.26,  14, 1.0),
    ("berry_left",  158, 1404, 0.24, -12, 1.0),
    ("leaf_lower",  200, 1434, 0.24,  22, 1.0),
    ("greenery",    162, 1464, 0.22, -16, 1.0),
    ("leaf_top",    196, 1496, 0.21,  18, 1.0),
    ("berry_right", 168, 1526, 0.19,  10, 1.0),
    ("greenery",    192, 1558, 0.18, -12, 1.0),
    ("leaf_mid",    176, 1590, 0.16,  20, 1.0),
    ("berry_left",  190, 1622, 0.14,  -8, 1.0),
]

for item in LAYOUT:
    place(*item)

canvas.save(os.path.join(ART, "trail.png"))
canvas.save(os.path.join(ART, "trail.webp"), "WEBP", quality=86, method=6)
print("elements placed:", len(LAYOUT))
print("webp: {:.0f} KB".format(os.path.getsize(os.path.join(ART, "trail.webp"))/1024))

prev = Image.new("RGB", canvas.size, "#F7DCE3")
prev.paste(canvas, (0, 0), canvas)
prev.thumbnail((250, 1200))
prev.save("/private/tmp/claude-501/-Users-nickymurphy-Desktop-FoobOnTheLoose/d558efa8-a861-4932-a105-576aa129e064/scratchpad/trail-preview.png")
