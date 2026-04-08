# 空间详情咨询功能完善 Spec

## Why
当前“空间详情页-咨询”入口为占位提示，用户无法完成有效咨询或触达客服，运营侧也无法沉淀线索与跟进状态。

## What Changes
- 小程序端空间详情页将“咨询”从 toast 占位升级为可用的咨询入口（表单提交 + 复制客服微信 + 拨打电话）。
- 后端新增“空间咨询线索（Inquiry）”数据模型与接口：创建咨询、管理端列表与状态更新。
- 管理后台新增“咨询线索”列表页，支持筛选与标记跟进状态。

## Impact
- Affected specs: 共居/空间详情展示、客服触达、线索沉淀与运营跟进
- Affected code:
  - ymd-app：`src/pages/coliving/detail.vue`（以及可能新增的通用咨询组件/配置）
  - ymd-server：新增 Inquiry model/schema/router、Alembic 迁移；挂载到 `main.py`
  - ymd-admin：新增咨询线索页面与 admin API 对接

## ADDED Requirements

### Requirement: 空间详情提供可用咨询入口
系统 SHALL 在空间详情页提供“咨询”功能，至少包含：提交咨询表单、复制客服微信、拨打电话三种方式。

#### Scenario: 提交咨询表单（成功）
- **GIVEN** 用户进入空间详情页
- **WHEN** 用户点击“咨询”并选择“提交咨询”
- **AND** 用户填写必填项并提交
- **THEN** 前端展示提交成功反馈
- **AND** 系统创建一条咨询线索记录（包含 space_id、联系方式、留言等）

#### Scenario: 提交咨询表单（校验失败）
- **GIVEN** 用户进入空间详情页
- **WHEN** 用户点击“咨询”并选择“提交咨询”
- **AND** 用户缺失必填项或手机号格式不合法
- **THEN** 前端阻止提交并提示错误

#### Scenario: 复制客服微信（成功）
- **GIVEN** 用户进入空间详情页
- **WHEN** 用户点击“咨询”并选择“复制客服微信”
- **THEN** 系统将客服微信号写入剪贴板
- **AND** 前端提示“已复制”

#### Scenario: 拨打电话（成功）
- **GIVEN** 用户进入空间详情页
- **WHEN** 用户点击“咨询”并选择“拨打电话”
- **THEN** 系统发起拨号（用户主动触发）

### Requirement: 后端提供咨询线索创建接口
系统 SHALL 提供创建咨询线索的公开接口，允许未登录用户提交（user_id 可为空），并进行服务端校验。

#### Scenario: 创建咨询线索（成功）
- **WHEN** 客户端提交包含 `space_id`、`contact_phone`、`message` 的请求
- **THEN** 后端返回创建成功的线索 ID 与创建时间
- **AND** 数据落库

#### Scenario: 创建咨询线索（失败）
- **WHEN** `contact_phone` 缺失或格式非法，或 `message` 为空/过长
- **THEN** 后端返回 4xx 校验错误

### Requirement: 管理端可查看与更新咨询线索
系统 SHALL 提供管理端接口以列表查看咨询线索并更新跟进状态，且仅 `is_superuser` 可访问。

#### Scenario: 管理端查看线索列表（成功）
- **GIVEN** 管理员已登录且为 superuser
- **WHEN** 管理员请求线索列表（可选筛选：status、关键字、时间范围）
- **THEN** 返回分页列表与总数

#### Scenario: 管理端更新线索状态（成功）
- **GIVEN** 管理员已登录且为 superuser
- **WHEN** 管理员更新某条线索的 `status` 或 `admin_note`
- **THEN** 线索记录被更新并返回最新内容

## MODIFIED Requirements
（无）

## REMOVED Requirements
（无）

