# 一键启动脚本（动态端口）Plan

## Summary
新增一个 Windows PowerShell 启动脚本，用于**一键启动**：
- 后端：`ymd-server`（Uvicorn/FastAPI）
- 管理后台前端：`ymd-admin`（Vite dev）
- 小程序前端（H5）：`ymd-app`（uni H5 dev）

脚本会为每个服务**自动选择未被占用的端口**，并把前端的 `VITE_API_BASE_URL` 指向后端实际端口，实现“前后端对齐”。启动成功后不自动打开浏览器，仅打印访问地址与进程信息。

## Current State Analysis（基于仓库现状）
- 后端入口为 `app.main:app`：[main.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/main.py)
- 后端允许跨域（`allow_origins=["*"]`），本地多端口开发可直接访问 API：[main.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/main.py#L12-L18)
- ymd-admin 启动脚本为 `npm run dev`（Vite）：[package.json](file:///c:/Users/brian/projects/ymd/ymd-admin/package.json#L6-L11)  
  - `vite.config.ts` 写死端口 5174，但 Vite CLI 可通过 `--port` 覆盖：[vite.config.ts](file:///c:/Users/brian/projects/ymd/ymd-admin/vite.config.ts#L4-L9)
- ymd-app(H5) 启动脚本为 `npm run dev:h5`（uni）：[package.json](file:///c:/Users/brian/projects/ymd/ymd-app/package.json#L4-L8)
- ymd-app API 基址已支持 `VITE_API_BASE_URL` 注入（无则回退 localhost）：[request.ts](file:///c:/Users/brian/projects/ymd/ymd-app/src/utils/request.ts#L1-L7)

## Proposed Changes
### 1) 新增启动脚本（PowerShell）
**新增文件**
- `scripts/dev-start.ps1`（主脚本）
- `dev-start.ps1`（根目录薄封装，转调 `scripts/dev-start.ps1`，方便双击/直接运行）

**脚本行为（决策已锁定）**
- **动态端口分配**：脚本内实现 `Get-FreePort()`（用 `System.Net.Sockets.TcpListener` 绑定 `0` 分配可用端口，再释放），得到：
  - `API_PORT`（后端）
  - `ADMIN_PORT`（ymd-admin）
  - `H5_PORT`（ymd-app H5）
- **前后端对齐**：
  - 设置环境变量 `VITE_API_BASE_URL="http://localhost:$API_PORT/api/v1"`（同一进程树下子进程继承），使：
    - ymd-admin 的请求走该基址（其 request 已支持）
    - ymd-app(H5) 的请求与上传同样走该基址（其 request 已支持）
- **启动后端**（在 `ymd-server` 目录）：
  - `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port $API_PORT`
  - 若用户已有虚拟环境，使用当前 `python`；脚本会先做 `python -c "import uvicorn"` 预检，失败则提示“先安装依赖”并退出。
- **启动 ymd-admin**（在 `ymd-admin` 目录）：
  - `npm run dev -- --port $ADMIN_PORT --strictPort`
  - 若端口不可用则脚本重新分配并重试一次（保证“动态且确定”）。
- **启动 ymd-app(H5)**（在 `ymd-app` 目录）：
  - 首选尝试：`npm run dev:h5 -- --port $H5_PORT --strictPort`
  - 若 uni CLI 不接受 `--port` 参数导致启动失败，则自动回退到 `npm run dev:h5`（此时由 uni/Vite 自行挑选端口），并从控制台输出解析最终 URL（脚本会打印“实际端口”）。
- **进程与窗口**：
  - 默认使用 `Start-Job` 在后台启动三个进程（兼容受限环境/CI）；主窗口负责汇总 URL 与健康检查结果。
- **健康检查**（超时可配置，默认 30s）：
  - 后端：轮询 `http://localhost:$API_PORT/api/v1/openapi.json`，成功后再启动前端（避免前端启动后接口不可用造成报错）。
  - 前端：仅打印启动端口与 URL（不做深度探测，避免依赖 dev server 输出格式）。

### 2) 最小文档（使用说明）
**新增文件**
- `scripts/README-dev-start.md`

**内容**
- 必备前置：已安装 Node.js、Python、并在 `ymd-admin/ymd-app` 执行过 `npm install`，后端 python 环境安装过 `ymd-server/requirements.txt`
- 启动命令：`pwsh ./dev-start.ps1`
- 输出说明：API/管理后台/H5 的访问地址与端口
- 常见问题：端口占用、python/uvicorn 未安装、npm 未安装依赖

## Assumptions & Decisions
- 启动方式锁定为“本地开发服务（uvicorn + npm dev）”，不依赖 Docker 镜像拉取。
- 不自动打开浏览器，只打印地址。
- 动态端口以脚本自动探测为准，且前端通过 `VITE_API_BASE_URL` 与后端端口联动。

## Verification Steps
1. 在仓库根目录执行：`pwsh ./dev-start.ps1`
2. 验证输出包含三个 URL：
   - API：`http://localhost:<API_PORT>/api/v1/openapi.json` 可访问
   - Admin：`http://localhost:<ADMIN_PORT>/`
   - H5：`http://localhost:<H5_PORT>/`
3. 打开 Admin 页面触发一次 API 请求（例如登录页/列表页），确认请求指向 `API_PORT`（非 8000/localhost 写死）。
4. 打开 H5 页面拉取活动/社区列表并上传一张图片，确认上传请求同样指向 `API_PORT`。
