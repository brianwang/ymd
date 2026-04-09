# 小程序前端与 Docker 后端对齐 Plan

## Summary
当前 **ymd-app（小程序/uni-app）没有与 Docker 化后的后端对齐**：请求基址被硬编码为 `http://localhost:8000/api/v1`，在真机/线上环境会指向“用户设备自身”，无法访问 Docker 容器后端。  
本计划通过“**把 API Base URL 做成可配置**（H5 用同域相对路径，小程序用域名绝对路径）”来完成对齐；不改变现有业务逻辑与页面内容，仅改请求配置与必要的构建配置。

## Current State Analysis
- ymd-app API 基址硬编码：
  - `BASE_URL = 'http://localhost:8000/api/v1'`：[request.ts](file:///c:/Users/brian/projects/ymd/ymd-app/src/utils/request.ts#L1-L4)
  - `uni.request` 拼接：`BASE_URL + options.url`：[request.ts](file:///c:/Users/brian/projects/ymd/ymd-app/src/utils/request.ts#L42)
  - 上传同样依赖 `BASE_URL`：
    - 发帖上传：[create.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/community/create.vue#L263-L284)
    - 头像上传：[edit.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/edit.vue#L106-L131)
- ymd-admin 已对齐 Docker/Nginx：
  - 通过 `VITE_API_BASE_URL` 支持 `/api/v1` 相对路径：[request.ts](file:///c:/Users/brian/projects/ymd/ymd-admin/src/utils/request.ts#L1-L5)
  - Nginx 反代 `/api/`、`/static/` 到后端 api 容器：[nginx.conf](file:///c:/Users/brian/projects/ymd/ymd-admin/nginx.conf#L7-L23)
  - compose 外部端口目前为 `8044:80`（由你调整）：[docker-compose.yml](file:///c:/Users/brian/projects/ymd/docker-compose.yml#L26-L36)

## Intent & Success Criteria
### 目标
- 小程序端与 Docker 后端“对齐”= 在真机/线上环境，ymd-app 的 API/上传都能指向你部署的 **Nginx 单入口** 或后端域名，而不是 localhost。

### 验收标准
- 小程序真机上登录/拉取列表/发布图文（含上传）均可成功。
- H5 构建在同一 Nginx 域名下部署时，API 走相对路径 `/api/v1` 工作正常。
- 不修改任何业务页面内容（仅请求/配置层改动）。

## Proposed Changes
### 1) ymd-app：将 API Base URL 改为“可配置 + 分端默认值”
**修改文件**
- `ymd-app/src/utils/request.ts`

**实现方案**
- 引入 `VITE_API_BASE_URL`（构建时注入）作为首选基址：
  - 若存在：`BASE_URL = VITE_API_BASE_URL`（可为绝对域名 `https://xxx/api/v1` 或相对路径 `/api/v1`）
  - 若不存在：保留开发回退 `http://localhost:8000/api/v1`
- 同步把所有上传/下载等依赖 `BASE_URL` 的地方统一引用同一来源，避免“请求对齐但上传没对齐”。

**注意点（uni-app）**
- 小程序端不能用相对路径访问后端；需要配置成你的域名（HTTPS）。
- H5 若与 Nginx 同域部署，可以使用相对路径 `/api/v1`，由 Nginx 反代到后端。

### 2) ymd-app：补齐 env 类型声明与构建注入方式
**修改文件**
- `ymd-app/src/env.d.ts`（新增 `VITE_API_BASE_URL?: string` 类型）
- （如仓库已有 `.env.*` 约定）新增或更新 `ymd-app/.env.production`（示例：`VITE_API_BASE_URL=https://your-domain.com/api/v1`）

> 说明：该步骤只用于构建时注入配置，不改变运行时逻辑。

### 3) Nginx 对齐策略（不新增 Docker 服务）
**不改动点**
- 小程序端不容器化发布，本次不把 ymd-app 放入 docker-compose。

**对齐方式**
- 小程序的 `VITE_API_BASE_URL` 指向你现在对外暴露的 Nginx 地址：
  - 例如 `https://your-domain.com/api/v1`（推荐）
  - 或若你用端口暴露：`http://<server-ip>:8044/api/v1`

## Assumptions & Decisions
- “对齐”指 API 基址与上传路径对齐，不涉及把小程序端容器化（小程序本身不适合用容器发布）。
- 你当前 Nginx 入口为 `8044`（见 compose），后续若改回 `80/443`，只需调整 `VITE_API_BASE_URL`。

## Verification Steps
### 本地构建验证
- `ymd-app`：
  - `npm run type-check`
  - `npm run build:h5`（验证相对路径 `/api/v1` 的构建无报错）

### 联调验证（真机/线上）
- 配置小程序构建的 `VITE_API_BASE_URL=https://<你的域名>/api/v1`
- 真机访问：
  - 登录与拉取社区/活动列表成功
  - 上传头像、发帖上传图片成功（验证上传路径也对齐）

