@echo off
title Git 자동 업데이트 - 관리자 권한 필수

:: 관리자 권한 확인 및 자동 승격
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo    관리자 권한이 필요합니다
    echo ========================================
    echo.
    echo 관리자 권한으로 재실행합니다...
    timeout /t 2 /nobreak >nul
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo ========================================
echo    관리자 권한으로 실행됩니다
echo ========================================
echo.

:: Git 작업 디렉토리로 이동
echo Git 작업 디렉토리로 이동 중...
cd /d "C:\Users\felab\stock_bot"

:: 현재 디렉토리 확인
echo 현재 디렉토리: %cd%
echo.

:: Git 작업 시작
echo Git 작업을 시작합니다...
echo.

:: Git add
echo [1/3] 변경사항 추가 중...
git add .
if %errorlevel% neq 0 (
    echo 오류: git add 실패
    goto :error
)
echo ✓ 변경사항 추가 완료

:: Git commit
echo [2/3] 커밋 생성 중...
git commit -m "Update: %date% %time%"
if %errorlevel% neq 0 (
    echo 경고: 커밋할 변경사항이 없거나 커밋 실패
    echo 계속 진행합니다...
) else (
    echo ✓ 커밋 생성 완료
)

:: Git push
echo [3/3] 원격 저장소에 푸시 중...
git push origin main
if %errorlevel% neq 0 (
    echo 오류: git push 실패
    goto :error
)
echo ✓ 원격 저장소 푸시 완료

echo.
echo ========================================
echo    모든 Git 작업이 완료되었습니다!
echo ========================================
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo    오류가 발생했습니다!
echo ========================================
echo.
pause
exit /b 1