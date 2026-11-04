#!/usr/bin/env bash
# Headless MT5 Background Runner with Virtual Framebuffer (Xvfb)
# Runs MT5 100% silently in background without showing any windows on your screen.

export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x16 >/dev/null 2>&1 &
XVFB_PID=$!

export WINEPREFIX="/home/vallencia/.wine-mt5"
wine "/home/vallencia/.wine-mt5/drive_c/Program Files/MetaTrader 5/terminal64.exe" /portable /login:34847308 /server:"VTMarkets-Live 3" >/dev/null 2>&1 &
MT5_PID=$!

echo "Headless MT5 Server started in background."
echo "Xvfb PID: $XVFB_PID | MT5 PID: $MT5_PID"

# Trap to kill both on exit
wait $MT5_PID
kill $XVFB_PID 2>/dev/null
