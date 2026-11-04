#!/bin/bash
ffmpeg -y -i /home/vallencia/pola_n_smooth.mp4 -vf "
drawtext=text='BEDAH STRATEGI KUANTITATIF':x=(w-text_w)/2:y=170:fontsize=46:fontcolor=white:box=1:boxcolor=black:boxborderw=10,
drawtext=text='POLA N BAKU + EXPIRED RULE':x=(w-text_w)/2:y=245:fontsize=62:fontcolor=0xFFD700:box=1:boxcolor=black:boxborderw=12,
drawtext=text='1. Resistance Swing High (hb)':x=110:y=350:fontsize=34:fontcolor=0xFFD700:enable='gte(t,1.0)',
drawtext=text='2. Support Swing Low (lc)':x=110:y=395:fontsize=34:fontcolor=0x2979FF:enable='gte(t,1.5)',
drawtext=text='3. BREAKOUT TRIGGER (BUY STOP)':x=110:y=440:fontsize=36:fontcolor=0x00E676:enable='gte(t,2.0)',
drawtext=text='4. TAKE PROFIT HIT (+1.5R)':x=110:y=485:fontsize=38:fontcolor=0x00E676:enable='gte(t,2.4)',
drawtext=text='Win Rate 64 persen - PF 2.37 (23.5 Thn Data)':x=(w-text_w)/2:y=1680:fontsize=40:fontcolor=white:box=1:boxcolor=black:boxborderw=14
" -c:v libx264 -pix_fmt yuv420p /home/vallencia/pola_n_smooth_final.mp4
