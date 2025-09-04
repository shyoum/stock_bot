@echo off
title Git 자동 업데이트
:: 관리자 권한 확인 및 자동 승격
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 관리자 권한으로 재실행합니다...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
cd /d "C:\Users\felab\stock_bot"
echo Git 작업 시작...
git add .
git commit -m "Update: %date% %time%"
git push origin main
echo 완료!
pause