import subprocess
import numpy as np
import polars as pl
import json
import datetime

WIDTH = 1080
HEIGHT = 1920
FPS = 60
OUT_PATH = "/home/vallencia/pola_n_real_market.mp4"

# Ambil Trade Nyata XAUUSD dari Parquet
df = pl.read_parquet('/home/vallencia/Projects/myfxjournal/server/data/market-data/XAUUSD_M1.parquet')
df = df.filter(pl.col('timestamp') >= 1735689600000)
df = df.with_columns(pl.from_epoch('timestamp', time_unit='ms').alias('dt'))
df_m15 = df.group_by_dynamic('dt', every='15m').agg([
    pl.col('open').first(),
    pl.col('high').max(),
    pl.col('low').min(),
    pl.col('close').last(),
    pl.col('timestamp').first(),
]).sort('dt')

# Potong trade asli (Swing High 2894.22 -> Swing Low 2884.15 -> Breakout 2894.22 -> TP Hit 2909.33)
start_idx = 3956
end_idx = 3975 # 20 candle riil
sample = df_m15.slice(start_idx, end_idx - start_idx + 1)

CANDLES = []
for r in sample.iter_rows(named=True):
    CANDLES.append((float(r['open']), float(r['high']), float(r['low']), float(r['close'])))

# Parameter Real Trade
HB = 2894.225 # Swing High candle index 5
LC = 2884.155 # Swing Low candle index 11
TRIGGER_IDX = 13 # Breakout Buy Stop kena di candle 13
TP = 2909.33 # TP 1:1.5 kena di candle 17
SL = 2883.65 # SL aman

PRICE_MIN = min(c[2] for c in CANDLES) - 3.0
PRICE_MAX = max(c[1] for c in CANDLES) + 4.0

CHART_TOP = 430
CHART_BOTTOM = 1450
CHART_LEFT = 70
CHART_RIGHT = 1010

# Styling
BG_COLOR = np.array([11, 15, 23], dtype=np.uint8)         # Obsidian Dark
GRID_COLOR = np.array([24, 32, 47], dtype=np.uint8)       # Grid bar
BULL_COLOR = np.array([38, 166, 154], dtype=np.uint8)     # Real Teal
BULL_WICK = np.array([50, 185, 170], dtype=np.uint8)
BEAR_COLOR = np.array([239, 83, 80], dtype=np.uint8)      # Real Coral Red
BEAR_WICK = np.array([255, 100, 95], dtype=np.uint8)
GOLD_COLOR = np.array([245, 171, 53], dtype=np.uint8)     # hb gold
CYAN_COLOR = np.array([56, 189, 248], dtype=np.uint8)     # lc cyan
ENTRY_GREEN = np.array([74, 222, 128], dtype=np.uint8)

def price_to_y(price):
    ratio = (price - PRICE_MIN) / (PRICE_MAX - PRICE_MIN)
    return int(CHART_BOTTOM - ratio * (CHART_BOTTOM - CHART_TOP))

def candle_to_x(idx, total):
    step = (CHART_RIGHT - CHART_LEFT) // (total + 1)
    return CHART_LEFT + (idx + 1) * step

def ease_out_cubic(t):
    return 1.0 - (1.0 - t) ** 3

def draw_rect(frame, x1, y1, x2, y2, color):
    x1, x2 = max(0, min(x1, x2)), min(WIDTH, max(x1, x2))
    y1, y2 = max(0, min(y1, y2)), min(HEIGHT, max(y1, y2))
    if x2 > x1 and y2 > y1:
        frame[y1:y2, x1:x2] = color

