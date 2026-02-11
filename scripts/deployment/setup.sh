#!/bin/bash

# ==========================================
# 环境初始化脚本
# ==========================================

set -e

echo "=========================================="
echo "Crypto-Trade 环境初始化"
echo "=========================================="

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装"
    exit 1
fi

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装"
    exit 1
fi

# 创建必要的目录
echo "创建目录结构..."
mkdir -p logs data/{timescaledb,postgresql,redis,rabbitmq,prometheus,grafana}

# 复制环境变量文件
if [ ! -f .env ]; then
    echo "创建.env文件..."
    cp .env.example .env
    echo "请编辑.env文件配置环境变量"
fi

# 设置权限
echo "设置目录权限..."
chmod -R 755 logs data

echo "=========================================="
echo "初始化完成！"
echo "=========================================="
echo "下一步："
echo "1. 编辑 .env 文件配置环境变量"
echo "2. 运行 ./scripts/deployment/start_services.sh 启动服务"
