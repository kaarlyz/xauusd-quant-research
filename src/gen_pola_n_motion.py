import subprocess
import numpy as np
import os

WIDTH = 1080
HEIGHT = 1920
FPS = 30
OUT_PATH = "/home/vallencia/pola_n_motion_candle.mp4"

# Color Palette (Dark Theme Modern Quant)
BG_COLOR = np.array([13, 17, 23], dtype=np.uint8)       # Dark Navy #0D1117
GRID_COLOR = np.array([25, 33, 44], dtype=np.uint8)     # Subtle grid
BULL_COLOR = np.array([38, 166, 154], dtype=np.uint8)   # Teal/Green #26A69A
BEAR_COLOR = np.array([239, 83, 80], dtype=np.uint8)    # Coral/Red #EF5350
TEXT_COLOR = np.array([240, 246, 252], dtype=np.uint8)  # White #F0F6FC
ACCENT_BLUE = np.array([88, 166, 255], dtype=np.uint8) # Neon Blue #58A6FF
GOLD_COLOR = np.array([245, 171, 53], dtype=np.uint8)   # Gold #F5AB35
BOX_FILL = np.array([30, 45, 65], dtype=np.uint8)       # Translucent box

# Data Lilin Contoh Pola N (Open, High, Low, Close)
# Membentuk Gelombang Pola N Baku:
# Swing Low (Point A) -> Swing High (Point B) -> Pullback (Point C) -> Breakout N (Point D)
CANDLES = [
    # Fase 1: Swing A -> B (Impuls Naik)
    (2710, 2718, 2708, 2716), # 0
    (2716, 2725, 2715, 2723), # 1
    (2723, 2736, 2722, 2734), # 2
    (2734, 2748, 2732, 2745), # 3 (High hb = 2748)
    # Fase 2: Retracement B -> C (Pullback Santai)
    (2745, 2746, 2735, 2738), # 4
    (2738, 2740, 2726, 2728), # 5 (Low lc = 2726)
    (2728, 2735, 2727, 2733), # 6
    # Fase 3: Persiapan Breakout
    (2733, 2744, 2731, 2742), # 7
    # Fase 4: Breakout Pola N (Tembus hb 2748)
    (2742, 2758, 2740, 2756), # 8 (Breakout Triggered!)
    (2756, 2772, 2754, 2770), # 9 (TP Hit 1:1.5!)
    (2770, 2780, 2768, 2778), # 10
]

PRICE_MIN = 2700
PRICE_MAX = 2785
CHART_TOP = 450
CHART_BOTTOM = 1450
CHART_LEFT = 100
CHART_RIGHT = 980

def price_to_y(price):
    ratio = (price - PRICE_MIN) / (PRICE_MAX - PRICE_MIN)
    return int(CHART_BOTTOM - ratio * (CHART_BOTTOM - CHART_TOP))

def candle_to_x(idx, total):
    step = (CHART_RIGHT - CHART_LEFT) // (total + 1)
    return CHART_LEFT + (idx + 1) * step

def draw_rect(frame, x1, y1, x2, y2, color, fill=True):
    x1, x2 = max(0, min(x1, x2)), min(WIDTH, max(x1, x2))
    y1, y2 = max(0, min(y1, y2)), min(HEIGHT, max(y1, y2))
    if fill:
        frame[y1:y2, x1:x2] = color
    else:
        frame[y1:y2, x1:x1+2] = color
        frame[y1:y2, x2-2:x2] = color
        frame[y1:y1+2, x1:x2] = color
        frame[y2-2:y2, x1:x2] = color