def draw_line(frame, x1, y1, x2, y2, color, width=2):
    if x1 == x2:
        draw_rect(frame, x1 - width//2, min(y1, y2), x1 + width//2 + 1, max(y1, y2), color)
    elif y1 == y2:
        draw_rect(frame, min(x1, x2), y1 - width//2, max(x1, x2), y1 + width//2 + 1, color)

def render_real_market_video():
    cmd = [
        'ffmpeg', '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{WIDTH}x{HEIGHT}', '-pix_fmt', 'rgb24', '-r', str(FPS),
        '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-pix_fmt', 'yuv420p',
        OUT_PATH
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    base_frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    base_frame[:] = BG_COLOR

    # Garis harga horizontal riil
    for p in np.arange(np.floor(PRICE_MIN), np.ceil(PRICE_MAX), 5.0):
        y = price_to_y(p)
        for gx in range(CHART_LEFT, CHART_RIGHT, 14):
            draw_rect(base_frame, gx, y, gx + 7, y + 1, GRID_COLOR)

    total_candles = len(CANDLES)
    # 10 frame per candle @ 60 FPS = 0.16s per candle (sangat cepat & mulus)
    frames_per_candle = 10
    c_width = 30

    for c_idx in range(total_candles):
        o, h, l, c = CANDLES[c_idx]
        is_bull = c >= o
        body_col = BULL_COLOR if is_bull else BEAR_COLOR
        wick_col = BULL_WICK if is_bull else BEAR_WICK
        x_center = candle_to_x(c_idx, total_candles)

        for f in range(frames_per_candle):
            t = (f + 1) / frames_per_candle
            alpha = ease_out_cubic(t)

            curr_c = o + (c - o) * alpha
            curr_h = max(o, curr_c, o + (h - o) * alpha)
            curr_l = min(o, curr_c, o + (l - o) * alpha)

            frame = base_frame.copy()

            # Gambarkan candle-candle riil sebelumnya (lengkap dengan ekor panjang/pendek alami)
            for past_i in range(c_idx):
                po, ph, pl, pc = CANDLES[past_i]
                p_bull = pc >= po
                p_col = BULL_COLOR if p_bull else BEAR_COLOR
                p_wick = BULL_WICK if p_bull else BEAR_WICK
                px = candle_to_x(past_i, total_candles)

                # Sumbu riil (Wick)
                draw_line(frame, px, price_to_y(ph), px, price_to_y(pl), p_wick, 2)
                # Badan lilin (Body)
                y_top = price_to_y(max(po, pc))
                y_bot = price_to_y(min(po, pc))
                draw_rect(frame, px - c_width//2, y_top, px + c_width//2, y_bot, p_col)

            # Candle yang sedang terbentuk
            draw_line(frame, x_center, price_to_y(curr_h), x_center, price_to_y(curr_l), wick_col, 2)
            y_top = price_to_y(max(o, curr_c))
            y_bot = price_to_y(min(o, curr_c))
            draw_rect(frame, x_center - c_width//2, y_top, x_center + c_width//2, y_bot, body_col)

            # Begitu Swing High (hb) dan Swing Low (lc) selesai (setelah candle 11):
            if c_idx >= 11:
                hb_y = price_to_y(HB)
                lc_y = price_to_y(LC)
                box_x1 = candle_to_x(5, total_candles) - 10
                box_x2 = candle_to_x(min(c_idx + 1, total_candles - 1), total_candles) + 20

                # Garis Resistance hb (Gold)
                draw_line(frame, box_x1, hb_y, box_x2, hb_y, GOLD_COLOR, 3)
                # Garis Support lc (Cyan)
                draw_line(frame, box_x1, lc_y, box_x2, lc_y, CYAN_COLOR, 3)

            # Saat candle breakout menyentuh Buy Stop (candle index 13 ke atas)
            if c_idx >= 13:
                entry_y = price_to_y(HB)
                tp_y = price_to_y(TP)
                sl_y = price_to_y(SL)
                x_trigger = candle_to_x(13, total_candles)

                # Garis Entry Hijau Neon
                draw_line(frame, x_trigger, entry_y, CHART_RIGHT, entry_y, ENTRY_GREEN, 2)
                # Garis TP Hijau Tegas
                draw_line(frame, x_trigger, tp_y, CHART_RIGHT, tp_y, BULL_COLOR, 4)
                # Garis SL Merah
                draw_line(frame, x_trigger, sl_y, CHART_RIGHT, sl_y, BEAR_COLOR, 3)

            proc.stdin.write(frame.tobytes())

    # Freeze 2 detik (120 frame di 60fps)
    for _ in range(120):
        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print("Real Market Video Rendered:", OUT_PATH)

if __name__ == "__main__":
    render_real_market_video()
