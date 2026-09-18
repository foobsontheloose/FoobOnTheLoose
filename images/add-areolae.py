"""Add nipple-areola complexes to the 'before surgery' panel.

The illustration is lit from the upper left, so each areola is shaded to match:
slightly lighter on its upper-left, deeper on its lower-right, with a soft
edge rather than a drawn outline, which is how the rest of the artwork reads.
"""
from PIL import Image, ImageDraw, ImageFilter

# Always read the untouched base, never the output - otherwise re-running
# this would composite a second set of areolae on top of the first.
SRC = "/Users/nickymurphy/Desktop/FoobOnTheLoose/images/recon-flatclosure-base.jpg"
OUT = "/Users/nickymurphy/Desktop/FoobOnTheLoose/images/recon-flatclosure.jpg"

im = Image.open(SRC).convert("RGB")
SS = 4  # supersample, so the soft edges are smooth once scaled back down

# apex of each breast mound, from the gridded reference
BREASTS = [(53, 248), (191, 248)]
AREOLA_W, AREOLA_H = 25, 23
NIPPLE_W, NIPPLE_H = 8, 7


def shade(base, dr, dg, db):
    return tuple(max(0, min(255, c + d)) for c, d in zip(base, (dr, dg, db)))


layer = Image.new("RGBA", (im.width * SS, im.height * SS), (0, 0, 0, 0))
d = ImageDraw.Draw(layer)
px = im.load()

for cx, cy in BREASTS:
    skin = px[cx, cy]

    # Areola: a touch deeper and browner than the surrounding skin, built in
    # a few concentric passes so it fades outward instead of ending on a line.
    for i, (scale, dr, dg, db, alpha) in enumerate((
        (1.00, -6, -26, -22, 90),
        (0.86, -10, -36, -30, 130),
        (0.70, -13, -44, -37, 165),
        (0.54, -15, -50, -42, 195),
    )):
        w, h = AREOLA_W * scale, AREOLA_H * scale
        col = shade(skin, dr, dg, db) + (alpha,)
        d.ellipse([(cx - w / 2) * SS, (cy - h / 2) * SS,
                   (cx + w / 2) * SS, (cy + h / 2) * SS], fill=col)

    # Nipple, seated centrally and a little deeper again.
    nw, nh = NIPPLE_W, NIPPLE_H
    d.ellipse([(cx - nw / 2) * SS, (cy - nh / 2) * SS,
               (cx + nw / 2) * SS, (cy + nh / 2) * SS],
              fill=shade(skin, -18, -58, -48) + (215,))

    # Lighting: the sheet is lit from the upper left throughout.
    d.ellipse([(cx - nw * 0.34) * SS, (cy - nh * 0.46) * SS,
               (cx + nw * 0.02) * SS, (cy - nh * 0.04) * SS],
              fill=shade(skin, 6, 10, 12) + (80,))
    d.ellipse([(cx - nw * 0.08) * SS, (cy + nh * 0.02) * SS,
               (cx + nw * 0.40) * SS, (cy + nh * 0.48) * SS],
              fill=shade(skin, -22, -64, -54) + (95,))

layer = layer.resize(im.size, Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.5))
out = im.convert("RGBA")
out.alpha_composite(layer)
out.convert("RGB").save(OUT, quality=86, optimize=True)

# side-by-side detail of the panel, before and after, enlarged
box = (10, 170, 240, 310)
before = im.crop(box); after = Image.open(OUT).crop(box)
cmp = Image.new("RGB", (before.width * 2 + 16, before.height), "white")
cmp.paste(before, (0, 0)); cmp.paste(after, (before.width + 16, 0))
cmp = cmp.resize((cmp.width * 3, cmp.height * 3), Image.LANCZOS)
cmp.save("/private/tmp/claude-501/-Users-nickymurphy-Desktop-FoobOnTheLoose/d558efa8-a861-4932-a105-576aa129e064/scratchpad/flat-compare.png")
print("written: before (left) / after (right)")