def draw_line(frame, x1, y1, x2, y2, color, width=2):
    # Simple Bresenham or axis-aligned
    if x1 == x2:
        draw_rect(frame, x1 - width//2, min(y1, y2), x1 + width//2 + 1, max(y1, y2), color)
    elif y1 == y2:
        draw_rect(frame, min(x1, x2), y1 - width//2, max(x1, x2), y1 + width//2 + 1, color)

def render_motion_video():
    cmd = [
        'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{WIDTH}x{HEIGHT}', '-pix_fmt', 'rgb24', '-r', str(FPS),
        '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        OUT_PATH
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Base Background Canvas
    base_frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    base_frame[:] = BG_COLOR

    # Draw Grid Lines
    for p in range(PRICE_MIN, PRICE_MAX + 1, 10):
        y = price_to_y(p)
        draw_line(base_frame, CHART_LEFT, y, CHART_RIGHT, y, GRID_COLOR, 1)

    # Animasi Lilin Bertahap (Step by Step)
    total_candles = len(CANDLES)
    num_frames_per_candle = 18 # 0.6 detik per lilin
    
    # We will build frames progressively
    for c_idx in range(total_candles):
        o, h, l, c = CANDLES[c_idx]
        is_bull = c >= o
        body_col = BULL_COLOR if is_bull else BEAR_COLOR
        x_center = candle_to_x(c_idx, total_candles)
        c_width = 36

        # Animasi formasi 1 lilin (tumbuh dari Open ke Close)
        for f in range(num_frames_per_candle):
            alpha = (f + 1) / num_frames_per_candle
            curr_c = o + (c - o) * alpha
            curr_h = max(o, curr_c, o + (h - o) * alpha)
            curr_l = min(o, curr_c, o + (l - o) * alpha)

            frame = base_frame.copy()

            # Gambarkan semua lilin yang sudah selesai sebelumnya
            for past_i in range(c_idx):
                po, ph, pl, pc = CANDLES[past_i]
                p_bull = pc >= po
                p_col = BULL_COLOR if p_bull else BEAR_COLOR
                px = candle_to_x(past_i, total_candles)
                # Wick
                draw_line(frame, px, price_to_y(ph), px, price_to_y(pl), p_col, 2)
                # Body
                y_top = price_to_y(max(po, pc))
                y_bot = price_to_y(min(po, pc))
                draw_rect(frame, px - c_width//2, y_top, px + c_width//2, y_bot, p_col)

            # Gambarkan lilin yang sedang tumbuh sekarang
            draw_line(frame, x_center, price_to_y(curr_h), x_center, price_to_y(curr_l), body_col, 2)
            y_top = price_to_y(max(o, curr_c))
            y_bot = price_to_y(min(o, curr_c))
            draw_rect(frame, x_center - c_width//2, y_top, x_center + c_width//2, y_bot, body_col)

            # Jika sudah mencapai fase Swing B dan C (setelah candle 5):
            # Gambar KOTAK POLA N (Bounding Box S/R)
            if c_idx >= 5:
                hb_y = price_to_y(2748) # Swing High
                lc_y = price_to_y(2726) # Swing Low
                box_x1 = candle_to_x(3, total_candles) - 20
                box_x2 = candle_to_x(min(c_idx + 1, total_candles - 1), total_candles) + 40

                # Garis Resistance hb
                draw_line(frame, box_x1, hb_y, box_x2, hb_y, GOLD_COLOR, 3)
                # Garis Support lc
                draw_line(frame, box_x1, lc_y, box_x2, lc_y, ACCENT_BLUE, 3)

            # Jika sudah di candle 8 (Breakout)
            if c_idx >= 8:
                tp_y = price_to_y(2770)
                sl_y = price_to_y(2725)
                # Garis TP hijau
                draw_line(frame, candle_to_x(8, total_candles), tp_y, CHART_RIGHT, tp_y, BULL_COLOR, 3)
                # Garis SL merah
                draw_line(frame, candle_to_x(8, total_candles), sl_y, CHART_RIGHT, sl_y, BEAR_COLOR, 3)

            proc.stdin.write(frame.tobytes())

    # Freeze frame akhir selama 2 detik (60 frame) agar audiens puas melihat hasilnya
    for _ in range(60):
        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print("Video Render Selesai:", OUT_PATH)

if __name__ == "__main__":
    render_motion_video()
