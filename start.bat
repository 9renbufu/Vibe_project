@echo off
echo ========================================
echo VoiceSketch AI - 启动脚本
echo ========================================
echo.

echo [1/2] 启动后端服务...
start "VoiceSketch Backend" cmd /k "cd backend && E:\Anaconda3\envs\voicesketch\python.exe -m uvicorn app.main:app --reload --port 8000"

echo [2/2] 启动前端服务...
timeout /t 3 /nobreak >nul
start "VoiceSketch Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo 服务启动中...
echo 前端: http://localhost:3000
echo 后端: http://localhost:8000
echo ========================================
echo.
pause
