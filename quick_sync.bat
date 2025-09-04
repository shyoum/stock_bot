@echo off
title Git 자동 업데이트
chcp 65001 > nul

:: 관리자 권한 확인 및 자동 승격
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 관리자 권한으로 재실행합니다...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

cd /d "C:\Users\felab\stock_bot"

echo [%date% %time%] Git 작업 시작...

:: Git 상태 확인
git status --porcelain > temp_status.txt
if %errorlevel% neq 0 (
    echo Git 저장소가 아니거나 오류가 발생했습니다.
    del temp_status.txt 2>nul
    timeout /t 3 /nobreak >nul
    exit /b
)

:: 변경사항이 있는지 확인
for /f %%i in (temp_status.txt) do (
    set HAS_CHANGES=1
    goto :has_changes
)
del temp_status.txt
echo 변경사항이 없습니다. 업데이트를 건너뜁니다.
exit /b

:has_changes
del temp_status.txt
echo 변경사항을 감지했습니다. Git 업데이트를 진행합니다...

git add .
if %errorlevel% neq 0 (
    echo Git add 실패
    timeout /t 3 /nobreak >nul
    exit /b
)

git commit -m "Auto-update: %date% %time%"
if %errorlevel% neq 0 (
    echo Git commit 실패 또는 커밋할 내용이 없습니다.
    timeout /t 3 /nobreak >nul
    exit /b
)

git push origin main
if %errorlevel% neq 0 (
    echo Git push 실패
    timeout /t 3 /nobreak >nul
    exit /b
)

echo [%date% %time%] Git 업데이트 완료!
timeout /t 2 /nobreak >nul