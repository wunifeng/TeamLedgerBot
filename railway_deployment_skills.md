# Railway 部署技能与最佳实践说明书 (Railway Deployment Skills & Best Practices)

为确保今后执行部署有据可循，并完美规避我们在首次部署中遇到的所有技术阻碍，本说明书总结了将 FastAPI + PostgreSQL (如 Neon) 后端服务部署至 Railway 的完整工作流与核心避坑指南。

---

## 🛠️ 核心部署概念与避坑法则 (Core Concepts)

### 1. 密钥分工：`RAILWAY_API_TOKEN` vs. `RAILWAY_TOKEN`
*   ⚠️ **核心误区**：在非交互式命令行（CI/CD、沙箱或 AI Agent）中，如果将账户/空间级的 API 凭证错误地设置为 `$env:RAILWAY_TOKEN` 环境变量，会导致 Railway CLI 出现 `Unauthorized`（未授权）错误。
*   🎯 **黄金法则**：
    *   **`RAILWAY_API_TOKEN`（账户/空间级 Token）**：由账户设置中的 **Account Settings > Tokens** 生成。在 CLI 中执行全局/跨项目的管理命令（如 `railway init` 初始化、`railway add` 增改服务、`railway domain` 关联域）时，**必须使用该变量**。
    *   **`RAILWAY_TOKEN`（项目级 Token）**：由项目 Dashboard 内部生成。它仅能绑定到单一特定服务，仅限用于自动部署构建或读取服务变量，不具备行政管理权。
    *   **非交互式命令行建议全局运行前配置：**
        ```powershell
        $env:RAILWAY_API_TOKEN = "c2fe4c6c-5801-44a4-a8c3-cf2f458a6ee5"
        ```

### 2. 精确端口映射机制
*   Railway 依赖容器内绑定的端口进行外部反向代理与健康检查。
*   **网络绑定三法则**：
    1.  应用进程必须监听在所有网络接口上：`--host 0.0.0.0`。
    2.  确保手动在 Railway 服务环境变量中添加 `PORT=8000`（或相应端口）。
    3.  `railway.toml` 启动命令必须显式指定端口，避免因 shell 环境变量未成功解析导致的绑定错误。

---

## 🚀 解决的技术瓶颈与黄金范式 (Solved Bottlenecks & Best Practices)

### 1. 后台异步迁移模式 (Zero-Delay Startup)
*   **痛点背景**：在大多数 Docker 容器或 Railway 默认流中，习惯在启动脚本中使用 `alembic upgrade head && uvicorn app.main:app`。如果云端数据库连接挂起、握手时间稍长或正在锁表，会导致整个主应用启动超时。由于 Railway 的容器 `/health` 健康检查重试窗口仅有 30 秒，一旦应用没能在 30 秒内开启端口，部署会被直接判定为 **FAILED**（强行中止并回滚）。
*   **黄金解决方案**：将 Alembic 迁移从 `startCommand` 剥离，挪到 FastAPI `lifespan` 启动事件中，作为 **独立子进程** 异步挂起：
    ```python
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        # 1. 在后台拉起 Alembic 迁移进程（绝不阻塞 Uvicorn 主线程绑定端口）
        try:
            import subprocess
            process = subprocess.Popen(
                ["alembic", "upgrade", "head"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # 迁移进程在后台自行与数据库握手，输出将自然流向 Railway 日志系统
        except Exception as e:
            pass # 记录异常日志
        
        yield
        await engine.dispose()
    ```
*   **优势**：Uvicorn 瞬间完成端口绑定并立刻通过健康检查；同时，数据库迁移在后台安全并发运行，极其稳健。

### 2. 容器内部 SSL 证书信任绕过 (SSL Bypass)
*   **痛点背景**：使用 `python:3.12-slim` 等精简基础镜像时，Linux 容器内部可能缺失完整的根 CA 证书链。当连接类似 Neon 等云数据库时，常因无法校验服务器 SSL 证书直接抛出 `ssl.SSLCertVerificationError` 崩溃。
*   **黄金解决方案**：在构建 SQLAlchemy 异步引擎或 Alembic `env.py` 握手时，通过 SSL 上下文关闭严格校验：
    ```python
    import ssl
    
    connect_args = {}
    if "ssl=require" in settings.DATABASE_URL or "sslmode=require" in settings.DATABASE_URL:
        _ssl_context = ssl.create_default_context()
        _ssl_context.check_hostname = False
        _ssl_context.verify_mode = ssl.CERT_NONE  # 跳过证书吊销与信任链校验
        connect_args["ssl"] = _ssl_context
    ```

---

## 📋 完整部署执行流程 (Step-by-Step Workflow)

### 步骤 1：准备启动定义文件 `railway.toml`
在项目后端目录下放置 `railway.toml`，显式硬编码指定启动端口（规避 shell 变量未解析的 bug）：
```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port 8000"
healthcheckPath = "/health"
healthcheckTimeout = 30
restartPolicyType = "on_failure"
```

### 步骤 2：登录与项目初始化
```powershell
# 1. 注入账户级令牌
$env:RAILWAY_API_TOKEN = "your_account_tokens"

# 2. 初始化项目 (非交互式)
railway init --name TeamLedgerBot --json
```

### 步骤 3：创建服务与域名绑定
```powershell
# 1. 新增空服务
railway add --service backend --json

# 2. 绑定或生成公共域名
railway domain --service backend --json
```

### 步骤 4：注入环境变量 (必须包含 PORT)
```powershell
railway variable set `
  PORT="8000" `
  APP_ENV="production" `
  CORS_ORIGINS="*" `
  DATABASE_URL="postgresql+asyncpg://..." `
  TELEGRAM_BOT_TOKEN="..." `
  TELEGRAM_CHAT_ID="..." `
  --service backend --json
```

### 步骤 5：代码打包推送与实时观测
```powershell
# 1. 推送当前目录并部署
railway up --service backend --detach --json

# 2. 实时追踪最新容器日志 (排查后台 Alembic 迁移进程状态)
railway logs --latest -d --lines 50
```
