# 个人资料编辑页增加手机号 Plan

## Summary
在小程序端“编辑个人资料”页面新增手机号输入项，并打通后端 `/users/me` 的读取与更新能力：用户可在个人资料里维护手机号；活动详情页和报名场景可直接使用该手机号自动回填。仅新增手机号字段与相关最小改动，不调整现有昵称/头像逻辑与页面其它内容。

## Current State Analysis
### 前端（ymd-app）
- 个人资料编辑页仅支持昵称与头像： [edit.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/edit.vue#L1-L35)
  - 保存调用 `PUT /users/me`，只提交 `{ nickname, avatar_url }`：[edit.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/edit.vue#L127-L157)
  - 页面打开与 onShow 会 `GET /users/me` 刷新 store：[edit.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/edit.vue#L71-L78)
- 当前 `userStore.userInfo` 会持久化存储任意结构：[user.ts](file:///c:/Users/brian/projects/ymd/ymd-app/src/store/user.ts#L4-L23)

### 后端（ymd-server）
- 用户模型已新增 `phone` 字段（本次不再新增迁移）：`ymd-server/app/models/user.py`
- `/users/me` 的返回 schema 已包含 `phone`：`ymd-server/app/schemas/user.py`
- 但 `PUT /users/me` 目前只处理 `nickname`、`avatar_url`，不处理 `phone`：[users.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/api/users.py#L32-L49)
- `UserUpdate` 目前未包含 `phone`（因为 `UserUpdate` 继承 `UserBase`，而 `UserBase` 未声明 phone）：[schemas/user.py](file:///c:/Users/brian/projects/ymd/ymd-server/app/schemas/user.py#L4-L15)

## Proposed Changes
> 决策：手机号按 **11 位数字** 进行校验；编辑页 **只新增手机号**，不合并邮箱入口。

### 1) 后端：允许更新 phone（并做 11 位校验）
**文件**
- `ymd-server/app/schemas/user.py`
- `ymd-server/app/api/users.py`

**修改内容**
- 在 `UserBase` 增加 `phone: Optional[str] = None`，使 `UserUpdate` 可接收 phone。
- 在 `PUT /users/me` 处理 `user_in.phone`：
  - `phone.strip()` 后若为空字符串则设置为 `None`（允许清空）
  - 若非空则校验为 11 位数字（`len==11` 且全为数字），不通过返回 400
  - 通过则写入 `current_user.phone` 并提交

### 2) 前端：个人资料编辑页新增手机号输入与保存
**文件**
- `ymd-app/src/pages/profile/edit.vue`

**修改内容**
- 增加 `phone` 状态并在 `syncFromStore()` 中读取 `userStore.userInfo?.phone`
- 在表单中新增手机号输入框（`type="number"`、占位 `请输入手机号`）
- 保存时在 `PUT /users/me` 的 data 中追加 `phone`（与昵称/头像一起提交）
- 客户端侧做轻量校验（11 位数字）；校验失败提示 toast 且不发送请求

## Assumptions & Decisions
- 本次只新增手机号字段，不调整昵称/头像布局与逻辑，不改动绑定邮箱流程与入口。
- 手机号作为用户资料字段用于“活动报名回填”等效率提升；不引入短信验证/授权流程。

## Verification Steps
### 后端
- 调用 `PUT /api/v1/users/me`：
  - phone=空字符串 => 数据库存为 NULL，`GET /users/me` 返回 `phone: null`
  - phone=非 11 位数字 => 400
  - phone=11 位数字 => 保存成功，`GET /users/me` 返回该 phone

### 前端
- 打开 [edit.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/edit.vue)：
  - 已登录且 userInfo.phone 存在 => 输入框预填
  - 修改手机号并保存 => 保存成功后返回上一页（保持现有行为）
- 构建验证：`ymd-app` 通过 `npm run type-check` 与 `npm run build:h5`

