#!/bin/bash
ffmpeg -y -i /home/vallencia/pola_n_motion_candle.mp4 -vf "
drawtext=text='BEDAH STRATEGI KUANTITATIF':x=(w-text_w)/2:y=180:fontsize=48:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=10,
drawtext=text='POLA N BAKU + EXPIRED RULE':x=(w-text_w)/2:y=260:fontsize=64:fontcolor=0xF5AB35:box=1:boxcolor=black@0.7:boxborderw=12,
drawtext=text='1. Deteksi Swing High (hb)':x=120:y=380:fontsize=36:fontcolor=0xF5AB35:enable='gte(t,2.0)',
drawtext=text='2. Deteksi Swing Low (lc)':x=120:y=430:fontsize=36:fontcolor=0x58A6FF:enable='gte(t,3.2)',
drawtext=text='3. BREAKOUT TRIGGER (BUY STOP)':x=120:y=480:fontsize=36:fontcolor=0x26A69A:enable='gte(t,4.8)',
drawtext=text='4. TAKE PROFIT HIT (+1.5R)':x=120:y=530:fontsize=40:fontcolor=0x26A69A:enable='gte(t,5.5)',
drawtext=text='Win Rate 64 persen - Profit Factor 2.37':x=(w-text_w)/2:y=1650:fontsize=44:fontcolor=white:box=1:boxcolor=0x1E293B@0.8:boxborderw=15
" -c:v libx264 -pix_fmt yuv420p /home/vallencia/pola_n_konten_final.mp4
