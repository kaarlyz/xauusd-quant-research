import subprocess
import numpy as np
import os

WIDTH = 1080
HEIGHT = 1920
FPS = 60 # 60 FPS untuk ultra-smooth
OUT_PATH = "/home/vallencia/pola_n_smooth.mp4"

# Color Palette (Dark Theme Modern Quant with Neon Accents)
BG_COLOR = np.array([10, 14, 20], dtype=np.uint8)         # Deep Space Navy #0A0E14
GRID_COLOR = np.array([22, 30, 42], dtype=np.uint8)       # Subtle grid
BULL_COLOR = np.array([0, 230, 118], dtype=np.uint8)      # Neon Bull Teal #00E676
BULL_GLOW = np.array([0, 100, 60], dtype=np.uint8)        # Glow green
BEAR_COLOR = np.array([255, 61, 0], dtype=np.uint8)       # Neon Bear Coral #FF3D00
BEAR_GLOW = np.array([120, 30, 15], dtype=np.uint8)       # Glow red
ACCENT_BLUE = np.array([41, 121, 255], dtype=np.uint8)   # Electric Blue #2979FF
GOLD_COLOR = np.array([255, 215, 0], dtype=np.uint8)     # Pure Gold #FFD700
WHITE = np.array([255, 255, 255], dtype=np.uint8)

# Data Lilin Pola N (Open, High, Low, Close)
CANDLES = [
    # Swing A -> B (Momentum Bullish)
    (2710, 2719, 2708, 2718), # 0
    (2718, 2728, 2717, 2726), # 1
    (2726, 2738, 2725, 2736), # 2
    (2736, 2748, 2734, 2747), # 3 (High hb = 2748)
    # Swing B -> C (Pullback Konsolidasi)
    (2747, 2748, 2737, 2739), # 4
    (2739, 2741, 2726, 2727), # 5 (Low lc = 2726)
    (2727, 2735, 2726, 2734), # 6
    (2734, 2745, 2732, 2743), # 7
    # Breakout & Explosion ke TP
    (2743, 2760, 2741, 2758), # 8 (Breakout tembus 2748)
    (2758, 2772, 2756, 2770), # 9 (TP Hit 2770!)
    (2770, 2780, 2768, 2779), # 10 (Follow-through)
]

PRICE_MIN = 2700
PRICE_MAX = 2785
CHART_TOP = 420
CHART_BOTTOM = 1460
CHART_LEFT = 80
CHART_RIGHT = 1000

def price_to_y(price):
    ratio = (price - PRICE_MIN) / (PRICE_MAX - PRICE_MIN)
    return int(CHART_BOTTOM - ratio * (CHART_BOTTOM - CHART_TOP))

def candle_to_x(idx, total):
    step = (CHART_RIGHT - CHART_LEFT) // (total + 1)
    return CHART_LEFT + (idx + 1) * step

# Cubic Easing Out: t in [0, 1] -> smooth decelerate
def ease_out_cubic(t):
    return 1.0 - (1.0 - t) ** 3

def draw_rect(frame, x1, y1, x2, y2, color):
    x1, x2 = max(0, min(x1, x2)), min(WIDTH, max(x1, x2))
    y1, y2 = max(0, min(y1, y2)), min(HEIGHT, max(y1, y2))
    if x2 > x1 and y2 > y1:
        frame[y1:y2, x1:x2] = color

def draw_glow_rect(frame, x1, y1, x2, y2, color, glow_color, glow_size=4):
    # Outer glow
    draw_rect(frame, x1 - glow_size, y1 - glow_size, x2 + glow_size, y2 + glow_size, glow_color)
    # Core body
    draw_rect(frame, x1, y1, x2, y2, color)

