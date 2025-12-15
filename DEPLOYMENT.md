# 部署指南

## 📦 生產環境部署

### 前置準備

1. **伺服器需求**
   - CPU: 2 核心以上
   - RAM: 4GB 以上
   - 磁碟: 20GB 以上
   - OS: Ubuntu 20.04+ 或其他 Linux 發行版

2. **安裝 Docker 和 Docker Compose**
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo apt-get install docker-compose-plugin
   ```

### 部署步驟

1. **複製專案到伺服器**
   ```bash
   git clone <your-repo-url>
   cd facebook_crawler_app
   ```

2. **配置環境變數**
   ```bash
   cp .env.example .env
   nano .env  # 編輯配置
   ```
   
   **重要配置項**：
   - `SECRET_KEY`: 必須使用強隨機金鑰
   - `DATABASE_URL`: 設定為外部資料庫（如果使用）
   - `DEBUG=False`: 關閉除錯模式
   - `CRAWLER_HEADLESS=True`: 使用無頭瀏覽器

3. **生成安全的 SECRET_KEY**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

4. **啟動服務**
   ```bash
   docker-compose up -d --build
   ```

5. **檢查服務狀態**
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

6. **初始化資料庫（如果需要）**
   ```bash
   docker-compose exec web python -c "from app.core.db import init_db; init_db()"
   ```

### 反向代理配置（Nginx）

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /metrics {
        # 限制 Prometheus 存取
        allow 127.0.0.1;
        deny all;
        proxy_pass http://localhost:8000/metrics;
    }
}
```

### SSL 配置（Let's Encrypt）

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 🔒 安全建議

1. **更改預設密碼**
   - 修改資料庫中的預設使用者密碼
   - 更改 Grafana 預設密碼

2. **防火牆配置**
   ```bash
   # 只開放必要端口
   sudo ufw allow 22/tcp    # SSH
   sudo ufw allow 80/tcp    # HTTP
   sudo ufw allow 443/tcp   # HTTPS
   sudo ufw enable
   ```

3. **限制內部服務存取**
   - PostgreSQL: 只允許內部網路存取
   - Redis: 只允許內部網路存取
   - Prometheus/Grafana: 使用身份驗證

4. **定期更新**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

## 📊 監控和告警

### Prometheus 告警規則

創建 `prometheus-alerts.yml`：

```yaml
groups:
  - name: api_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "API 錯誤率過高"
          description: "過去 5 分鐘錯誤率超過 10%"

      - alert: SlowResponse
        expr: histogram_quantile(0.95, http_request_duration_seconds_bucket) > 2
        for: 5m
        annotations:
          summary: "API 回應緩慢"
          description: "95% 的請求超過 2 秒"

      - alert: CeleryTaskFailed
        expr: rate(crawler_tasks_total{status="FAILURE"}[10m]) > 0.1
        for: 10m
        annotations:
          summary: "Celery 任務失敗率高"
          description: "過去 10 分鐘任務失敗率超過 10%"
```

### Grafana 儀表板 JSON

可以從 Grafana 導出儀表板配置並保存為 `grafana-dashboard.json`。

## 🔄 備份和恢復

### 資料庫備份

```bash
# 備份
docker-compose exec db pg_dump -U postgres postgres > backup_$(date +%Y%m%d).sql

# 定期備份（crontab）
0 2 * * * cd /path/to/facebook_crawler_app && docker-compose exec -T db pg_dump -U postgres postgres > backups/backup_$(date +\%Y\%m\%d).sql
```

### 資料庫恢復

```bash
# 恢復
docker-compose exec -T db psql -U postgres postgres < backup_20240101.sql
```

### Redis 備份

```bash
# Redis 會自動持久化到 /data
docker-compose exec redis redis-cli SAVE
docker cp facebook_crawler_app_redis_1:/data/dump.rdb ./redis_backup.rdb
```

## 📈 效能調優

### 資料庫優化

在 `docker-compose.yml` 中調整 PostgreSQL 配置：

```yaml
db:
  image: postgres:15-alpine
  command:
    - "postgres"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "effective_cache_size=1GB"
    - "-c"
    - "max_connections=200"
```

### Celery Worker 擴展

```bash
# 增加 worker 數量
docker-compose up -d --scale celery_worker=3
```

### Redis 優化

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

## 🐛 故障排除

### 查看日誌

```bash
# 即時日誌
docker-compose logs -f --tail=100

# 特定服務日誌
docker-compose logs web
docker-compose logs celery_worker

# 匯出日誌
docker-compose logs > app_logs_$(date +%Y%m%d).log
```

### 重啟服務

```bash
# 重啟單個服務
docker-compose restart web

# 重啟所有服務
docker-compose restart
```

### 清理資源

```bash
# 清理未使用的映像
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理未使用的卷
docker volume prune
```

## 📞 健康檢查

創建監控腳本 `health_check.sh`：

```bash
#!/bin/bash

# 檢查 API 健康狀態
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "API is healthy"
else
    echo "API is down - restarting..."
    docker-compose restart web
fi

# 檢查 Celery Worker
WORKER_COUNT=$(docker-compose ps celery_worker | grep -c "Up")
if [ $WORKER_COUNT -lt 1 ]; then
    echo "Celery worker is down - restarting..."
    docker-compose restart celery_worker
fi
```

定期執行：
```bash
# 每 5 分鐘檢查一次
*/5 * * * * /path/to/health_check.sh >> /var/log/health_check.log 2>&1
```

## 🎯 效能基準

在生產環境中進行壓力測試：

```bash
# 安裝 Apache Bench
sudo apt-get install apache2-utils

# 測試 API 效能
ab -n 1000 -c 10 http://localhost:8000/health

# 使用 token 測試認證端點
ab -n 100 -c 5 -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/posts/
```

預期效能：
- 簡單端點: 500+ req/s
- 資料庫查詢: 100-200 req/s
- 爬蟲任務: 根據網路和目標網站而定
