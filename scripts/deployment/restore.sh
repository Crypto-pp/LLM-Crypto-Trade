#!/bin/bash

# ==========================================
# 数据恢复脚本
# ==========================================

set -e

if [ -z "$1" ]; then
    echo "用法: ./restore.sh <备份文件时间戳>"
    echo "示例: ./restore.sh 20260208_120000"
    exit 1
fi

BACKUP_DIR="/opt/Crypto-Trade/backups"
TIMESTAMP=$1

echo "=========================================="
echo "开始恢复数据"
echo "=========================================="

# 恢复TimescaleDB
if [ -f "$BACKUP_DIR/timescaledb_$TIMESTAMP.sql.gz" ]; then
    echo "恢复TimescaleDB..."
    gunzip -c $BACKUP_DIR/timescaledb_$TIMESTAMP.sql.gz | docker exec -i crypto-timescaledb psql -U crypto_user crypto_trade
else
    echo "警告: TimescaleDB备份文件不存在"
fi

# 恢复PostgreSQL
if [ -f "$BACKUP_DIR/postgresql_$TIMESTAMP.sql.gz" ]; then
    echo "恢复PostgreSQL..."
    gunzip -c $BACKUP_DIR/postgresql_$TIMESTAMP.sql.gz | docker exec -i crypto-postgresql psql -U config_user crypto_config
else
    echo "警告: PostgreSQL备份文件不存在"
fi

# 恢复Redis
if [ -f "$BACKUP_DIR/redis_$TIMESTAMP.rdb" ]; then
    echo "恢复Redis..."
    docker cp $BACKUP_DIR/redis_$TIMESTAMP.rdb crypto-redis:/data/dump.rdb
    docker restart crypto-redis
else
    echo "警告: Redis备份文件不存在"
fi

echo "=========================================="
echo "恢复完成！"
echo "=========================================="
