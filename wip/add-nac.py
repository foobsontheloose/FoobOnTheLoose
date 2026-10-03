"""Draw a nipple-areola complex onto an illustration that was generated without one.

The image generator will draw a bare chest but leaves the nipples off, which
makes step 1 instruct the reader to look for "nipple changes" on a body that
has none. This puts them back.

Nothing is placed by eye. The mound is measured from the artist's own drawn
contours and the complex goes at its centre, biased laterally -- the midpoint
between the breast's inner and outer edges sits too far toward the sternum,
because the medial side flattens. Nicky caught that immediately the first time.

Colour is sampled from the skin directly above each site and shifted from
there, so it lands in the illustration's own palette rather than a tone picked
by hand. Structure follows images/add-areolae.py, which did the same job on the
flat-closure diagram: concentric areola passes so the edge fades instead of
ending on a line, then the nipple, then light from the upper left to match how
the rest of the drawing is lit.

`clip` takes a function x -> y and erases everything below that line, so a limb
drawn over the breast still occludes the complex. Step 4 needs it: the forearm
crosses the nipple, and without clipping the areola would float on top of the
arm.
"""
from PIL import Image, ImageDraw, ImageFilter

SS = 4  # supersample, so the soft edges survive being scaled back down


def _shade(base, dr, dg, db):
    return tuple(max(0, min(255, c + d)) for c, d in zip(base, (dr, dg, db)))


def add_nac(im, spots, clip=None):
    """spots: iterable of (cx, cy, areola_w, areola_h, nipple_w, nipple_h)."""
    W, H = im.size
    px = im.load()
    lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)

    for cx, cy, AW, AH, NW, NH in spots:
        skin = px[cx, max(0, cy - 28)]

        for s, dr, dg, db, a in ((1.00, -8, -30, -34, 100),
                                 (0.84, -13, -41, -46, 145),
                                 (0.68, -17, -50, -56, 180),
                                 (0.52, -20, -57, -63, 210)):
            w, h = AW * s, AH * s
            d.ellipse([(cx - w / 2) * SS, (cy - h / 2) * SS,
                       (cx + w / 2) * SS, (cy + h / 2) * SS],
                      fill=_shade(skin, dr, dg, db) + (a,))

        d.ellipse([(cx - NW / 2) * SS, (cy - NH / 2) * SS,
                   (cx + NW / 2) * SS, (cy + NH / 2) * SS],
                  fill=_shade(skin, -28, -72, -78) + (235,))
        d.ellipse([(cx - NW * 0.36) * SS, (cy - NH * 0.48) * SS,
                   (cx + NW * 0.04) * SS, (cy - NH * 0.02) * SS],
                  fill=_shade(skin, 10, 16, 18) + (95,))
        d.ellipse([(cx - NW * 0.06) * SS, (cy + NH * 0.04) * SS,
                   (cx + NW * 0.42) * SS, (cy + NH * 0.50) * SS],
                  fill=_shade(skin, -32, -80, -86) + (115,))

    lay = lay.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.35))

    if clip is not None:
        lp = lay.load()
        for x in range(W):
            edge = clip(x)
            if edge is None:
                continue
            for y in range(int(edge), H):
                r, g, b, a = lp[x, y]
                if a:
                    lp[x, y] = (r, g, b, 0)

    out = im.convert("RGBA")
    out.alpha_composite(lay)
    return out.convert("RGB")


def curve(points):
    """Turn sampled {x: y} into a function, for use as `clip`."""
    ks = sorted(points)

    def f(x):
        if x < ks[0] or x > ks[-1]:
            return None
        lo = max(k for k in ks if k <= x)
        hi = min(k for k in ks if k >= x)
        if lo == hi:
            return points[lo]
        return points[lo] + (points[hi] - points[lo]) * (x - lo) / (hi - lo)

    return f
