from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import os

ROOT="/Users/nickymurphy/Desktop/FoobOnTheLoose"
F=os.path.join(os.path.dirname(os.path.abspath(__file__)),"fonts")
W,H=1200,630
PAPER=(251,243,242); INK=(92,58,69); ROSE=(232,160,180); DEEP=(201,106,133)
card=Image.new("RGB",(W,H),PAPER)

def grad(size, stops, horizontal=True):
    w,h=size; m=Image.new("L",(w,h)); px=m.load()
    n=w if horizontal else h
    vals=[]
    for i in range(n):
        t=i/(n-1); a=stops[-1][1]
        for k in range(len(stops)-1):
            t0,a0=stops[k]; t1,a1=stops[k+1]
            if t<=t1:
                a=a0 if t<=t0 else a0+(a1-a0)*(t-t0)/(t1-t0); break
        vals.append(int(max(0,min(1,a))*255))
    for y in range(h):
        for x in range(w):
            px[x,y]=vals[x if horizontal else y]
    return m


def flourish(width, rose=(232,160,180), deep=(201,106,133), opacity=0.9):
    """The page's brand-flourish: two sweeps meeting at a petal. viewBox 0 0 120 22."""
    SS=6; sc=width/120.0*SS
    w=int(120*sc)+2; h=int(22*sc)+2
    im=Image.new("RGBA",(w,h),(0,0,0,0)); dr=ImageDraw.Draw(im)
    def bez(p0,p1,p2,p3,n=160):
        pts=[]
        for i in range(n+1):
            t=i/n; u=1-t
            x=u*u*u*p0[0]+3*u*u*t*p1[0]+3*u*t*t*p2[0]+t*t*t*p3[0]
            y=u*u*u*p0[1]+3*u*u*t*p1[1]+3*u*t*t*p2[1]+t*t*t*p3[1]
            pts.append((x*sc,y*sc))
        return pts
    lw=max(1,int(round(1.6*sc)))
    for pts in (bez((6,14),(30,4),(44,4),(56,11)), bez((114,14),(90,4),(76,4),(64,11))):
        dr.line(pts, fill=rose+(255,), width=lw, joint="curve")
        for c in (pts[0],pts[-1]):
            dr.ellipse([c[0]-lw/2,c[1]-lw/2,c[0]+lw/2,c[1]+lw/2], fill=rose+(255,))
    petal=bez((60,4),(55,8),(55,14),(60,17))+bez((60,17),(65,14),(65,8),(60,4))
    dr.polygon(petal, fill=deep+(255,))
    im=im.resize((int(w/SS),int(h/SS)), Image.LANCZOS)
    a=im.split()[3].point(lambda v:int(v*opacity)); im.putalpha(a)
    return im

# --- side trails, the page's garland ---
def trail(width, flip=False, opacity=0.72):
    t=Image.open(os.path.join(ROOT,"images/trail.webp")).convert("RGBA")
    t=t.crop((0,0,t.width,1170))                       # the full, dense top stretch
    h=round(t.height*width/t.width)
    t=t.resize((width,h), Image.LANCZOS)
    t=t.crop((0,0,width,H))
    if flip: t=t.transpose(Image.FLIP_LEFT_RIGHT)
    # fade the inner edge away, and both ends, so it emerges rather than starts
    inner=grad((width,H), [(0.0,1.0),(0.42,1.0),(0.78,0.45),(1.0,0.0)], horizontal=True)
    if flip: inner=inner.transpose(Image.FLIP_LEFT_RIGHT)
    ends=grad((width,H), [(0.0,0.0),(0.07,0.85),(0.30,1.0),(0.72,1.0),(0.93,0.5),(1.0,0.0)], horizontal=False)
    m=ImageChops.multiply(inner,ends)
    a=ImageChops.multiply(t.split()[3], m).point(lambda v:int(v*opacity))
    t.putalpha(a)
    t=ImageEnhance.Color(t).enhance(0.76)
    return t.filter(ImageFilter.GaussianBlur(0.5))

