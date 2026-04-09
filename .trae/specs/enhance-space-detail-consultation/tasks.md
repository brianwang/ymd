# Tasks
- [x] 1. 后端：咨询线索（Inquiry）数据与 API
  - [x] 1.1 新增 Inquiry 数据模型与 Alembic 迁移（包含 status/admin_note/时间字段）
  - [x] 1.2 新增公开创建接口：`POST /api/v1/coliving/spaces/{space_id}/inquiries`
  - [x] 1.3 新增管理端列表接口：`GET /api/v1/admin/coliving/inquiries`（分页 + 基础筛选）
  - [x] 1.4 新增管理端更新接口：`PATCH /api/v1/admin/coliving/inquiries/{inquiry_id}`（更新 status/admin_note）
  - [x] 1.5 验证：补充最小化接口冒烟脚本或测试用例（创建 + admin 列表/更新）

- [x] 2. 小程序端：空间详情页咨询入口落地
  - [x] 2.1 更新空间详情页“咨询”交互：弹出咨询方式选择（表单/复制微信/拨号）
  - [x] 2.2 实现“提交咨询”表单：字段校验、loading/错误态、提交成功反馈
  - [x] 2.3 对接后端创建接口并传递必要字段（space_id、联系方式、留言、可选 user_id）
  - [x] 2.4 统一配置客服微信号与电话（优先走前端配置项/环境变量；无则隐藏对应入口）

- [x] 3. 管理后台：咨询线索管理页面
  - [x] 3.1 新增“咨询线索”菜单与列表页（表格 + 分页 + status 筛选）
  - [x] 3.2 支持更新线索状态与备注（对接 PATCH 接口）
  - [x] 3.3 基础体验：空态/错误态/权限错误提示

- [x] 4. 联调与回归
  - [x] 4.1 后端：确认仅 superuser 可访问 admin 线索接口
  - [x] 4.2 前端：在空间详情页完成一次完整咨询提交流程
  - [x] 4.3 管理端：可看到新提交线索并能更新状态

# Task Dependencies
- 2 依赖 1（小程序端提交咨询需要后端创建接口）
- 3 依赖 1（管理后台依赖 admin API）
- 4 依赖 1/2/3
