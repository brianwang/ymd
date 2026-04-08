# 游牧岛：页面内容填充 + 账号体系 + 后台管理 Spec

## Why
当前小程序各 Tab 页面内容较少，缺少明确的产品信息架构与可用的账号体系；同时缺少运营与内容治理的后台入口，导致内容生产、审核、运营配置难以规模化。

## What Changes
- 小程序端：为活动、共居、社区、我的等页面补齐可用的信息架构与内容模块，默认提供可浏览的示例数据与交互入口。
- 账号体系：在保留微信登录（wx-login）基础上，新增邮箱/密码注册与登录；支持在小程序端绑定邮箱账号（可选入口），统一发放 JWT。
- 后台管理系统：提供独立的 Web 管理端（Admin Portal）与一组受保护的管理 API，用于管理用户、帖子/评论、积分流水与运营配置。
- **BREAKING**：无（新增字段与新增接口不影响现有调用；旧的 wx-login 仍可用）。

## Impact
- Affected specs: 账号与鉴权、页面信息架构、内容生产/治理、运营配置、后台管理
- Affected code:
  - 前端（ymd-app）：`src/pages/events/*`、`src/pages/coliving/*`、`src/pages/profile/*`、`src/pages/community/*`、`src/pages/points/*`、`src/pages.json`、`src/utils/request.ts`、`src/store/*`
  - 后端（ymd-server）：`app/models/user.py`、`app/api/auth.py`、`app/api/users.py`、`app/api/posts.py`、`app/api/points.py`、`app/core/security.py`、`app/core/config.py`
  - 新增（建议）：`ymd-admin/*`（管理端 SPA）与 `app/api/admin/*`（管理 API）

## ADDED Requirements

### Requirement: 页面内容填充（小程序端）
系统 SHALL 在四个 Tab（活动、社区、共居、我的）提供可浏览的内容模块与明确的导航入口。

#### Scenario: 首次打开活动页
- **WHEN** 用户打开“活动”Tab
- **THEN** 看到 Banner/推荐活动/筛选项/活动列表卡片
- **AND** 点击活动卡片进入活动详情页（MVP 可为静态详情页或占位页）

#### Scenario: 首次打开共居页
- **WHEN** 用户打开“共居”Tab
- **THEN** 看到城市筛选/推荐空间/空间列表卡片
- **AND** 点击空间卡片进入空间详情页（MVP 可为静态详情页或占位页）

#### Scenario: 社区页入口完整
- **WHEN** 用户打开“社区”Tab
- **THEN** 可浏览帖子列表、进入详情、发帖（已实现基础功能）

#### Scenario: 我的页入口完整
- **WHEN** 用户打开“我的”Tab
- **THEN** 可登录/退出、进入积分中心、进入邀请海报

### Requirement: 邮箱/密码注册与登录（统一 JWT）
系统 SHALL 支持通过邮箱/密码注册与登录，并返回与现有体系一致的 JWT（Bearer Token）。

#### Scenario: 注册成功
- **WHEN** 用户提交邮箱与密码完成注册
- **THEN** 返回 access_token 与 user_id
- **AND** 后续请求使用 Authorization: Bearer <token> 可访问受保护资源

#### Scenario: 登录成功
- **WHEN** 用户输入正确邮箱与密码登录
- **THEN** 返回 access_token 与 user_id

#### Scenario: 邮箱已存在
- **WHEN** 用户使用已注册邮箱尝试注册
- **THEN** 返回 400/409 并给出可理解的错误信息

### Requirement: 后台管理系统（Admin Portal）
系统 SHALL 提供后台管理系统，用于运营管理与内容治理，并且仅允许管理员访问。

#### Scenario: 管理员登录
- **WHEN** 管理员在后台输入邮箱/密码登录
- **THEN** 获得管理端 token 并进入后台首页

#### Scenario: 管理帖子与评论
- **WHEN** 管理员查看帖子列表
- **THEN** 可按时间/关键字筛选并查看详情
- **AND** 可执行下架/删除帖子、删除评论

#### Scenario: 管理用户与积分
- **WHEN** 管理员查看用户列表
- **THEN** 可禁用/启用用户、调整积分（记录到积分流水）
- **AND** 可查看某用户积分流水

#### Scenario: 管理运营配置
- **WHEN** 管理员进入运营配置
- **THEN** 可配置“签到/邀请/首帖/发帖/评论”的积分值与每日上限（持久化配置）

## MODIFIED Requirements

### Requirement: 现有微信登录流程
系统 SHALL 继续支持 `POST /api/v1/auth/wx-login` 获取 token，并兼容邀请绑定逻辑不变。

## REMOVED Requirements
无。

