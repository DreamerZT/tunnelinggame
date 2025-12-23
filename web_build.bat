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
echo [추가] 로컬 실행 스크립트를 build\web 에 복사합니다...
if not exist "build\web" (
  echo ❌ build\web 폴더가 없습니다. 빌드가 실패했을 수 있습니다.
  pause
  exit /b 1
)
copy /Y "web_run_local_ps.bat" "build\web\web_run_local_ps.bat" > nul
copy /Y "web_run_local.ps1" "build\web\web_run_local.ps1" > nul

echo.
echo ✅ 완료! 산출물 폴더: build\web
echo - build\web\index.html
echo - build\web\tunnelinggame_app.apk
echo - build\web\web_run_local_ps.bat  (Python 없이 실행)
echo - build\web\web_run_local.ps1
echo.
echo 다음 단계:
echo - 로컬에서 확인: build\web\web_run_local_ps.bat 실행 후 안내된 주소로 접속
echo - 사내 배포: build\web 폴더를 사내 웹서버(정적 호스팅)에 업로드
echo.
pause


