# UTF-8 인코딩 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# 현재 스크립트 위치로 이동
Set-Location $PSScriptRoot

# 게임 실행
python tunneling_game.py

# 종료 대기
Write-Host "`n게임이 종료되었습니다. 아무 키나 눌러 창을 닫으세요..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

