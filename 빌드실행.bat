@echo off
chcp 65001 >nul
echo ===================================
echo 땅굴파기 게임 빌드 중...
echo ===================================
echo.

pyinstaller --clean build_game.spec

echo.
echo ===================================
echo 빌드 완료!
echo 실행 파일 위치: dist\땅굴파기게임.exe
echo ===================================
pause



