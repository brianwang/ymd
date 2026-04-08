# 社区图文/音视频与点赞图标 Spec

## Why
当前社区发帖仅支持文字+图片。为了提升内容表达与互动效率，需要支持音频/视频，并将点赞交互以图标形态呈现以强化可见性。

## What Changes
- 帖子支持“图文 + 音频 + 视频”的媒体附件能力（统一为 media 列表表达）
- 发帖校验从“必须有文字”调整为“文字或至少一个媒体”
- 复用现有媒体上传接口 `/api/v1/media/upload` 上传图片/音频/视频
- 点赞按钮在信息流与详情页使用图标展示，已点赞/未点赞有明确态
- **兼容**：保留并继续返回/接收 `image_urls`（旧字段），新增 `media` 为新字段

## Impact
- Affected specs: 社区发帖、信息流展示、帖子详情展示、点赞交互
- Affected code: 后端 Post 模型/Schema/接口与迁移；前端社区信息流/详情/发帖页与相关组件

## ADDED Requirements
### Requirement: Rich Media Post
系统 SHALL 支持帖子携带媒体附件 `media[]`，每个媒体项包含类型与 URL。

#### Scenario: Create post with images
- **WHEN** 登录用户发布帖子并携带 1-9 张图片
- **THEN** 服务端保存并返回 `media`（包含这些图片项），信息流与详情页能展示图片预览

#### Scenario: Create post with video
- **WHEN** 登录用户发布帖子并携带 1 个视频附件（可带或不带文字）
- **THEN** 服务端保存并返回 `media`（包含 video 项），信息流与详情页能展示视频预览入口

#### Scenario: Create post with audio
- **WHEN** 登录用户发布帖子并携带 1 个音频附件（可带或不带文字）
- **THEN** 服务端保存并返回 `media`（包含 audio 项），详情页支持播放

### Requirement: Media Upload Reuse
系统 SHALL 复用现有 `/api/v1/media/upload` 用于图片/音频/视频上传，并在服务端进行基本安全校验。

#### Scenario: Upload validation
- **WHEN** 用户上传不允许的文件类型或超出限制大小
- **THEN** 服务端返回 4xx，并给出可读错误信息

### Requirement: Like Icon UI
系统 SHALL 在社区信息流与帖子详情页将点赞交互以图标展示，且有明确的“已点赞”态。

#### Scenario: Toggle like
- **WHEN** 登录用户点击点赞图标
- **THEN** UI 立即切换态并更新计数；若请求失败则回滚并提示

## MODIFIED Requirements
### Requirement: Post Create Validation
系统 SHALL 允许“纯媒体帖”（无文字）与“纯文字帖”（无媒体），但禁止“文字为空且 media 为空”的发帖请求。

## REMOVED Requirements
### Requirement: Content Must Be Non-empty
**Reason**: 支持音视频与图片后，帖子不再强制要求文字内容。
**Migration**: 前端校验与后端校验统一改为“文字或媒体至少一项”。媒体为空时仍需非空文字。

