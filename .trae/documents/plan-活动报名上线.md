# 计划：活动报名功能完善到可上线

## Summary
- 目标：把“活动浏览 → 详情 → 填写报名信息 → 报名成功/取消 → 我的报名”做成端到端闭环，并补齐后台（`ymd-admin`）的活动管理与报名名单查看，达到可运营上线的最小版本。
- 核心约束（已确认）：免费报名；报名字段=姓名+手机号+备注；支持限额+截止；允许取消报名；后台需要活动管理界面与报名名单。

## Current State Analysis
- 小程序端活动是前端假数据：活动列表用 `seed()` 生成本地数组，不请求后端。[index.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/events/index.vue#L185-L252)
- 活动详情是占位页：按钮仅提示“功能开发中”，无报名流程。[detail.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/events/detail.vue#L1-L44)
- 后端没有活动/报名域：FastAPI 路由未注册 `events`，models 中也不存在 Event/Registration 表。[main.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/main.py#L6-L28)
- 后台管理端（`ymd-admin`）没有活动管理入口与页面：当前仅用户/帖子/评论/奖励配置。[LayoutView.vue](file:///c:/Users/brian/projects/ymd/ymd-admin/src/views/LayoutView.vue#L8-L13)

## Assumptions & Decisions
- 活动浏览：活动列表/详情对未登录用户可见；报名/取消/我的报名需要登录。
- 幂等与并发：同一用户同一活动只允许存在一条报名记录（可取消后再报名）；报名扣减名额用数据库原子更新避免超卖。
- 隐私：手机号、备注只在“管理员报名名单接口”返回；公开活动接口不返回报名者隐私字段。
- 后台权限：活动管理与报名名单仅 `is_superuser` 可访问（复用现有 `get_current_active_superuser`）。

## Proposed Changes

### A) 后端（ymd-server）：数据模型与迁移
1) 新增活动表 `events`
- 新文件：[event.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/models/event.py)
- 关键字段（建议最小可用）：
  - `id`（PK）
  - `title`、`category`、`city`、`address`
  - `cover_url`（活动封面）、`summary`（简介）、`content`（详情富文本/markdown，先按纯文本存）
  - `start_at`、`end_at`
  - `signup_deadline_at`
  - `capacity`（nullable；null=无限名额）
  - `registered_count`（默认 0）
  - `is_published`（默认 false）、`published_at`（nullable）
  - `created_at`、`updated_at`

2) 新增报名表 `event_registrations`
- 新文件：[event_registration.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/models/event_registration.py)
- 关键字段：
  - `id`（PK）
  - `event_id`（FK -> events.id, index）
  - `user_id`（FK -> users.id, index）
  - `name`、`phone`、`remark`
  - `status`（`registered` / `canceled`）
  - `created_at`、`canceled_at`
  - 唯一约束：`(event_id, user_id)`，用于防重复报名与支持“取消后再报名”（通过更新同一行恢复为 registered）。

3) Alembic 迁移
- 新增 migration 文件：`ymd-server/alembic/versions/*_events_and_registrations.py`
- 更新 Alembic 元数据导入：在 [env.py](file:///c:/Users/brian/projects/ymd/ymd-server/alembic/env.py#L10-L18) 增加对新 model 的 import，确保 autogenerate/metadata 完整。

### B) 后端（ymd-server）：API（用户侧）
1) 新增 `events` 路由
- 新文件：[events.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/api/events.py)
- 在 [main.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/main.py#L6-L28) 注册路由（prefix=`/api/v1`）

2) 接口设计（最小可上线）
- `GET /api/v1/events`
  - 返回：已发布活动列表（按 `start_at` 升序或近期开头）
  - 支持 Query：`category`、`city`、`from`/`to`（可选，若不做则前端继续本地筛选）
- `GET /api/v1/events/{event_id}`
  - 返回：活动详情（公开字段）
  - 若用户已登录：额外返回 `my_registration_status`（`none/registered/canceled`）与 `my_registration_id`（可选）
- `POST /api/v1/events/{event_id}/registrations`
  - 入参：`name`、`phone`、`remark`
  - 行为：校验已发布、未过截止、名额未满；对同一 `(event_id,user_id)` 幂等（已报名则返回已报名状态）
  - 并发：用“带条件的 update + returning”原子增加 `registered_count`（capacity 不为 null 时）避免超卖
- `POST /api/v1/events/{event_id}/registrations/cancel`
  - 行为：把该用户报名状态置为 canceled，并原子减少 `registered_count`（下限 0）；可限制“截止后不可取消”（如需，作为后续可选）
- `GET /api/v1/events/registrations/me`
  - 返回：当前用户的报名列表（含活动基础信息 + 报名状态/时间）

3) 依赖与鉴权
- 报名/取消/我的报名：依赖 `get_current_active_user`。
- 列表/详情：允许匿名访问；如需“登录态下返回我的报名状态”，新增一个“可选 token”的依赖（在 `deps.py` 中新增 `get_current_user_optional`）。

