#!/usr/bin/env python3
"""THE WORLD IN ONE PAGE - 21 November 2026.

Renders a one-page newspaper front page that sums up the world news of
Saturday 21 November 2026 into a single 1024x1024 PNG. Pure Python
standard library: the picture is drawn at 2048x2048 (2x supersample)
with flat, saturated shapes and a hand-built 5x7 pixel font, then
box-downscaled to 1024x1024 so every edge and letter stays sharp.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   (writes out/entry.png)
"""

import os
import struct
import zlib

SS = 2                 # supersample factor
W = 1024 * SS          # render width  (2048)
H = 1024 * SS          # render height (2048)


# ---------------------------------------------------------------- canvas
class Canvas:
    """A flat RGB pixel buffer with simple saturated-shape primitives."""

    def __init__(self, w, h, color):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(color) * (w * h))

    def _span(self, x0, x1, y, color):
        if y < 0 or y >= self.h:
            return
        x0 = max(0, x0)
        x1 = min(self.w - 1, x1)
        if x1 < x0:
            return
        row = y * self.w * 3
        a = row + x0 * 3
        b = row + (x1 + 1) * 3
        self.buf[a:b] = bytes(color) * (x1 - x0 + 1)

    def rect(self, x, y, w, h, color):
        for yy in range(int(y), int(y + h)):
            self._span(int(x), int(x + w) - 1, yy, color)

    def circle(self, cx, cy, r, color):
        r = int(r)
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self._span(int(cx) - dx, int(cx) + dx, int(cy) + dy, color)

    def ring(self, cx, cy, r, thick, color):
        r = int(r)
        inner = max(0, r - int(thick))
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            if abs(dy) <= inner:
                di = int((inner * inner - dy * dy) ** 0.5)
                self._span(int(cx) - dx, int(cx) - di - 1, int(cy) + dy, color)
                self._span(int(cx) + di + 1, int(cx) + dx, int(cy) + dy, color)
            else:
                self._span(int(cx) - dx, int(cx) + dx, int(cy) + dy, color)

    def poly(self, pts, color):
        ys = [p[1] for p in pts]
        y0, y1 = int(min(ys)), int(max(ys))
        n = len(pts)
        for yy in range(y0, y1 + 1):
            nodes = []
            for i in range(n):
                x1, yy1 = pts[i]
                x2, yy2 = pts[(i + 1) % n]
                if (yy1 <= yy < yy2) or (yy2 <= yy < yy1):
                    nodes.append(x1 + (yy - yy1) * (x2 - x1) / (yy2 - yy1))
            nodes.sort()
            for i in range(0, len(nodes) - 1, 2):
                self._span(int(nodes[i]), int(nodes[i + 1]), yy, color)

    def line(self, x1, y1, x2, y2, thick, color):
        steps = max(1, int(max(abs(x2 - x1), abs(y2 - y1)) / max(1, thick // 2)))
        r = thick / 2
        for i in range(steps + 1):
            t = i / steps
            self.circle(x1 + (x2 - x1) * t, y1 + (y2 - y1) * t, r, color)

    def tri(self, x1, y1, x2, y2, x3, y3, color):
        self.poly([(x1, y1), (x2, y2), (x3, y3)], color)


def save_png(canvas, path):
    """Write the canvas as a PNG, box-downscaled by SS to 1024x1024."""
    sw, sh = canvas.w // SS, canvas.h // SS
    src = canvas.buf
    stride = canvas.w * 3
    raw = bytearray()
    for oy in range(sh):
        rows = []
        for k in range(SS):
            off = (oy * SS + k) * stride
            rows.append(src[off:off + stride])
        out = bytearray(sw * 3)
        for ox in range(sw):
            base = ox * SS * 3
            r = g = b = 0
            for row in rows:
                for k in range(SS):
                    i = base + k * 3
                    r += row[i]
                    g += row[i + 1]
                    b += row[i + 2]
            n = SS * SS
            j = ox * 3
            out[j] = r // n
            out[j + 1] = g // n
            out[j + 2] = b // n
        raw.append(0)
        raw += out

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", sw, sh, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# ------------------------------------------------------------------ font
# Hand-built 5x7 pixel font. Every glyph is 7 rows of 5 pixels.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "2": (".###.", "#...#", "....#", "..##.", ".#...", "#....", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": (".##..", ".##..", ".#...", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "..##.", "..#..", ".....", "..#.."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#.###"),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    "\u2022": (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
}


def text_w(s, scale, tracking=1):
    return len(s) * (5 + tracking) * scale - tracking * scale


def draw_text(cv, x, y, s, scale, color, tracking=1):
    """Draw one line of text with its top-left corner at (x, y)."""
    s = s.upper().replace("\u2019", "'").replace("\u2013", "-")
    cx = int(x)
    for ch in s:
        glyph = FONT.get(ch, FONT[" "])
        for r, row in enumerate(glyph):
            for c, px in enumerate(row):
                if px == "#":
                    cv.rect(cx + c * scale, int(y) + r * scale, scale, scale, color)
        cx += (5 + tracking) * scale
    return cx


def wrap(s, scale, max_w, tracking=1):
    """Greedy word wrap: returns a list of lines that fit max_w."""
    words = s.split()
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if text_w(trial, scale, tracking) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def draw_block(cv, x, y, s, scale, color, max_w, line_h, tracking=1, max_lines=3):
    lines = wrap(s, scale, max_w, tracking)[:max_lines]
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * line_h, ln, scale, color, tracking)
    return len(lines)

# --------------------------------------------------------------- palette
PAPER = (247, 242, 228)
INK = (16, 22, 38)
RED = (214, 4, 41)
NAVY = (23, 42, 84)
SKY = (58, 134, 255)
TEAL = (6, 148, 148)
ORANGE = (244, 96, 54)
GOLD = (255, 183, 3)
GREEN = (32, 160, 60)
DARKGREEN = (14, 110, 60)
PURPLE = (94, 44, 160)
PINK = (232, 64, 128)
GRAY = (96, 104, 120)
LIGHT = (255, 255, 255)
BLACK = (8, 10, 16)
BROWN = (146, 90, 32)
SAND = (240, 200, 120)


# ---------------------------------------------------------------- scenes
# Every scene paints inside the box (x, y, w, h) it is given.
def sc_bahrain(cv, x, y, w, h):
    """Night sky, missile trails and fires over a coastal base (hero)."""
    cv.rect(x, y, w, h * 0.72, (10, 16, 44))
    cv.rect(x, y + h * 0.72, w, h * 0.28, (16, 64, 110))
    for sx, sy, sr in ((0.12, 0.2, 3), (0.3, 0.12, 2), (0.55, 0.22, 3),
                       (0.72, 0.1, 2), (0.88, 0.3, 3), (0.42, 0.34, 2)):
        cv.circle(x + w * sx, y + h * sy, sr * SS, LIGHT)
    cv.circle(x + w * 0.9, y + h * 0.16, 13 * SS, (245, 240, 200))
    cv.circle(x + w * 0.885, y + h * 0.14, 12 * SS, (10, 16, 44))
    for mx, my in ((0.16, 0.6), (0.3, 0.66), (0.46, 0.58)):
        cv.line(x + w * (mx + 0.22), y + h * 0.08, x + w * mx, y + h * my,
                3 * SS, (255, 210, 120))
        cv.circle(x + w * mx, y + h * my, 5 * SS, GOLD)
    cv.rect(x, y + h * 0.66, w, h * 0.08, BLACK)
    for bx in (0.06, 0.2, 0.62, 0.78):
        cv.rect(x + w * bx, y + h * 0.56, w * 0.1, h * 0.12, BLACK)
    for fx, fs in ((0.13, 1.0), (0.3, 0.7), (0.68, 0.9), (0.83, 0.6)):
        cx, by = x + w * fx, y + h * 0.68
        cv.tri(cx - 9 * SS * fs, by, cx + 9 * SS * fs, by, cx, by - 30 * SS * fs, ORANGE)
        cv.tri(cx - 5 * SS * fs, by, cx + 5 * SS * fs, by, cx, by - 19 * SS * fs, GOLD)
        cv.circle(cx, by - 34 * SS * fs, 6 * SS * fs, (70, 70, 80))


def sc_kryvyi(cv, x, y, w, h):
    """Apartment block under a missile streak, smoke rising."""
    cv.rect(x, y, w, h, (70, 84, 110))
    cv.line(x + w * 0.85, y + h * 0.06, x + w * 0.42, y + h * 0.5, 4 * SS, (255, 220, 150))
    cv.circle(x + w * 0.4, y + h * 0.52, 7 * SS, ORANGE)
    bx, by, bw, bh = x + w * 0.14, y + h * 0.3, w * 0.42, h * 0.7
    cv.rect(bx, by, bw, bh, (38, 42, 56))
    for r in range(3):
        for c in range(3):
            col = GOLD if (r * 3 + c) % 3 else (20, 24, 34)
            if r == 1 and c == 1:
                col = (90, 96, 110)
            cv.rect(bx + bw * (0.12 + 0.3 * c), by + bh * (0.12 + 0.3 * r),
                    bw * 0.16, bh * 0.16, col)
    cv.circle(bx + bw * 0.5, by - h * 0.04, 10 * SS, (120, 124, 136))
    cv.circle(bx + bw * 0.66, by - h * 0.1, 13 * SS, (140, 144, 156))
    cv.rect(x + w * 0.66, y + h * 0.44, w * 0.24, h * 0.56, (48, 54, 70))


def sc_mexico(cv, x, y, w, h):
    """Desert sun, sierra and a sheriff star: a most-wanted capture."""
    cv.rect(x, y, w, h, (250, 176, 92))
    cv.circle(x + w * 0.82, y + h * 0.24, 11 * SS, (255, 226, 120))
    cv.poly([(x, y + h * 0.62), (x + w * 0.3, y + h * 0.3),
             (x + w * 0.55, y + h * 0.62)], (168, 108, 62))
    cv.poly([(x + w * 0.45, y + h * 0.62), (x + w * 0.75, y + h * 0.36),
             (x + w, y + h * 0.62)], (146, 90, 48))
    cv.rect(x, y + h * 0.62, w, h * 0.38, SAND)
    cx, cy = x + w * 0.3, y + h * 0.78
    for a in range(5):
        import math
        ang = -math.pi / 2 + a * 2 * math.pi / 5
        cv.tri(cx, cy, cx + 15 * SS * math.cos(ang - 0.32), cy + 15 * SS * math.sin(ang - 0.32),
               cx + 15 * SS * math.cos(ang + 0.32), cy + 15 * SS * math.sin(ang + 0.32), GOLD)
    cv.circle(cx, cy, 5 * SS, BROWN)
    gx = x + w * 0.78
    cv.rect(gx, y + h * 0.6, 4 * SS, h * 0.34, DARKGREEN)
    cv.rect(gx - 8 * SS, y + h * 0.66, 8 * SS, 4 * SS, DARKGREEN)
    cv.rect(gx + 4 * SS, y + h * 0.7, 8 * SS, 4 * SS, DARKGREEN)


def sc_stocks(cv, x, y, w, h):
    """A plunging red chart: the AI sell-off."""
    cv.rect(x, y, w, h, (14, 18, 34))
    for i in range(4):
        cv.line(x + w * 0.08, y + h * (0.2 + 0.2 * i), x + w * 0.94, y + h * (0.2 + 0.2 * i),
                1 * SS, (52, 60, 84))
    pts = [(0.08, 0.24), (0.26, 0.3), (0.4, 0.22), (0.55, 0.44),
           (0.68, 0.4), (0.82, 0.66), (0.93, 0.78)]
    for i in range(len(pts) - 1):
        cv.line(x + w * pts[i][0], y + h * pts[i][1], x + w * pts[i + 1][0],
                y + h * pts[i + 1][1], 4 * SS, RED)
    ax, ay = x + w * 0.93, y + h * 0.78
    cv.tri(ax, ay + 9 * SS, ax - 10 * SS, ay - 3 * SS, ax + 3 * SS, ay - 8 * SS, RED)
    for bx, bh in ((0.16, 0.3), (0.34, 0.42), (0.52, 0.55), (0.7, 0.68)):
        cv.rect(x + w * bx, y + h * (0.92 - bh * 0.4), w * 0.09, h * bh * 0.4, (214, 4, 41))


def sc_cop(cv, x, y, w, h):
    """Globe and thermometer under a hot sun: climate talks in overtime."""
    cv.rect(x, y, w, h, (16, 96, 140))
    cv.circle(x + w * 0.38, y + h * 0.52, h * 0.34, (24, 130, 220))
    cv.poly([(x + w * 0.2, y + h * 0.36), (x + w * 0.34, y + h * 0.3),
             (x + w * 0.4, y + h * 0.44), (x + w * 0.26, y + h * 0.5)], (64, 196, 96))
    cv.poly([(x + w * 0.42, y + h * 0.58), (x + w * 0.56, y + h * 0.52),
             (x + w * 0.58, y + h * 0.68), (x + w * 0.44, y + h * 0.72)], (64, 196, 96))
    tx = x + w * 0.78
    cv.rect(tx - 3 * SS, y + h * 0.16, 6 * SS, h * 0.56, LIGHT)
    cv.rect(tx - 3 * SS, y + h * 0.3, 6 * SS, h * 0.42, RED)
    cv.circle(tx, y + h * 0.8, 9 * SS, RED)
    cv.circle(x + w * 0.12, y + h * 0.16, 9 * SS, GOLD)


def sc_summit(cv, x, y, w, h):
    """Three flags over a summit table in Shenzhen."""
    cv.rect(x, y, w, h, (36, 52, 96))
    fw, fh = w * 0.26, h * 0.4
    for i, base in enumerate((RED, (240, 240, 240), (28, 84, 200))):
        fx = x + w * (0.08 + 0.31 * i)
        cv.rect(fx, y + h * 0.14, fw, fh, base)
        cv.rect(fx, y + h * 0.14 + fh, 2 * SS, h * 0.3, (200, 200, 210))
    cv.rect(x + w * 0.08, y + h * 0.14, fw, fh * 0.5, (28, 84, 200))
    for r in range(3):
        cv.rect(x + w * 0.08, y + h * 0.14 + fh * (0.08 + 0.15 * r), fw * 0.9, fh * 0.07, LIGHT)
    cv.circle(x + w * 0.47, y + h * 0.3, 4 * SS, GOLD)
    cv.circle(x + w * 0.72, y + h * 0.34, 5 * SS, (28, 84, 200))
    cv.rect(x + w * 0.06, y + h * 0.78, w * 0.88, h * 0.1, BROWN)
    cv.rect(x + w * 0.06, y + h * 0.88, w * 0.88, h * 0.04, (100, 64, 30))


def sc_icj(cv, x, y, w, h):
    """Courthouse columns and the scales of justice at The Hague."""
    cv.rect(x, y, w, h, (44, 62, 110))
    cv.tri(x + w * 0.08, y + h * 0.2, x + w * 0.92, y + h * 0.2, x + w * 0.5, y + h * 0.04, GOLD)
    for i in range(4):
        cx = x + w * (0.16 + 0.2 * i)
        cv.rect(cx, y + h * 0.26, w * 0.08, h * 0.52, (226, 230, 240))
    cv.rect(x + w * 0.08, y + h * 0.8, w * 0.84, h * 0.09, (226, 230, 240))
    cx, cy = x + w * 0.5, y + h * 0.4
    cv.line(cx, cy - 12 * SS, cx, cy + 10 * SS, 3 * SS, GOLD)
    cv.line(cx - 13 * SS, cy - 8 * SS, cx + 13 * SS, cy - 8 * SS, 3 * SS, GOLD)
    for sgn in (-1, 1):
        px = cx + sgn * 13 * SS
        cv.line(px, cy - 8 * SS, px - 6 * SS, cy + 4 * SS, 2 * SS, GOLD)
        cv.line(px, cy - 8 * SS, px + 6 * SS, cy + 4 * SS, 2 * SS, GOLD)
        cv.poly([(px - 8 * SS, cy + 4 * SS), (px + 8 * SS, cy + 4 * SS),
                 (px + 4 * SS, cy + 10 * SS), (px - 4 * SS, cy + 10 * SS)], GOLD)


def sc_riemann(cv, x, y, w, h):
    """A zeta curve and prime dots: a claimed proof of Riemann."""
    cv.rect(x, y, w, h, (24, 20, 52))
    prev = None
    import math
    for i in range(41):
        t = i / 40
        px = x + w * (0.08 + 0.84 * t)
        py = y + h * (0.52 - 0.3 * math.sin(t * 9.0) * (1 - t * 0.4))
        if prev:
            cv.line(prev[0], prev[1], px, py, 3 * SS, (120, 220, 255))
        prev = (px, py)
    for i, px_ in enumerate((0.16, 0.3, 0.42, 0.58, 0.7, 0.86)):
        cv.circle(x + w * px_, y + h * (0.78 - 0.06 * (i % 2)), 3.5 * SS, GOLD)
    cv.line(x + w * 0.08, y + h * 0.86, x + w * 0.94, y + h * 0.86, 2 * SS, (120, 124, 160))


def sc_mercury(cv, x, y, w, h):
    """BepiColombo arrives: a grey planet and a probe with big panels."""
    cv.rect(x, y, w, h, (6, 8, 20))
    for sx, sy in ((0.1, 0.2), (0.3, 0.7), (0.55, 0.15), (0.8, 0.6), (0.92, 0.25), (0.66, 0.82)):
        cv.circle(x + w * sx, y + h * sy, 1.8 * SS, LIGHT)
    cv.circle(x + w * 0.76, y + h * 0.62, h * 0.3, (168, 164, 156))
    cv.circle(x + w * 0.68, y + h * 0.52, h * 0.07, (140, 136, 128))
    cv.circle(x + w * 0.84, y + h * 0.72, h * 0.05, (140, 136, 128))
    cv.circle(x + w * 0.8, y + h * 0.44, h * 0.04, (148, 144, 136))
    px, py = x + w * 0.3, y + h * 0.36
    cv.rect(px - w * 0.2, py - h * 0.07, w * 0.13, h * 0.14, (40, 90, 200))
    cv.rect(px + w * 0.07, py - h * 0.07, w * 0.13, h * 0.14, (40, 90, 200))
    cv.rect(px - w * 0.05, py - h * 0.1, w * 0.1, h * 0.2, (220, 224, 232))
    cv.circle(px, py - h * 0.16, 4 * SS, GOLD)


def sc_gta(cv, x, y, w, h):
    """Vice-city sunset, palms and a sports car: GTA VI's record day."""
    bands = ((244, 96, 54), (250, 130, 60), (255, 183, 3), (240, 110, 160))
    for i, col in enumerate(bands):
        cv.rect(x, y + h * i / 4, w, h / 4 + 1, col)
    cv.circle(x + w * 0.5, y + h * 0.52, h * 0.2, (255, 236, 170))
    cv.rect(x, y + h * 0.68, w, h * 0.32, (30, 24, 60))
    for px in (0.1, 0.88):
        bx = x + w * px
        cv.line(bx, y + h * 0.7, bx + 3 * SS, y + h * 0.3, 4 * SS, (20, 60, 30))
        for a in (-0.9, -0.4, 0.1, 0.6):
            import math
            cv.line(bx + 3 * SS, y + h * 0.3, bx + 3 * SS + 16 * SS * math.sin(a),
                    y + h * 0.3 - 8 * SS * math.cos(a) + 4 * SS, 3 * SS, (20, 110, 50))
    cy = y + h * 0.8
    cv.poly([(x + w * 0.32, cy), (x + w * 0.4, cy - h * 0.12), (x + w * 0.58, cy - h * 0.12),
             (x + w * 0.68, cy)], (16, 16, 24))
    cv.rect(x + w * 0.44, cy - h * 0.2, w * 0.12, h * 0.09, (16, 16, 24))
    cv.circle(x + w * 0.38, cy + h * 0.03, 5 * SS, (200, 200, 210))
    cv.circle(x + w * 0.62, cy + h * 0.03, 5 * SS, (200, 200, 210))


def sc_dengue(cv, x, y, w, h):
    """A mosquito behind a shield: Wolbachia cuts dengue in Brazil."""
    cv.rect(x, y, w, h, (18, 120, 70))
    cx, cy = x + w * 0.42, y + h * 0.52
    cv.poly([(cx - w * 0.16, cy - h * 0.3), (cx - w * 0.02, cy - h * 0.04),
             (cx - w * 0.2, cy - h * 0.02)], (210, 240, 255))
    cv.poly([(cx + w * 0.16, cy - h * 0.3), (cx + w * 0.02, cy - h * 0.04),
             (cx + w * 0.2, cy - h * 0.02)], (210, 240, 255))
    for i in range(4):
        bx = cx - w * 0.12 + i * w * 0.08
        cv.circle(bx, cy, (7 - i * 0.8) * SS, (30, 30, 36))
    cv.circle(cx + w * 0.14, cy - h * 0.02, 5 * SS, (30, 30, 36))
    cv.line(cx + w * 0.18, cy, cx + w * 0.3, cy + h * 0.1, 2 * SS, (30, 30, 36))
    for sgn in (-1, 1):
        cv.line(cx, cy + h * 0.06, cx + sgn * w * 0.14, cy + h * 0.3, 2 * SS, (30, 30, 36))
    sx, sy = x + w * 0.78, y + h * 0.5
    cv.poly([(sx - w * 0.1, sy - h * 0.3), (sx + w * 0.1, sy - h * 0.3), (sx + w * 0.1, sy + h * 0.08),
             (sx, sy + h * 0.32), (sx - w * 0.1, sy + h * 0.08)], TEAL)
    cv.line(sx - w * 0.05, sy + h * 0.02, sx - w * 0.01, sy + h * 0.1, 4 * SS, LIGHT)
    cv.line(sx - w * 0.01, sy + h * 0.1, sx + w * 0.06, sy - h * 0.1, 4 * SS, LIGHT)


def sc_quake(cv, x, y, w, h):
    """Houses over cracked ground: the Peru earthquake."""
    cv.rect(x, y, w, h * 0.62, (120, 180, 235))
    cv.rect(x, y + h * 0.62, w, h * 0.38, (150, 104, 60))
    for hx, col in ((0.12, (240, 240, 235)), (0.42, (250, 214, 150)), (0.7, (240, 240, 235))):
        bx, by = x + w * hx, y + h * 0.36
        cv.rect(bx, by, w * 0.2, h * 0.26, col)
        cv.tri(bx - w * 0.02, by, bx + w * 0.22, by, bx + w * 0.1, by - h * 0.14, RED)
    pts = [(0.05, 0.7), (0.2, 0.78), (0.32, 0.72), (0.48, 0.84), (0.6, 0.76),
           (0.74, 0.86), (0.86, 0.78), (0.97, 0.84)]
    for i in range(len(pts) - 1):
        cv.line(x + w * pts[i][0], y + h * pts[i][1], x + w * pts[i + 1][0],
                y + h * pts[i + 1][1], 3 * SS, (60, 40, 20))
    cv.line(x + w * 0.48, y + h * 0.84, x + w * 0.44, y + h * 0.97, 3 * SS, (60, 40, 20))


def sc_football(cv, x, y, w, h):
    """Pitch, goal and ball: Leeds stun Chelsea at Stamford Bridge."""
    cv.rect(x, y, w, h, (24, 140, 60))
    cv.rect(x, y + h * 0.5, w, 2 * SS, LIGHT)
    cv.ring(x + w * 0.5, y + h * 0.52, h * 0.2, 2 * SS, LIGHT)
    gx, gy = x + w * 0.66, y + h * 0.08
    cv.rect(gx, gy, w * 0.28, h * 0.44, (200, 235, 255))
    for i in range(1, 4):
        cv.line(gx + w * 0.07 * i, gy, gx + w * 0.07 * i, gy + h * 0.44, 1 * SS, (150, 180, 200))
        cv.line(gx, gy + h * 0.11 * i, gx + w * 0.28, gy + h * 0.11 * i, 1 * SS, (150, 180, 200))
    cv.rect(gx, gy, w * 0.28, 3 * SS, LIGHT)
    bx, by = x + w * 0.24, y + h * 0.66
    cv.circle(bx, by, 10 * SS, LIGHT)
    cv.circle(bx, by, 4 * SS, BLACK)
    cv.circle(bx - 7 * SS, by - 5 * SS, 3 * SS, BLACK)
    cv.circle(bx + 7 * SS, by + 5 * SS, 3 * SS, BLACK)


def sc_tennis(cv, x, y, w, h):
    """A hard court and racket: Alcaraz reaches the ATP Finals final."""
    cv.rect(x, y, w, h, (30, 90, 170))
    cv.rect(x + w * 0.08, y + h * 0.12, w * 0.84, h * 0.76, (36, 130, 90))
    cv.line(x + w * 0.08, y + h * 0.5, x + w * 0.92, y + h * 0.5, 3 * SS, LIGHT)
    cv.line(x + w * 0.5, y + h * 0.12, x + w * 0.5, y + h * 0.88, 2 * SS, (220, 230, 240))
    cv.ring(x + w * 0.3, y + h * 0.34, 11 * SS, 3 * SS, (240, 240, 240))
    cv.line(x + w * 0.37, y + h * 0.44, x + w * 0.48, y + h * 0.62, 4 * SS, BROWN)
    cv.circle(x + w * 0.72, y + h * 0.3, 5 * SS, (205, 235, 60))


def sc_kate(cv, x, y, w, h):
    """A gold crown on royal purple: the Princess of Wales in remission."""
    cv.rect(x, y, w, h, (70, 30, 110))
    cx, by = x + w * 0.5, y + h * 0.72
    cv.poly([(cx - w * 0.3, by), (cx - w * 0.3, by - h * 0.34), (cx - w * 0.15, by - h * 0.14),
             (cx, by - h * 0.44), (cx + w * 0.15, by - h * 0.14), (cx + w * 0.3, by - h * 0.34),
             (cx + w * 0.3, by)], GOLD)
    cv.rect(cx - w * 0.3, by, w * 0.6, h * 0.08, (230, 160, 0))
    for px in (-0.3, 0.0, 0.3):
        cv.circle(cx + w * px, by - h * (0.36 if px else 0.46), 4 * SS, (255, 220, 90))
    cv.circle(cx, by - h * 0.16, 5 * SS, RED)
    cv.circle(cx - w * 0.16, by - h * 0.12, 4 * SS, SKY)
    cv.circle(cx + w * 0.16, by - h * 0.12, 4 * SS, TEAL)

# ------------------------------------------------------------- the news
# All stories reported on Saturday 21 November 2026 (sources checked
# against BBC, Al Jazeera, Reuters, AP, The Guardian, UPI, France 24,
# Euronews, CBC, NPR and the day's sports wires).
GRID = [
    (sc_stocks, "ECONOMY - CORRECTION", "AI SELL-OFF HITS US STOCKS"),
    (sc_cop, "CLIMATE - ANTALYA", "COP31 TALKS RUN INTO OVERTIME"),
    (sc_summit, "POLITICS - CHINA", "TRUMP, XI, PUTIN: SHENZHEN SUMMIT"),
    (sc_icj, "JUSTICE - THE HAGUE", "UN COURT FINDS MYANMAR GENOCIDE"),
    (sc_riemann, "SCIENCE - UNVERIFIED", "RIEMANN PROOF CLAIMED WITH AI"),
    (sc_mercury, "SPACE - BEPICOLOMBO", "PROBE REACHES MERCURY ORBIT"),
    (sc_gta, "CULTURE - RECORD", "GTA VI: $3.8BN IN ONE DAY"),
    (sc_dengue, "HEALTH - WOLBACHIA", "MOSQUITOES CUT DENGUE IN BRAZIL"),
    (sc_quake, "DISASTER - PERU", "MAGNITUDE 6.7 QUAKE HITS PERU"),
    (sc_football, "SPORT - PREMIER LEAGUE", "LEEDS STUN CHELSEA 4-1 AWAY"),
    (sc_tennis, "SPORT - TURIN", "ALCARAZ REACHES ATP FINAL"),
    (sc_kate, "SOCIETY - LONDON", "PRINCESS KATE IN REMISSION"),
]

BRIEFS_LEFT = [
    "GAZA: ISRAELI STRIKE KILLS 3 IN FOOD VEHICLE",
    "HOUTHIS AND SAUDI COALITION TRADE STRIKES",
    "DRONES HIT RUSSIAN CARGO SHIP OFF FINLAND",
    "TWO TANKERS HIT NEAR STRAIT OF HORMUZ",
    "UK AND EU SIGN THREE POST-BREXIT DEALS",
    "EU-INDONESIA DEAL REMOVES 98.5% OF TARIFFS",
    "EU BUDGET PLAN ADDS 3% TAX ON BIG TECH",
    "DENMARK EXPELS RUSSIAN DEFENSE ATTACHE",
    "ESTONIA TO CLOSE RUSSIA BORDER FROM DEC 1",
    "FBI PROBES REPORTED CRIME-DATABASE HACK",
    "TRUMP FLOATS TAX ON DATA CENTERS ABROAD",
    "NVIDIA CHIEF HUANG OUSTED; TRUMP TOLD XI",
    "UN TALKS KEEP WORKING ON AI WEAPONS RULES",
]

BRIEFS_RIGHT = [
    "PARIS OFFICERS SENTENCED OVER RACIST BEATING",
    "MAN CONVICTED OVER DEADLY PALISADES FIRE",
    "VIRGINIA: CHILD DIES OF MEASLES",
    "UGANDA CURBS GATHERINGS OVER EBOLA FEARS",
    "NIGERIA: FUNERAL BOAT CAPSIZE KILLS 24",
    "BASRA POWER-STATION FIRE KILLS 4, HURTS 35",
    "SAUDI-JAPAN DEAL TRIPLES OIL STORED IN JAPAN",
    "ARGENTINA BONDS SLIDE INTO DISTRESS",
    "BOLSONARO IN INTENSIVE CARE IN BRASILIA",
    "CERN FINDS FIRST SIGN OF ULTRA-RARE DECAY",
    "VOYAGER 1 NOW 24 LIGHT-HOURS FROM EARTH",
    "HARDEN SCORES 51, PASSES KOBE BRYANT MARK",
    "SALVADORAN TROOPS FIGHT GANGS IN HAITI",
]


# --------------------------------------------------------------- layout
def border(cv, x, y, w, h, color=INK, t=3 * SS // 2):
    cv.rect(x, y, w, t, color)
    cv.rect(x, y + h - t, w, t, color)
    cv.rect(x, y, t, h, color)
    cv.rect(x + w - t, y, t, h, color)


def grid_panel(cv, x, y, w, h, scene, kicker, label):
    cv.rect(x, y, w, h, LIGHT)
    border(cv, x, y, w, h)
    scene(cv, x + 6, y + 6, w - 12, 96)
    draw_text(cv, x + 16, y + 112, kicker, 4, RED, 0)
    draw_block(cv, x + 16, y + 146, label, 5, INK, w - 32, 42, 0, 2)


def stack_panel(cv, x, y, w, h, scene, kicker, label, sub):
    cv.rect(x, y, w, h, LIGHT)
    border(cv, x, y, w, h)
    scene(cv, x + 6, y + 6, 228, h - 12)
    tx = x + 252
    draw_text(cv, tx, y + 16, kicker, 4, RED, 0)
    draw_block(cv, tx, y + 50, label, 5, INK, w - 268, 44, 0, 2)
    draw_block(cv, tx, y + 142, sub, 4, GRAY, w - 268, 36, 0, 3)


def compose():
    cv = Canvas(W, H, PAPER)
    mx = 32                      # page margin (render px)
    cw = W - 2 * mx              # content width

    # masthead
    draw_text(cv, mx, 30, "THE WORLD IN ONE PAGE", 6, INK, 1)
    r = "ONE IMAGE - EVERY STORY SOURCED"
    draw_text(cv, mx + cw - text_w(r, 4, 1), 36, r, 4, GRAY, 1)
    cx = draw_text(cv, mx, 80, "21", 20, RED, 1)
    draw_text(cv, cx, 80, " NOVEMBER 2026", 20, INK, 1)
    draw_text(cv, mx, 232, "SATURDAY - WORLD NEWS IN ONE IMAGE", 5, INK, 1)
    r = "41 STORIES - 15 PICTURED"
    draw_text(cv, mx + cw - text_w(r, 5, 1), 232, r, 5, RED, 1)
    cv.rect(mx, 278, cw, 8, RED)
    cv.rect(mx, 292, cw, 3, INK)

    # hero row
    hy, hh = 308, 500
    hero_w, stack_w = 1290, cw - 1290 - 16
    cv.rect(mx, hy, hero_w, hh, LIGHT)
    border(cv, mx, hy, hero_w, hh)
    sc_bahrain(cv, mx + hero_w - 526, hy + 6, 520, hh - 12)
    tx = mx + 28
    draw_text(cv, tx, hy + 22, "MIDDLE EAST - TOP STORY", 5, RED, 1)
    draw_text(cv, tx, hy + 70, "IRAN STRIKES US", 8, INK, 0)
    draw_text(cv, tx, hy + 138, "BASES IN BAHRAIN", 8, INK, 0)
    draw_block(cv, tx, hy + 218,
               "IRAN SAYS IT HIT TWO US BASES AT AL-RIFFA AND AWALI. "
               "BAHRAIN REPORTS A FIRE AT A CIVILIAN PLANT AND NO "
               "INJURIES. TRUMP WANTS A PERMANENT DEAL.",
               5, (52, 58, 74), 700, 44, 0, 7)
    sx = mx + hero_w + 16
    stack_panel(cv, sx, hy, stack_w, (hh - 16) // 2, sc_kryvyi,
                "UKRAINE - RUSSIA WAR", "MISSILE HITS KRYVYI RIH",
                "2 DEAD, 58 HURT; MISSILES DOWN IN POLAND")
    stack_panel(cv, sx, hy + (hh + 16) // 2, stack_w, (hh - 16) // 2, sc_mexico,
                "MEXICO - JUSTICE", "CHAPO ISIDRO CAPTURED",
                "FBI MOST-WANTED MAN; 11 DIE IN AFTERMATH")

    # pictured grid: 4 columns x 3 rows
    gy = hy + hh + 16
    pw = (cw - 3 * 16) // 4
    ph = 228
    for i, (scene, kicker, label) in enumerate(GRID):
        px = mx + (i % 4) * (pw + 16)
        py = gy + (i // 4) * (ph + 16)
        grid_panel(cv, px, py, pw, ph, scene, kicker, label)

    # in-brief band
    by = gy + 3 * ph + 2 * 16 + 12
    cv.rect(mx, by, cw, 42, RED)
    draw_text(cv, mx + 16, by + 8, "IN BRIEF - 26 MORE STORIES FROM THE DAY", 5, LIGHT, 1)
    iy = by + 56
    for col, briefs in enumerate((BRIEFS_LEFT, BRIEFS_RIGHT)):
        bx = mx + col * (cw // 2 + 12)
        for i, b in enumerate(briefs):
            yy = iy + i * 31
            draw_text(cv, bx, yy, "\u2022", 4, RED, 0)
            draw_text(cv, bx + 26, yy, b, 4, INK, 0)
    fy = iy + 13 * 31 + 8
    draw_text(cv, mx, fy,
              "SOURCES: BBC - AL JAZEERA - REUTERS - AP - THE GUARDIAN - "
              "UPI - FRANCE 24 - EURONEWS - CBC - NPR", 3, GRAY, 0)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = save_png(compose(), path)
    print("wrote", path, size, "bytes")


if __name__ == "__main__":
    main()


