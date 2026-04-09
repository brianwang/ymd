# 修复小程序端 API 地址（动态端口对齐）Plan

## Summary
修复 ymd-app 小程序端在“后端端口动态变化（dev-start）”场景下 API 地址不对的问题。实现方式：由 `dev-start` 自动生成 `ymd-app/.env.local` 写入 `VITE_API_BASE_URL`（含动态端口），让微信开发者工具重新编译后自动对齐到当前后端端口；不改动业务页面内容，仅改配置与启动脚本行为。

## Current State Analysis（基于仓库现状）
- ymd-app API Base 取自 `import.meta.env.VITE_API_BASE_URL`，缺省回退 `http://localhost:8000/api/v1`：[request.ts](file:///c:/Users/brian/projects/ymd/ymd-app/src/utils/request.ts#L1-L7)
- dev-start 目前仅为 **ymd-admin** 与 **ymd-app(H5)** 的启动进程注入 `VITE_API_BASE_URL`，不会影响微信开发者工具发起的 mp-weixin 编译/运行进程：[dev-start.ps1](file:///c:/Users/brian/projects/ymd/scripts/dev-start.ps1#L82-L102)
- ymd-app 目前没有 `.env.*` 文件，因此 mp-weixin 编译时很容易读不到 `VITE_API_BASE_URL`，进而走回退地址（导致接口不对）。
- ymd-app 的 `.gitignore` 已忽略 `*.local`，适合使用 `.env.local` 作为本机配置文件：[.gitignore](file:///c:/Users/brian/projects/ymd/ymd-app/.gitignore#L10-L14)

## Goal & Success Criteria
### 目标
- 微信开发者工具运行小程序时，API/上传地址能对齐 dev-start 启动的后端动态端口。

### 验收标准
- 执行 `pwsh ./dev-start.ps1` 后，脚本自动写入 `ymd-app/.env.local`，内容包含正确的 `VITE_API_BASE_URL=http://localhost:<API_PORT>/api/v1`。
- 微信开发者工具重新编译小程序后：
  - `GET /api/v1/openapi.json` 可正常访问
  - 社区/活动列表请求正常
  - 上传头像/发帖上传图片正常（同一基址）

## Proposed Changes
### 1) ymd-app：补齐 env 示例文件（只做说明，不影响运行）
**新增文件**
- `ymd-app/.env.example`

**内容**
- 说明 `VITE_API_BASE_URL` 的用途与示例：
  - `VITE_API_BASE_URL=http://localhost:8000/api/v1`（本机 devtools）
  - `VITE_API_BASE_URL=https://your-domain.com/api/v1`（线上/真机）

### 2) dev-start：自动生成 ymd-app/.env.local（关键修复）
**修改文件**
- `scripts/dev-start.ps1`

**实现细节**
- 在选出 `$apiPort` 之后、启动前端之前：
  - 计算 `$apiBase = "http://localhost:$apiPort/api/v1"`
  - 写入 `ymd-app/.env.local`：
    - 文件内容固定为 `VITE_API_BASE_URL=<apiBase>`
    - 写入方式使用 `Set-Content -Encoding UTF8 -NoNewline`，避免 BOM/换行差异导致 Vite 解析异常
- 同时可选写入 `ymd-admin/.env.local`（不是必须，因为脚本已为 ymd-admin 进程注入 env；但写入可便于你脱离脚本启动 ymd-admin 时也能对齐）

### 3) 风险收敛：避免“没配 env 就静默回退”导致误连
**修改文件（可选，但推荐）**
- `ymd-app/src/utils/request.ts`

**实现细节（不改业务，仅提示）**
- 当检测到运行在 mp-weixin 且 `VITE_API_BASE_URL` 为空时，打印一次明确的 toast/console 提示：
  - “未配置 VITE_API_BASE_URL，已回退到 localhost:8000，可能导致接口不通”
- 注意：不改变现有回退逻辑，只增加提示，避免误判“接口挂了”。

## Assumptions & Decisions
- 你的问题发生在 **微信开发者工具** 场景，因此使用 `localhost` 作为默认 host 是可接受的。
- 对齐方式采用 **dev-start 自动写 .env.local**，小程序重新编译即可生效。

## Verification Steps
1. 运行 `pwsh ./dev-start.ps1`
2. 检查 `ymd-app/.env.local` 内容是否为 `VITE_API_BASE_URL=http://localhost:<API_PORT>/api/v1`
3. 微信开发者工具重新编译并打开小程序：
   - 进入任一会发请求的页面（社区/活动）
   - 验证请求域名与端口为 `<API_PORT>`
   - 验证上传接口同样走 `<API_PORT>`

