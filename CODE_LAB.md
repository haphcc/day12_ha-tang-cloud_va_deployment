#  Code Lab: Deploy Your AI Agent to Production

> **AICB-P1 · VinUniversity 2026**  
> Thời gian: 3-4 giờ | Độ khó: Intermediate

##  Mục Tiêu

Sau khi hoàn thành lab này, bạn sẽ:
- Hiểu sự khác biệt giữa development và production
- Containerize một AI agent với Docker
- Deploy agent lên cloud platform
- Bảo mật API với authentication và rate limiting
- Thiết kế hệ thống có khả năng scale và reliable

---

##  Yêu Cầu

```bash
 Python 3.11+
 Docker & Docker Compose
 Git
 Text editor (VS Code khuyến nghị)
 Terminal/Command line
```

**Không cần:**
-  OpenAI API key (dùng mock LLM)
-  Credit card
-  Kinh nghiệm DevOps trước đó

---

##  Lộ Trình Lab

| Phần | Thời gian | Nội dung |
|------|-----------|----------|
| **Part 1** | 30 phút | Localhost vs Production |
| **Part 2** | 45 phút | Docker Containerization |
| **Part 3** | 45 phút | Cloud Deployment |
| **Part 4** | 40 phút | API Security |
| **Part 5** | 40 phút | Scaling & Reliability |
| **Part 6** | 60 phút | Final Project |

---

## Part 1: Localhost vs Production (30 phút)

###  Concepts

**Vấn đề:** "It works on my machine" — code chạy tốt trên laptop nhưng fail khi deploy.

**Nguyên nhân:**
- Hardcoded secrets
- Khác biệt về environment (Python version, OS, dependencies)
- Không có health checks
- Config không linh hoạt

**Giải pháp:** 12-Factor App principles

###  Exercise 1.1: Phát hiện anti-patterns

```bash
cd 01-localhost-vs-production/develop
```

**Nhiệm vụ:** Đọc `app.py` và tìm ít nhất 5 vấn đề.

**Đáp án mẫu (từ `01-localhost-vs-production/develop/app.py`):**

1. Hardcode secret trong code:
  - `OPENAI_API_KEY = "sk-hardcoded-fake-key-never-do-this"`
  - `DATABASE_URL = "postgresql://admin:password123@localhost:5432/mydb"`
2. Không dùng config management từ environment variables (`DEBUG`, `MAX_TOKENS` bị hardcode).
3. Dùng `print()` thay vì structured logging.
4. Log lộ secret (`print(f"[DEBUG] Using key: {OPENAI_API_KEY}")`).
5. Không có health check endpoint (`/health`).
6. Port cố định `8000`, không đọc từ `PORT` env var.
7. Bind `host="localhost"` nên không phù hợp container/cloud (nên dùng `0.0.0.0`).
8. `reload=True` bật debug behavior không phù hợp production.

<details>
<summary> Gợi ý</summary>

Tìm:
- API key hardcode
- Port cố định
- Debug mode
- Không có health check
- Không xử lý shutdown

</details>

###  Exercise 1.2: Chạy basic version

```bash
pip install -r requirements.txt
python app.py
```

