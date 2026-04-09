# 修复小程序端 API 地址不随 env 生效 Plan

## Summary
修复 ymd-app（mp-weixin）在已生成 `ymd-app/.env.local` 且包含 `VITE_API_BASE_URL` 时，运行仍然回退到 `http://localhost:8000/api/v1` 的问题。根因是 mp-weixin 构建产物中 `import.meta.env` 被编译为 `{}`，导致运行时读不到 `VITE_API_BASE_URL`。本方案改为使用 **Vite define 注入常量**，保证 mp-weixin/H5 均能在构建期拿到正确的 API Base，并继续保持 dev-start 生成 `.env.local` 的工作流。

## Current State Analysis（已确认）
- `ymd-app/src/utils/request.ts` 目前通过 `import.meta.env.VITE_API_BASE_URL` 取值，取不到则回退 `http://localhost:8000/api/v1`：[request.ts](file:///c:/Users/brian/projects/ymd/ymd-app/src/utils/request.ts#L1-L7)
- `dev-start` 已生成 `ymd-app/.env.local` 写入 `VITE_API_BASE_URL=http://localhost:<动态端口>/api/v1`：[dev-start.ps1](file:///c:/Users/brian/projects/ymd/scripts/dev-start.ps1#L32-L38)
- 但 mp-weixin 构建产物中 env 为空对象，最终 `BASE_URL` 仍固化为 `http://localhost:8000/api/v1`（说明 `.env.local` 没有通过 `import.meta.env` 注入到 mp-weixin 产物）。

## Proposed Changes
### 1) 在 ymd-app 的 Vite 配置中显式加载 env，并通过 define 注入常量
**修改文件**
- `ymd-app/vite.config.ts`

**修改内容**
- 使用 `loadEnv(mode, process.cwd())` 读取 `.env.local/.env.*`。
- 增加 `define` 注入常量（例如）：
  - `__YMD_API_BASE_URL__ = env.VITE_API_BASE_URL || ''`

### 2) request.ts 改为优先使用注入常量（兼容 mp-weixin）
**修改文件**
- `ymd-app/src/utils/request.ts`

**修改内容**
- `BASE_URL` 取值优先级调整为：
  1. `__YMD_API_BASE_URL__`（构建期注入，mp-weixin 可用）
  2. `import.meta.env.VITE_API_BASE_URL`（H5 仍可用）
  3. 回退 `http://localhost:8000/api/v1`（仅本机兜底）
- 保持现有“去尾斜杠”逻辑，避免拼接双斜杠。

### 3) 补齐全局常量类型声明
**修改文件**
- `ymd-app/src/env.d.ts`

**修改内容**
- 增加：
  - `declare const __YMD_API_BASE_URL__: string;`

### 4) 验证（必须）
**mp-weixin 构建验证**
- `npm run build:mp-weixin`
- 在 `dist/build/mp-weixin/utils/request.js` 中确认不再出现 `http://localhost:8000/api/v1`，而是 `.env.local` 里写入的动态端口。

**H5 构建验证**
- `npm run build:h5`、`npm run type-check`

## Assumptions & Decisions
- 需要同时兼容“开发者工具 + 真机调试”：dev-start 增加可选参数决定 API Host。
  - 默认 `localhost`（适合开发者工具）
  - 可选 `auto`（自动取本机局域网 IPv4，用于真机访问：`http://<LAN_IP>:<port>/api/v1`）
- dev-start 继续负责生成 `ymd-app/.env.local`，本方案保证该 env 能被 mp-weixin 构建期正确注入。
- 真机调试需要微信“合法域名/请求域名”配置满足要求；本计划仅提供可访问的 URL 方案与开关，不代替微信域名备案/配置流程。

## Additional Change（为真机提供 API Host 开关）
### 5) dev-start：支持生成 localhost 或 LAN IP 的 VITE_API_BASE_URL
**修改文件**
- `scripts/dev-start.ps1`

**修改内容**
- 增加参数（例如）：`-ApiHostMode localhost|auto`（默认 localhost）
- 当选择 auto：
  - 自动获取本机优先 IPv4（非 127.0.0.1、非 link-local）
  - 写入 `ymd-app/.env.local`：`VITE_API_BASE_URL=http://<LAN_IP>:<API_PORT>/api/v1`
  - 同时在控制台打印该 URL，方便复制到微信开发者工具/真机配置
