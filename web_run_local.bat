@echo off
chcp 65001 > nul
setlocal

if not exist "build\web\index.html" (
  echo ❌ build\web\index.html 이 없습니다.
  echo 먼저 web_build.bat 를 실행해 웹 빌드를 생성해 주세요.
  echo.
  pause
  exit /b 1
)

echo ✅ 로컬 웹 서버를 시작합니다.
echo - 접속: http://localhost:8000
echo - 종료: 이 창을 닫거나 Ctrl+C
echo.

cd /d "build\web"
python -m http.server 8000


