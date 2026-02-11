# Crypto-Trade 部署指南

## 环境要求

### 硬件要求
- CPU: 4核以上
- 内存: 8GB以上
- 存储: 100GB SSD以上
- 网络: 10Mbps以上

### 软件要求
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (开发环境)

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/crypto-trade.git
cd crypto-trade
```

### 2. 环境初始化

```bash
# 运行初始化脚本
./scripts/deployment/setup.sh

# 配置环境变量
cp .env.example .env
# 编辑.env文件，填入实际配置
nano .env
```

### 3. 启动服务

```bash
# 启动所有服务
./scripts/deployment/start_services.sh

# 查看服务状态
docker-compose -f config/docker-compose.yml ps
```

### 4. 验证部署

访问以下地址验证服务：

- API文档: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/your-password)
- Prometheus: http://localhost:9090
- RabbitMQ管理: http://localhost:15672 (crypto_user/your-password)

## 服务管理

### 使用管理工具

```bash
# 查看服务状态
python scripts/management/manage.py status

# 启动特定服务
python scripts/management/manage.py start api

# 停止特定服务
python scripts/management/manage.py stop api

# 查看日志
python scripts/management/manage.py logs api -f

# 健康检查
python scripts/management/manage.py health
```

### 手动管理

```bash
# 启动所有服务
docker-compose -f config/docker-compose.yml up -d

# 停止所有服务
docker-compose -f config/docker-compose.yml down

# 重启服务
docker-compose -f config/docker-compose.yml restart api

# 查看日志
docker-compose -f config/docker-compose.yml logs -f api
```

## 数据备份

### 自动备份

```bash
# 运行备份脚本
./scripts/deployment/backup.sh
```

备份文件保存在 `/opt/Crypto-Trade/backups/` 目录。

### 数据恢复

```bash
# 恢复数据（使用备份时间戳）
./scripts/deployment/restore.sh 20260208_120000
```

## 监控和告警

### Grafana仪表板

1. 访问 http://localhost:3000
2. 使用管理员账号登录
3. 导入预配置的仪表板

### Prometheus查询

访问 http://localhost:9090 查询指标：

```promql
# CPU使用率
100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 内存使用率
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100

# API请求速率
rate(http_requests_total[5m])
```

### 告警配置

告警规则位于 `config/prometheus/alerts/` 目录：

- `system.yml` - 系统告警
- `application.yml` - 应用告警
- `business.yml` - 业务告警

## 故障排查

### 服务无法启动

```bash
# 检查Docker服务
systemctl status docker

# 查看容器日志
docker-compose -f config/docker-compose.yml logs

# 检查端口占用
netstat -tulpn | grep -E '8000|5432|6379|5672'
```

### 数据库连接失败

```bash
# 检查数据库状态
docker exec crypto-timescaledb pg_isready

# 查看数据库日志
docker logs crypto-timescaledb

# 测试连接
docker exec -it crypto-timescaledb psql -U crypto_user -d crypto_trade
```

### 性能问题

```bash
# 查看资源使用
docker stats

# 查看慢查询
docker exec crypto-timescaledb psql -U crypto_user -d crypto_trade \
  -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"
```

## 安全加固

### 1. 修改默认密码

编辑 `.env` 文件，修改所有默认密码。

### 2. 配置防火墙

```bash
# 只开放必要端口
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp
ufw enable
```

### 3. 启用SSL

将SSL证书放置在 `config/nginx/ssl/` 目录，并更新Nginx配置。

### 4. 限制访问

在 `config/nginx/nginx.conf` 中配置IP白名单。

## 性能优化

### 数据库优化

```sql
-- 创建索引
CREATE INDEX idx_klines_symbol_timestamp ON klines(symbol, timestamp);

-- 启用查询缓存
ALTER SYSTEM SET shared_buffers = '2GB';
```

### Redis优化

```bash
# 调整内存策略
docker exec crypto-redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### 应用优化

- 调整Worker数量
- 配置连接池大小
- 启用缓存

## 扩展部署

### 水平扩展

```bash
# 扩展API服务
docker-compose -f config/docker-compose.yml up -d --scale api=3

# 扩展Worker服务
docker-compose -f config/docker-compose.yml up -d --scale collector=2
```

### 负载均衡

使用Nginx进行负载均衡，配置文件位于 `config/nginx/nginx.conf`。

## 更新升级

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose -f config/docker-compose.yml build

# 重启服务
docker-compose -f config/docker-compose.yml up -d
```

## 支持

如有问题，请查看：

- 项目文档: `/opt/Crypto-Trade/docs/`
- GitHub Issues: https://github.com/your-repo/crypto-trade/issues
- 邮件支持: support@crypto-trade.com
