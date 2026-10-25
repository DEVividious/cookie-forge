"""Draws the test templates in this directory: star, gingerbread, donut, sheet, badge, grid."""
from PIL import Image, ImageDraw, ImageFilter
import math, os, numpy as np

OUT = os.path.dirname(os.path.abspath(__file__))

def out(name):
    return os.path.join(OUT, name)

def star(n=5, r1=400, r2=170, cx=500, cy=500):
    pts=[]
    for i in range(2*n):
        r = r1 if i%2==0 else r2
        a = -math.pi/2 + i*math.pi/n
        pts.append((cx+r*math.cos(a), cy+r*math.sin(a)))
    return pts

im = Image.new("L",(1000,1000),255); d=ImageDraw.Draw(im); d.polygon(star(), fill=0); im.save(out("star.png"))

# gingerbread man: contour + details
W=14
mask = Image.new("L",(900,1200),0); dm=ImageDraw.Draw(mask)
dm.ellipse((300,60,600,360), fill=255); dm.rounded_rectangle((330,330,570,760), radius=80, fill=255)
dm.rounded_rectangle((90,380,340,520), radius=60, fill=255); dm.rounded_rectangle((560,380,810,520), radius=60, fill=255)
dm.rounded_rectangle((330,720,460,1120), radius=60, fill=255); dm.rounded_rectangle((440,720,570,1120), radius=60, fill=255)
er = mask.filter(ImageFilter.MinFilter(2*W+1))
m = np.array(mask); e = np.array(er)
res = np.full_like(m,255); res[(m>0)&(e==0)] = 0
im = Image.fromarray(res); d=ImageDraw.Draw(im)
d.ellipse((380,160,410,190), fill=0); d.ellipse((490,160,520,190), fill=0)
d.arc((390,200,510,290), 20, 160, fill=0, width=10)
for y in (450,540,630): d.ellipse((435,y,465,y+30), fill=0)
im.save(out("gingerbread.png"))

im = Image.new("L",(1000,1000),255); d=ImageDraw.Draw(im); d.ellipse((100,100,900,900), fill=0); d.ellipse((380,380,620,620), fill=255); im.save(out("donut.png"))
# sheet with three shapes: heart, circle, six-pointed star
im = Image.new("L",(1800,800),255); d=ImageDraw.Draw(im)
pts=[]
for t in np.linspace(0,2*math.pi,400):
    x=16*math.sin(t)**3; y=13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t)
    pts.append((300+x*17, 400-y*17))
d.polygon(pts, fill=0)
d.ellipse((700,150,1200,650), fill=0)
d.polygon(star(6, 200, 110, 1500, 400), fill=0)
im.save(out("sheet.png"))

# badge: contour drawing whose inner line touches the outline on both sides (for `prepare`)
im = Image.new("L",(1000,1000),255); d=ImageDraw.Draw(im)
d.ellipse((100,100,900,900), outline=0, width=24)
d.line((110,500,890,500), fill=0, width=16)
d.ellipse((470,280,530,340), fill=0)
im.save(out("badge.png"))

# grid: 2 x 2 squares of 20 mm, 0.85 mm apart (shared walls), 20 px/mm; any simplification merges them
im = Image.new("L",(1017,1017),255); d=ImageDraw.Draw(im)
for r in range(2):
    for c in range(2):
        x0, y0 = 5 + c*20.85, 5 + r*20.85
        d.rectangle([round(x0*20), round(y0*20), round((x0+20)*20)-1, round((y0+20)*20)-1], fill=0)
im.save(out("grid.png"), dpi=(508, 508))

print("ok")
