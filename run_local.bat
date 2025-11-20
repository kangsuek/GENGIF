@echo off
REM 로컬 개발 서버 실행 스크립트 (Windows)

echo 🚀 Starting GIF Generator Web App locally...
echo.

REM Python 확인
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    where python3 >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python3
    ) else (
        echo ❌ Python not found. Please install Python 3.11+
        pause
        exit /b 1
    )
)

echo Using: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

REM 의존성 설치
echo 📦 Installing dependencies...
%PYTHON_CMD% -m pip install -r requirements.txt
echo.

echo ✅ Starting Flask development server...
echo 🌐 Open http://localhost:8080 in your browser
echo.
echo Press Ctrl+C to stop the server
echo.

REM Flask 개발 서버 실행
set FLASK_APP=app.py
set FLASK_ENV=development
%PYTHON_CMD% app.py
