# ymd-app 高级 UE/UI 重构（大气风格）Spec

## Why
当前 ymd-app 虽已具备基础主题与图标，但整体观感仍偏“拼装感”：层级不够清晰、留白与对齐不统一、组件风格不成体系，导致“不美观、不大气”。需要对信息架构与视觉系统进行一次面向“高级体验”的整体重构。

## What Changes
- 设计方向升级：从“青春多彩”调整为“清爽高级”的大气风格（更克制的色彩、更明确的字体层级、更统一的组件与留白规则）。
- 组件体系化：抽象出可复用的 UI primitives（AppBar、Section、Card、Pill、Button、EmptyState、Skeleton、Divider），页面只做组合。
- 页面重新编排：对活动/共居/社区/我的/积分等页面进行信息架构重排，提升首屏信息密度与可读性，减少突兀元素。
- 资源升级：替换为更高级的 Tab 图标（线性/填充统一风格），新增“高级质感”banner/空态插画/占位图。
- **BREAKING**：无（仅前端视觉与布局改造；既有路由/API 保持兼容）。

## Impact
- Affected specs: 视觉系统（token/组件）、页面信息架构、导航体验、空态/加载态统一
- Affected code:
  - `ymd-app/src/uni.scss`
  - `ymd-app/src/styles/tokens.scss`
  - `ymd-app/src/pages.json`
  - `ymd-app/src/pages/**`
  - `ymd-app/src/static/**`

## ADDED Requirements

### Requirement: 大气风格设计系统（V2 Tokens）
系统 SHALL 提供 V2 主题 token，并将所有页面统一迁移到 V2 token（不允许页面自定义“私有色值/私有阴影”破坏一致性）。

#### Scenario: 统一的层级与留白
- **WHEN** 用户打开任一页面
- **THEN** 标题/副标题/正文/辅助信息的字号、字重与颜色遵循同一套层级
- **AND** 卡片/列表/分组之间的间距遵循同一套 8pt 网格

#### V2 Token 约束（默认方向）
- 主色：清爽但克制（青蓝/薄荷可保留，但降低饱和度；减少大面积纯色）
- 背景：浅雾白/冷灰渐变（避免纯白刺眼）
- 卡片：统一圆角、统一阴影强度（更轻、更“浮”）
- 文本：深色主文本 + 冷灰次文本（高对比但不硬）
- 点缀：少量紫/粉仅用于插画与 badge，避免 UI 元素大面积使用

### Requirement: 组件体系（UI Primitives）
系统 SHALL 提供可复用的基础组件，使页面仅通过组合实现一致的视觉与交互。

#### Scenario: 组件可复用
- **WHEN** 页面展示 section header、卡片列表、空态、加载态
- **THEN** 使用统一组件，不允许页面重复实现同类样式

### Requirement: TabBar 高级图标与对齐
系统 SHALL 提供一套统一风格的 Tab 图标（普通态/选中态），并保证：
- icon 与文字的对齐一致
- 选中态颜色与主色一致
- 在 H5 与微信小程序中都清晰（无拉伸/模糊）

### Requirement: 页面信息架构重排
系统 SHALL 对以下页面进行“高级体验”重排（不增加业务复杂度，以现有数据/占位为主）：

#### Scenario: 活动页更大气
- **WHEN** 用户打开活动页
- **THEN** 首屏包含：轻量 AppBar、Hero Banner、快速筛选、推荐活动、活动列表
- **AND** 卡片信息层级清晰：标题 > 城市/时间 > 标签/价格

#### Scenario: 共居页更大气
- **WHEN** 用户打开共居页
- **THEN** 首屏包含：城市选择、推荐空间、空间列表
- **AND** 空间卡片包含“卖点”（例如 Wi-Fi/工位/评分占位）并对齐统一样式

#### Scenario: 社区页更大气
- **WHEN** 用户打开社区页
- **THEN** 信息流卡片统一（头像/昵称/时间/内容/九宫格图片/操作区），操作区按钮统一样式

#### Scenario: 我的/积分更大气
- **WHEN** 用户打开我的页与积分中心
- **THEN** 顶部信息区更克制、卡片更统一、任务中心更像“清单”而不是“按钮堆叠”

### Requirement: 高级资源图集
系统 SHALL 内置一套更高级的图片资源：
- Banner：2–3 张（统一风格）
- 空态：至少 2 张（空列表/网络错误）
- 占位图：活动/共居封面、头像占位、邀请海报背景

## MODIFIED Requirements
无。

## REMOVED Requirements
无。

