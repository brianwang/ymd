# 后台登录与联调冒烟修复 Spec

## Why
当前提供的测试账号无法登录后台，导致后台页面与管理接口无法继续联调与测试，需要提供可复现、可验证、可持续使用的后台登录闭环。

## What Changes
- 修复后台（ymd-admin）使用的邮箱/密码登录链路，确保可获取 JWT 并用于访问 `/api/v1/admin/*`
- 明确并固化“后台可登录管理员账号”的生成与维护方式（种子/脚本/文档）
- 增强后台端联调与冒烟验证手段（最小自动化脚本 + 前端错误提示一致性）

## Impact
- Affected specs: 管理后台登录、管理 API 鉴权、测试账号交付、联调/冒烟验证
- Affected code: ymd-server（auth 登录与管理员校验、seed/脚本、admin deps）、ymd-admin（登录页与请求鉴权）、test_accounts.md（账号文档）

## ADDED Requirements
### Requirement: 可用的后台管理员账号
系统 SHALL 提供至少 1 个可用于后台登录的管理员账号（`is_superuser=true`），并在测试账号文档中给出其邮箱与明文密码（仅限本地/测试环境约定）。

#### Scenario: 管理员账号生成成功
- **WHEN** 开发者执行测试账号生成/种子脚本
- **THEN** 数据库中存在管理员用户，且具备 email、hashed_password，并标记为 `is_superuser=true`
- **AND** `test_accounts.md` 中存在对应账号信息（邮箱/密码/用途说明）

### Requirement: 后台登录闭环可验证
系统 SHALL 支持 ymd-admin 使用邮箱/密码登录并获取 JWT，且该 JWT 可成功访问至少一个管理接口。

#### Scenario: 登录成功并访问管理接口
- **WHEN** 在 ymd-admin 输入管理员邮箱与密码并提交登录
- **THEN** 登录接口返回 JWT（或等价 token）
- **AND** 后续访问 `/api/v1/admin/*` 返回 200（对管理员）

#### Scenario: 非管理员访问被拒绝
- **WHEN** 使用非管理员用户的 JWT 访问 `/api/v1/admin/*`
- **THEN** 服务端返回 403

## MODIFIED Requirements
### Requirement: 测试账号可用于联调
系统 SHALL 保证提供的后台测试账号与服务端当前的密码哈希/校验策略一致，并在变更策略时同步更新生成脚本与账号文档，避免“文档账号不可用”的漂移。

## REMOVED Requirements
### Requirement: 无
**Reason**: 本变更不移除既有能力
**Migration**: 无
