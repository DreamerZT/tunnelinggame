@echo off
chcp 65001 > nul
setlocal

echo [1/2] (필요 시) pygbag 설치/업데이트...
python -m pip install -r requirements.txt

echo.
echo [2/2] 웹(브라우저) 빌드 생성 중...
REM pygbag 옵션은 반드시 파일 경로 뒤가 아니라 앞에 와야 합니다.
python -m pygbag --build tunneling_game.py

echo.
echo ✅ 완료! 산출물 폴더: build\web
echo - build\web\index.html
echo - build\web\tunnelinggame_app.apk
echo.
echo 다음 단계:
echo - 로컬에서 확인: 웹로컬실행.bat 실행 후 http://localhost:8000 접속
echo - 사내 배포: build\web 폴더를 사내 웹서버(정적 호스팅)에 업로드
echo.
pause


