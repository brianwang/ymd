# Tasks
- [x] Task 1: 补齐数据模型与迁移（用户/活动/帖子）
  - [x] 为用户表新增偏好位置字段（lat/lng/display_name/city/source/updated_at），并更新对应 Pydantic Schema
  - [x] 为活动表新增可选经纬度字段（lat/lng），并更新对应 Schema 与管理端必要展示（如有）
  - [x] 为帖子表新增可选经纬度字段（lat/lng/city），并更新对应 Schema
  - [x] 编写 Alembic 迁移并确保向后兼容（字段可空，默认不影响现有查询）

- [x] Task 2: 后端 API（位置设置 + 距离排序/过滤）
  - [x] 新增用户偏好位置读取/写入 API（例如 `GET/PUT /users/me/location`，或扩展 `/users/me`）
  - [x] 扩展活动列表接口支持 `near_lat/near_lng/radius_km/sort`，并在启用时返回 `distance_km`
  - [x] 扩展帖子列表接口支持 `near_lat/near_lng/radius_km/sort=distance`，并对无位置帖子降级处理
  - [x] 新增（或复用）活动“推荐”接口/模式，替代前端 `slice(0,6)` 逻辑
  - [x] 增加必要的单元测试/接口测试：经纬度校验、排序稳定性、半径过滤正确性

- [x] Task 3: ymd-app 前端（位置设置入口 + 附近推荐接入）
  - [x] 在“我的/个人资料”增加位置展示与“设置位置”入口（优先使用位置选择能力；无法选择时提供城市文本输入）
  - [x] 将活动页推荐改为调用服务端推荐/排序能力（优先距离 + 兼容原模式）
  - [x] 在社区页增加“附近”排序入口：使用用户偏好位置或允许临时定位参数
  - [x] 共居页为种子空间数据补充 `lat/lng`，并按用户偏好位置做距离排序展示“附近推荐”
  - [x] 端到端自测：未设置位置降级、设置位置后推荐变化、刷新后持久化生效

- [x] Task 4: 文档与回归
  - [x] 更新必要的 API 文档（OpenAPI/README 如项目已有约定）说明新参数与响应字段
  - [x] 回归测试：活动列表原有过滤（category/city/time）仍可用；帖子/评论/登录不受影响

# Task Dependencies
- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 1, Task 2, Task 3