4) Schemas
- 新增目录文件：
  - [event.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/schemas/event.py)
  - [event_registration.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/schemas/event_registration.py)
- 对齐现有风格：`BaseModel + Config(from_attributes=True)` 或 `model_validate`。

### C) 后端（ymd-server）：API（管理员侧）
1) 新增管理员活动管理路由
- 新文件：[admin_events.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/api/admin_events.py)
- 在 [main.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/main.py#L6-L28) 注册路由（prefix=`/api/v1/admin`）
- 权限：全部依赖 `get_current_active_superuser`（复用 [admin.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/api/admin.py#L7-L8) 的模式）

2) 接口设计（匹配后台页面）
- `GET /api/v1/admin/events`：列表（支持按发布状态/关键字过滤）
- `POST /api/v1/admin/events`：创建活动（draft）
- `PUT /api/v1/admin/events/{event_id}`：编辑活动
- `PATCH /api/v1/admin/events/{event_id}/publish`：发布/下架（切 `is_published`）
- `GET /api/v1/admin/events/{event_id}/registrations`：报名名单（返回姓名/手机号/备注/时间/状态）

### D) 小程序端（ymd-app）：活动列表/详情/报名/我的报名
1) 活动列表改为后端数据
- 修改：[index.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/events/index.vue)
- 改动：
  - `reload()` 改为 `request({ url: '/events' })` 拉取数据
  - 保留筛选 UI（分类/时间）但基于真实字段（`category`、`start_at`）进行本地筛选或按后端 query 筛选

2) 活动详情改为真实详情 + 报名入口
- 修改：[detail.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/events/detail.vue)
- 改动：
  - `onLoad` 读取 `id` 后调用 `GET /events/{id}`
  - CTA：
    - 未登录：跳转登录页（或直接发请求触发 401/403 跳转）
    - 已报名：展示“已报名/取消报名”
    - 已截止/已满：展示不可报名状态
    - 可报名：进入报名表单页

3) 新增报名表单页
- 新增：`ymd-app/src/pages/events/signup.vue`（并在 `pages.json` 注册）
- 表单字段：姓名、手机号、备注
- 提交：`POST /events/{id}/registrations`，成功后返回详情页并刷新状态

4) 新增“我的活动/我的报名”页
- 新增：`ymd-app/src/pages/events/my.vue`（并在 `pages.json` 注册）
- 数据：`GET /events/registrations/me`
- 入口：修改 [profile/index.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/index.vue) 的菜单点击，跳转到该页

### E) 后台管理端（ymd-admin）：活动管理与报名名单
1) 路由与侧边栏
- 修改路由：[router/index.ts](file:///c:/Users/brian/projects/ymd/ymd-admin/src/router/index.ts#L10-L24) 新增：
  - `/events`（活动管理）
  - `/events/:id/registrations`（报名名单）
- 修改侧边栏：[LayoutView.vue](file:///c:/Users/brian/projects/ymd/ymd-admin/src/views/LayoutView.vue#L8-L13) 增加入口，并完善标题映射

2) 新增页面
- 新增 `EventsView.vue`：活动列表 + 新建/编辑弹窗 + 发布/下架按钮
- 新增 `EventRegistrationsView.vue`：某活动报名名单表格（支持分页/刷新，最小版不做导出）
- API 调用复用现有 [request.ts](file:///c:/Users/brian/projects/ymd/ymd-admin/src/utils/request.ts)，对接后端 `/api/v1/admin/events*`

## Edge Cases / Failure Modes
- 重复报名：同一用户同一活动多次点击报名应返回“已报名”而不是创建多条；后端以唯一约束 + upsert/查询保证。
- 名额超卖：并发报名时，后端通过“带条件 update events set registered_count = registered_count + 1 where ... returning”确保不超过 capacity。
- 截止时间：`now > signup_deadline_at` 禁止报名；取消是否也受截止限制（默认允许取消，可在实现中按需求加限制）。
- 活动未发布：仅管理员可见/可编辑；用户侧列表/详情不返回未发布活动。

## Verification
- 数据库迁移：
  - `alembic upgrade head` 通过；表结构与索引存在；默认值正确。
- 后端接口冒烟：
  - 新建活动（admin）→ 发布 → 用户报名 → 重复报名 → 取消 → 再报名 → capacity 满额行为与错误提示正确。
  - 建议新增 `ymd-server/verify_event_registration.py` 用 `TestClient` 跑一遍链路（参考现有 [verify_auth_admin_ops.py](file:///c:/Users/brian/projects/ymd/ymd-server/verify_auth_admin_ops.py) 风格）。
- 前端构建检查：
  - `ymd-app`：`npm run type-check`
  - `ymd-admin`：`npm run type-check`（或 `npm run build`）
- 手动验收清单（最小上线）：
  - 小程序：列表可加载 → 详情可看 → 报名表单可提交 → 我的报名可查看/取消
  - 后台：可创建/编辑/发布活动 → 可查看报名名单

