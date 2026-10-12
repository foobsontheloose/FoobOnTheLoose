#!/usr/bin/env python3
"""Generate a standalone page for each panel in index.html.

index.html stays the single source of truth. This reads it, lifts the
stylesheet and each panel, and writes a real page per panel so every
section has its own address. Run it after editing index.html.
"""
import html as _html
import os
import re
import datetime as _dt

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
    "q-breast":           "questions-to-ask/breast-surgeon",
    "q-plastic":          "questions-to-ask/plastic-surgeon",
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


def site_footer(h):
    """The homepage's own footer, rewritten to work on a page with no script.

    These pages are where Google sends people, and until now they ended with
    a single link back to the homepage - so a woman who arrived at TRAM flap
    had no way of learning that the site also holds the questions to take to
    her surgeon, or a monthly reminder she could set. The footer is lifted
    from index.html rather than copied into this file, so it cannot drift
    from the homepage's.
    """
    foot = h[h.rindex("<footer>"):]
    foot = foot[:foot.index("</footer>") + len("</footer>")]

    # A reader who arrives from a search wants the answer, not an
    # introduction - so Foobie waits until she has had it. By the foot of the
    # page the question that brought her here is answered, and "who are these
    # people, what else is here" is finally a question she might have.
    welcome = (
        '<a class="sa-welcome" href="/" aria-label="Go to the Foobs On the Loose homepage">'
        '<span class="mascot-wrap">'
        '<img src="/images/foobie.webp" alt="" aria-hidden="true" width="408" height="470" />'
        '<span class="reg-mark" aria-hidden="true">&trade;</span>'
        '</span>'
        '<span class="sa-welcome-name">Foobs On The Loose</span>'
        '<span class="sa-welcome-home">'
        '<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
        '<path d="M3.5 11.2 12 4l8.5 7.2" stroke="currentColor" stroke-width="1.9" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        '<path d="M5.9 10.3V20h12.2v-9.7" stroke="currentColor" stroke-width="1.9" '
        'stroke-linecap="round" stroke-linejoin="round"/>'
        '</svg> Tap for more</span>'
        '</a>'
    )
    foot = foot.replace("<footer>", "<footer>\n  " + welcome, 1)

    # panel triggers become real addresses
    def panel(m):
        pid = m.group(1)
        if pid not in SLUGS:
            return m.group(0)
        return '<a class="sitemap-link" href="/%s">' % SLUGS[pid]
    foot = re.sub(r'<button type="button" class="sitemap-link" data-panel="([^"]+)">', panel, foot)

    # the reminder is built in JavaScript, which these pages do not load, so
    # it points at the calendar badge on the homepage instead
    foot = foot.replace('<button type="button" class="sitemap-link" data-cal>',
                        '<a class="sitemap-link" href="/#cal-btn">')
    foot = foot.replace("</button>", "</a>")

    # anchors on the homepage need the homepage in front of them
    foot = foot.replace('href="#', 'href="/#')
    return foot


