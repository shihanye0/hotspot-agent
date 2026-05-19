@echo off
schtasks /Create /TN "HotspotAgent" /TR "C:\Users\Lenovo\anaconda3\python E:\hotspot-agent\main.py" /SC DAILY /ST 09:00 /F
echo Done
pause
