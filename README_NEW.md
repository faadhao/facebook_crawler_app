# Facebook 爬蟲應用 - 企業級版本

## ✨ 功能特色

- 🚀 **非同步爬蟲**：使用 Celery 實現背景任務處理
- 🛡️ **API 限流**：保護 API 免受濫用
- 📊 **完整監控**：Prometheus + Grafana 監控儀表板
- 🧪 **單元測試**：完整的測試覆蓋率
- 🐳 **Docker 優化**：多階段構建，減少映像大小
- 🔒 **JWT 認證**：安全的使用者身份驗證
- 💾 **資料持久化**：PostgreSQL + Redis

## 🚀 快速啟動指南

### 方法一：使用 Docker Compose（推薦）

1. **確保已安裝 Docker 和 Docker Compose**

2. **複製或導航到專案目錄**
   ```bash
   cd facebook_crawler_app
   ```

3. **創建環境變數檔案**
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env
   
   # 編輯 .env 檔案，修改 SECRET_KEY（重要！）
   ```

4. **構建並啟動所有服務**
   ```bash
   docker-compose up --build -d
   ```
   
   此命令會啟動以下服務：
   - **web**: FastAPI 應用（端口 8000）
   - **celery_worker**: 異步任務處理器
   - **celery_beat**: 定時任務調度器
   - **db**: PostgreSQL 資料庫（端口 5432）
   - **redis**: Redis 快取（端口 6379）
   - **prometheus**: 指標收集（端口 9090）
   - **grafana**: 監控儀表板（端口 3000）

5. **存取服務**
   - API 文檔 (Swagger): http://localhost:8000/docs
   - API 文檔 (ReDoc): http://localhost:8000/redoc
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (預設帳號/密碼: admin/admin)
   - Metrics 端點: http://localhost:8000/metrics

### 方法二：本地開發環境

1. **安裝 Python 3.10+**

2. **創建虛擬環境**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **安裝依賴**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **配置環境變數**
   ```bash
   Copy-Item .env.example .env
   # 編輯 .env，配置資料庫和 Redis 連接
   ```

5. **啟動 PostgreSQL 和 Redis**
   ```bash
   # 使用 Docker 啟動依賴服務
   docker-compose up db redis -d
   ```

6. **運行應用**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

7. **啟動 Celery Worker（另一個終端）**
   ```bash
   celery -A app.core.celery_app worker --loglevel=info
   ```

8. **啟動 Celery Beat（另一個終端）**
   ```bash
   celery -A app.core.celery_app beat --loglevel=info
   ```

## 📖 API 使用示例

### 1. 使用者登入

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin1",
    "password": "1minda"
  }'
```

**回應：**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 2. 同步爬取 Facebook 貼文（即時）

```bash
curl -X POST "http://localhost:8000/crawler/crawl" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page_url": "https://www.facebook.com/PAGE_NAME",
    "limit": 30
  }'
```

### 3. 異步爬取 Facebook 貼文（背景任務）

```bash
# 提交異步任務
curl -X POST "http://localhost:8000/crawler/crawl/async" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page_url": "https://www.facebook.com/PAGE_NAME",
    "limit": 30
  }'
```

**回應：**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "爬蟲任務已提交"
}
```

### 4. 查詢異步任務狀態

```bash
curl "http://localhost:8000/crawler/task/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**回應：**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "SUCCESS",
  "result": {
    "total_crawled": 25,
    "category_stats": {"圖片": 10, "影片": 8, "文字": 7}
  }
}
```

### 5. 查詢貼文

```bash
# 從快取查詢（快速）
curl "http://localhost:8000/posts/?category=video&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 從資料庫查詢（完整）
curl "http://localhost:8000/posts/db?category=video&limit=10&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 6. 獲取貼文類別統計

```bash
curl "http://localhost:8000/posts/categories" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 7. 檢查爬蟲狀態

```bash
curl "http://localhost:8000/crawler/status" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 8. 健康檢查

```bash
curl "http://localhost:8000/health"
```

## 🛡️ API 限流說明

為保護 API 資源，已實施以下限流規則：

- **一般 API 端點**: 每分鐘 100 次請求
- **爬蟲端點 (同步)**: 每小時 10 次請求
- **爬蟲端點 (異步)**: 每小時 5 次請求
- **狀態查詢端點**: 每分鐘 30 次請求
- **登入端點**: 每分鐘 5 次請求

超過限流將返回 `429 Too Many Requests` 錯誤。

## 📊 監控和指標

### Prometheus 指標

存取 `http://localhost:8000/metrics` 可查看以下指標：

- `http_requests_total`: HTTP 請求總數（按方法、端點、狀態碼分類）
- `http_request_duration_seconds`: HTTP 請求持續時間
- `crawler_tasks_total`: 爬蟲任務總數（按狀態分類）
- `crawler_task_duration_seconds`: 爬蟲任務執行時間
- `redis_operations_total`: Redis 操作次數
- `database_queries_total`: 資料庫查詢次數

### Grafana 儀表板

1. 存取 http://localhost:3000
2. 使用預設帳號: `admin` / 密碼: `admin`
3. 添加 Prometheus 資料源: `http://prometheus:9090`
4. 導入儀表板或創建自訂視圖

## 🧪 執行測試

### 執行所有測試

```bash
pytest
```

### 執行特定測試文件

```bash
# 測試認證功能
pytest tests/test_auth.py

# 測試貼文功能
pytest tests/test_posts.py

# 測試服務層
pytest tests/test_services.py
```

### 生成測試覆蓋率報告

```bash
pytest --cov=app --cov-report=html
```