Test:
```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

**Quan sát:** Nó chạy! Nhưng có production-ready không?

###  Exercise 1.3: So sánh với advanced version

```bash
cd ../production
cp .env.example .env
pip install -r requirements.txt
python app.py
```

**Nhiệm vụ:** So sánh 2 files `app.py`. Điền vào bảng:

| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
| Config | Hardcode trong code | Đọc từ env vars qua `config.py` | Tách config khỏi code, đổi môi trường không cần sửa source |
| Health check | Không có | Có `/health` (liveness) và `/ready` (readiness) | Platform biết khi nào restart và khi nào route traffic |
| Logging | `print()` | Structured JSON logging | Dễ parse log, theo dõi và debug trên cloud |
| Shutdown | Đột ngột | Graceful qua `lifespan` + SIGTERM handler | Giảm rớt request khi deploy/restart |
| Host/Port | `localhost:8000` cố định | `0.0.0.0` + port từ env `PORT` | Chạy được trong container/cloud và linh hoạt theo platform |
| Secrets | Secret nằm trong code, còn bị log ra | Secret từ env, không log secret | Tránh lộ key, an toàn khi push code |

###  Checkpoint 1

- [x] Hiểu tại sao hardcode secrets là nguy hiểm
- [x] Biết cách dùng environment variables
- [x] Hiểu vai trò của health check endpoint
- [x] Biết graceful shutdown là gì

---

## Part 2: Docker Containerization (45 phút)

###  Concepts

**Vấn đề:** "Works on my machine" part 2 — Python version khác, dependencies conflict.

**Giải pháp:** Docker — đóng gói app + dependencies vào container.

**Benefits:**
- Consistent environment
- Dễ deploy
- Isolation
- Reproducible builds

###  Exercise 2.1: Dockerfile cơ bản

```bash
cd ../../02-docker/develop
```

**Đáp án (`02-docker/develop/Dockerfile`):**

1. Base image: `python:3.11`.
2. Working directory: `/app`.
3. `COPY requirements.txt` trước để tận dụng Docker layer cache. Nếu source code đổi mà dependencies không đổi thì không phải cài lại toàn bộ packages, build nhanh hơn.
4. `CMD` là lệnh mặc định (dễ override khi `docker run <image> <command>`), còn `ENTRYPOINT` là executable chính của container (argument từ `docker run` thường được append).

###  Exercise 2.2: Build và run

```bash
# Build image
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .

# Run container
docker run -p 8000:8000 my-agent:develop

# Test
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

**Quan sát:** Image size là bao nhiêu?: 424MB
```bash
docker images my-agent:develop
```

###  Exercise 2.3: Multi-stage build

```bash
cd ../production
```

**Nhiệm vụ:** Đọc `Dockerfile` và tìm:
- Stage 1 làm gì?
- Stage 2 làm gì?
- Tại sao image nhỏ hơn?

**Đáp án mẫu (`02-docker/production/Dockerfile`):**

- Stage 1 (builder):
  - Dùng `python:3.11-slim`.
  - Cài build tools (`gcc`, `libpq-dev`).
  - Cài dependencies bằng pip vào `/root/.local`.
- Stage 2 (runtime):
  - Dùng image slim mới, tạo non-root user (`appuser`).
  - Chỉ copy packages cần chạy từ builder + source code app.
  - Thiết lập `PATH`, `PYTHONPATH`, `HEALTHCHECK`, rồi chạy uvicorn.
- Image nhỏ hơn vì không mang theo compiler/build dependencies của stage build vào image runtime cuối cùng.

Build và so sánh:
```bash
docker build -t my-agent:advanced .
docker images | grep my-agent
```

###  Exercise 2.4: Docker Compose stack

**Nhiệm vụ:** Đọc `docker-compose.yml` và vẽ architecture diagram.

**Architecture diagram (`02-docker/production/docker-compose.yml`):**

```text
Client
  |
  v
Nginx (reverse proxy + rate limit)
  |
  v
Agent (FastAPI)
  |\
  | \-> Redis (cache/session/rate-limit state)
  |
  \----> Qdrant (vector database)
```

**Services được start:**
- `agent`
- `redis`
- `qdrant`
- `nginx`

**Chúng communicate thế nào:**
- Client gọi vào `nginx` qua port 80.
- `nginx` proxy request vào `agent` qua internal network.
- `agent` dùng `REDIS_URL=redis://redis:6379/0` để nói chuyện với Redis.
- `agent` dùng `QDRANT_URL=http://qdrant:6333` để nói chuyện với Qdrant.

```bash
# Windows PowerShell (from repo root)
if (-not (Test-Path "02-docker/production/.env.local")) { New-Item -Path "02-docker/production/.env.local" -ItemType File | Out-Null }
docker compose -f 02-docker/production/docker-compose.yml up --build
```

