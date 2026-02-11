#!/bin/bash

# ==========================================
# 数据备份脚本
# ==========================================

set -e

BACKUP_DIR="/opt/Crypto-Trade/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "开始备份数据"
echo "=========================================="

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份TimescaleDB
echo "备份TimescaleDB..."
docker exec crypto-timescaledb pg_dump -U crypto_user crypto_trade | gzip > $BACKUP_DIR/timescaledb_$TIMESTAMP.sql.gz

# 备份PostgreSQL
echo "备份PostgreSQL..."
docker exec crypto-postgresql pg_dump -U config_user crypto_config | gzip > $BACKUP_DIR/postgresql_$TIMESTAMP.sql.gz

# 备份Redis
echo "备份Redis..."
docker exec crypto-redis redis-cli --rdb /data/dump.rdb
docker cp crypto-redis:/data/dump.rdb $BACKUP_DIR/redis_$TIMESTAMP.rdb

# 清理旧备份（保留最近7天）
echo "清理旧备份..."
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete

echo "=========================================="
echo "备份完成！"
echo "备份位置: $BACKUP_DIR"
echo "=========================================="
