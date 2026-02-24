@echo off

echo ==========================================
echo 智能家居语音助手 - 启动脚本
echo ==========================================

if not exist data mkdir data
if not exist models mkdir models
if not exist cache mkdir cache
if not exist mosquitto\data mkdir mosquitto\data
if not exist mosquitto\log mkdir mosquitto\log

echo.
echo 启动服务...
echo.

docker-compose up -d

echo.
echo [OK] 服务启动中...
echo.
echo 查看日志: docker-compose logs -f
echo 停止服务: docker-compose down
echo.
echo 等待服务启动完成...
timeout /t 5 /nobreak >nul
docker-compose ps
echo.
