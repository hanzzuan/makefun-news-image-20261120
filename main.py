#!/usr/bin/env python3
"""news-image-20261120 — draw one newspaper front page summing up the
world news of Friday 20 November 2026, as a 1024x1024 PNG.

Pure Python 3.13 standard library only. No network, no randomness, no
clock: two runs write byte-identical output.
"""

import os
import struct
import zlib

from font5x7 import glyph, text_width, wrap

W = 1024
H = 1024

# --- palette -------------------------------------------------------------
PAPER = (247, 243, 231)
PANEL = (255, 253, 246)
INK = (26, 26, 26)
NAVY = (31, 58, 95)
NAVY_DK = (20, 38, 64)
RED = (179, 39, 30)
BLUE = (46, 95, 163)
TEAL = (42, 127, 111)
GOLD = (201, 151, 28)
GREY = (138, 133, 120)
LIGHT_BLUE = (234, 240, 247)
LIGHT_RED = (253, 236, 234)
LIGHT_GREEN = (234, 246, 241)
LIGHT_GOLD = (253, 243, 220)
WHITE = (255, 255, 255)
GREEN = (46, 134, 84)
BROWN = (122, 84, 52)
DARK = (16, 24, 40)


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg[0] for _ in range(w * h))
        self.px = bytearray(w * h * 3)
        for i in range(w * h):
            self.px[i * 3] = bg[0]
            self.px[i * 3 + 1] = bg[1]
            self.px[i * 3 + 2] = bg[2]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = c[0]
            self.px[i + 1] = c[1]
            self.px[i + 2] = c[2]

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = c[0]
                self.px[i + 1] = c[1]
                self.px[i + 2] = c[2]

    def rect(self, x, y, w, h, c, t=2):
        self.fill_rect(x, y, w, t, c)
        self.fill_rect(x, y + h - t, w, t, c)
        self.fill_rect(x, y, t, h, c)
        self.fill_rect(x + w - t, y, t, h, c)

    def hline(self, x, y, w, c, t=2):
        self.fill_rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=2):
        self.fill_rect(x, y, t, h, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            if t <= 1:
                self.set(x, y, c)
            else:
                self.fill_rect(x - t // 2, y - t // 2, t, t, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def circle(self, cx, cy, r, c, fill=True):
        if fill:
            for yy in range(-r, r + 1):
                half = int((r * r - yy * yy) ** 0.5)
                self.fill_rect(cx - half, cy + yy, half * 2 + 1, 1, c)
        else:
            steps = max(24, r * 6)
            for k in range(steps):
                import math
                a = 2 * math.pi * k / steps
                self.set(int(cx + r * math.cos(a)), int(cy + r * math.sin(a)), c)

    def triangle(self, pts, c):
        (x0, y0), (x1, y1), (x2, y2) = pts
        ymin = min(y0, y1, y2)
        ymax = max(y0, y1, y2)
        for y in range(ymin, ymax + 1):
            xs = []
            for (ax, ay), (bx, by) in (((x0, y0), (x1, y1)),
                                       ((x1, y1), (x2, y2)),
                                       ((x2, y2), (x0, y0))):
                if ay == by:
                    continue
                if min(ay, by) <= y < max(ay, by):
                    xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
            if len(xs) >= 2:
                xa = int(min(xs))
                xb = int(max(xs))
                self.fill_rect(xa, y, xb - xa + 1, 1, c)

    def star(self, cx, cy, r, c):
        """A simple five-point star drawn as a small filled polygon."""
        import math
        pts = []
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.42
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        ymin = int(min(p[1] for p in pts))
        ymax = int(max(p[1] for p in pts))
        for y in range(ymin, ymax + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                (ax, ay), (bx, by) = pts[i], pts[(i + 1) % n]
                if ay == by:
                    continue
                if min(ay, by) <= y < max(ay, by):
                    xs.append(ax + (y - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), y, int(xs[i + 1]) - int(xs[i]) + 1, 1, c)


# --- text ------------------------------------------------------------------
def draw_char(cv, x, y, ch, scale, color):
    g = glyph(ch)
    for r, row in enumerate(g):
        for col, cell in enumerate(row):
            if cell == "#":
                cv.fill_rect(x + col * scale, y + r * scale, scale, scale, color)


def draw_text(cv, x, y, text, scale, color, align="left", max_x=None):
    """Draw one line. align may be 'left' or 'center' around x."""
    w = text_width(text, scale)
    if align == "center":
        x = x - w // 2
    elif align == "right" and max_x is not None:
        x = max_x - w
    for i, ch in enumerate(text):
        draw_char(cv, x + i * 6 * scale, y, ch, scale, color)
    return x + w


def draw_block(cv, x, y, text, scale, color, max_width, line_gap=4):
    """Draw wrapped text; returns the y just below the last line."""
    for line in wrap(text, max_width, scale):
        draw_text(cv, x, y, line, scale, color)
        y += 7 * scale + line_gap
    return y


# --- PNG encoding (pure stdlib, deterministic) -----------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        start = y * cv.w * 3
        raw += cv.px[start:start + cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


# --- illustrations ---------------------------------------------------------
def draw_flags(cv, x, y, w, h):
    """Three flags on poles above a summit table: US, China, Russia."""
    # table
    cv.fill_rect(x, y + h - 26, w, 26, BROWN)
    cv.fill_rect(x, y + h - 30, w, 4, (150, 108, 66))
    # three seated figures behind the table
    for i, col in enumerate((NAVY, RED, BLUE)):
        fx = x + 40 + i * 105
        cv.circle(fx + 22, y + h - 58, 13, col)
        cv.fill_rect(fx, y + h - 44, 44, 18, col)
    # poles and flags
    pole_x = [x + 30, x + 150, x + 270]
    flag_w, flag_h = 92, 52
    for px in pole_x:
        cv.fill_rect(px, y, 4, h - 30, INK)
        cv.circle(px + 2, y - 2, 4, GOLD)
    # US flag
    fx, fy = pole_x[0] + 4, y + 4
    for s in range(7):
        cv.fill_rect(fx, fy + s * 8, flag_w, 8,
                     RED if s % 2 == 0 else WHITE)
    cv.fill_rect(fx, fy, 38, 28, NAVY)
    for r in range(3):
        for c in range(4):
            cv.fill_rect(fx + 5 + c * 9, fy + 4 + r * 9, 3, 3, WHITE)
    # China flag
    fx, fy = pole_x[1] + 4, y + 4
    cv.fill_rect(fx, fy, flag_w, flag_h, RED)
    cv.star(fx + 18, fy + 18, 11, GOLD)
    for sx, sy in ((52, 10), (66, 16), (68, 30), (54, 38)):
        cv.star(fx + sx, fy + sy, 5, GOLD)
    # Russia flag
    fx, fy = pole_x[2] + 4, y + 4
    cv.fill_rect(fx, fy, flag_w, 18, WHITE)
    cv.fill_rect(fx, fy + 18, flag_w, 17, BLUE)
    cv.fill_rect(fx, fy + 35, flag_w, 17, RED)


def draw_scales(cv, x, y, w, h):
    """Scales of justice with a gavel, on a pale blue panel."""
    cv.fill_rect(x, y, w, h, LIGHT_BLUE)
    cx = x + w // 2
    base_y = y + h - 18
    # stand
    cv.fill_rect(cx - 4, y + 30, 8, base_y - y - 30, NAVY)
    cv.fill_rect(cx - 42, base_y, 84, 8, NAVY)
    cv.fill_rect(cx - 30, y + 22, 60, 8, NAVY)
    # crossbar
    cv.fill_rect(x + 22, y + 42, w - 44, 6, NAVY)
    # pans
    for px in (x + 34, x + w - 34):
        cv.line(px, y + 48, px - 26, y + 86, NAVY, 3)
        cv.line(px, y + 48, px + 26, y + 86, NAVY, 3)
        cv.triangle([(px - 28, y + 86), (px + 28, y + 86),
                     (px, y + 104)], GOLD)


def draw_cyclone(cv, x, y, w, h):
    """A swirling storm over the sea, with a small house and rain."""
    cv.fill_rect(x, y, w, h, LIGHT_BLUE)
    cx, cy = x + w // 2 - 10, y + h // 2 - 6
    # spiral bands
    for r, col in ((66, TEAL), (52, BLUE), (38, NAVY), (24, TEAL),
                   (12, WHITE)):
        cv.circle(cx, cy, r, col, fill=False)
    cv.circle(cx, cy, 8, WHITE)
    # rain streaks
    for rx in range(x + 14, x + w - 10, 26):
        cv.line(rx, y + 12, rx - 6, y + 30, BLUE, 2)
    # sea
    cv.fill_rect(x, y + h - 30, w, 30, BLUE)
    cv.hline(x, y + h - 30, w, WHITE, 3)
    # small house on the shore, right
    hx, hy = x + w - 74, y + h - 66
    cv.fill_rect(hx, hy + 16, 44, 20, RED)
    cv.triangle([(hx - 6, hy + 18), (hx + 50, hy + 18),
                 (hx + 22, hy - 6)], BROWN)
    cv.fill_rect(hx + 17, hy + 26, 10, 10, WHITE)


def draw_calendar(cv, x, y, w, h):
    """A calendar page marked 2027 beside a clock."""
    cv.fill_rect(x, y, w, h, LIGHT_GOLD)
    # calendar page
    px, py, pw, ph = x + 18, y + 16, 118, h - 32
    cv.fill_rect(px, py, pw, ph, WHITE)
    cv.rect(px, py, pw, ph, INK, 3)
    cv.fill_rect(px, py, pw, 30, RED)
    cv.fill_rect(px + 22, py - 6, 8, 16, INK)
    cv.fill_rect(px + pw - 30, py - 6, 8, 16, INK)
    draw_text(cv, px + pw // 2, py + 44, "2027", 4, INK, align="center")
    draw_text(cv, px + pw // 2, py + 84, "JAN 1", 2, RED, align="center")
    # clock
    cx, cy = x + w - 58, y + h // 2
    cv.circle(cx, cy, 42, WHITE)
    cv.circle(cx, cy, 42, INK, fill=False)
    cv.circle(cx, cy, 4, INK)
    cv.line(cx, cy, cx, cy - 26, INK, 3)
    cv.line(cx, cy, cx + 20, cy + 10, INK, 3)


def draw_chart(cv, x, y, w, h):
    """A rising market chart with bars and an arrow."""
    cv.fill_rect(x, y, w, h, LIGHT_GREEN)
    # bars
    bx = x + 22
    for i, bh in enumerate((30, 46, 40, 60, 80)):
        cv.fill_rect(bx + i * 34, y + h - 22 - bh, 22, bh,
                     BLUE if i < 4 else GREEN)
    # rising line with arrowhead, ending at the tallest bar
    pts = [(x + 20, y + h - 30), (x + 62, y + h - 56),
           (x + 104, y + h - 48), (x + 146, y + h - 76),
           (x + 188, y + h - 96)]
    for a, b in zip(pts, pts[1:]):
        cv.line(a[0], a[1], b[0], b[1], RED, 4)
    ex, ey = pts[-1]
    cv.triangle([(ex, ey), (ex - 16, ey + 4), (ex - 2, ey + 16)], RED)
    # dollar badge
    cv.circle(x + w - 40, y + 34, 20, GOLD)
    draw_text(cv, x + w - 40, y + 24, "$", 3, WHITE, align="center")


def draw_voyager(cv, x, y, w, h):
    """Voyager 1 in deep space: stars, a probe with a dish, a dotted path."""
    cv.fill_rect(x, y, w, h, DARK)
    # stars
    for sx, sy, s in ((18, 16, 2), (70, 40, 3), (120, 12, 2),
                      (170, 30, 2), (210, 14, 3), (250, 44, 2),
                      (300, 18, 2), (40, 62, 2), (150, 58, 2),
                      (280, 60, 3), (330, 30, 2), (100, 70, 2)):
        cv.fill_rect(x + sx, y + sy, s, s, WHITE)
        cv.fill_rect(x + sx - 2, y + sy + s // 2, s + 4, 1, WHITE)
    # dotted trajectory, bottom-left rising to the probe
    for k in range(0, 170, 14):
        cv.fill_rect(x + 20 + k, y + h - 40 - k // 6, 5, 5, GOLD)
    # probe body
    px, py = x + 230, y + 16
    cv.fill_rect(px, py, 56, 26, GOLD)
    cv.fill_rect(px + 56, py + 7, 22, 12, (200, 170, 90))
    # dish below the body, kept inside the panel
    cv.line(px + 26, py + 26, px + 12, py + 50, WHITE, 3)
    cv.triangle([(px - 8, py + 50), (px + 32, py + 50),
                 (px + 12, py + 60)], WHITE)
    # boom antenna, top right
    cv.line(px + 56, py + 8, px + 78, py - 6, WHITE, 3)
    cv.circle(px + 80, py - 8, 4, RED)


# --- page layout -----------------------------------------------------------
M = 24            # side margin
CW = W - 2 * M    # content width


def story_cell(cv, x, y, w, h, tag, art, headline, sub, bg):
    cv.fill_rect(x, y, w, h, PANEL)
    cv.rect(x, y, w, h, INK, 3)
    draw_text(cv, x + 14, y + 12, tag, 1, RED)
    art(cv, x + 14, y + 30, w - 28, 108)
    yy = y + 30 + 108 + 12
    yy = draw_block(cv, x + 14, yy, headline, 2, INK, w - 28, line_gap=3)
    draw_block(cv, x + 14, yy + 2, sub, 2, GREY, w - 28, line_gap=3)


def build():
    cv = Canvas(W, H, PAPER)
    # frame
    cv.rect(10, 10, W - 20, H - 20, INK, 4)

    # --- masthead ---
    draw_text(cv, W // 2, 34, "THE WORLD", 8, NAVY_DK, align="center")
    cv.hline(M + 60, 102, CW - 120, INK, 3)
    draw_text(cv, W // 2, 114, "FRIDAY, 20 NOVEMBER 2026", 3, RED,
              align="center")
    cv.hline(M, 146, CW, INK, 4)

    # --- lead story: trilateral summit ---
    hx, hy, hw, hh = M, 160, CW, 216
    cv.fill_rect(hx, hy, hw, hh, PANEL)
    cv.rect(hx, hy, hw, hh, INK, 3)
    draw_text(cv, hx + 16, hy + 12, "LEAD STORY - SHENZHEN, CHINA", 2,
              RED)
    draw_flags(cv, hx + 16, hy + 44, 380, 158)
    tx = hx + 420
    tw = hw - 420 - 18
    yy = draw_block(cv, tx, hy + 48, "TRUMP, XI AND PUTIN MEET IN CHINA",
                    3, INK, tw, line_gap=5)
    draw_block(cv, tx, yy + 6,
               "FIRST THREE-WAY SUMMIT OF THE THREE LEADERS ENDS WITH "
               "A JOINT PEACE DECLARATION", 2, NAVY, tw, line_gap=4)

    # --- four stories in a 2x2 grid ---
    gw = (CW - 16) // 2
    gh = 216
    gy = 392
    story_cell(cv, M, gy, gw, gh, "THE HAGUE - JUSTICE",
               draw_scales,
               "MYANMAR COMMITTED GENOCIDE, UN COURT RULES",
               "HISTORIC ROHINGYA VERDICT", LIGHT_BLUE)
    story_cell(cv, M + gw + 16, gy, gw, gh, "INDIA - WEATHER",
               draw_cyclone,
               "CYCLONE AKVAN NEARS ODISHA COAST",
               "300,000 EVACUATED AS LANDFALL LOOMS", LIGHT_BLUE)
    story_cell(cv, M, gy + gh + 16, gw, gh, "WASHINGTON - IRAN",
               draw_calendar,
               "TRUMP PUTS IRAN DECISION OFF TO 2027",
               "NO RUSH, HE SAYS - DECISION IN 2027",
               LIGHT_GOLD)
    story_cell(cv, M + gw + 16, gy + gh + 16, gw, gh, "BUSINESS - TECH",
               draw_chart,
               "ANTHROPIC LISTS, FIRST PURE AI COMPANY ON MARKET",
               "REPORTED $1.5 TRILLION DEBUT",
               LIGHT_GREEN)

    # --- bottom strip: Voyager ---
    sx, sy, sw, sh = M, 856, CW, 116
    cv.fill_rect(sx, sy, sw, sh, PANEL)
    cv.rect(sx, sy, sw, sh, INK, 3)
    draw_text(cv, sx + 16, sy + 10, "SPACE - SCIENCE", 1, RED)
    draw_voyager(cv, sx + 16, sy + 28, 360, 78)
    tx = sx + 400
    tw = sw - 400 - 18
    yy = draw_block(cv, tx, sy + 30, "VOYAGER 1 REACHES A LIGHT-DAY "
                    "FROM EARTH", 3, INK, tw, line_gap=5)
    draw_block(cv, tx, yy + 4,
               "NASA CONFIRMS THE MILESTONE", 2, NAVY, tw, line_gap=4)

    # --- footer ---
    draw_text(cv, W // 2, 986, "SIX STORIES FROM FRIDAY 20 NOVEMBER 2026",
              2, INK, align="center")
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    cv = build()
    size = write_png(cv, path)
    print(f"wrote {path}: {cv.w}x{cv.h}, {size} bytes")


if __name__ == "__main__":
    main()
