# 管理端 UI 重设计（桌面端优先）页面设计说明

## Global Styles（全局规范）
- Layout
  - 桌面端优先：内容区采用“侧边栏 + 主内容”的两栏结构；主内容容器设置 `max-width`（避免超宽导致阅读困难），并居中。
  - 间距体系：以 8px 为基础单位（8/16/24/32/48），控制区块间距与表单控件垂直节奏。
- Design Tokens（建议以 CSS 变量落地）
  - 颜色：`--bg`、`--surface`、`--text`、`--muted`、`--border`、`--primary`、`--danger`、`--success`、`--focus`。
  - 字体层级：H1（页面标题）、H2（区块标题）、Body（正文）、Caption（辅助说明/时间/次要信息）。
  - 圆角与阴影：卡片使用轻阴影或细边框（避免“厚重”），按钮与输入框统一圆角。
- Button Hierarchy（按钮层级与位置）
  - 主按钮（Primary）：每个页面默认仅 1 个视觉主按钮，放在页面标题区右侧或表单底部右侧。
  - 次按钮（Secondary）：用于次要操作（取消/返回/重置），与主按钮保持明确间距。
  - 危险按钮（Danger）：仅用于删除/不可逆操作；默认不与主按钮并列为同等强调。
  - 行内操作：高频动作可直接露出 1–2 个按钮；低频/危险动作收纳到“更多”菜单。

## Meta Information（全站）
- Title 模板：`{页面名} - 管理后台`
- Description：简述页面用途（便于浏览器标签与分享预览）
- Open Graph：与 Title/Description 对齐（内部系统可简化）

---

## Page 1：登录页（/login）
- Page Structure
  - 居中单列卡片：上方标题/说明；中部表单；底部提交按钮。
- Sections & Components
  - Header：产品名 + “管理后台”说明（弱化）。
  - Form：输入框统一高度；label 使用中等字重；错误提示固定在字段下方。
  - Primary CTA：登录按钮（全宽或对齐右侧，二选一并全站统一）。
  - Feedback：登录失败提示在表单区顶部或字段下方，避免跳动。

## Page 2：后台通用布局（Layout Shell）
- Layout
  - 左侧 Sidebar 固定宽度；右侧 Content 可滚动。
  - Content 顶部为页面标题区（Title Bar），下方为页面主体。
- Sections & Components
  - Sidebar：导航分组（用户/内容/运营）；当前项高亮；折叠态仅保留图标（可选）。
  - Title Bar：
    - 左：页面标题 + 简短描述（可选）
    - 右：主操作区（Primary/Secondary 按钮）
  - Surface：页面主体使用卡片/区块承载，减少大面积纯白导致“空而散”。

## Page 3：用户管理（/users）
- Page Structure
  1) 筛选区（Filter Bar）
  2) 结果区（Table Card）
- Sections & Components
  - Filter Bar：首行放最关键输入（搜索/状态）；次行放高级筛选（可折叠）。右侧放“重置/查询”。
  - Table：表头固定高度；文本对齐规则统一（数字右对齐、文本左对齐）。
  - Row Actions：
    - 露出：高频操作（如查看/编辑一类）
    - 收纳：危险/低频操作到更多菜单；删除类操作必须二次确认。

## Page 4：内容管理（/posts、/comments）
- Page Structure
  - 与用户管理一致：筛选区 + 表格区（保证跨页面一致性）。
- Sections & Components
  - 内容摘要：使用两行截断，避免撑高行高；次要元信息（作者/时间）使用 muted。
  - 删除：Danger 样式 + 确认对话框；对话框按钮遵循“主操作在右”。

## Page 5：运营配置（/reward-config）
- Page Structure
  - 多区块表单：每个配置组一个 Card（标题 + 说明 + 字段）。
- Sections & Components
  - Form Groups：字段对齐成网格（桌面端 2 列优先，复杂字段独占整行）。
  - Submit Area：表单底部固定区域（或最后一个区块底部），提供“保存（Primary）/取消（Secondary）”。
  - Feedback：保存成功/失败提示在提交区附近，避免全局弹窗过多打扰。
