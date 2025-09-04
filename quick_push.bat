@echo off
cd /d "C:\Users\felab\stock_bot"
git add .
git commit -m "Update: %date% %time%"
git push origin main
pause