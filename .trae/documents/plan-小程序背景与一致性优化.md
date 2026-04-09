# 小程序背景与一致性优化 Plan

## Summary
为 ymd-app（小程序端优先）补齐统一的页面背景，并通过“浅色渐变背景 + 统一容器/分割线/留白”增强全站一致性；主色保持现有青绿（#12C8C0），不引入业务改动。

## Current State Analysis
已确认当前项目存在的基础样式与配置：
- 设计 tokens：`ymd-app/src/styles/tokens.scss`
  - 背景色：`$ymd-v2-color-bg: #f7fafb`
  - 主色：`$ymd-v2-color-brand: #12c8c0`
  - 软色：`$ymd-v2-color-soft: rgba(18, 200, 192, 0.12)`、`$ymd-v2-color-soft-2: rgba(109, 94, 252, 0.12)`
- 全局样式：`ymd-app/src/uni.scss`
  - `.ymd-page` 已设置 `background: $ymd-v2-color-bg`
  - 但背景依赖页面根节点是否带 `.ymd-page`；部分页面/三方组件/系统默认容器可能不会继承，导致“看起来没背景/不统一”的感受
- 全局页面配置：`ymd-app/src/pages.json`
  - `globalStyle.backgroundColor` 已设置为 `#F6FBFC`，但与实际页面视觉（自定义导航、局部背景、H5 body）仍可能不完全一致
- 顶部导航组件：`ymd-app/src/components/ui/AppBar.vue`
  - 使用半透明背景 + blur，适合配合浅色渐变背景

## Proposed Changes
目标：让“无论页面是否使用 `.ymd-page`，都能得到一致的背景 + 视觉层级”，并采用你选定的“浅色渐变”方案。

### 1) 建立全局背景（覆盖所有页面容器）
**修改文件**
- `ymd-app/src/uni.scss`

**怎么改**
- 增加全局 `page` 选择器背景（uni-app 小程序端生效），避免依赖 `.ymd-page`：
  - `page { background: <渐变>; color: $ymd-v2-color-text; }`
- 增加 H5 的 `body, html` 背景（确保 H5 与小程序一致）：
  - `html, body { background: <渐变>; }`
- `.ymd-page` 保留，但改为同一套渐变（保持语义一致）。

**渐变建议（扁平、轻、不会抢内容）**
- `linear-gradient(180deg, rgba(18, 200, 192, 0.10), $ymd-v2-color-bg 240px)`
  - 顶部轻微青绿色调，向下自然过渡到 bg

### 2) 统一系统配置背景色（与渐变底色一致）
**修改文件**
- `ymd-app/src/pages.json`

**怎么改**
- 将 `globalStyle.backgroundColor` 与 `navigationBarBackgroundColor` 统一到与 `$ymd-v2-color-bg` 更接近的值（例如 `#F7FAFB`），让系统默认背景与自定义背景一致。
- 视感一致性增强项（可选、但推荐一起做）：`tabBar.backgroundColor` 从 `#ffffff` 调整为 `#F7FAFB`（视觉更统一，仍保持足够对比度）。

### 3) 页面容器一致性小修（仅在发现“露白/断层”的页面）
**修改文件（按需）**
- `ymd-app/src/pages/**/index.vue`（仅对不使用 `.ymd-page` 的页面或背景断层明显的页面做最小调整）

**怎么改**
- 统一页面根节点使用 `.ymd-page`（如果缺失）。
- 统一内容区用 `.ymd-container ymd-page-inner`，避免不同页面 padding/背景表现不一致。

### 4) 验证与回归（小程序端优先）
**构建验证**
- `ymd-app`：`npm run type-check`
- `ymd-app`：`npm run build:h5`

**人工验收（小程序端）**
- Tab 页（活动/社区/共居/我的/积分）背景从顶部到列表底部一致，无“突然变白”的断层。
- 带自定义 AppBar 的页面：AppBar 半透明背景与渐变融合自然，标题/按钮对比度足够。
- 列表页滚动：背景不闪烁、不出现底部露白（含安全区）。

## Assumptions & Decisions
- 已确认你选择：**浅色渐变背景**；主色 **保留青绿 #12C8C0**。
- 本次仅做“背景与一致性”优化，不引入新的业务功能、不改接口。
- 若后续你确认要“扁平化整体卡片风格”，将基于现有 `flatten-ui-retune-colors` 规格继续推进（本计划不覆盖）。

## Execution Order
1. 修改 `uni.scss`：实现 `page/html/body/.ymd-page` 同步渐变背景
2. 修改 `pages.json`：统一 backgroundColor/navigationBarBackgroundColor（以及可选 tabBar 背景）
3. 快速巡检关键页面：若存在未使用 `.ymd-page` 导致断层的页面，做最小修复
4. 跑 `type-check` 与 `build:h5`
5. 小程序端手测关键路径并截图对比（背景一致性、对比度、无露白）