def draw_line(frame, x1, y1, x2, y2, color, width=2):
    if x1 == x2:
        draw_rect(frame, x1 - width//2, min(y1, y2), x1 + width//2 + 1, max(y1, y2), color)
    elif y1 == y2:
        draw_rect(frame, min(x1, x2), y1 - width//2, max(x1, x2), y1 + width//2 + 1, color)

def render_smooth_video():
    cmd = [
        'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{WIDTH}x{HEIGHT}', '-pix_fmt', 'rgb24', '-r', str(FPS),
        '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p',
        OUT_PATH
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    base_frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    base_frame[:] = BG_COLOR

    # Subtle horizontal grid lines with dashed feel
    for p in range(PRICE_MIN, PRICE_MAX + 1, 10):
        y = price_to_y(p)
        for gx in range(CHART_LEFT, CHART_RIGHT, 16):
            draw_rect(base_frame, gx, y, gx + 8, y + 1, GRID_COLOR)

    total_candles = len(CANDLES)
    # Lebih cepat: 14 frame per candle di 60 FPS = 0.23 detik per candle (snappy & dynamic)
    frames_per_candle = 14
    c_width = 38

    for c_idx in range(total_candles):
        o, h, l, c = CANDLES[c_idx]
        is_bull = c >= o
        body_col = BULL_COLOR if is_bull else BEAR_COLOR
        glow_col = BULL_GLOW if is_bull else BEAR_GLOW
        x_center = candle_to_x(c_idx, total_candles)

        for f in range(frames_per_candle):
            # Smooth cubic ease
            t = (f + 1) / frames_per_candle
            alpha = ease_out_cubic(t)

            curr_c = o + (c - o) * alpha
            curr_h = max(o, curr_c, o + (h - o) * alpha)
            curr_l = min(o, curr_c, o + (l - o) * alpha)

            frame = base_frame.copy()

            # Lilin-lilin lampau
            for past_i in range(c_idx):
                po, ph, pl, pc = CANDLES[past_i]
                p_bull = pc >= po
                p_col = BULL_COLOR if p_bull else BEAR_COLOR
                p_glow = BULL_GLOW if p_bull else BEAR_GLOW
                px = candle_to_x(past_i, total_candles)

                # Wick
                draw_line(frame, px, price_to_y(ph), px, price_to_y(pl), p_col, 2)
                # Body with subtle glow
                y_top = price_to_y(max(po, pc))
                y_bot = price_to_y(min(po, pc))
                draw_glow_rect(frame, px - c_width//2, y_top, px + c_width//2, y_bot, p_col, p_glow, glow_size=2)

            # Lilin yang sedang berdetak / tumbuh (Active Candle dengan pulse glow)
            pulse = int(3 * np.sin(f * 0.4)) + 4
            draw_line(frame, x_center, price_to_y(curr_h), x_center, price_to_y(curr_l), body_col, 3)
            y_top = price_to_y(max(o, curr_c))
            y_bot = price_to_y(min(o, curr_c))
            draw_glow_rect(frame, x_center - c_width//2, y_top, x_center + c_width//2, y_bot, body_col, glow_col, glow_size=pulse)

            # Swing Points & Bounding Box
            if c_idx >= 5:
                hb_y = price_to_y(2748) # Resistance hb
                lc_y = price_to_y(2726) # Support lc
                box_x1 = candle_to_x(3, total_candles) - 15
                box_x2 = candle_to_x(min(c_idx + 1, total_candles - 1), total_candles) + 30

                # Garis Resistance Gold tebal
                draw_line(frame, box_x1, hb_y, box_x2, hb_y, GOLD_COLOR, 3)
                # Garis Support Cyan tebal
                draw_line(frame, box_x1, lc_y, box_x2, lc_y, ACCENT_BLUE, 3)

            # Breakout Signal Flash
            if c_idx >= 8:
                tp_y = price_to_y(2770)
                sl_y = price_to_y(2725)
                # Garis TP hijau neon
                draw_line(frame, candle_to_x(8, total_candles), tp_y, CHART_RIGHT, tp_y, BULL_COLOR, 3)
                # Garis SL merah neon
                draw_line(frame, candle_to_x(8, total_candles), sl_y, CHART_RIGHT, sl_y, BEAR_COLOR, 3)

            proc.stdin.write(frame.tobytes())

    # Freeze frame akhir selama 2 detik (120 frame di 60 FPS)
    for _ in range(120):
        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print("Ultra-Smooth Video Generated:", OUT_PATH)

if __name__ == "__main__":
    render_smooth_video()