def build(pid, slug, classes, inner):
    depth = slug.count("/")
    root = "/" if depth == 0 else "/"          # absolute paths throughout

    heading = re.search(r"<h2[^>]*>(.*?)</h2>", inner, re.S)
    title = text_of(heading.group(1)) if heading else slug

    body = re.search(r'<p class="(?:recon-body|about-body|lede)"[^>]*>(.*?)</p>', inner, re.S)
    desc = text_of(body.group(1)) if body else ""
    if len(desc) > 155:
        desc = desc[:152].rsplit(" ", 1)[0] + "..."

    # The in-modal back button becomes a real link. It reads "Back" in both
    # places so one journey has one label, and the aria-label carries the
    # destination for a screen reader, where "Back" on its own says nothing.
    # Where it goes is read off the button rather than hardcoded, because a
    # reconstruction detail goes back to /reconstruction while a question
    # list goes back to /questions-to-ask.
    def _back_link(m):
        tag = m.group(0)
        tgt = re.search(r'data-panel="([^"]+)"', tag)
        aria = re.search(r'aria-label="([^"]*)"', tag)
        href = "/" + SLUGS[tgt.group(1)] if tgt and tgt.group(1) in SLUGS else "/"
        label = ' aria-label="%s"' % aria.group(1) if aria else ""
        return ('<a class="recon-back" href="%s"%s>'
                '<span>&lsaquo; Back</span></a>') % (href, label)

    inner = re.sub(
        r'<button type="button" class="recon-back"[^>]*>.*?</button>',
        _back_link, inner, flags=re.S)
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
<link rel="icon" href="/favicon.ico" sizes="32x32">
<link rel="icon" type="image/png" sizes="32x32" href="/images/icon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/images/icon-16.png">
<link rel="apple-touch-icon" href="/images/apple-touch-icon.png">
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
<nav class="ribbon-nav" aria-label="Jump to a section">
  <button type="button" class="nav-toggle" id="nav-toggle"
          aria-expanded="false" aria-controls="ribbon-inner" aria-label="Open menu">
    <span class="nav-toggle-bars" aria-hidden="true"></span>
  </button>
  <div class="ribbon-inner" id="ribbon-inner">
    <a class="ribbon-link" href="/#howto">Self-exam</a>
    <a class="ribbon-link" href="/know-the-signs">Know the signs</a>
    <a class="ribbon-link" href="/screening">Screening</a>
    <a class="ribbon-link" href="/reconstruction">Reconstruction</a>
    <a class="ribbon-link" href="/questions-to-ask">Questions to ask</a>
    <a class="ribbon-link" href="/support">Support</a>
    <a class="ribbon-link" href="/why-it-matters">Why it matters</a>
    <a class="ribbon-link" href="/#cal-btn">Monthly reminder</a>
  </div>
</nav>
<div class="page-wrap">
  <img class="trail trail--l" src="/images/trail.webp" alt="" aria-hidden="true" width="380" height="2600" />
  <img class="trail trail--r" src="/images/trail.webp" alt="" aria-hidden="true" width="380" height="2600" />
  <main class="modal-card page-card">
    <a class="modal-close page-close" href="/" aria-label="Close and go to the homepage">&times;</a>
    <div class="{classes}">{inner}</div>
  </main>
</div>
{footer}
{lightbox}<script src="/assets/nav.js"></script>
</body>
</html>
""".format(lightbox=LIGHTBOX if 'wall-shot' in inner else "",
           footer=site_footer(slurp()),
           title=_html.escape(full_title, quote=True),
           desc=_html.escape(desc, quote=True), site=SITE, slug=slug,
           classes=classes.replace(" recon-detail", " recon-detail"), inner=inner)


def write_sitemap(paths):
    """sitemap.xml from the same SLUGS table that builds the pages.

    It used to be maintained by hand, so adding a page meant remembering to
    add it here too - and the two question lists were missed the moment they
    were built. Generating it means a page cannot exist without being
    listed. Depth sets priority: the homepage, then sections, then the
    pages beneath them.
    """
    today = _dt.date.today().isoformat()
    rows = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path in [""] + paths:
        loc = SITE + "/" + path
        priority = "1.0" if path == "" else ("0.9" if "/" not in path else "0.8")
        rows += ["  <url>",
                 "    <loc>%s</loc>" % loc,
                 "    <lastmod>%s</lastmod>" % today,
                 "    <changefreq>monthly</changefreq>",
                 "    <priority>%s</priority>" % priority,
                 "  </url>"]
    rows.append("</urlset>")
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(rows) + "\n")
    print("  sitemap.xml%s%d URLs" % (" " * 26, len(paths) + 1))


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
    # Only a full build knows the whole set, so a single-page rebuild leaves
    # the sitemap alone rather than truncating it to one URL.
    if not only:
        write_sitemap(list(SLUGS.values()))


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else None)