Test:
```bash
# Health check
curl http://localhost/health

# Agent endpoint
curl http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain microservices"}'
```

###  Checkpoint 2

- [x] Hiểu cấu trúc Dockerfile
- [x] Biết lợi ích của multi-stage builds
- [x] Hiểu Docker Compose orchestration
- [x] Biết cách debug container (`docker logs`, `docker exec`)

---

## Part 3: Cloud Deployment (45 phút)

###  Concepts

**Vấn đề:** Laptop không thể chạy 24/7, không có public IP.

**Giải pháp:** Cloud platforms — Railway, Render, GCP Cloud Run.

**So sánh:**

| Platform | Độ khó | Free tier | Best for |
|----------|--------|-----------|----------|
| Railway | ⭐ | $5 credit | Prototypes |
| Render | ⭐⭐ | 750h/month | Side projects |
| Cloud Run | ⭐⭐⭐ | 2M requests | Production |

###  Exercise 3.1: Deploy Render (15 phút)

```bash
cd .
```

**Steps:**

1. Push code lên GitHub (nếu chưa có)
2. Vào [render.com](https://render.com) → Sign up
3. New → Blueprint
4. Connect GitHub repo
5. Render tự động đọc `render.yaml` ở repo root
6. Set environment variables trong dashboard
7. Deploy! Render sẽ tạo web service và Redis từ `render.yaml`

**Nhiệm vụ:** Sau khi deploy xong, mở Render Dashboard và copy public URL của web service, rồi test 2 endpoint sau:

Test bằng curl:
```bash
# Health check
curl https://ai-agent-5cj8.onrender.com/health

# Agent endpoint
curl https://ai-agent-5cj8.onrender.com/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello from Render"}'
```

Test bằng Windows PowerShell:
```powershell
Invoke-RestMethod -Uri "https://ai-agent-5cj8.onrender.com/health" -Method Get
Invoke-RestMethod -Uri "https://ai-agent-5cj8.onrender.com/ask" -Method Post -ContentType "application/json" -Body '{"question":"Hello from Render"}'
```

Nếu `/health` trả về `200 OK` và `/ask` trả về câu trả lời từ agent, nghĩa là deploy đã thành công.

###  Exercise 3.2: (Optional) Deploy Railway (15 phút)

```bash
cd ../railway
```

**Steps:**

1. Install Railway CLI:
```bash
npm i -g @railway/cli
```

2. Login:
```bash
railway login
```

3. Initialize project:
```bash
railway init
```

4. Link service:
```bash
railway service
```

5. Set environment variables:
```bash
railway variables set PORT=8000
railway variables set AGENT_API_KEY=my-secret-key
```

6. Deploy:
```bash
railway up
```

7. Get public URL:
```bash
railway domain
```

**Nhiệm vụ:** So sánh `render.yaml` với `railway.toml`. Khác nhau gì?

**Đáp án ngắn:**

- `render.yaml` là Blueprint ở cấp repo root, dùng để khai báo nhiều service cùng lúc như web service và Redis.
- `railway.toml` là cấu hình cho một Railway service/project, tập trung vào cách build và start app.
- Render hỗ trợ khai báo `envVars`, `rootDir`, `healthCheckPath`, và cả Redis ngay trong cùng một file.
- Railway thường cần `railway init`, `railway service`, rồi set biến môi trường bằng CLI hoặc dashboard trước khi deploy.
- Render phù hợp khi muốn Infra as Code rõ ràng cho cả app và dependency đi kèm; Railway phù hợp khi muốn deploy nhanh một service đơn giản.

###  Exercise 3.3: (Optional) GCP Cloud Run (15 phút)

```bash
cd ../production-cloud-run
```

**Yêu cầu:** GCP account (có free tier).

**Nhiệm vụ:** Đọc `cloudbuild.yaml` và `service.yaml`. Hiểu CI/CD pipeline.

###  Checkpoint 3

- [ ] Deploy thành công lên ít nhất 1 platform
- [ ] Có public URL hoạt động
- [ ] Hiểu cách set environment variables trên cloud
- [ ] Biết cách xem logs

---

## Part 4: API Security (40 phút)

###  Concepts

**Vấn đề:** Public URL = ai cũng gọi được = hết tiền OpenAI.

**Giải pháp:**
1. **Authentication** — Chỉ user hợp lệ mới gọi được
2. **Rate Limiting** — Giới hạn số request/phút
3. **Cost Guard** — Dừng khi vượt budget

###  Exercise 4.1: API Key authentication

```bash
cd ../../04-api-gateway/develop
```

**Nhiệm vụ:** Đọc `app.py` và tìm:
1. API key được check trong dependency `verify_api_key()`:
  - Header được lấy qua `APIKeyHeader(name="X-API-Key", auto_error=False)`.
  - Endpoint `/ask` bắt buộc auth bằng `Depends(verify_api_key)`.
2. Nếu key sai hoặc thiếu:
  - Thiếu key: trả `401` với message yêu cầu gửi header `X-API-Key`.
  - Sai key: trả `403` với message `Invalid API key.`
3. Rotate key:
  - Key lấy từ env var `AGENT_API_KEY` (không hardcode trong source).
  - Đổi giá trị `AGENT_API_KEY` trên môi trường deploy (Render/Railway/GCP).
  - Redeploy/restart service để app nạp key mới.
  - (Khuyến nghị) dùng giai đoạn chuyển tiếp chấp nhận cả key cũ + key mới trong thời gian ngắn, sau đó thu hồi key cũ.

Test:
```bash
python app.py

#  Không có key
curl -i "http://localhost:8000/ask?question=Hello" -X POST

#  Có key
curl -i "http://localhost:8000/ask?question=Hello" -X POST \
  -H "X-API-Key: demo-key-change-in-production"
```

Windows PowerShell:
```powershell
python app.py

# Không có key
try {
  Invoke-RestMethod -Uri "http://localhost:8000/ask?question=Hello" -Method Post
} catch {
  $_.Exception.Response.StatusCode.value__
  $_.ErrorDetails.Message
}

# Có key
Invoke-RestMethod -Uri "http://localhost:8000/ask?question=Hello" -Method Post -Headers @{"X-API-Key"="demo-key-change-in-production"}
```

###  Exercise 4.2: JWT authentication (Advanced)

```bash
cd ../production
```

**Nhiệm vụ:** 
1. Đọc `auth.py` — hiểu JWT flow
2. Lấy token:eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHVkZW50Iiwicm9sZSI6InVzZXIiLCJpYXQiOjE3NzY0...

```bash
python app.py
```

Windows PowerShell:
```powershell
python app.py

Invoke-RestMethod -Uri "http://localhost:8000/auth/token" -Method Post -ContentType "application/json" -Body '{"username":"student","password":"demo123"}'
```

3. Dùng token để gọi API:
```bash
TOKEN="<token_từ_bước_2>"
curl http://localhost:8000/ask -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain JWT"}'
```

Windows PowerShell:
```powershell
$token = (Invoke-RestMethod -Uri "http://localhost:8000/auth/token" -Method Post -ContentType "application/json" -Body '{"username":"student","password":"demo123"}').access_token
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method Post -Headers @{"Authorization"="Bearer $token"} -ContentType "application/json" -Body '{"question":"Explain JWT"}'
```

###  Exercise 4.3: Rate limiting

**Nhiệm vụ:** Đọc `rate_limiter.py` và trả lời:
- Algorithm nào được dùng? (Token bucket? Sliding window?)
- Limit là bao nhiêu requests/minute?
- Làm sao bypass limit cho admin?

**Đáp án mẫu (từ `04-api-gateway/production/rate_limiter.py`):**

1. Algorithm: **Sliding Window Counter** (dùng `deque` để lưu timestamps theo user, loại bỏ request cũ ngoài cửa sổ 60 giây).
2. Limit mặc định:
  - User thường: `10 requests / 60 giây`.
  - Admin: `100 requests / 60 giây`.
3. Bypass cho admin không phải "vô hạn", mà là chuyển sang limiter riêng:
  - Trong `app.py`, nếu role là `admin` thì dùng `rate_limiter_admin`.
  - Nếu role là `user` thì dùng `rate_limiter_user`.
  - Nghĩa là admin được quota cao hơn (100/phút) thay vì 10/phút.

Test:
```bash
# Gọi liên tục 20 lần
for i in {1..20}; do
  curl.exe http://localhost:8000/ask -X POST \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"question": "Test '$i'"}'
  echo ""
done
```

Quan sát response khi hit limit.

Windows PowerShell:
```powershell
for ($i = 1; $i -le 20; $i++) {
  try {
    Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method Post -Headers @{"Authorization"="Bearer $token"} -ContentType "application/json" -Body "{\"question\":\"Test $i\"}"
  } catch {
    $_.Exception.Response.StatusCode.value__
    $_.ErrorDetails.Message
  }
}
```

###  Exercise 4.4: Cost guard

**Nhiệm vụ:** Đọc `cost_guard.py` và implement logic:

```python
def check_budget(user_id: str, estimated_cost: float) -> bool:
    """
    Return True nếu còn budget, False nếu vượt.
    
    Logic:
    - Mỗi user có budget $10/tháng
    - Track spending trong Redis
    - Reset đầu tháng
    """
    # TODO: Implement
    pass
```

<details>
<summary> Solution</summary>

```python
import redis
from datetime import datetime

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

MONTHLY_BUDGET_USD = 10.0

def check_budget(user_id: str, estimated_cost: float) -> bool:
  if estimated_cost < 0:
    raise ValueError("estimated_cost must be >= 0")

  # Key theo user + tháng hiện tại, ví dụ: budget:alice:2026-04
  month_key = datetime.now().strftime("%Y-%m")
  key = f"budget:{user_id}:{month_key}"

    current = float(r.get(key) or 0)
  if current + estimated_cost > MONTHLY_BUDGET_USD:
        return False

    r.incrbyfloat(key, estimated_cost)
  # TTL > 1 tháng để key tự hết sau kỳ billing
  r.expire(key, 32 * 24 * 3600)
    return True
```

</details>

**Giải thích nhanh:**

- Redis key theo tháng giúp tự tách dữ liệu từng kỳ (`budget:<user_id>:YYYY-MM`).
- Mỗi request ước lượng chi phí trước khi gọi LLM, nếu vượt `$10/tháng` thì trả `False` để chặn.
- `expire(32 ngày)` đảm bảo key cũ tự dọn sau khi qua kỳ mới.

Test nhanh (Windows PowerShell):

```powershell
# Cần Redis đang chạy ở localhost:6379
@'
from datetime import datetime
import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
user_id = "student"
month = datetime.now().strftime("%Y-%m")
key = f"budget:{user_id}:{month}"
r.delete(key)

def check_budget(user_id: str, estimated_cost: float) -> bool:
  month_key = datetime.now().strftime("%Y-%m")
  k = f"budget:{user_id}:{month_key}"
  current = float(r.get(k) or 0)
  if current + estimated_cost > 10.0:
    return False
  r.incrbyfloat(k, estimated_cost)
  r.expire(k, 32 * 24 * 3600)
  return True

print(check_budget("student", 3.5))  # True
print(check_budget("student", 6.0))  # True
print(check_budget("student", 1.0))  # False (3.5 + 6.0 + 1.0 > 10)
print("current_spent=", r.get(key))
'@ | python -
```

###  Checkpoint 4

- [x] Implement API key authentication
- [x] Hiểu JWT flow
- [x] Implement rate limiting
- [x] Implement cost guard với Redis

---

## Part 5: Scaling & Reliability (40 phút)

###  Concepts

**Vấn đề:** 1 instance không đủ khi có nhiều users.

**Giải pháp:**
1. **Stateless design** — Không lưu state trong memory
2. **Health checks** — Platform biết khi nào restart
3. **Graceful shutdown** — Hoàn thành requests trước khi tắt
4. **Load balancing** — Phân tán traffic

###  Exercise 5.1: Health checks

```bash
cd ../../05-scaling-reliability/develop
```

**Nhiệm vụ:** Implement 2 endpoints:

```python
@app.get("/health")
def health():
    """Liveness probe — container còn sống không?"""
    # TODO: Return 200 nếu process OK
    pass

@app.get("/ready")
def ready():
    """Readiness probe — sẵn sàng nhận traffic không?"""
    # TODO: Check database connection, Redis, etc.
    # Return 200 nếu OK, 503 nếu chưa ready
    pass
```

<details>
<summary> Solution</summary>

```python
@app.get("/health")
def health():
  uptime = round(time.time() - START_TIME, 1)

  checks = {}
  try:
    import psutil
    mem = psutil.virtual_memory()
    checks["memory"] = {
      "status": "ok" if mem.percent < 90 else "degraded",
      "used_percent": mem.percent,
    }
  except ImportError:
    checks["memory"] = {"status": "ok", "note": "psutil not installed"}

  overall_status = "ok" if all(v.get("status") == "ok" for v in checks.values()) else "degraded"
  return {
    "status": overall_status,
    "uptime_seconds": uptime,
    "version": "1.0.0",
    "environment": os.getenv("ENVIRONMENT", "development"),
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "checks": checks,
  }

@app.get("/ready")
def ready():
  if not _is_ready:
    raise HTTPException(
      status_code=503,
      detail="Agent not ready. Check back in a few seconds.",
        )
  return {
    "ready": True,
    "in_flight_requests": _in_flight_requests,
  }
```

*(Nhớ import: `time`, `os`, `datetime, timezone` từ `datetime`, và `HTTPException`.)*

</details>

###  Exercise 5.2: Graceful shutdown

**Nhiệm vụ:** Implement signal handler:

```python
import signal
import logging

logger = logging.getLogger(__name__)

def shutdown_handler(signum, frame):
    """Handle SIGTERM/SIGINT and delegate graceful shutdown to uvicorn."""
    logger.info(f"Received signal {signum} - uvicorn will handle graceful shutdown")

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
```

**Đáp án mẫu (khớp `05-scaling-reliability/develop/app.py`):**

- Signal handler chỉ log tín hiệu; phần shutdown chính do `uvicorn` + `lifespan` đảm nhiệm.
- Trong `lifespan` shutdown:
  - Đặt `_is_ready = False` để ngừng nhận request mới.
  - Chờ `_in_flight_requests` về 0 (tối đa 30 giây).
  - Log `Shutdown complete`.
- `uvicorn.run(..., timeout_graceful_shutdown=30)` đảm bảo có thời gian hoàn tất request đang xử lý.

Test (Linux/macOS):
```bash
python app.py &
PID=$!

# Gửi request
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Long task"}' &

# Ngay lập tức kill
kill -TERM $PID

# Quan sát: Request có hoàn thành không?
```

Test (Windows PowerShell):
```powershell
# Terminal 1: start app
python app.py

# Terminal 2: gọi request
Invoke-RestMethod -Uri "http://localhost:8000/ask?question=Long task" -Method Post

# Quay lại Terminal 1 và nhấn Ctrl+C (SIGINT)
# Quan sát log: "Received signal ..." và "Shutdown complete"
```

###  Exercise 5.3: Stateless design

```bash
cd ../production
```

**Nhiệm vụ:** Refactor code để stateless.

**Anti-pattern:**
```python
#  State trong memory
conversation_history = {}

@app.post("/ask")
def ask(user_id: str, question: str):
    history = conversation_history.get(user_id, [])
    # ...
```

**Correct:**
```python
# State trong Redis (hoặc storage dùng chung), không để trong RAM của từng instance
def save_session(session_id: str, data: dict, ttl_seconds: int = 3600):
  serialized = json.dumps(data)
  _redis.setex(f"session:{session_id}", ttl_seconds, serialized)

def load_session(session_id: str) -> dict:
  data = _redis.get(f"session:{session_id}")
  return json.loads(data) if data else {}

@app.post("/chat")
async def chat(body: ChatRequest):
  session_id = body.session_id or str(uuid.uuid4())

  session = load_session(session_id)
  history = session.get("history", [])
  history.append({"role": "user", "content": body.question})

  answer = ask(body.question)
  history.append({"role": "assistant", "content": answer})

  save_session(session_id, {"history": history})
  return {"session_id": session_id, "answer": answer}
```

###  Exercise 5.4: Load balancing

**Nhiệm vụ:** Chạy stack với Nginx load balancer:

```bash
docker compose up --scale agent=3
```

Quan sát:
- 3 agent instances được start
- Nginx phân tán requests
- Nếu 1 instance die, traffic chuyển sang instances khác

Test:
```bash
# Gọi 10 requests
for i in {1..10}; do
  curl http://localhost:8080/chat -X POST \
    -H "Content-Type: application/json" \
    -d '{"question": "Request '$i'"}'
done

for ($i = 1; $i -le 10; $i++) {
  try {
    $res = Invoke-RestMethod -Uri "http://localhost:8080/ask" -Method Post -ContentType "application/json" -Body (@{ question = "Request $i" } | ConvertTo-Json -Compress)
    Write-Host "[$i] OK answer=$($res.answer)"
  } catch {
    $status = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { "N/A" }
    $msg = if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $_.ErrorDetails.Message } else { $_.Exception.Message }
    Write-Host "[$i] FAIL status=$status msg=$msg"
  }
}

# Check logs — requests được phân tán
docker compose logs agent
```

###  Exercise 5.5: Test stateless

```bash
python test_stateless.py
```

Script này:
1. Gọi API để tạo conversation
2. Kill random instance
3. Gọi tiếp — conversation vẫn còn không?

###  Checkpoint 5

- [x] Implement health và readiness checks
- [x] Implement graceful shutdown
- [x] Refactor code thành stateless
- [x] Hiểu load balancing với Nginx
- [x] Test stateless design

---

## Part 6: Final Project (60 phút)

###  Objective

Hoàn thiện một production-ready AI agent, kết hợp TẤT CẢ concepts đã học.

Trong lab này, bản hoàn chỉnh nằm ở thư mục `06-lab-complete` và đã được verify chạy thực tế.

###  Requirements

**Functional:**
- [x] Agent trả lời câu hỏi qua REST API
- [ ] Support conversation history (không bắt buộc cho bài nộp tối thiểu)
- [ ] Streaming responses (optional)

**Non-functional:**
- [x] Dockerized với multi-stage build
- [x] Config từ environment variables
- [x] API key authentication
- [x] Rate limiting
- [x] Cost guard
- [x] Health check endpoint
- [x] Readiness check endpoint
- [x] Graceful shutdown
- [x] Stateless-friendly architecture (shared services qua Redis)
- [x] Structured JSON logging
- [x] Deploy lên Railway hoặc Render (config sẵn)
- [x] Public URL hoạt động

### 🏗 Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Nginx (LB)     │
└──────┬──────────┘
       │
       ├─────────┬─────────┐
       ▼         ▼         ▼
   ┌──────┐  ┌──────┐  ┌──────┐
   │Agent1│  │Agent2│  │Agent3│
   └───┬──┘  └───┬──┘  └───┬──┘
       │         │         │
       └─────────┴─────────┘
                 │
                 ▼
           ┌──────────┐
           │  Redis   │
           └──────────┘
```

###  Step-by-step (đã hoàn thành)

#### Step 1: Mở project hoàn chỉnh

```bash
cd 06-lab-complete
```

#### Step 2: Chuẩn bị environment

Windows PowerShell:

```powershell
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
```

#### Step 3: Build và chạy stack local

```bash
docker compose up -d --build
```

#### Step 4: Verify runtime endpoints

Windows PowerShell:

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
Invoke-RestMethod -Uri "http://localhost:8000/ready" -Method Get

$apiKey = (Get-Content .env | Where-Object { $_ -match '^AGENT_API_KEY=' } | Select-Object -First 1).Split('=')[1]
Invoke-RestMethod -Uri "http://localhost:8000/ask" -Method Post -Headers @{"X-API-Key"=$apiKey} -ContentType "application/json" -Body '{"question":"Part 6 smoke test"}'
```

Kết quả kỳ vọng:
- `health.status = ok`
- `ready = true`
- `/ask` trả về `answer`

#### Step 5: Chạy checker của lab

```bash
python check_production_ready.py
```

Kết quả đã verify:
- `Result: 20/20 checks passed (100%)`
- `PRODUCTION READY`

#### Step 6: Deploy cloud

Railway:

```bash
railway init
railway variables set AGENT_API_KEY=your-secret-key
railway variables set JWT_SECRET=your-jwt-secret
railway up
```

Render:
- Push code lên GitHub
- Connect repo trên Render
- Render đọc file `render.yaml`
- Set secrets trên dashboard rồi deploy

Public URL đã verify:
- Docs: https://ai-agent-5cj8.onrender.com/docs
- Health: https://ai-agent-5cj8.onrender.com/health (`status = ok`)

###  Validation

Chạy script kiểm tra:

```bash
cd 06-lab-complete
python check_production_ready.py
```

Script sẽ kiểm tra:
-  Dockerfile exists và valid
-  Multi-stage build
-  .dockerignore exists
-  Health endpoint returns 200
-  Readiness endpoint returns 200
-  Auth required (401 without key)
-  Rate limiting works (429 after limit)
-  Cost guard works (402 when exceeded)
-  Graceful shutdown (SIGTERM handled)
-  Stateless (state trong Redis, không trong memory)
-  Structured logging (JSON format)

**Kết quả thực tế đã chạy trong lab này:** `20/20 checks passed (100%)`.

###  Grading Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Functionality** | 20 | Agent hoạt động đúng |
| **Docker** | 15 | Multi-stage, optimized |
| **Security** | 20 | Auth + rate limit + cost guard |
| **Reliability** | 20 | Health checks + graceful shutdown |
| **Scalability** | 15 | Stateless + load balanced |
| **Deployment** | 10 | Public URL hoạt động |
| **Total** | 100 | |

---

##  Hoàn Thành!

Bạn đã:
-  Hiểu sự khác biệt dev vs production
-  Containerize app với Docker
-  Deploy lên cloud platform
-  Bảo mật API
-  Thiết kế hệ thống scalable và reliable

###  Next Steps

1. **Monitoring:** Thêm Prometheus + Grafana
2. **CI/CD:** GitHub Actions auto-deploy
3. **Advanced scaling:** Kubernetes
4. **Observability:** Distributed tracing với OpenTelemetry
5. **Cost optimization:** Spot instances, auto-scaling

###  Resources

- [12-Factor App](https://12factor.net/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)

---

##  Q&A

**Q: Tôi không có credit card, có thể deploy không?**  
A: Có! Railway cho $5 credit, Render có 750h free tier.

**Q: Mock LLM khác gì với OpenAI thật?**  
A: Mock trả về canned responses, không gọi API. Để dùng OpenAI thật, set `OPENAI_API_KEY` trong env.

**Q: Làm sao debug khi container fail?**  
A: `docker logs <container_id>` hoặc `docker exec -it <container_id> /bin/sh`

**Q: Redis data mất khi restart?**  
A: Dùng volume: `volumes: - redis-data:/data` trong docker-compose.

**Q: Làm sao scale trên Railway/Render?**  
A: Railway: `railway scale <replicas>`. Render: Dashboard → Settings → Instances.

---

**Happy Deploying! **
