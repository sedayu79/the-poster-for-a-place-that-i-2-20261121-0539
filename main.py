"""NUSA SENJA — a travel poster for a place that does not exist.

Program entry for make.fun bounty the-poster-for-a-place-that-i-2-20261121-0539.
Writes one 1024x1024 PNG to /output/entry.png (or MAKEFUN_OUTPUT_DIR).
Python 3.13, standard library only. Deterministic: identical bytes every run.

Scene v2 (vintage Indonesian travel-poster style, Yogyakarta/Bali
school, more natural and detailed): a fictional island, NUSA SENJA,
at golden hour — a volcano on the horizon, a tiered temple on a
terraced hill, palm trees framing the view, an ocean with a surfer
riding a curling wave, a sandy beach in the foreground with a stone
gate, and the island's name set in big condensed capitals across
the sky.
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
# v2: a living beach scene — ocean, surf, sand, palms, volcano, temple.
# Extra palette for the natural look.
SAND_WET = (206, 172, 128)
SAND = (228, 196, 150)
SAND_LIGHT = (242, 220, 178)
FOAM = (248, 250, 244)
WAVE_GREEN = (28, 130, 120)
WAVE_LIGHT = (52, 160, 148)
PALM_TRUNK = (96, 66, 44)
PALM_LEAF = (34, 96, 62)
PALM_LEAF_L = (52, 130, 84)
HAZE = (96, 128, 138)
CLOUD = (246, 198, 132)
SMOKE = (250, 232, 205)


def sky():
    stops = [(0.0, (16, 66, 92)), (0.25, (48, 116, 132)),
             (0.42, (120, 170, 150)), (0.55, (244, 178, 100)),
             (0.62, (250, 196, 120))]
    for y in range(0, 481):
        t = y / 480.0
        color = stops[-1][1]
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                color = lerp(c0, c1, (t - t0) / (t1 - t0))
                break
        hfill(y, 0, W - 1, color)


def sun_glow():
    # soft halo: wide rings fading into the sky, bright core last
    for r, c in ((195, (248, 196, 122)), (162, (250, 206, 138)),
                 (132, SUN_RING), (105, SUN_CORE)):
        fill_circle(640, 420, r, c)
    # thin bright rim
    for r in (106, 107):
        for a in range(0, 360, 2):
            rad = math.radians(a)
            set_px(int(640 + r * math.cos(rad)),
                   int(420 + r * math.sin(rad)), CREAM)


def clouds():
    # soft puffy clouds: three overlapping discs each, pale against gold
    for (cx, cy) in ((180, 330), (850, 305), (150, 215), (880, 345)):
        for (ox, oy, r) in ((-38, 6, 16), (0, 0, 22), (38, 6, 15),
                            (-18, -8, 14), (20, -8, 13)):
            fill_circle(cx + ox, cy + oy, r, CLOUD)


def birds():
    for bx, by, s in ((180, 180, 14), (240, 150, 10), (830, 200, 12)):
        line(bx - s, by, bx, by - 6, INK, 2)
        line(bx, by - 6, bx + s, by, INK, 2)


def volcano():
    # hazy foothill ridge behind the cone
    fill_poly([(0, 480), (0, 430), (90, 408), (180, 436), (260, 414),
               (340, 440), (420, 420), (470, 448), (470, 480)], HAZE)
    # cone with a crater notch at the top
    fill_poly([(60, 480), (270, 300), (300, 324), (336, 308), (366, 332),
               (500, 480)], VOLCANO)
    # sunlit flank
    fill_poly([(300, 324), (336, 308), (366, 332), (420, 480), (330, 480)],
              (74, 66, 92))
    # crater rim catching the light
    fill_poly([(270, 300), (300, 324), (336, 308), (316, 292)], SUNSET)
    # smoke wisps curling off the crater
    fill_circle(306, 282, 9, SMOKE)
    fill_circle(322, 268, 7, SMOKE)
    fill_circle(336, 256, 5, SMOKE)


def terraced_hill():
    # hill on the right, sloping down to the sea
    fill_poly([(620, 480), (1024, 480), (1024, 400), (940, 392),
               (820, 396), (700, 402), (640, 440)], HILL)
    # terrace contour lines following the hill
    for i, cy in enumerate((414, 432, 450, 466)):
        color = HILL_LIGHT if i % 2 == 0 else TERRACE_GOLD
        x0 = 690 + i * 25
        for x in range(x0, 1024, 4):
            yy = cy + int(8 * math.sin((x - x0) / 80.0))
            hfill(yy, x, x + 3, color)
            hfill(yy + 1, x, x + 3, color)


def temple(x0, base):
    # tiered meru temple, compact so the finial clears the tagline
    rect(x0 - 10, base, x0 + 110, base + 14, MAROON_DARK)
    rect(x0 - 10, base, x0 + 110, base + 4, TRIM)
    tiers = [(x0 - 24, x0 + 124, base - 28, base),
             (x0 - 6, x0 + 106, base - 56, base - 28),
             (x0 + 12, x0 + 88, base - 84, base - 56)]
    for (lx, rx, ty, by) in tiers:
        fill_poly([(lx, by), (rx, by), ((lx + rx) // 2 + 12, ty),
                   ((lx + rx) // 2 - 12, ty)], MAROON)
        hfill(by - 2, lx + 4, rx - 4, TRIM)
    fill_poly([(x0 + 44, base - 84), (x0 + 60, base - 84),
               (x0 + 52, base - 102)], TRIM)
    fill_circle(x0 + 52, base - 105, 4, TRIM)
    rect(x0 + 42, base - 24, x0 + 62, base, SUN_CORE)


def ocean():
    # gradient: deep teal at the horizon, pale shallows at the shore
    stops = [(0.0, (14, 78, 94)), (0.45, (22, 106, 118)),
             (0.8, (46, 140, 138)), (1.0, (96, 176, 158))]
    for y in range(480, 780):
        t = (y - 480) / 299.0
        color = stops[-1][1]
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                color = lerp(c0, c1, (t - t0) / (t1 - t0))
                break
        hfill(y, 0, W - 1, color)
    # sun glitter path under the sun
    for i in range(10):
        y = 500 + i * 24
        wdt = int(120 * (0.6 + 0.4 * math.sin(i * 1.7)))
        cx = 690 + int(16 * math.sin(i * 2.3))
        col = SUN_CORE if i % 3 == 0 else SUN_RING
        hfill(y, cx - wdt // 2, cx + wdt // 2, col)
        hfill(y + 1, cx - wdt // 2, cx + wdt // 2, col)
    # rolling swell lines with foam flecks
    for j, wy in enumerate((520, 560, 600, 640, 690, 730)):
        for x in range(0, W, 6):
            yy = wy + int(6 * math.sin(x / 70.0 + j * 1.3))
            hfill(yy, x, x + 4,
                  (210, 235, 225) if j % 2 == 0 else (140, 200, 195))


def breaking_wave():
    # the hero wave: a curling breaker on the right, foam crest, spray
    crest = [(560, 760), (590, 690), (630, 640), (690, 612), (750, 606),
             (800, 620), (830, 650), (845, 690), (850, 730), (855, 760)]
    fill_poly(crest, WAVE_GREEN)
    # lighter face band inside the curl
    face = [(600, 760), (620, 700), (655, 660), (700, 640), (750, 638),
            (795, 655), (820, 690), (828, 730), (830, 760)]
    fill_poly(face, WAVE_LIGHT)
    # foam along the crest
    for (fx, fy) in crest[1:-1]:
        fill_circle(fx, fy, 8, FOAM)
        fill_circle(fx + 6, fy + 4, 5, FOAM)
    # spray above the lip
    for (sx, sy, sr) in ((770, 596, 4), (790, 588, 5), (812, 592, 4),
                         (828, 604, 3), (748, 600, 3), (800, 580, 3)):
        fill_circle(sx, sy, sr, FOAM)
    # smaller breaker to the left, for depth
    fill_poly([(380, 760), (400, 712), (440, 690), (490, 692), (520, 716),
               (530, 760)], (36, 138, 128))
    for (fx, fy) in ((400, 712), (440, 690), (490, 692), (520, 716)):
        fill_circle(fx, fy, 6, FOAM)


def surfer():
    # a surfer riding the face of the hero wave, dark silhouette
    # board, angled with the wave face
    line(668, 720, 726, 702, CREAM, 4)
    line(668, 720, 726, 702, INK, 1)
    # legs: back leg planted, front leg bent toward the nose
    line(694, 706, 682, 718, INK, 4)
    line(694, 706, 710, 716, INK, 4)
    # torso leaning into the wave
    line(694, 706, 700, 688, INK, 5)
    # arms out for balance
    line(698, 692, 682, 686, INK, 3)
    line(698, 692, 714, 684, INK, 3)
    # head
    fill_circle(702, 682, 5, INK)


def beach():
    # wet sand band at the waterline, dry sand to the foot
    stops = [(0.0, SAND_WET), (0.25, SAND), (1.0, SAND_LIGHT)]
    for y in range(780, H):
        t = (y - 780) / 243.0
        color = stops[-1][1]
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                color = lerp(c0, c1, (t - t0) / (t1 - t0))
                break
        hfill(y, 0, W - 1, color)
    # foam edge where the sea meets the sand, scalloped
    for x in range(0, W, 8):
        yy = 782 + int(6 * math.sin(x / 55.0))
        fill_circle(x, yy, 5, FOAM)
        fill_circle(x + 4, yy + 3, 3, FOAM)
    # sand texture: deterministic speckles (fixed seed, same every run)
    state = 20261121
    tones = ((216, 186, 140), (232, 204, 158), (198, 168, 122),
             (244, 226, 186))
    for _ in range(2600):
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        x = state % W
        state = (state * 1103515245 + 12345) & 0x7FFFFFFF
        y = 790 + state % 230
        c = tones[state % 4]
        set_px(x, y, c)
        set_px(x + 1, y, c)
    # a few footprints wandering up the beach
    for i in range(7):
        fx = 420 + i * 14
        fy = 880 + i * 16
        fill_circle(fx, fy, 3, (198, 168, 122))
        fill_circle(fx + 8, fy + 8, 3, (198, 168, 122))


def stone_gate():
    # candi bentar split gate standing on the sand, framing the beach
    for gx in (24, 900):
        rect(gx, 852, gx + 100, H - 1, INK)
        rect(gx - 8, 822, gx + 108, 852, INK)
        rect(gx - 16, 794, gx + 116, 822, INK)
        fill_poly([(gx - 22, 794), (gx + 122, 794), (gx + 50, 758)],
                  MAROON_DARK)
        hfill(796, gx - 14, gx + 114, TRIM)
        # carved band
        hfill(880, gx + 6, gx + 94, MAROON_DARK)
        hfill(920, gx + 6, gx + 94, MAROON_DARK)


def frond(x0, y0, x1, y1, x2, y2, flip, color):
    # one palm frond: quadratic bezier rib with leaflets
    steps = 24
    prev = None
    for i in range(steps + 1):
        t = i / steps
        x = int((1 - t) ** 2 * x0 + 2 * (1 - t) * t * x1 + t * t * x2)
        y = int((1 - t) ** 2 * y0 + 2 * (1 - t) * t * y1 + t * t * y2)
        if prev is not None:
            line(prev[0], prev[1], x, y, color, 3)
            if i % 3 == 0:
                lx = x + (18 if flip else -18)
                ly = y + 16
                line(x, y, lx, ly, color, 2)
        prev = (x, y)


def palm(cx_base, lean):
    # a full palm tree: curved trunk, crown of fronds, coconuts
    top_x = cx_base + lean * 55
    top_y = 430
    # trunk as one continuous curve: thick segments between points
    pts = []
    for i in range(26):
        t = i / 25.0
        pts.append((int(cx_base + lean * 55 * t * t), int(1000 - t * 570)))
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
             PALM_TRUNK, 15)
    # trunk rings: short darker bands across the trunk
    for i in range(4, 26, 4):
        x, y = pts[i]
        hfill(y, x - 7, x + 7, (70, 48, 32))
    # crown: fronds fanning out
    for (dx, dy, fx) in ((-160, 40, False), (-120, 90, False),
                         (-60, 110, False), (30, 110, True),
                         (110, 80, True), (170, 30, True),
                         (-40, -50, False), (60, -45, True)):
        frond(top_x, top_y, top_x + dx // 2, top_y + dy // 2,
              top_x + dx, top_y + dy, fx,
              PALM_LEAF if (dx + dy) % 2 == 0 else PALM_LEAF_L)
    # coconuts under the crown
    fill_circle(top_x - 12, top_y + 14, 7, (96, 66, 44))
    fill_circle(top_x + 10, top_y + 16, 7, (96, 66, 44))


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
    # small line at the foot of the poster, dark on the pale sand
    draw_text_centered("AN ISLAND BEYOND THE MAP", 972, 3, MAROON_DARK)


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
    sun_glow()
    clouds()
    birds()
    volcano()
    terraced_hill()
    temple(780, 400)
    ocean()
    breaking_wave()
    surfer()
    beach()
    palm(40, 1)
    palm(984, -1)
    stone_gate()
    border()
    lettering()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = write_png(path)
    print(f"wrote {path} ({size} bytes)")


if __name__ == "__main__":
    main()
