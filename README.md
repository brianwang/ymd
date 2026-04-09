# 游牧岛（Nomad Island）
一个围绕“共居生活方式”的开源全栈项目：把活动组织、社区内容沉淀、共居空间信息与咨询流程放在同一个产品里，方便大家一起共建、一起迭代。

Nomad Island is an open-source full-stack project for coliving communities.

## 主要功能
- 用户与认证：邮箱注册/登录、JWT 鉴权（后端对外 API：`/api/v1`）。
- 活动：活动列表/详情、报名与取消、我的报名状态。
- 社区：发帖/删帖（软删）、评论、点赞、收藏、分享计数；支持图片/音频等媒体；支持话题标签（#hashtag）与位置信息。
- 共居：空间咨询/登记（inquiries）基础流程。
- 积分：每日签到、首帖奖励、积分流水与任务状态。
- 管理后台（ymd-admin）：用户/帖子/评论/活动报名/共居咨询管理；积分奖励配置与调整入口。

## 技术栈与模块
- ymd-app：UniApp（Vue3）+ Pinia + Vite（支持 H5/小程序等多端形态）
- ymd-admin：Vue3 + Pinia + Vite
- ymd-server：FastAPI + PostgreSQL + SQLAlchemy(Async) + Alembic
- 部署：`docker-compose.yml`（api + web），上传文件挂载到 `uploads` volume

## 快速开始（开发）
仓库提供一键启动脚本（动态端口）用于本地开发调试：

```powershell
pwsh ./dev-start.ps1
```

启动说明与常见问题见 [README-dev-start.md](scripts/README-dev-start.md)。

### 依赖与准备
- Node.js + npm（用于 ymd-app / ymd-admin）
- Python（用于 ymd-server，需能运行 `python`）
- PostgreSQL（ymd-server 使用 PostgreSQL；连接参数可通过环境变量配置）

各端环境变量示例：
- [ymd-app/.env.example](ymd-app/.env.example)
- [ymd-admin/.env.example](ymd-admin/.env.example)

测试账号文档（可用种子脚本生成/重置）：
- [test_accounts.md](test_accounts.md)

## API 文档与约定
- API Base Path：`/api/v1`
- OpenAPI JSON：`/api/v1/openapi.json`（FastAPI 自动生成）
- Swagger UI：`/docs`（开发环境可用）

### 位置与推荐相关接口

#### `GET /users/me/location`
- 说明：读取当前登录用户的“偏好位置”
- 鉴权：需要登录（Bearer Token）
- 响应：未设置位置时返回 `null`；已设置时返回：
  - `lat`/`lng`：经纬度
  - `display_name`：展示名（如“望京 SOHO”）
  - `city`：可选
  - `source`：`manual` | `device`
  - `updated_at`：更新时间

#### `PUT /users/me/location`
- 说明：更新当前登录用户的“偏好位置”
- 鉴权：需要登录（Bearer Token）
- 请求体：
  - `lat`/`lng`：经纬度（必须成对提供）
  - `display_name`：展示名（必填）
  - `city`：可选
  - `source`：`manual` | `device`（默认 `manual`）
- 响应：返回最新的偏好位置对象

#### `GET /events`
- 说明：活动列表；保留原有过滤能力，并可选启用“附近排序/过滤”
- 原有过滤参数（回归要求）：
  - `category`：活动分类
  - `city`：城市
  - `start_from`/`start_to`：开始时间范围（ISO 8601）
- 新增可选参数（附近能力）：
  - `near_lat`/`near_lng`：同时提供时启用距离计算
  - `radius_km`：半径过滤（仅在提供 `near_lat/near_lng` 时可用）
  - `sort`：`default` | `distance` | `start_time`
- `distance_km` 行为：
  - 仅当请求启用距离计算（提供 `near_lat/near_lng`）且该活动有 `lat/lng` 时返回
  - 单位 km，四舍五入到 0.1km
  - 未启用距离计算或活动无坐标时不返回该字段

#### `GET /events/recommended`
- 说明：首页/列表用“推荐活动”；默认取“即将开始”的活动 Top N
- 参数：
  - `limit`：默认 6
  - `near_lat`/`near_lng`：同时提供时优先按距离排序
  - `radius_km`：半径过滤（需配合 `near_lat/near_lng`）
- `distance_km` 行为同 `GET /events`

#### `GET /posts`
- 说明：帖子列表；保留原默认排序，并可选启用“附近排序/过滤”
- 新增可选参数（附近能力）：
  - `near_lat`/`near_lng`：同时提供时启用距离计算
  - `radius_km`：半径过滤（仅在提供 `near_lat/near_lng` 时可用）
  - `sort`：`default` | `distance`
- `distance_km` 行为：
  - 仅当请求启用距离计算且帖子有 `lat/lng` 时返回；否则不返回该字段
  - 单位 km，四舍五入到 0.1km

## 目录结构
```
ymd/
  ymd-app/      # UniApp 客户端（H5/小程序等）
  ymd-admin/    # 管理后台（Web）
  ymd-server/   # FastAPI 后端
  scripts/      # 开发辅助脚本
```

## Roadmap（欢迎共建）
- 本地开发与部署体验：补齐 PostgreSQL 一键启动方案、统一初始化脚本（migrate/seed）。
- 社区能力：帖子搜索/筛选、标签/话题页、用户关注与个人主页体验增强。
- 活动能力：更丰富的报名字段、日历视图、活动分类与城市筛选体验优化。
- 共居能力：空间详情信息结构化、咨询流转与状态管理、运营侧工具完善。
- 工程化：E2E/单测覆盖、CI、发布流程与版本管理。

## Contributing（如何参与）
默认协作流程：Issue → PR → Review。参与方式与约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License
本项目以 MIT License 开源，详见 [LICENSE](LICENSE)。
