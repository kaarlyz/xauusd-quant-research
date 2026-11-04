#!/bin/bash
ffmpeg -y -i /home/vallencia/pola_n_failed_market.mp4 -vf "
drawtext=text='BEDAH ANATOMI LOSS KUANTITATIF':x=(w-text_w)/2:y=160:fontsize=44:fontcolor=white:box=1:boxcolor=black:boxborderw=10,
drawtext=text='KASUS FALSE BREAKOUT - KENA SL':x=(w-text_w)/2:y=230:fontsize=56:fontcolor=0xEF5350:box=1:boxcolor=black:boxborderw=12,
drawtext=text='1. Resistance hb\: 2784.50':x=100:y=340:fontsize=32:fontcolor=0xF5AB35:enable='gte(t,1.3)',
drawtext=text='2. Support lc\: 2773.59':x=100:y=385:fontsize=32:fontcolor=0x38BDF8:enable='gte(t,1.7)',
drawtext=text='3. BREAKOUT TERPICU (BUY TERISI)':x=100:y=430:fontsize=34:fontcolor=0x4ADE80:enable='gte(t,2.3)',
drawtext=text='4. HARGA REVERSAL - HIT SL (-1.0R)':x=100:y=475:fontsize=36:fontcolor=0xEF5350:enable='gte(t,3.4)',
drawtext=text='SL Terkunci Ketat - Rugi Hanya -1R Saja':x=(w-text_w)/2:y=1680:fontsize=38:fontcolor=white:box=1:boxcolor=black:boxborderw=14
" -c:v libx264 -pix_fmt yuv420p /home/vallencia/pola_n_failed_final.mp4
