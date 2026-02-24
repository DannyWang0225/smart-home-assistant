#!/bin/bash

set -e

echo "=========================================="
echo "智能家居语音助手 - 停止脚本"
echo "=========================================="

echo ""
echo "停止所有服务..."
echo ""

docker-compose down

echo ""
echo "✓ 服务已停止"
