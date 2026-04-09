# 社区发帖支持语音、地理位置与 #标签 Spec

## Why
当前发帖能力仍偏“轻量文本”，表达信息不足。需要在不破坏既有富媒体能力的前提下，补齐语音表达、地理位置与 #标签，提升内容可读性与组织能力。

## What Changes
- 发帖请求与帖子返回新增可选字段：`location`（地理位置对象）与 `tags[]`（标签列表）
- 服务端在创建帖子时支持从正文内容中解析 `#标签`，与显式提交的 `tags[]` 合并去重并归一化
- 发帖页新增：
  - 语音录制并上传（复用现有媒体上传接口，产出 audio 媒体项写入 `media[]`）
  - 选择/移除地理位置（展示位置名，按平台能力可携带经纬度）
  - 标签编辑（手动添加与从正文解析的标签展示/去重）
- 信息流与详情页新增展示：地理位置与标签

## Impact
- Affected specs: 社区发帖、信息流展示、帖子详情展示、媒体上传（语音文件类型覆盖）
- Affected code: 后端 Post 表结构与 Schema、创建/查询接口；前端发帖页与帖子卡片/详情渲染组件

## ADDED Requirements
### Requirement: Post Location
系统 SHALL 支持帖子携带可选的地理位置 `location`。

#### Scenario: Create post with location
- **WHEN** 登录用户发布帖子并选择了一个地理位置
- **THEN** 服务端保存并在信息流与详情接口中返回该 `location`，前端展示位置名

#### Scenario: Location is optional and removable
- **WHEN** 用户在发帖页移除已选位置后提交
- **THEN** 创建请求不包含 `location`，帖子展示不出现位置信息

### Requirement: Hashtags
系统 SHALL 支持帖子标签 `tags[]`，并支持从正文内容中解析 `#标签` 作为补充来源。

#### Scenario: Parse hashtags from content
- **WHEN** 用户发布正文包含 `#露营`、`#共居` 的帖子（可带或不带显式 `tags[]`）
- **THEN** 服务端返回的 `tags[]` 包含解析出的标签（与显式标签合并去重并归一化）

#### Scenario: Tag validation
- **WHEN** 用户提交的标签数量或单个标签长度超出限制，或包含非法字符
- **THEN** 服务端返回 4xx，并给出可读错误信息

### Requirement: Voice Recording and Upload
系统 SHALL 在 ymd-app 支持“录制语音并上传”以生成音频媒体项（audio）写入帖子 `media[]`。

#### Scenario: Record voice and create post
- **WHEN** 用户在发帖页录制一段语音并提交发帖（可带或不带文字）
- **THEN** 前端上传语音文件获取 URL，创建帖子时将其作为 audio 媒体项写入 `media[]`，详情页可播放

## MODIFIED Requirements
### Requirement: Post Create Payload Extension
系统 SHALL 在不破坏既有 `media[]` 与 `image_urls` 兼容策略的前提下，扩展创建帖子接口以接收并返回 `location` 与 `tags[]`。

### Requirement: Post Create Validation
系统 SHALL 继续满足“文字或至少一个媒体”约束；`tags[]` 与 `location` 不应被视为满足该约束的内容实体。

## REMOVED Requirements
（无）