TW=196
lt=trail(TW); rt=trail(TW, flip=True)
card.paste(lt,(-16,0),lt)
card.paste(rt,(W-TW+16,0),rt)

# --- Foobie + words, grouped and centred together ---
fo=Image.open(os.path.join(ROOT,"images/foobie.webp")).convert("RGBA")
FW=268; fo=fo.resize((FW, round(fo.height*FW/fo.width)), Image.LANCZOS)

d0=ImageDraw.Draw(card)
f_mark=ImageFont.truetype(os.path.join(F,"fraunces-italic700.ttf"), 94)
f_otl =ImageFont.truetype(os.path.join(F,"fraunces-italic600.ttf"), 41)
f_tag =ImageFont.truetype(os.path.join(F,"fraunces-italic700.ttf"), 35)
f_sub =ImageFont.truetype(os.path.join(F,"nunito-800.ttf"), 29)

lines=[("Foobs",f_mark),("On The Loose",f_otl),("Feel It on the First",f_tag),
       ("Know your normal.",f_sub),("Know your options.",f_sub)]
textw=max(d0.textlength(t,font=f) for t,f in lines)

GAP=46
groupw=FW+GAP+textw
GX=(W-groupw)/2
FX=int(GX); FY=(H-fo.height)//2 + 2

sh=Image.new("RGBA",(fo.width+80,fo.height+80),(0,0,0,0))
sh.paste(Image.new("RGBA",fo.size,(92,58,69,52)),(40,52),fo)
sh=sh.filter(ImageFilter.GaussianBlur(17))
card.paste(sh,(FX-40,FY-40),sh)
card.paste(fo,(FX,FY),fo)

d=ImageDraw.Draw(card)

def tracked(draw, cx, y, text, font, fill, track):
    wdt=sum(draw.textlength(ch,font=font)+track for ch in text)-track
    x=cx-wdt/2
    for ch in text:
        draw.text((x,y),ch,font=font,fill=fill); x+=draw.textlength(ch,font=font)+track
    return wdt

f_pur=ImageFont.truetype(os.path.join(F,"nunito-800.ttf"), 24)
tracked(d, W/2, 52, "BREAST HEALTH & EARLY DETECTION", f_pur, DEEP, 3.4)

X=int(GX+FW+GAP)

# the block is Foobs / On The Loose / flourish, centred on Foobie's own middle
fl=flourish(168)
h_mark = f_mark.getbbox("Foobs")[3] - f_mark.getbbox("Foobs")[1]
GAP1, GAP2 = 30, 26                      # Foobs -> On The Loose -> flourish
w_otl  = d.textlength("On The Loose", font=f_otl)
h_otl  = f_otl.getbbox("On The Loose")[3] - f_otl.getbbox("On The Loose")[1]
block_h = h_mark + GAP1 + h_otl + GAP2 + fl.height

foobie_mid = FY + fo.height/2
y = foobie_mid - block_h/2 - f_mark.getbbox("Foobs")[1] + 22

d.text((X+2,y+3),"Foobs",font=f_mark,fill=(255,255,255))
d.text((X,y),  "Foobs",font=f_mark,fill=DEEP)
y += h_mark + GAP1
d.text((X,y),"On The Loose",font=f_otl,fill=INK)
y += h_otl + GAP2
card.paste(fl,(int(X + (w_otl - fl.width)/2), int(y)), fl)   # centred under On The Loose

f_cta =ImageFont.truetype(os.path.join(F,"fraunces-italic700.ttf"), 37)
f_cta2=ImageFont.truetype(os.path.join(F,"nunito-800.ttf"), 27)
cta="Your hands. Your health. Your power."
cw=d.textlength(cta,font=f_cta)
d.text(((W-cw)/2, H-132), cta, font=f_cta, fill=INK)
tracked(d, W/2, H-74, "FEEL IT ON THE FIRST", f_cta2, DEEP, 3.0)

out=os.path.join(os.path.dirname(os.path.abspath(__file__)),"share-card-v2.png")
card.save(out); print(out, card.size, "%d KB"%(os.path.getsize(out)/1024))
