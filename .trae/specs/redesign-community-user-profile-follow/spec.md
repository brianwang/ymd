# 社区用户详情页重设计 + 关注/取消关注 Spec

## Why
从社区点击用户头像进入的用户详情页目前信息层级偏弱、视觉不统一，且“关注/取消关注”需要更清晰的主次状态与交互反馈，提升浏览与社交关系建立的效率。

## What Changes
- 重设计用户详情页（`/pages/user/profile`）：统一到 ymd-app 现有 V2 视觉体系（AppBar/Card/EmptyState/Skeleton/PostMedia），信息层级更清晰。
- 关注/取消关注：在用户详情页头部提供明确的关注按钮状态（关注/已关注/加载中），并支持取消关注。
- 列表区：展示该用户的帖子列表（复用社区帖子展示组件/样式），保持与社区列表/详情一致的媒体与排版。
- 状态与反馈：完善加载态、错误态、空态；关注操作失败回滚并提示。
- **不新增业务逻辑**（如粉丝数/关注数统计），仅使用现有 API 完成最小闭环。

## Impact
- Affected specs: 社区用户详情浏览、关注关系建立与解除
- Affected code:
  - ymd-app：`src/pages/user/profile.vue`
  - ymd-app：`src/pages/community/index.vue`、`src/pages/community/detail.vue`（仅验证入口一致性，必要时微调跳转参数）
  - ymd-server（验证现有接口）：`GET /api/v1/users/{user_id}`、`POST|DELETE /api/v1/users/{user_id}/follow`

## ADDED Requirements

### Requirement: 从社区进入用户详情
系统 SHALL 在用户点击社区帖子作者头像时，进入“用户详情页”并展示该用户信息与其帖子列表。

#### Scenario: 进入用户详情成功
- **WHEN** 用户在社区页/帖子详情页点击作者头像
- **THEN** 跳转到用户详情页并展示：头像、昵称（或兜底 `用户 #id`）、ID
- **AND** 展示该用户帖子列表（支持分页加载）

### Requirement: 关注与取消关注
系统 SHALL 在用户详情页为非本人提供关注与取消关注能力，并在 UI 上清晰表达当前关注状态。

#### Scenario: 未关注 -> 关注成功
- **WHEN** 已登录用户点击“关注”
- **THEN** 立即进入 loading 状态并进行乐观更新（按钮状态变为“已关注”）
- **AND** 调用 `POST /api/v1/users/{target_user_id}/follow` 成功后保持“已关注”

#### Scenario: 已关注 -> 取消关注成功
- **WHEN** 已登录用户点击“已关注”
- **THEN** 进入 loading 状态并进行乐观更新（按钮状态变为“关注”）
- **AND** 调用 `DELETE /api/v1/users/{target_user_id}/follow` 成功后保持“关注”

#### Scenario: 关注/取消关注失败
- **WHEN** 关注/取消关注请求失败
- **THEN** UI 回滚到操作前状态，并给出明确提示（toast/页面提示）

#### Scenario: 未登录尝试关注
- **WHEN** 未登录用户点击关注按钮
- **THEN** 引导登录（复用现有 ensureLoggedIn 行为），且不改变当前关注状态

### Requirement: 状态页（加载/错误/空）
系统 SHALL 在用户详情页提供稳定的加载态、错误态与空态，避免页面跳动与信息缺失。

#### Scenario: 加载中
- **WHEN** 用户详情与首屏帖子加载中
- **THEN** 展示 Skeleton（用户信息 + 列表占位），布局稳定

#### Scenario: 加载失败
- **WHEN** 用户信息或帖子加载失败
- **THEN** 展示错误态（含重试按钮），并保留返回能力

#### Scenario: 无帖子
- **WHEN** 目标用户无帖子
- **THEN** 展示空态文案（例如“Ta 还没有发布动态”）

## MODIFIED Requirements
（无）

## REMOVED Requirements
（无）

