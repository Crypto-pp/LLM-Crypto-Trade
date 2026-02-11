#!/bin/bash

# ==========================================
# 启动所有服务
# ==========================================

set -e

echo "=========================================="
echo "启动 Crypto-Trade 服务"
echo "=========================================="

# 检查.env文件
if [ ! -f .env ]; then
    echo "错误: .env文件不存在"
    echo "请先运行 ./scripts/deployment/setup.sh"
    exit 1
fi

# 启动服务
echo "启动Docker Compose服务..."
cd /opt/Crypto-Trade
docker-compose -f config/docker-compose.yml up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose -f config/docker-compose.yml ps

echo "=========================================="
echo "服务启动完成！"
echo "=========================================="
echo "访问地址："
echo "- API文档: http://localhost:8000/docs"
echo "- Grafana: http://localhost:3000"
echo "- Prometheus: http://localhost:9090"
echo "- RabbitMQ管理: http://localhost:15672"
