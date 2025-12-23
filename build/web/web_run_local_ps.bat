@echo off
chcp 65001 > nul
setlocal

REM Python 없이도 실행되도록 PowerShell 내장 HttpListener로 정적 파일 서버를 띄웁니다.
REM (실행 정책 때문에 막힐 수 있어 -ExecutionPolicy Bypass 사용)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0web_run_local.ps1"


