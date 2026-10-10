#!/usr/bin/env python3
"""Generate a standalone page for each panel in index.html.

index.html stays the single source of truth. This reads it, lifts the
stylesheet and each panel, and writes a real page per panel so every
section has its own address. Run it after editing index.html.
"""
import html as _html
import os
import re

SRC = "index.html"
SITE = "https://foobsontheloose.com"

# panel id -> url path (no leading slash, no extension)
SLUGS = {
    "panel-why":          "why-it-matters",
    "panel-signs":        "know-the-signs",
    "panel-screening":    "screening",
    "panel-recon":        "reconstruction",
    "panel-questions":    "questions-to-ask",
    "panel-men":          "men",
    "panel-support":      "support",
    "panel-risk":         "know-your-risk",
    "panel-about":        "about",
    "panel-follow":       "follow",
    "recon-Direct":       "reconstruction/direct-to-implant",
    "recon-TEtoIMPLANT":  "reconstruction/tissue-expander",
    "recon-DIEP":         "reconstruction/diep",
    "recon-TRAM":         "reconstruction/tram",
    "recon-PAP":          "reconstruction/pap",
    "recon-SGAP":         "reconstruction/sgap",
    "recon-IGAP":         "reconstruction/igap",
    "recon-TUG":          "reconstruction/tug",
    "recon-LAT":          "reconstruction/latissimus",
    "recon-FatGrafting":  "reconstruction/fat-grafting",
    "recon-ComboHybrid":  "reconstruction/combination",
    "recon-NippleAreola": "reconstruction/nipple-areola",
    "recon-FlatClosure":  "reconstruction/flat-closure",
}


# The photo wall only appears on one page, so only that page carries the
# overlay and the script that drives it. Without them the captions written
# for all 18 photos would sit in the markup and never be shown.
LIGHTBOX = """  <button type="button" class="lightbox" id="lightbox" aria-label="Close photo">
    <span class="lightbox-inner">
      <img id="lightbox-img" src="" alt="" />
      <span class="lightbox-cap" id="lightbox-cap"></span>
      <span class="lightbox-date" id="lightbox-date"></span>
    </span>
  </button>
  <script src="/assets/lightbox.js"></script>
"""

PAGE_CSS = """
/* ---- Standalone section pages -------------------------------------------
   Each panel also exists at its own address. These rules give that page the
   same card the modal uses, without the modal's overlay behaviour. */
.page-wrap { padding: 92px 18px 60px; position: relative; z-index: 1; }
/* The card carries .modal-card too, so it inherits that element's width,
   padding and radius at every breakpoint and cannot drift from it. These
   rules undo only the parts that exist because it is normally an overlay. */
.page-card {
  margin: 0 auto;
  transform: none;
  max-height: none;
  overflow: visible;
}
.page-card .tab-panel { display: block; }
/* Buttons that became links on the standalone pages must not pick up link
   styling: on the homepage these are pills and a back control, not text
   links, and they should look identical here. */
a.recon-opt, a.recon-back, a.tab-square, a.wall-shot, a.ribbon-link, a.panel-link.recon-opt {
  text-decoration: none;
}
a.recon-opt:hover, a.recon-back:hover { text-decoration: none; }

.page-home {
  display: block;
  max-width: 520px;
  margin: 22px auto 0;
  text-align: center;
  font-family: 'Nunito Sans', sans-serif;
  font-size: 0.95rem;
  color: var(--rose-deep);
}
"""


def slurp():
    return open(SRC, encoding="utf-8").read()


def extract_style(h):
    m = re.search(r"<style>(.*?)</style>", h, re.S)
    return m.group(1)


def extract_panel(h, pid):
    m = re.search(r'<div class="([^"]*)" id="%s"[^>]*>' % re.escape(pid), h)
    if not m:
        raise SystemExit("panel not found: " + pid)
    i, depth = m.end(), 1
    tag = re.compile(r"<(/?)div\b[^>]*>")
    while depth and i < len(h):
        t = tag.search(h, i)
        if not t:
            break
        depth += -1 if t.group(1) else 1
        i = t.end()
    return m.group(1), h[m.end():i - len("</div>")]


def text_of(frag):
    """Plain text from a fragment. Entities are decoded here so the caller can
    escape once; escaping already-escaped text gave "Screening &amp;amp; ..."."""
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", frag)).strip())


