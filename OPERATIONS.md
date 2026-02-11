# Crypto-Trade 运维手册

## 日常运维任务

### 每日检查

1. **服务健康检查**
```bash
python scripts/management/manage.py health
```

2. **查看告警**
```bash
python scripts/management/monitor.py alerts
```

3. **检查磁盘空间**
```bash
df -h
```

4. **查看日志**
```bash
python scripts/management/manage.py logs api | tail -100
```

### 每周任务

1. **数据备份**
```bash
./scripts/deployment/backup.sh
```

2. **性能分析**
```bash
python scripts/management/monitor.py performance
```

3. **清理旧日志**
```bash
find logs/ -name "*.log" -mtime +7 -delete
```

### 每月任务

1. **系统更新**
```bash
apt update && apt upgrade -y
```

2. **Docker镜像清理**
```bash
docker system prune -a
```

3. **数据库优化**
```bash
docker exec crypto-timescaledb vacuumdb -U crypto_user -d crypto_trade -z
```

## 监控指标

### 关键指标

1. **系统指标**
   - CPU使用率 < 80%
   - 内存使用率 < 80%
   - 磁盘使用率 < 80%

2. **应用指标**
   - API响应时间 < 2s
   - 错误率 < 5%
   - 请求成功率 > 95%

3. **业务指标**
   - 数据采集延迟 < 5分钟
   - 数据采集成功率 > 95%
   - 策略执行成功率 > 90%

## 告警处理

### 告警级别

- **Critical**: 立即处理，影响核心功能
- **Warning**: 1小时内处理，可能影响性能
- **Info**: 记录日志，定期检查

### 常见告警处理

#### HighCPUUsage
```bash
# 查看CPU占用进程
docker stats
# 检查是否有异常进程
docker exec api top -b -n 1
```

#### HighMemoryUsage
```bash
# 查看内存使用
docker stats
# 重启占用内存高的服务
docker-compose restart api
```

#### ServiceDown
```bash
# 查看服务状态
docker ps -a
# 查看日志
docker logs crypto-api
# 重启服务
docker-compose restart api
```

## 性能优化

### 数据库优化

1. **查询优化**
```sql
-- 查看慢查询
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- 创建索引
CREATE INDEX CONCURRENTLY idx_name ON table_name(column);
```

2. **连接池优化**
```python
# 调整连接池大小
pool_size = 20
max_overflow = 10
```

### Redis优化

```bash
# 查看内存使用
docker exec crypto-redis redis-cli INFO memory

# 清理过期键
docker exec crypto-redis redis-cli --scan --pattern "cache:*" | xargs redis-cli DEL
```

### 应用优化

1. **调整Worker数量**
```yaml
# docker-compose.yml
deploy:
  replicas: 3
```

2. **启用缓存**
```python
# 使用Redis缓存
@cache(ttl=300)
def get_market_data(symbol):
    pass
```

## 故障恢复

### 数据库故障

1. **主库故障**
```bash
# 检查数据库状态
docker exec crypto-timescaledb pg_isready

# 从备份恢复
./scripts/deployment/restore.sh <timestamp>
```

2. **数据损坏**
```bash
# 检查数据完整性
docker exec crypto-timescaledb pg_checksums -D /var/lib/postgresql/data
```

### Redis故障

```bash
# 检查Redis状态
docker exec crypto-redis redis-cli PING

# 重启Redis
docker-compose restart redis
```

### RabbitMQ故障

```bash
# 检查队列状态
docker exec crypto-rabbitmq rabbitmqctl list_queues

# 清理死信队列
docker exec crypto-rabbitmq rabbitmqctl purge_queue dead_letter_queue
```

## 安全管理

### 访问控制

1. **SSH密钥管理**
```bash
# 生成SSH密钥
ssh-keygen -t ed25519 -C "admin@crypto-trade.com"

# 禁用密码登录
sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
```

2. **防火墙配置**
```bash
# 配置UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 日志审计

```bash
# 查看登录日志
last -n 20

# 查看sudo日志
grep sudo /var/log/auth.log

# 查看Docker日志
journalctl -u docker -n 100
```

## 容量规划

### 存储容量

- 时序数据: 约1GB/天/100交易对
- 日志数据: 约100MB/天
- 备份数据: 约5GB/周

### 计算资源

- API服务: 2核4GB内存
- Worker服务: 1核2GB内存/实例
- 数据库: 4核8GB内存
- Redis: 1核2GB内存

## 升级维护

### 滚动升级

```bash
# 1. 备份数据
./scripts/deployment/backup.sh

# 2. 拉取新版本
git pull origin main

# 3. 构建新镜像
docker-compose build

# 4. 逐个重启服务
docker-compose up -d --no-deps api
sleep 30
docker-compose up -d --no-deps collector
```

### 回滚操作

```bash
# 1. 切换到旧版本
git checkout <old-version>

# 2. 重新构建
docker-compose build

# 3. 重启服务
docker-compose up -d

# 4. 恢复数据（如需要）
./scripts/deployment/restore.sh <timestamp>
```

## 联系方式

- 技术支持: support@crypto-trade.com
- 紧急联系: +86 138-xxxx-xxxx
- 值班群: Telegram @crypto_trade_ops
