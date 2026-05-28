@echo off
cd /d "C:\Users\aaa\Documents\New project 2\red-culture-rag"
echo 正在启动红色文化智能学习平台...
start "" ".python\python.exe" app.py serve
echo 服务已启动！访问 http://localhost:8000
pause
