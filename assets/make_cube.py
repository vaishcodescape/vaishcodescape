#!/usr/bin/env python3
"""Render a shaded, seamlessly-looping rotating ASCII cube as a GIF."""
import numpy as np, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 40, 22            # character grid
S = 46                   # samples per face edge
RAMP = " .:-=+*#%@"      # dark -> bright
FS = 15
font = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', FS)
cw = font.getlength('X'); ch = FS * 1.16
BG = (13, 17, 23)
NFR = 36
SPAN = 2 * math.pi / 3     # 120° == one full seamless loop (cube's diagonal 3-fold symmetry)

# ---- build cube surface points + normals (6 faces) ----
lin = np.linspace(-1, 1, S)
uu, vv = np.meshgrid(lin, lin)
uu = uu.ravel(); vv = vv.ravel(); one = np.ones_like(uu)
faces = [
    (np.stack([ one,  vv,  uu], 1), (1, 0, 0)),
    (np.stack([-one,  vv,  uu], 1), (-1, 0, 0)),
    (np.stack([ uu,  one,  vv], 1), (0, 1, 0)),
    (np.stack([ uu, -one,  vv], 1), (0, -1, 0)),
    (np.stack([ uu,  vv,  one], 1), (0, 0, 1)),
    (np.stack([ uu,  vv, -one], 1), (0, 0, -1)),
]
pts = np.concatenate([f[0] for f in faces], 0)
nrm = np.concatenate([np.tile(f[1], (f[0].shape[0], 1)) for f in faces], 0).astype(float)

light = np.array([0.4, 0.62, -0.78]); light /= np.linalg.norm(light)   # oblique -> 3 distinct faces
DIST, SCALE = 4.6, 34.0
cx, cy = W / 2, H / 2
yscale = SCALE * (cw / ch)

def rotx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def axis_rot(k, th):                      # Rodrigues rotation about unit axis k
    k = np.asarray(k, float); k /= np.linalg.norm(k)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)

# fixed base rotation that points the body diagonal (1,1,1) toward the camera (0,0,1),
# so a corner always faces the viewer -> three faces always visible (isometric cube).
_diag = np.array([1, 1, 1]) / math.sqrt(3)
_b = np.array([0, 0, 1.0])
_ax = np.cross(_diag, _b); _ax /= np.linalg.norm(_ax)
BASE = axis_rot(_ax, math.acos(np.dot(_diag, _b)))
VIEWTILT = rotx(0.42)                      # slight tip for depth / asymmetry

frames = []
for f in range(NFR):
    ang = SPAN * f / NFR
    R = VIEWTILT @ BASE @ axis_rot([1, 1, 1], ang)   # corner-forward spin, always 3D, loops
    p = pts @ R.T
    n = nrm @ R.T
    zc = p[:, 2] + DIST
    ooz = 1.0 / zc
    sx = (cx + SCALE * p[:, 0] * ooz).astype(int)
    sy = (cy - yscale * p[:, 1] * ooz).astype(int)
    lum = np.clip((n @ light), 0, 1)
    vis = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
    zbuf = np.full(W * H, -1e9)
    cbuf = np.zeros(W * H)            # luminance buffer
    order = np.argsort(ooz)           # far -> near, near overwrites
    sxs, sys, oozs, lums, viss = sx[order], sy[order], ooz[order], lum[order], vis[order]
    idx = sys * W + sxs
    for i in range(len(idx)):
        if not viss[i]:
            continue
        j = idx[i]
        if oozs[i] > zbuf[j]:
            zbuf[j] = oozs[i]; cbuf[j] = lums[i]
    # ---- rasterize to image ----
    IMG_W = int(W * cw) + 24
    IMG_H = int(H * ch) + 24
    layer = Image.new("RGBA", (IMG_W, IMG_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for yy in range(H):
        for xx in range(W):
            j = yy * W + xx
            if zbuf[j] <= -1e8:
                continue
            b = cbuf[j]
            bc = 0.2 + 0.8 * b                       # floor so faces always glow
            rmp = RAMP[min(len(RAMP) - 1, int(bc * len(RAMP)))]
            if rmp == " ":
                continue
            base = np.array([0x22, 0xd3, 0xee])
            col = base * (0.5 + 0.5 * b)
            col = col + (np.array([255, 255, 255]) - col) * (b ** 3) * 0.55
            color = tuple(int(min(255, c)) for c in col)
            d.text((12 + xx * cw, 12 + yy * ch), rmp, font=font, fill=color + (255,))
    glow = layer.filter(ImageFilter.GaussianBlur(2.5))
    base_img = Image.new("RGB", (IMG_W, IMG_H), BG)
    scan = Image.new("RGBA", (IMG_W, IMG_H), (0, 0, 0, 0)); sd = ImageDraw.Draw(scan)
    for yy in range(0, IMG_H, 3):
        sd.line([(0, yy), (IMG_W, yy)], fill=(0, 0, 0, 24))
    base_img.paste(glow, (0, 0), glow); base_img.paste(layer, (0, 0), layer)
    base_img.paste(scan, (0, 0), scan)
    frames.append(base_img.convert("P", palette=Image.ADAPTIVE, colors=64))

out = "/Users/avaish/vaishcodescape/assets/cube.gif"
frames[0].save(out, save_all=True, append_images=frames[1:], duration=70, loop=0, optimize=True, disposal=2)
print("saved", out, IMG_W, "x", IMG_H, "frames", NFR)
