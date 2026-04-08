# 个人信息页美化与未开发功能完善 Spec

## Why
当前“我的/个人信息”页面存在明显占位与未完成交互（如“编辑个人资料”仅 Toast、菜单项不可点击），影响可用性与整体观感。

## What Changes
- 美化“我的/个人信息”页面：信息区、账户区与菜单区的层级、间距、交互反馈统一为现有主题风格
- 完成“编辑个人资料”：新增编辑页，支持修改昵称与头像并保存到后端
- 完成“我的活动”：新增列表页，展示用户已报名活动；支持查看活动详情与取消报名
- 完成“我的订单”：新增列表页（当前无订单体系时提供可用的空态与引导）
- 新增活动与报名的最小可用 API：活动公开列表/详情、活动报名/取消、我的报名列表

## Impact
- Affected specs: 个人信息/资料编辑、活动报名、我的活动、我的订单
- Affected code:
  - 小程序端（ymd-app）：个人信息页、新增页面路由、头像上传与资料保存、活动详情报名入口
  - 后端（ymd-server）：新增 events 与 event_registrations 的迁移、活动/报名路由与业务校验

## ADDED Requirements

### Requirement: 个人资料编辑
系统 SHALL 提供“编辑个人资料”页面，允许已登录用户修改昵称与头像，并在保存后同步到本地状态与服务端。

#### Scenario: 打开编辑页
- **WHEN** 用户在“我的”页点击“编辑个人资料”
- **THEN** 跳转到编辑页并加载当前用户资料（头像、昵称）

#### Scenario: 修改昵称并保存成功
- **WHEN** 用户输入合法昵称并点击保存
- **THEN** 调用 `PUT /api/v1/users/me` 更新昵称成功
- **AND** 返回“我的”页后昵称展示为新值

#### Scenario: 更换头像并保存成功
- **WHEN** 用户选择图片作为头像并点击保存
- **THEN** 先调用 `POST /api/v1/media/upload` 上传图片获得 `avatar_url`
- **AND** 再调用 `PUT /api/v1/users/me` 更新 `avatar_url`
- **AND** 返回“我的”页后头像展示为新图

#### Scenario: 保存失败
- **WHEN** 上传或保存请求失败
- **THEN** 页面展示明确错误提示且不清空用户输入

#### Constraints
- 昵称校验（前端 + 后端一致性目标）：
  - 去除首尾空格后长度在 2–20 之间
  - 不允许全为空白字符

### Requirement: 我的活动（已报名）
系统 SHALL 提供“我的活动”页面，展示当前用户已报名的活动列表，并可取消报名。

#### Scenario: 列表为空
- **WHEN** 用户打开“我的活动”且无任何有效报名
- **THEN** 展示空态（含“去看看活动”的引导入口）

#### Scenario: 列表展示
- **WHEN** 用户打开“我的活动”
- **THEN** 展示活动卡片列表（标题、城市、开始时间、封面/占位、报名状态）
- **AND** 支持下拉刷新

#### Scenario: 进入活动详情
- **WHEN** 用户点击某条活动
- **THEN** 跳转到活动详情页并展示该活动信息

#### Scenario: 取消报名
- **WHEN** 用户在“我的活动”对某活动执行取消报名确认
- **THEN** 调用取消接口成功并从列表移除/标记为已取消

### Requirement: 活动公开与报名 API（最小可用）
系统 SHALL 提供活动公开查询与报名的最小可用接口以支撑“我的活动”与活动报名闭环。

#### Scenario: 获取活动列表（公开）
- **WHEN** 客户端请求 `GET /api/v1/events`
- **THEN** 返回已发布活动列表（支持按 `city`、`category` 可选筛选，支持分页参数 `limit/offset`）

#### Scenario: 获取活动详情（公开）
- **WHEN** 客户端请求 `GET /api/v1/events/{event_id}`
- **THEN** 返回该活动详情（仅已发布）

#### Scenario: 报名活动（登录）
- **WHEN** 已登录用户请求 `POST /api/v1/events/{event_id}/registrations` 并提交 `name/phone/remark`
- **THEN** 若未过报名截止且未超出容量且未重复报名，创建报名记录并返回报名信息

#### Scenario: 取消报名（登录）
- **WHEN** 已登录用户请求 `DELETE /api/v1/events/{event_id}/registrations/me`
- **THEN** 将该用户对该活动的报名标记为 canceled（保留历史），并返回成功

#### Scenario: 获取我的报名（登录）
- **WHEN** 已登录用户请求 `GET /api/v1/users/me/event-registrations`
- **THEN** 返回该用户报名列表（默认仅有效报名；可通过参数包含已取消）

#### Constraints
- 重复报名：同一用户对同一活动不允许存在两个有效报名（利用现有唯一约束 + 业务校验）
- 截止时间：当前时间超过 `signup_deadline_at` 时拒绝报名
- 容量：`capacity` 非空时，`registered_count` 达到 capacity 时拒绝报名

### Requirement: 我的订单（最小可用）
系统 SHALL 提供“我的订单”页面；在尚未接入订单体系时，页面提供可用的空态与下一步引导。

#### Scenario: 打开订单页
- **WHEN** 用户从“我的”页进入“我的订单”
- **THEN** 展示订单列表布局与空态文案（例如“暂无订单”），并提供可点击引导（例如返回活动/共居浏览）

## MODIFIED Requirements

### Requirement: 我的页菜单交互
系统 SHALL 保证“我的/个人信息”页面中所有显示的菜单项均具备明确行为（跳转页面或执行动作），不出现“开发中”占位 Toast。

## REMOVED Requirements

### Requirement: “编辑资料开发中”占位提示
**Reason**: 已实现“编辑个人资料”页面与保存能力  
**Migration**: 将原 Toast 行为替换为页面跳转*** End Patch"}]}цара*toolcall_result to=functions.apply_patch  大发游戏<commentary  彩神争霸官网  patt_end_of_file: "*** End of File" LF
