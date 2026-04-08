# Tasks
- [ ] Task 1: 统一帖子媒体数据结构（后端）
  - [ ] 在 posts 表增加 `media`（JSON/JSONB）列，并保持 `image_urls` 兼容
  - [ ] 更新 Post 模型与 Pydantic schema：新增 `media`，并定义媒体项结构（image/video/audio）
  - [ ] 更新发帖接口校验：允许纯媒体/纯文字；拒绝二者皆空

- [ ] Task 2: 上传接口支持音视频（后端）
  - [ ] 复用 `/api/v1/media/upload`：增加 MIME/扩展名白名单与大小限制（图片/音频/视频分别限制）
  - [ ] 错误响应保持可读（4xx + detail 文案）

- [ ] Task 3: 信息流与详情返回富媒体（后端）
  - [ ] `GET /api/v1/posts` 与 `GET /api/v1/posts/{id}` 返回 `media`（并继续返回 `image_urls` 以兼容）
  - [ ] 确认软删帖子不出现在信息流与详情

- [ ] Task 4: 发帖页支持图文/音视频（前端 ymd-app）
  - [ ] 增加选择视频/音频入口；复用上传接口拿到 URL 后写入 `media`
  - [ ] 提交发帖 payload 同时包含 `media` 与（必要时）`image_urls`（兼容期）
  - [ ] UI：图片宫格、视频卡片（封面/时长）、音频卡片（名称/时长/播放）

- [ ] Task 5: 信息流与详情页渲染媒体（前端 ymd-app）
  - [ ] 信息流卡片支持展示媒体预览（优先展示视频封面，其次图片宫格，其次音频条）
  - [ ] 详情页支持视频播放与音频播放

- [ ] Task 6: 点赞按钮改为图标（前端 ymd-app）
  - [ ] 信息流与详情页点赞按钮统一为图标样式（未点赞/已点赞态）
  - [ ] 保持现有“失败回滚 + toast”交互

- [ ] Task 7: 验证与回归
  - [ ] 后端：接口手测（上传/发帖/信息流/详情/点赞）+ 迁移可升级
  - [ ] 前端：H5 或小程序端手测：发布图片/视频/音频、信息流展示、详情播放、点赞图标态

# Task Dependencies
- Task 3 depends on Task 1
- Task 4 depends on Task 1 and Task 2
- Task 5 depends on Task 3
- Task 6 depends on Task 5
