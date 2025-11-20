#!/bin/bash
# 로컬 개발 서버 실행 스크립트

echo "🚀 Starting GIF Generator Web App locally..."
echo ""

# Python 버전 확인
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Python not found. Please install Python 3.11+"
    exit 1
fi

echo "Using: $PYTHON_CMD"
$PYTHON_CMD --version
echo ""

# 필요한 패키지 설치 여부 확인
echo "Checking dependencies..."
$PYTHON_CMD -c "import flask" 2>/dev/null || {
    echo "📦 Installing dependencies for local development..."
    echo "Using requirements-local.txt (Python 3.9+ compatible)"
    $PYTHON_CMD -m pip install --upgrade pip
    $PYTHON_CMD -m pip install -r requirements-local.txt
}

echo ""
echo "✅ Starting Flask development server..."
echo "🌐 Open http://localhost:5000 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Flask 개발 서버 실행
export FLASK_APP=app.py
export FLASK_ENV=development
export PORT=5000
$PYTHON_CMD app.py
