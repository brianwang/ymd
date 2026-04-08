# 计划：完善后台接口与管理端页面（ymd-admin + ymd-server）

## Summary
- 目标：补齐管理后台（ymd-admin）的页面能力，并把后端（ymd-server）的后台管理 API 补全到“可运营/可治理”的程度。
- 覆盖范围：评论管理页、列表筛选/搜索、积分流水查看、管理员提权（基于现有用户）、管理端 API BaseURL 环境化。
- 交付标准：管理端可完成上述操作；后端提供相应 API；基础冒烟验证通过（含鉴权与查询）。

## Current State Analysis
### 已有后端能力（ymd-server）
- 已有 admin 路由前缀：`/api/v1/admin/*`（由主应用挂载）。
- 已有端点：
  - 用户：列表、启用/禁用、调整积分。
  - 帖子：列表、删除（含清理评论与点赞）。
  - 评论：列表、删除（含回写 comment_count）。
  - 运营配置：reward-config 读写。
- 鉴权：所有 admin 端点都依赖 superuser 鉴权（`get_current_active_superuser`）。
- 缺口：
  - 列表类端点缺少筛选/搜索查询参数（当前仅 limit/offset）。
  - 缺少管理员提权 API（目前只有脚本/改库方式）。
  - 缺少“查看某用户积分流水”的 admin API（用户侧已有 `/points/ledger`，但只能看自己）。
  - OAuth2 `tokenUrl` 声明与实际登录端点不一致（主要影响 OpenAPI 展示/交互）。

### 已有管理端页面（ymd-admin）
- 已有路由/页面：
  - 登录 `/login`
  - 用户 `/users`（启用/禁用、调积分）
  - 帖子 `/posts`（删除）
  - 积分奖励配置 `/reward-config`
- 缺口：
  - 没有“评论管理”页面/路由/菜单入口（但后端已有 `/admin/comments`）。
  - 没有筛选/搜索 UI（对齐 spec 需求不足）。
  - 没有“积分流水查看”UI。
  - 没有“授予管理员（superuser）”UI。
  - 请求层 baseURL 写死 localhost（缺少环境变量支持）。

## Assumptions & Decisions（已确认）
- “后台页面”指 ymd-admin 管理端 SPA。
- 优先补齐：评论管理页、筛选/搜索、积分流水查看、管理员管理（通过“现有用户提权”）。
- 管理端 API BaseURL 通过 Vite 环境变量配置（例如 `VITE_API_BASE_URL`）。

## Proposed Changes
### 1) ymd-server：补齐后台管理 API
**文件：** `ymd-server/app/api/admin.py`
- 增加“管理员提权”端点：
  - `PATCH /api/v1/admin/users/{user_id}/superuser`，body：`{ is_superuser: boolean }`
  - 返回更新后的用户（与现有 `set_user_active` 风格一致：`update().returning(User)`）。
- 增加“查看用户积分流水”端点：
  - `GET /api/v1/admin/users/{user_id}/ledger?limit&offset&event_type&start_at&end_at`
  - response_model 复用 `app/schemas/points.py::PointsLedgerItem`（避免重复 schema）。
  - 查询 `PointsLedger`，按 `created_at desc, id desc` 排序；可选过滤：
    - `event_type` 精确匹配
    - `start_at/end_at` 对 `created_at` 范围过滤
- 为列表端点补“筛选/搜索”参数（最小闭环，前后端一致）：
  - `GET /admin/users`：支持 `q`（匹配 `email/open_id/nickname`，采用 ILIKE/contains），可选 `is_active`、`is_superuser`。
  - `GET /admin/posts`：支持 `q`（content contains）、可选 `user_id`、`start_at/end_at`。
  - `GET /admin/comments`：支持 `q`（content contains）、可选 `user_id`、`post_id`、`start_at/end_at`。
  - 保持 `limit/offset` 行为不变。
- 错误处理与鉴权保持既有风格（404/403/400，统一依赖 `get_current_active_superuser`）。

**文件：** `ymd-server/app/api/deps.py`
- 修正 `OAuth2PasswordBearer(tokenUrl=...)` 与实际登录端点一致（仅影响 OpenAPI/Swagger 授权交互展示，不改业务逻辑）。

### 2) ymd-admin：补齐页面与交互
**文件：** `ymd-admin/src/router/index.ts`
- 增加路由 `/comments` 指向新页面 `CommentsView.vue`。
- 如当前路由有布局守卫/鉴权守卫，则复用既有模式接入。

**文件：** `ymd-admin/src/views/LayoutView.vue`
- 菜单补入口：评论管理（与 Users/Posts/RewardConfig 同级）。

**新增文件：** `ymd-admin/src/views/CommentsView.vue`
- 功能：
  - 列表加载：调用 `GET /admin/comments`
  - 删除：调用 `DELETE /admin/comments/{id}`
  - 筛选：`q`、`user_id`、`post_id`、时间范围（start_at/end_at）
  - 分页：limit/offset（沿用现有页面风格）

**文件：** `ymd-admin/src/views/UsersView.vue`
- 增加：
  - 授予/取消管理员：调用 `PATCH /admin/users/{id}/superuser`
  - 查看积分流水：在用户行提供“查看流水”按钮，展示 ledger 列表（可用简单弹窗/抽屉式 UI；保持与现有组件/样式一致）
  - 筛选：`q`、`is_active`、`is_superuser`

**文件：** `ymd-admin/src/views/PostsView.vue`
- 增加筛选：`q`、`user_id`、时间范围（start_at/end_at）
- 列表请求携带查询参数。

**文件：** `ymd-admin/src/utils/request.ts`
- 将 `BASE_URL` 改为读取 `import.meta.env.VITE_API_BASE_URL`：
  - 默认值仍回退到当前 `http://localhost:8000/api/v1`，保证本地不配 env 也能跑。
- 确保路径拼接规则不变（避免双斜杠）。

**新增文件（可选但推荐）：** `ymd-admin/.env.example`
- 示例：`VITE_API_BASE_URL=http://localhost:8000/api/v1`

### 3) 兼容性与边界
- 筛选参数全部为可选；未提供时行为与现在一致。
- 时间范围参数统一使用 ISO8601 datetime 字符串（由 FastAPI/Pydantic 自动解析为 `datetime`）。
- 管理端如果没有组件库，UI 采用现有页面的原生表格/输入框风格实现。

## Verification
### 后端
- 运行现有冒烟脚本（如有）并扩展/新增验证点：
  - 使用管理员 token 调用：users/posts/comments 列表（含筛选参数）返回 200。
  - 调用 `PATCH /admin/users/{id}/superuser` 生效（再次 list_users 看到字段变化）。
  - 调用 `GET /admin/users/{id}/ledger` 返回积分流水（先通过调积分制造流水）。
  - 非 superuser token 访问 admin 端点返回 403。
- 确认 OpenAPI 中 OAuth2 tokenUrl 指向实际登录端点（用于 Swagger Authorize）。

### 前端（ymd-admin）
- 本地用默认 baseURL 运行：登录成功后能进入 Users/Posts/Comments/RewardConfig。
- 验证操作闭环：
  - Users：启用/禁用、调积分、授予管理员、查看积分流水。
  - Posts：筛选后列表变化、删除成功。
  - Comments：筛选后列表变化、删除成功。
- 切换环境变量 `VITE_API_BASE_URL` 后请求指向正确后端。

