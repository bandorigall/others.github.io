@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   3초 곡 퀴즈 - 클립 재생성
echo ============================================
echo.
python build_quiz.py
if errorlevel 1 (
  echo.
  echo [오류] 위 메시지를 확인하세요.
)
echo.
pause
