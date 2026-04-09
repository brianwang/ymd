# 扁平化 UI 与小程序色调重置 Spec

## Why
当前 ymd-app 的整体风格以“卡片式 + 阴影分层”为主，视觉偏厚重且页面被切得过碎。希望改为更扁平、更清爽的层级表达，并为小程序端统一更好看的主色调与辅助色体系。

## What Changes
- 扁平化全局分层：减少/移除卡片阴影，主要用背景色块 + 分割线 + 字重/字号层级表达信息层次。
- 扁平化组件外观：`Card`/`EmptyState`/列表容器默认不带阴影，圆角收敛，边框与分隔线更一致。
- 色调重置：更新 V2 设计 tokens（主色/强调色/背景/文字/线色/状态色），让小程序端整体更统一、更“干净”。
- 页面微调：对首页 Tab 页面（活动/共居/社区/我的/积分中心）做少量样式跟随，避免扁平化后出现“白板/粘连/层级丢失”。
- **不新增业务逻辑**，仅样式/布局/视觉层级调整。

## Impact
- Affected specs: 全站视觉一致性、可读性、层级表达、品牌色调
- Affected code:
  - tokens：`ymd-app/src/styles/tokens.scss`
  - 全局样式：`ymd-app/src/uni.scss`
  - UI 组件：`ymd-app/src/components/ui/Card.vue`、`EmptyState.vue`、`AppBar.vue`、`SectionHeader.vue`（若需要）
  - 页面样式：`ymd-app/src/pages/**/index.vue`（重点：积分中心、社区、活动、我的）

## ADDED Requirements

### Requirement: 扁平化分层策略
系统 SHALL 在全站默认视觉层级中使用“背景色块 + 细边框/分割线 + 字体层级”作为主要分层手段，默认不依赖阴影。

#### Scenario: 列表页与详情页
- **WHEN** 用户浏览任意列表/详情页面
- **THEN** 页面区块之间的层级关系清晰（靠留白/分割线/标题层级），不会因去掉阴影而显得“糊成一片”

### Requirement: 卡片组件扁平化
系统 SHALL 将通用 `Card` 组件默认样式改为扁平化：无阴影、统一边框与圆角、背景色一致。

#### Scenario: 扁平化后仍可区分区块
- **WHEN** 页面使用多个 `Card` 组件并上下堆叠
- **THEN** 区块边界清晰（分割线/圆角/背景对比），不出现“边界丢失”

### Requirement: 小程序端色调统一
系统 SHALL 以 V2 tokens 为中心提供一套新的色调方案，并在小程序端保持一致的主色、强调色、背景与文字对比度。

#### Scenario: 主色覆盖范围
- **WHEN** 用户在小程序端访问任意 Tab 页与常见按钮（主按钮/次按钮/幽灵按钮）
- **THEN** 主色/强调色使用统一规范，按钮与标题栏风格一致
- **AND** 状态色（成功/危险/禁用）可辨识且对比度足够

## MODIFIED Requirements
（无）

## REMOVED Requirements
（无）

