#!/bin/bash

set -e

echo "=========================================="
echo "智能家居语音助手 - 启动脚本"
echo "=========================================="

mkdir -p data models cache mosquitto/data mosquitto/log

echo ""
echo "启动服务..."
echo ""

docker-compose up -d

echo ""
echo "✓ 服务启动中..."
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo ""
echo "等待服务启动完成..."
sleep 5
docker-compose ps
