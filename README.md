# Facebook 爬蟲應用 - 快速開始

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

4. **構建并啟動服務**
   ```bash
   docker-compose up --build
   ```

5. **存取 API 文檔**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### 方法二：本地开发環境

1. **安装 Python 3.10+**

2. **創建虚拟環境**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **安装依賴**
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
   docker-compose up db redis
   ```

6. **運行應用**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
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

### 2. 爬取 Facebook 貼文

```bash
curl -X POST "http://localhost:8000/crawler/crawl" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "page_url": "https://www.facebook.com/PAGE_NAME",
    "limit": 30
  }'
```

### 3. 查詢貼文

```bash
# 從快取查詢（快速）
curl "http://localhost:8000/posts/?category=video&limit=10"

# 從資料庫查詢（完整）
curl "http://localhost:8000/posts/db?category=video&limit=10&offset=0"
```

### 4. 獲取貼文類別別统計

```bash
curl "http://localhost:8000/posts/categories"
```

### 5. 健康檢查

```bash
curl "http://localhost:8000/health"
```

## 🔑 預設使用者憑據

- **使用者名**: admin1
- **密碼**: 1minda

- **使用者名**: admin2
- **密碼**: （见 init.sql 中的 bcrypt 雜湊）

## ⚙️ 主要配置項

編輯 `.env` 檔案來修改配置：

```env
# 生产環境必須修改！
SECRET_KEY=your-super-secret-key-change-this-in-production

# 爬蟲配置
CRAWLER_MAX_POSTS=30        # 最多爬取貼文數
CRAWLER_SCROLL_COUNT=5      # 頁面滾動次數
CRAWLER_HEADLESS=True       # 是否使用無頭瀏覽器

# Redis 快取時間（秒）
REDIS_POST_TTL=86400        # 24小時
```

## 📊 查看日誌

日誌檔案位於 `logs/` 目錄：

- `app.log` - 所有日誌
- `error.log` - 仅錯誤日誌

```bash
# 实時查看日誌
# Windows PowerShell
Get-Content logs\app.log -Wait

# Linux/Mac
tail -f logs/app.log
```

## 🐛 故障排除

### 问题：无法連接資料庫

**解决方案：**
1. 確保 PostgreSQL 正在運行
2. 檢查 `.env` 中的 `DATABASE_URL` 配置
3. 檢查 Docker 容器狀態：`docker-compose ps`

### 问题：爬蟲失敗

**可能原因：**
1. Facebook 頁面需要登入
2. 頁面结构變化
3. 網路連接问题

**解决方案：**
- 查看詳細日誌：`logs/app.log`
- 嘗試其他公开頁面
- 調整 `CRAWLER_TIMEOUT` 配置

### 问题：Token 無效

**解决方案：**
1. 重新登入獲取新 Token
2. 檢查 Token 是否過期
3. 確保 Redis 正在運行

## 📚 更多資訊

- **API 文檔**: http://localhost:8000/docs
- **優化说明**: 查看 `OPTIMIZATION.md`
- **專案结构**: 查看源代碼注释

## 🔄 更新依賴

```bash
pip install --upgrade -r requirements.txt
```

## 🛑 停止服務

```bash
# Docker Compose
docker-compose down

# 本地开发（Ctrl+C 后）
deactivate  # 退出虚拟環境
```

---

遇到问题？查看日誌檔案或 API 文檔獲取更多資訊。