def build(pid, slug, classes, inner):
    depth = slug.count("/")
    root = "/" if depth == 0 else "/"          # absolute paths throughout

    heading = re.search(r"<h2[^>]*>(.*?)</h2>", inner, re.S)
    title = text_of(heading.group(1)) if heading else slug

    body = re.search(r'<p class="(?:recon-body|about-body|lede)"[^>]*>(.*?)</p>', inner, re.S)
    desc = text_of(body.group(1)) if body else ""
    if len(desc) > 155:
        desc = desc[:152].rsplit(" ", 1)[0] + "..."

    # the in-modal back button becomes a real link
    # the in-modal back button becomes a real link, and says where it goes:
    # in the modal "All options" is obvious from context, on its own page it is not
    inner = re.sub(
        r'<button type="button" class="recon-back" data-panel="panel-recon">.*?</button>',
        '<a class="recon-back" href="/reconstruction">&lsaquo; All reconstruction options</a>',
        inner, flags=re.S)
    # Every remaining panel trigger is a <button> that only works with the
    # modal script. On a standalone page it has to be a real link, so the
    # button becomes an <a> carrying the same classes, and its matching
    # </button> becomes </a>. Done by walking the string so nested markup
    # inside a button does not confuse the pairing.
    def buttons_to_links(frag):
        out, i = [], 0
        trigger = re.compile(r'<button\b[^>]*?data-(?:panel|goto)="([^"]+)"[^>]*>')
        closer = re.compile(r'</?button\b[^>]*>')
        while True:
            m = trigger.search(frag, i)
            if not m:
                out.append(frag[i:])
                break
            out.append(frag[i:m.start()])
            target = m.group(1)
            href = "/" + SLUGS[target] if target in SLUGS else "/"
            cls = re.search(r'class="([^"]*)"', m.group(0))
            out.append('<a class="%s" href="%s">' % (cls.group(1) if cls else "", href))
            # find this button's own closing tag, accounting for nesting
            j, depth = m.end(), 1
            while depth:
                c = closer.search(frag, j)
                if not c:
                    break
                depth += -1 if c.group(0).startswith("</") else 1
                if depth == 0:
                    out.append(frag[m.end():c.start()])
                    out.append("</a>")
                    j = c.end()
                    break
                j = c.end()
            i = j
        return "".join(out)

    inner = buttons_to_links(inner)
    # images and links resolve from any depth
    inner = inner.replace('src="images/', 'src="/images/')

    full_title = "%s \u2014 Foobs On the Loose" % title
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#C96A85">
<link rel="canonical" href="{site}/{slug}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Foobs On the Loose">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{site}/{slug}">
<meta property="og:image" content="{site}/images/share-card.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{site}/images/share-card.jpg">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,500&family=Nunito+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body class="standalone">
<nav class="sa-nav" aria-label="Sections">
  <a href="/#howto">Self-exam</a>
  <a href="/know-the-signs">Know the signs</a>
  <a href="/screening">Screening</a>
  <a href="/reconstruction">Reconstruction</a>
  <a href="/support">Support</a>
  <a href="/why-it-matters">Why it matters</a>
</nav>
<div class="page-wrap">
  <img class="trail trail--l" src="/images/trail.webp" alt="" aria-hidden="true" width="380" height="2600" />
  <img class="trail trail--r" src="/images/trail.webp" alt="" aria-hidden="true" width="380" height="2600" />
  <main class="modal-card page-card">
    <div class="{classes}">{inner}</div>
  </main>
  <a class="page-home" href="/">&larr; Foobs On the Loose</a>
</div>
{lightbox}</body>
</html>
""".format(lightbox=LIGHTBOX if 'wall-shot' in inner else "",
           title=_html.escape(full_title, quote=True),
           desc=_html.escape(desc, quote=True), site=SITE, slug=slug,
           classes=classes.replace(" recon-detail", " recon-detail"), inner=inner)


def main(only=None):
    h = slurp()
    # assets/site.css is now the stylesheet itself, shared by index.html and
    # every generated page. It is no longer produced from an inline copy, so
    # this only checks the standalone rules are still in it.
    css = open("assets/site.css", encoding="utf-8").read()
    if ".page-card" not in css:
        raise SystemExit("assets/site.css is missing the .page-card rules")
    print("assets/site.css  %d bytes (source, not regenerated)" % len(css))

    made = 0
    for pid, slug in SLUGS.items():
        if only and pid != only:
            continue
        classes, inner = extract_panel(h, pid)
        page = build(pid, slug, classes.replace(" hidden", ""), inner)
        path = slug + ".html"
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        open(path, "w", encoding="utf-8").write(page)
        print("  %-34s %6d bytes   /%s" % (path, len(page), slug))
        made += 1
    print("%d page(s)" % made)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
