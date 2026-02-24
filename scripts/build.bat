@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo 智能家居语音助手 - 构建脚本
echo ==========================================

set VERSION=%~1
if "%VERSION%"=="" set VERSION=latest
set IMAGE_NAME=smart-home-assistant

echo.
echo 构建 Docker 镜像: %IMAGE_NAME%:%VERSION%
echo.

docker build -t %IMAGE_NAME%:%VERSION% .

echo.
echo [OK] 镜像构建完成: %IMAGE_NAME%:%VERSION%
echo.
echo 如需标记并推送至仓库:
echo   docker tag %IMAGE_NAME%:%VERSION% your-registry/%IMAGE_NAME%:%VERSION%
echo   docker push your-registry/%IMAGE_NAME%:%VERSION%
echo.
