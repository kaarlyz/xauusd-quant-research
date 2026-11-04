#!/bin/bash
ffmpeg -y -i /home/vallencia/pola_n_real_market.mp4 -vf "
drawtext=text='BEDAH TRADE ASLI XAUUSD':x=(w-text_w)/2:y=160:fontsize=46:fontcolor=white:box=1:boxcolor=black:boxborderw=10,
drawtext=text='POLA N BAKU + EXPIRED RULE':x=(w-text_w)/2:y=230:fontsize=58:fontcolor=0xF5AB35:box=1:boxcolor=black:boxborderw=12,
drawtext=text='1. Swing High hb\: 2894.22':x=100:y=340:fontsize=32:fontcolor=0xF5AB35:enable='gte(t,1.8)',
drawtext=text='2. Swing Low lc\: 2884.15':x=100:y=385:fontsize=32:fontcolor=0x38BDF8:enable='gte(t,2.2)',
drawtext=text='3. BREAKOUT BUY STOP\: 2894.22':x=100:y=430:fontsize=34:fontcolor=0x4ADE80:enable='gte(t,2.8)',
drawtext=text='4. TAKE PROFIT HIT\: 2909.33 (+1.5R)':x=100:y=475:fontsize=36:fontcolor=0x26A69A:enable='gte(t,3.4)',
drawtext=text='Data Riil M15 XAUUSD - Net +15.1 USD':x=(w-text_w)/2:y=1680:fontsize=38:fontcolor=white:box=1:boxcolor=black:boxborderw=14
" -c:v libx264 -pix_fmt yuv420p /home/vallencia/pola_n_real_final.mp4