覆蓋率報告會生成在 `htmlcov/index.html`。

### 在 Docker 中執行測試

```bash
docker-compose run --rm web pytest
```

## 🔑 預設使用者憑據

- **使用者名**: admin1
- **密碼**: 1minda

## ⚙️ 主要配置項

編輯 `.env` 檔案來修改配置：

```env
# 生產環境必須修改！
SECRET_KEY=your-super-secret-key-change-this-in-production

# 資料庫配置
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres

# Redis 配置
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_POST_TTL=86400        # 24小時

# JWT 配置
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 爬蟲配置
CRAWLER_MAX_POSTS=30        # 最多爬取貼文數
CRAWLER_SCROLL_COUNT=5      # 頁面滾動次數
CRAWLER_HEADLESS=True       # 是否使用無頭瀏覽器

# Celery 配置
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

## 📊 查看日誌

### Docker 日誌

```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f web
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

### 本地日誌

日誌檔案位於 `logs/` 目錄：
- `logs/app.log`: 應用程式日誌
- `logs/crawler.log`: 爬蟲日誌
- `logs/celery.log`: Celery 任務日誌

## 🐳 Docker 管理命令

```bash
# 啟動所有服務
docker-compose up -d

# 停止所有服務
docker-compose down

# 重新構建並啟動
docker-compose up --build -d

# 查看服務狀態
docker-compose ps

# 進入容器內部
docker-compose exec web bash
docker-compose exec celery_worker bash

# 清除所有資料（包括資料庫）
docker-compose down -v
```

## 📦 專案結構

```
facebook_crawler_app/
├── app/
│   ├── main.py                 # 應用程式入口
│   ├── dependencies.py         # 全域依賴
│   ├── api/                    # API 路由
│   │   ├── auth.py            # 認證端點
│   │   ├── crawler.py         # 爬蟲端點
│   │   └── posts.py           # 貼文端點
│   ├── core/                   # 核心功能
│   │   ├── config.py          # 配置管理
│   │   ├── db.py              # 資料庫連接
│   │   ├── redis.py           # Redis 連接
│   │   ├── logger.py          # 日誌配置
│   │   ├── monitoring.py      # Prometheus 監控
│   │   ├── rate_limit.py      # API 限流
│   │   └── celery_app.py      # Celery 配置
│   ├── crawler/                # 爬蟲實現
│   │   └── facebook.py        # Facebook 爬蟲
│   ├── models/                 # SQLAlchemy 模型
│   │   ├── user.py            # 使用者模型
│   │   └── post.py            # 貼文模型
│   ├── schemas/                # Pydantic 模式
│   │   ├── auth.py            # 認證模式
│   │   └── crawl.py           # 爬蟲模式
│   ├── services/               # 業務邏輯
│   │   ├── auth.py            # 認證服務
│   │   └── post_service.py    # 貼文服務
│   └── tasks/                  # Celery 任務
│       ├── __init__.py
│       └── crawler_tasks.py   # 異步爬蟲任務
├── tests/                      # 測試套件
│   ├── conftest.py            # Pytest 配置
│   ├── test_auth.py           # 認證測試
│   ├── test_posts.py          # 貼文測試
│   └── test_services.py       # 服務測試
├── docker-compose.yml          # Docker Compose 配置
├── Dockerfile                  # Web 應用 Dockerfile
├── Dockerfile.celery          # Celery Worker Dockerfile
├── prometheus.yml             # Prometheus 配置
├── requirements.txt           # Python 依賴
├── pytest.ini                 # Pytest 配置
└── README.md                  # 本文檔
```

## 🔧 故障排除

### 1. Playwright 瀏覽器安裝失敗

```bash
# 在容器內手動安裝
docker-compose exec web playwright install chromium --with-deps
```

### 2. 資料庫連接失敗

確保 PostgreSQL 服務正在運行：
```bash
docker-compose ps db
docker-compose logs db
```

### 3. Redis 連接失敗

確保 Redis 服務正在運行：
```bash
docker-compose ps redis
docker-compose logs redis
```

### 4. Celery 任務不執行

檢查 Celery Worker 日誌：
```bash
docker-compose logs -f celery_worker
```

確保 Redis 正常運行且可連接。

### 5. 映像構建緩慢

使用多階段構建優化的 Dockerfile 會在首次構建時較慢，但後續構建會使用快取層，速度會快很多。

## 📈 效能優化

1. **資料庫索引**: 已在 `created_at` 和 `category` 欄位建立索引
2. **Redis 快取**: 所有查詢結果都會快取 24 小時
3. **連接池**: 使用 SQLAlchemy 連接池管理資料庫連接
4. **異步處理**: 長時間運行的爬蟲任務使用 Celery 異步處理
5. **API 限流**: 防止 API 濫用和過載

## 📝 開發指南

### 添加新的 API 端點

1. 在 `app/api/` 中創建或修改路由文件
2. 添加 Pydantic 模式到 `app/schemas/`
3. 實現業務邏輯在 `app/services/`
4. 添加相應的測試到 `tests/`

### 添加新的 Celery 任務

1. 在 `app/tasks/` 中定義任務
2. 使用 `@celery_app.task` 裝飾器
3. 在 API 路由中調用 `task.delay()`
4. 添加監控指標

### 添加新的監控指標

1. 在 `app/core/monitoring.py` 中定義新指標
2. 在相關代碼中更新指標
3. 在 Grafana 中創建視圖

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

## 📄 授權

MIT License

## 📞 聯繫方式

如有問題，請通過 GitHub Issues 聯繫。
