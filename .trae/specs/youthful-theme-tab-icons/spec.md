# 视觉升级：青春色调 + Tab 图标 + 资源图集 Spec

## Why
当前整体色调与组件风格不统一、底部 Tab 缺少图标导致视觉突兀，影响第一印象与可用性；同时缺少可复用的视觉资源（banner/插画/图标），页面“有内容但不够好看”。

## What Changes
- 设计系统：为小程序端与后台管理端建立统一的“青春感”主题（色板、字体层级、圆角、阴影、间距、状态色）。
- 小程序 TabBar：补齐 4 个 Tab 的 icon + 选中 icon，并统一尺寸/对齐/色彩。
- 页面视觉：活动/共居/社区/我的/积分中心等页面对齐主题，优化背景、卡片、按钮、空态。
- 图片资源：生成并内置一套静态资源（Tab 图标、Banner、空态插画/占位图）供页面使用。
- **BREAKING**：无（仅样式与静态资源变更，API 不变）。

## Impact
- Affected specs: 视觉设计系统、导航体验、页面可读性与一致性、品牌调性
- Affected code:
  - 小程序端（ymd-app）：`src/uni.scss`、`src/pages.json`、`src/pages/**`、`src/static/**`
  - 后台端（ymd-admin）：`src/style.css`、`src/views/**`、`src/assets/**`

## ADDED Requirements

### Requirement: 青春主题（Design Tokens）
系统 SHALL 提供一套主题变量，并在小程序端与后台端复用。

#### Scenario: 主题变量可复用
- **WHEN** 页面渲染主按钮/卡片/标题/辅助文字/背景
- **THEN** 颜色、圆角、阴影、间距来自统一的 token

#### Token 约束（默认值）
- 主色（Primary）：偏青/薄荷或天蓝系，强调“青春、清爽”
- 辅色（Secondary/Accent）：一到两个辅助色（偏紫/粉做点缀）
- 中性色（Neutral）：用于背景、分割线、正文与弱提示
- 状态色（Success/Warning/Danger）：用于提示与危险操作
- 圆角：卡片/按钮统一圆角体系（例如 10–14px）
- 阴影：统一轻阴影（避免厚重）

### Requirement: TabBar 图标
系统 SHALL 为 4 个 Tab（活动、社区、共居、我的）提供未选中与选中图标，并在真实设备与开发者工具中显示清晰、不变形。

#### Scenario: TabBar icon 显示正常
- **WHEN** 用户切换 Tab
- **THEN** icon 与文字色同步切换到选中态
- **AND** icon 在深浅背景下对比度足够

#### 资源规范
- 图标类型：PNG
- 命名：`tab-events.png` / `tab-events-active.png` 等
- 存放路径：`ymd-app/src/static/tab/`
- 统一尺寸：同一套尺寸输出，确保对齐一致（实现阶段固定具体 px）

### Requirement: 页面视觉填充与空态优化
系统 SHALL 在各页面提供统一的空态/加载态/错误态，并使用内置的插画/占位图提升观感。

#### Scenario: 列表为空
- **WHEN** 活动/共居/社区列表为空
- **THEN** 展示一致的空态组件（含插画 + 文案 + 行动按钮）

### Requirement: 图片资源生成与落地
系统 SHALL 内置可用于页面的图片资源包（banner、空态插画、占位图），并保证体积与清晰度平衡。

#### Scenario: 资源可用
- **WHEN** 页面引用静态资源
- **THEN** 资源可正常加载且不会出现明显锯齿/模糊
- **AND** 资源体积控制在合理范围（避免影响首屏）

## MODIFIED Requirements
无。

## REMOVED Requirements
无。

