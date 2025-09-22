@echo off
cls
echo =====================================
echo   NaruTalk Beta v0.033 Test System
echo =====================================
echo.
echo 가상환경 활성화 중...
cd /d c:\kdy\Projects\narutalk_upgrade\beta_v0033
call venv\Scripts\activate

echo.
echo 테스트 시스템 실행 중...
echo.
python tests\run_tests.py %*

echo.
echo =====================================
echo 테스트가 완료되었습니다.
echo =====================================
pause