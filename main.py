"""NUSA SENJA — a travel poster for a place that does not exist.

Program entry for make.fun bounty the-poster-for-a-place-that-i-2-20261121-0539.
Writes one 1024x1024 PNG to /output/entry.png (or MAKEFUN_OUTPUT_DIR).
Python 3.13, standard library only. Deterministic: identical bytes every run.

Scene (vintage Indonesian travel-poster style, Yogyakarta/Bali school):
a fictional island, NUSA SENJA, at golden hour — a volcano on the
horizon, a tiered temple on a terraced hill, a lagoon, a stone gate
framing the view, palm fronds overhead, and the island's name set in
big condensed capitals across the sky.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
DEEP_TEAL = (14, 62, 80)
TEAL = (32, 104, 108)
GOLD = (232, 150, 80)
SUNSET = (240, 176, 96)
SUN_CORE = (255, 216, 132)
SUN_RING = (244, 164, 96)
CREAM = (250, 240, 214)
MAROON = (94, 38, 44)
MAROON_DARK = (74, 28, 36)
RIDGE = (74, 96, 116)
VOLCANO = (58, 52, 74)
HILL = (46, 110, 82)
HILL_LIGHT = (64, 138, 96)
TERRACE_GOLD = (150, 160, 90)
SEA = (13, 74, 88)
SEA_LIGHT = (22, 96, 108)
INK = (10, 40, 52)
TRIM = (232, 176, 90)

buf = bytearray(W * H * 3)


def hfill(y, x0, x1, color):
    """Fill a horizontal run on row y, clipped to the canvas."""
    if y < 0 or y >= H:
        return
    x0 = max(0, int(x0))
    x1 = min(W - 1, int(x1))
    if x0 > x1:
        return
    i0 = (y * W + x0) * 3
    i1 = (y * W + x1 + 1) * 3
    buf[i0:i1] = bytes(color) * (x1 - x0 + 1)


def set_px(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = color[0]
        buf[i + 1] = color[1]
        buf[i + 2] = color[2]


def rect(x0, y0, x1, y1, color):
    for y in range(max(0, y0), min(H, y1 + 1)):
        hfill(y, x0, x1, color)


def fill_circle(cx, cy, r, color):
    for dy in range(-r, r + 1):
        dx = int(math.sqrt(max(0, r * r - dy * dy)))
        hfill(cy + dy, cx - dx, cx + dx, color)


def fill_poly(pts, color):
    n = len(pts)
    ys = [p[1] for p in pts]
    ymin = max(0, min(ys))
    ymax = min(H - 1, max(ys))
    for y in range(ymin, ymax + 1):
        xs = []
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for j in range(0, len(xs) - 1, 2):
            hfill(y, xs[j], xs[j + 1], color)


def line(x0, y0, x1, y1, color, thick=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        for t in range(-(thick // 2), thick // 2 + 1):
            set_px(x, y + t, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- 5x7 font
# Bold condensed capitals, drawn as solid blocks. Each glyph is 7 rows of 5.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
}


def text_width(text, s):
    return len(text) * 5 * s + (len(text) - 1) * s


def draw_text(text, x, y, s, color, shadow=None, shadow_dx=0, shadow_dy=0):
    """Draw text left-aligned at (x, y); s = pixel size of one font cell."""
    if shadow is not None:
        draw_text(text, x + shadow_dx, y + shadow_dy, s, shadow)
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for row in range(7):
            for col in range(5):
                if glyph[row][col] == "#":
                    for dy in range(s):
                        hfill(y + row * s + dy, cx + col * s,
                              cx + col * s + s - 1, color)
        cx += 6 * s


def draw_text_centered(text, y, s, color, shadow=None, shadow_dx=0, shadow_dy=0):
    x = (W - text_width(text, s)) // 2
    draw_text(text, x, y, s, color, shadow, shadow_dx, shadow_dy)


# ---------------------------------------------------------------- scene
def sky():
    stops = [(0.0, DEEP_TEAL), (0.30, TEAL), (0.52, GOLD), (0.62, SUNSET)]
    for y in range(0, 641):
        t = y / 640.0
        color = stops[-1][1]
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                color = lerp(c0, c1, (t - t0) / (t1 - t0))
                break
        hfill(y, 0, W - 1, color)


def sun():
    fill_circle(660, 430, 132, SUN_RING)
    fill_circle(660, 430, 105, SUN_CORE)
    # thin bright rim
    for r in (106, 107):
        for a in range(0, 360, 2):
            rad = math.radians(a)
            set_px(int(660 + r * math.cos(rad)), int(430 + r * math.sin(rad)),
                   CREAM)


def birds():
    for bx, by, s in ((180, 180, 14), (240, 150, 10), (830, 200, 12)):
        line(bx - s, by, bx, by - 6, INK, 2)
        line(bx, by - 6, bx + s, by, INK, 2)


def far_ridge():
    fill_poly([(0, 600), (0, 540), (120, 500), (220, 545), (330, 505),
               (470, 550), (600, 510), (760, 548), (900, 512), (1024, 545),
               (1024, 600)], RIDGE)


def volcano():
    # big cone left of centre, crater notch at the top
    fill_poly([(80, 600), (290, 330), (318, 352), (352, 338), (380, 362),
               (520, 600)], VOLCANO)
    # snow-light crater rim
    fill_poly([(290, 330), (318, 352), (352, 338), (330, 322)], SUNSET)
    # drifting smoke, kept tight to the crater so it clears the tagline
    fill_circle(325, 312, 10, CREAM)
    fill_circle(342, 298, 8, CREAM)
    fill_circle(356, 286, 6, CREAM)


def terraced_hill():
    # hill on the right, sloping down to the lagoon
    fill_poly([(560, 640), (1024, 640), (1024, 540), (900, 512),
               (760, 520), (640, 560)], HILL)
    # terrace contour lines following the hill
    for i, (cy, w) in enumerate(((548, 420), (572, 380), (596, 330),
                                 (618, 270))):
        color = HILL_LIGHT if i % 2 == 0 else TERRACE_GOLD
        x0 = 1024 - w
        for x in range(x0, 1024, 4):
            yy = cy + int(10 * math.sin((x - x0) / 90.0))
            hfill(yy, x, x + 3, color)
            hfill(yy + 1, x, x + 3, color)


def temple():
    # tiered meru temple on the hill — the poster's one landmark
    x0, base = 700, 522
    # base platform
    rect(x0 - 12, base, x0 + 132, base + 18, MAROON_DARK)
    rect(x0 - 12, base, x0 + 132, base + 4, TRIM)
    # three roof tiers, widest at the bottom
    tiers = [(x0 - 30, x0 + 150, base - 42, base),
             (x0 - 8, x0 + 128, base - 82, base - 42),
             (x0 + 14, x0 + 106, base - 118, base - 82)]
    for (lx, rx, ty, by) in tiers:
        fill_poly([(lx, by), (rx, by), ((lx + rx) // 2 + 14, ty),
                   ((lx + rx) // 2 - 14, ty)], MAROON)
        hfill(by - 2, lx + 4, rx - 4, TRIM)
    # finial
    fill_poly([(x0 + 52, base - 118), (x0 + 68, base - 118),
               (x0 + 60, base - 142)], TRIM)
    fill_circle(x0 + 60, base - 146, 5, TRIM)
    # door glow
    rect(x0 + 50, base - 30, x0 + 70, base, SUN_CORE)


def sea():
    rect(0, 640, W - 1, H - 1, SEA)
    for y in range(660, 1000, 46):
        hfill(y, 0, W - 1, SEA_LIGHT)
    # sun reflection: shimmering band under the sun, ending clear of the
    # footline so no streak crosses the lettering
    for i in range(12):
        y = 660 + i * 22
        wdt = int(150 * (0.55 + 0.45 * math.sin(i * 1.7)))
        cx = 660 + int(18 * math.sin(i * 2.3))
        col = SUN_CORE if i % 3 == 0 else SUN_RING
        hfill(y, cx - wdt // 2, cx + wdt // 2, col)
        hfill(y + 1, cx - wdt // 2, cx + wdt // 2, col)


def canoe():
    # small outrigger canoe with a triangular sail, drifting on the lagoon
    fill_poly([(400, 806), (470, 806), (452, 818), (418, 818)], INK)
    line(435, 806, 435, 758, INK, 3)
    fill_poly([(437, 762), (437, 802), (478, 802)], CREAM)
    hfill(824, 408, 462, SEA_LIGHT)
    hfill(826, 412, 458, SEA_LIGHT)


def stone_gate():
    # candi bentar split gate framing the foreground, left and right
    for gx in (24, 900):
        # stepped pillar
        rect(gx, 830, gx + 100, H - 1, INK)
        rect(gx - 8, 800, gx + 108, 830, INK)
        rect(gx - 16, 772, gx + 116, 800, INK)
        # small roof cap
        fill_poly([(gx - 22, 772), (gx + 122, 772), (gx + 50, 736)],
                  MAROON_DARK)
        hfill(774, gx - 14, gx + 114, TRIM)


def palm_fronds():
    # dark fronds hanging in from the top corners
    def frond(x0, y0, x1, y1, x2, y2, flip):
        # quadratic bezier rib
        steps = 24
        prev = None
        for i in range(steps + 1):
            t = i / steps
            x = int((1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t * t * x2)
            y = int((1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t * t * y2)
            if prev is not None:
                line(prev[0], prev[1], x, y, INK, 3)
                # leaflets angling off the rib
                if i % 3 == 0:
                    lx = x + (18 if flip else -18)
                    ly = y + 16
                    line(x, y, lx, ly, INK, 2)
            prev = (x, y)

    frond(0, 10, 120, 60, 260, 150, True)
    frond(30, 0, 160, 30, 300, 90, True)
    frond(1024, 10, 904, 60, 764, 150, False)
    frond(994, 0, 864, 30, 724, 90, False)


def border():
    for t in range(5):
        i = 20 + t
        hfill(i, i, W - 1 - i, CREAM)
        hfill(H - 1 - i, i, W - 1 - i, CREAM)
        for y in range(i, H - i):
            set_px(i, y, CREAM)
            set_px(W - 1 - i, y, CREAM)


def lettering():
    # the invented place's name, big and legible across the sky
    draw_text_centered("NUSA SENJA", 96, 16, CREAM,
                       shadow=MAROON_DARK, shadow_dx=5, shadow_dy=6)
    # tagline with rules either side
    draw_text_centered("THE ISLAND WHERE THE SUN NEVER SETS", 252, 4, CREAM,
                       shadow=MAROON_DARK, shadow_dx=2, shadow_dy=2)
    tw = text_width("THE ISLAND WHERE THE SUN NEVER SETS", 4)
    cx = (W - tw) // 2
    line(cx - 64, 266, cx - 16, 266, CREAM, 2)
    line(cx + tw + 16, 266, cx + tw + 64, 266, CREAM, 2)
    # small line at the foot of the poster
    draw_text_centered("AN ISLAND BEYOND THE MAP", 972, 3, CREAM,
                       shadow=INK, shadow_dx=1, shadow_dy=2)


# ---------------------------------------------------------------- PNG out
def write_png(path):
    raw = bytearray()
    for y in range(H):
        raw.append(0)  # filter: none
        raw.extend(buf[y * W * 3:(y + 1) * W * 3])
    comp = zlib.compress(bytes(raw), 6)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", comp)
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    sky()
    sun()
    birds()
    far_ridge()
    volcano()
    terraced_hill()
    temple()
    sea()
    canoe()
    stone_gate()
    palm_fronds()
    border()
    lettering()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path)
    print(f"wrote {path} ({size} bytes)")


if __name__ == "__main__":
    main()
