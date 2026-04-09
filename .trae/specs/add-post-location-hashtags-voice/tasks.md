# Tasks
- [x] Task 1: 后端支持 location 与 tags 字段
  - [x] 在 posts 表新增 `location`（JSON/JSONB）与 `tags`（JSON/JSONB 数组）列，并提供迁移
  - [x] 更新 Post ORM 模型与 Pydantic schema：在创建/返回结构中加入 `location` 与 `tags`
  - [x] 创建帖子接口：校验 tags（数量/长度/字符集），从正文解析 `#标签` 并与显式 tags 合并去重归一化
  - [x] `GET /api/v1/posts` 与 `GET /api/v1/posts/{id}` 返回 `location` 与 `tags`

- [x] Task 2: 后端上传接口覆盖语音文件常见格式
  - [x] 确认 `/api/v1/media/upload` 对录音常见格式（如 m4a/aac/wav/mp3）白名单与大小限制满足需求
  - [x] 补充必要的后端自动化测试（类型/大小校验、返回结构）

- [x] Task 3: 前端发帖页新增语音录制、位置选择、标签编辑（ymd-app）
  - [x] 语音：在可用平台启用录制能力；录制完成后复用上传接口获得 URL，写入 `media[]`（audio）
  - [x] 位置：提供选择/移除地理位置入口，提交时携带 `location`
  - [x] 标签：支持输入/删除标签，并展示从正文解析的 `#标签`（提交时携带 `tags[]`）
  - [x] 保持现有“文字或 media 至少一项”前端校验；tags/location 不计入内容

- [x] Task 4: 信息流与详情页展示位置与标签（ymd-app）
  - [x] 信息流卡片与详情页增加位置展示（优先展示位置名）
  - [x] 标签以 `#标签` 形式展示（展示/换行策略与样式与现有 UI 保持一致）

- [x] Task 5: 验证与回归
  - [x] 后端：迁移可正常升级；发帖/信息流/详情包含 location 与 tags；非法 tags 返回可读错误
  - [x] 前端：至少覆盖一条“带语音 + 标签 + 位置”的发帖流程（H5 可走文件选择；小程序/APP 走录制）

# Task Dependencies
- Task 4 depends on Task 1
- Task 3 depends on Task 1 and Task 2
