# 容器化发布（移除本地 DB/Redis）Plan

## Summary

把仓库现有 `docker-compose.yml` 中的本地 Postgres/Redis 移除，改为仅编排：

* **后端** `ymd-server`（FastAPI/Uvicorn）

* **前端** `ymd-admin`（Vite 构建为静态资源，由 Nginx 托管）

对外仅暴露一个入口 **Nginx :80**，并反代 `/api/*` 到后端；后端通过环境变量连接你已有的外部数据库/Redis（compose 不再启动它们）。同时做基础的“构建/启动/健康检查/压测验收（单机 p95 < 500ms）”。

## Current State Analysis（基于仓库现状）

* 当前 compose 只有本地 `db` 与 `redis` 两个 service：[docker-compose.yml](file:///c:/Users/brian/projects/ymd/docker-compose.yml)

* 仓库内暂无 Dockerfile（后端/前端均未容器化）。

* 后端为 FastAPI 应用入口：[main.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/main.py)

  * 路由前缀 `/api/v1`：[config.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/core/config.py#L3-L29)

  * 数据库连接通过 `POSTGRES_*` 环境变量拼接：[config.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/core/config.py#L7-L29)

  * SQLAlchemy engine 当前 `echo=True`（生产会显著拖慢响应）：[database.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/core/database.py#L1-L6)

* ymd-admin 默认 API 地址为 `VITE_API_BASE_URL`（无则回落 localhost:8000）：[request.ts](file:///c:/Users/brian/projects/ymd/ymd-admin/src/utils/request.ts#L1-L5)

## Proposed Changes

### 1) 新增后端 Dockerfile（ymd-server）

**新增文件**

* `ymd-server/Dockerfile`

**实现要点**

* 基础镜像：`python:3.11-slim`（或当前项目要求的 Python 版本，以 `requirements.txt` 为准）

* 安装依赖：`pip install -r requirements.txt`

* 工作目录 `/app`，拷贝 `ymd-server/app` 与 alembic 配置

* 暴露端口 `8000`

* 启动命令（生产向）：`uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-2} --proxy-headers`

* 挂载上传目录：为 `uploads` 提供可写目录（compose 中用 named volume 挂载到 `/app/uploads`）

### 2) 新增前端 Dockerfile（ymd-admin）+ Nginx 反代

**新增文件**

* `ymd-admin/Dockerfile`（多阶段：Node 构建 → Nginx 托管）

* `ymd-admin/nginx.conf`（或 `nginx/default.conf`）

**实现要点**

* 构建阶段：`node:20-alpine` 执行 `npm ci && npm run build`

* 运行阶段：`nginx:alpine`

  * 把 `dist/` 拷贝到 Nginx 静态目录

  * Nginx 反代：

    * `/api/` → `http://api:8000/`（或直接 `/api/v1/` 转发，按你希望路径一致性配置）

    * `/static/` → `http://api:8000/static/`（后端上传文件访问）

  * SPA 路由：`try_files $uri /index.html`

* Vite API 基址：在 Docker build 时注入 `VITE_API_BASE_URL=/api/v1`（同域访问，避免写死 localhost）

  * 使用 `ARG VITE_API_BASE_URL` + `ENV VITE_API_BASE_URL`，构建时传入

### 3) 重写根 docker-compose.yml：移除 db/redis，加入 api + web

**修改文件**

* 根目录：[docker-compose.yml](file:///c:/Users/brian/projects/ymd/docker-compose.yml)

**目标形态**

* `services.api`：build `./ymd-server`，仅在内部网络暴露 8000（不对外暴露端口或可选映射用于调试）

  * `environment` 通过 `.env` 传入：`POSTGRES_SERVER/PORT/USER/PASSWORD/DB`、`SECRET_KEY` 等

  * `volumes`：`uploads:/app/uploads`

  * `healthcheck`：请求 `GET http://localhost:8000/` 或 `GET /api/v1/openapi.json`

* `services.web`：build `./ymd-admin`，对外暴露 `80:80`

  * 通过 Nginx 反代把 `/api/*` 转发到 `api`

  * `depends_on` 等待 `api` 健康后启动（compose v3 的限制下用 healthcheck + depends\_on condition（如可用）或文档化启动顺序）

* 删除 `volumes.postgres_data` / `volumes.redis_data`

### 4) 后端“500ms 内”基础优化（不引入复杂架构）

**修改文件**

* `ymd-server/app/core/config.py`

* `ymd-server/app/core/database.py`

**实现要点**

* 把 SQLAlchemy `echo` 改为可配置且默认关闭（生产关闭，开发可开）

  * 新增 settings：`SQL_ECHO: bool = False`

  * `create_async_engine(..., echo=settings.SQL_ECHO)`

* Docker 运行侧：通过 Uvicorn 多 worker + 合理 keep-alive 达到单机 p95 指标（在外部 DB 网络正常前提下）

## Assumptions & Decisions

* 你确认：前端容器化范围为 **ymd-admin**；对外暴露方式为 **一个入口 Nginx**；性能验收口径为 **单机 p95 < 500ms**。

* 外部 DB/Redis 由你提供地址与凭据；本仓库 compose 不再启动它们。

* 由于后端目前未发现 Redis 客户端使用点，compose 中不会强制配置 Redis（如后续接入，可再补环境变量与依赖）。

## Verification Steps（必须执行）

### A. 容器构建与启动校验

1. `docker compose build`（确保 ymd-server 与 ymd-admin 镜像可构建）
2. `docker compose up -d`
3. 冒烟测试（从宿主机访问 Nginx 单入口）：

   * `GET http://localhost/` 返回 ymd-admin 页面

   * `GET http://localhost/api/v1/openapi.json` 返回 OpenAPI JSON

   * `GET http://localhost/` 登录后管理端主要页面可正常拉取数据（依赖外部 DB）

### B. 性能验收（单机 p95 < 500ms）

> 说明：性能受“外部 DB 网络延迟/实例规格/数据量”影响；验收需在目标部署机上进行。

1. 选择 1–2 个关键读接口（建议）：

   * `GET /api/v1/events?limit=20&offset=0`

   * `GET /api/v1/posts?limit=20&offset=0`
2. 使用压测工具对 **Nginx 入口**发压测（保证路径与真实流量一致）：

   * 例如 `hey`：`hey -n 2000 -c 50 http://localhost/api/v1/events?limit=20&offset=0`
3. 验收标准：

   * p95 < 500ms

   * 错误率 \~ 0（除非外部 DB 不可用）
4. 若不达标的排查顺序（只做必要项）：

   * 确认 `SQL_ECHO` 关闭

   * 提升 `WEB_CONCURRENCY`（例如 2 → 4）并观察收益

   * 选择更轻的验收接口或加索引/优化查询（另开性能优化任务单独做，避免本次变更扩大）

