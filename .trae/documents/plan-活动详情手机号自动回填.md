# 活动详情页手机号自动回填 Plan

## Summary
在活动详情页报名表单中，基于“用户登录态”自动回填手机号，减少用户重复输入。实现方式为：后端为用户资料新增可选 `phone` 字段，并在用户报名活动时写入该字段；前端登录后获取的 `userInfo` 中包含 `phone`，活动详情页自动回填到手机号输入框。除该目标外不改动其他页面与交互。

## Current State Analysis
### 前端（ymd-app）
- 活动详情页报名表单手机号字段：`v-model="formPhone"`，目前无自动回填逻辑：[detail.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/events/detail.vue#L40-L54)
- 默认表单仅同步了昵称到姓名输入框，不处理手机号：[detail.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/events/detail.vue#L91-L95)
- 登录后会调用 `GET /users/me` 并将结果存入 `userStore.userInfo`：[login.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/auth/login.vue#L49-L62)，但当前 `userInfo` 不包含手机号字段。
- `userStore` 仅存储 `token` 与 `userInfo`（任意结构）：[user.ts](file:///c:/Users/brian/projects/ymd/ymd-app/src/store/user.ts#L4-L23)

### 后端（ymd-server）
- 用户数据模型 `User` 当前没有手机号字段：[user.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/models/user.py#L5-L22)
- `GET /users/me` 直接返回 `current_user`，由 `app/schemas/user.py` 决定响应字段：[users.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/api/users.py#L28-L31)，当前 schema 不含手机号：[schemas/user.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/schemas/user.py#L4-L27)
- 活动报名接口 `POST /events/{event_id}/registrations` 接收并保存 `phone` 到 `EventRegistration`，但不会写回用户资料：[events.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/api/events.py#L130-L233)

## Proposed Changes
### 1) 后端：为用户资料新增 phone 字段并对外返回
**文件**
- `ymd-server/app/models/user.py`
- `ymd-server/app/schemas/user.py`
- `ymd-server/alembic/versions/*.py`（新增迁移）

**修改内容**
- 在 `User` 表新增可空字段：`phone`（String，nullable，index 可选）。
- 在 `User` 响应 schema 中新增 `phone: Optional[str]`，确保 `GET /users/me` 返回手机号（若存在）。
- 生成并应用 Alembic 迁移：为 `users` 表添加 `phone` 列（默认 NULL）。

### 2) 后端：在报名成功时写入用户手机号（无新增 UI）
**文件**
- `ymd-server/app/api/events.py`

**修改内容**
- 在 `register_event` 内，校验通过后将 `current_user.phone = phone`（可选择仅当为空或不同才更新），并与报名数据同事务提交。
- 目的：用户首次报名时采集手机号并持久化到用户资料，后续登录即可自动回填，且无需改动其他页面/流程。

### 3) 前端：活动详情页自动回填手机号
**文件**
- `ymd-app/src/pages/events/detail.vue`

**修改内容**
- 扩展 `syncDefaultForm()`：当 `userStore.userInfo?.phone` 存在且 `formPhone` 为空时，自动写入 `formPhone`。
- 在报名成功后（`submitRegistration` 成功分支），将手机号同步写回本地 `userStore.userInfo`（使用 `userStore.setUserInfo({ ...userStore.userInfo, phone })`），避免用户不重新登录时无法在其他活动页复用已保存手机号。

> 限制：仅修改活动详情页与必要的后端字段/写回逻辑，不调整页面排版、不改动按钮文案、不引入新的交互步骤。

## Assumptions & Decisions
- 手机号来源以“用户资料字段 phone”为准，且通过“报名活动时写入”完成最小闭环；不新增单独的“绑定手机号”页面或授权流程。
- 不对手机号格式做复杂校验（保持现有报名接口的最小校验：非空）；如需更严格校验可后续另开需求。

## Verification Steps
### 后端验证
- 运行迁移：`alembic upgrade head`
- 调用 `GET /api/v1/users/me`：登录后响应包含 `phone` 字段（首次可能为空，报名后应为最新手机号）。
- 调用报名接口 `POST /api/v1/events/{id}/registrations` 后再次 `GET /users/me`：`phone` 被写入并持久化。

### 前端验证
- 登录后打开活动详情页：若 `userInfo.phone` 已存在，手机号输入框自动填入且用户可编辑。
- 首次无手机号：输入手机号并报名成功后，返回/进入其他活动详情页时手机号可自动回填（无需退出重新登录）。
- 构建验证：`ymd-app` 通过 `npm run type-check` 与 `npm run build:h5`。

