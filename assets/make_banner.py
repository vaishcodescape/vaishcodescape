import pyfiglet, colorsys, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------- ASCII art ----------
def art(txt): 
    return [l for l in pyfiglet.figlet_format(txt, font='ansi_shadow').splitlines()]
top, bot = art("ADITYA"), art("VAISH")
def trim(rows):
    while rows and not rows[0].strip(): rows.pop(0)
    while rows and not rows[-1].strip(): rows.pop()
    return rows
top, bot = trim(top), trim(bot)
W = max(max(len(l) for l in top), max(len(l) for l in bot))
def center(rows):
    return [l + " "*(W-len(l)) for l in rows]   # left align, pad right
top, bot = center(top), center(bot)
lines = top + [" "*W] + bot          # blank separator row
H = len(lines)
sub = "> open source developer_"     # subtitle line (typed feel)

# ---------- fonts / metrics ----------
FS = 22
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', FS)
sfont = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 15)
cw = font.getlength('█')
ch = FS * 1.16
PAD = 26
IMG_W = int(W*cw + PAD*2)
IMG_H = int(H*ch + PAD*2 + 34)      # room for subtitle
BG = (13, 17, 23)                    # GitHub dark #0d1117

# ---------- cyclic neon palette (cyan -> blue -> purple) ----------
anchors = [(0x22,0xd3,0xee),(0x38,0xbd,0xf8),(0x81,0x8c,0xf8),(0xc0,0x84,0xfc),(0x81,0x8c,0xf8),(0x38,0xbd,0xf8)]
def sample(p):
    p %= 1.0
    n = len(anchors); x = p*n; i = int(x)%n; j=(i+1)%n; t=x-int(x)
    a,b = anchors[i], anchors[j]
    return tuple(int(a[k]+(b[k]-a[k])*t) for k in range(3))

NFRAMES = 24
CYCLES = 1.15
frames = []
for f in range(NFRAMES):
    phase = f/NFRAMES
    layer = Image.new("RGBA",(IMG_W,IMG_H),(0,0,0,0))
    d = ImageDraw.Draw(layer)
    for row,line in enumerate(lines):
        for col,chpix in enumerate(line):
            if chpix==" ": continue
            pp = ((col + row*0.30)/(W + H*0.30))*CYCLES + phase
            color = sample(pp)
            x = PAD + col*cw; y = PAD + row*ch
            d.text((x,y), chpix, font=font, fill=color+(255,))
    # glow = blurred copy of glyph layer under sharp layer
    glow = layer.filter(ImageFilter.GaussianBlur(3))
    base = Image.new("RGB",(IMG_W,IMG_H),BG)
    # subtle scanlines
    scan = Image.new("RGBA",(IMG_W,IMG_H),(0,0,0,0)); sd=ImageDraw.Draw(scan)
    for yy in range(0,IMG_H,3): sd.line([(0,yy),(IMG_W,yy)],fill=(0,0,0,26))
    base.paste(glow,(0,0),glow); base.paste(layer,(0,0),layer)
    base.paste(scan,(0,0),scan)
    # subtitle with blinking cursor
    d2 = ImageDraw.Draw(base)
    sy = PAD + H*ch + 6
    cursor = "" if (f//8)%2 else "█"
    d2.text((PAD, sy), sub[:-1]+ (cursor if cursor else " "), font=sfont, fill=(88,166,255))
    frames.append(base.convert("P", palette=Image.ADAPTIVE, colors=64))

out="/Users/avaish/vaishcodescape/assets/banner.gif"
frames[0].save(out, save_all=True, append_images=frames[1:], duration=90, loop=0, optimize=True, disposal=2)
print("saved", out, IMG_W,"x",IMG_H, "frames", NFRAMES)
