# 项目规划: 游牧岛 (Nomad Island) 综合生活平台

## 1. 概述 (Summary)
本项目旨在打造一个类似“NCC 游牧岛小程序”的综合生活平台，服务于数字游民和创新者。平台集成了活动报名、社区互动、共居空间展示与预订、以及用户积分体系等核心功能。

## 2. 当前状态分析 (Current State Analysis)
- 当前项目目录 `c:\Users\brian\projects\ymd` 为空，属于从零开始的全新项目。
- 确认技术栈选型：
  - **前端**：UniApp (Vue 3 + TypeScript) — 跨平台开发，主打微信小程序。
  - **后端**：Python (FastAPI) — 高性能、支持异步。
  - **数据库**：PostgreSQL — 强大的关系型数据库。

## 3. 假设与决策 (Assumptions & Decisions)
- **遵循 Plan Harness 规范**：为了保证项目的规范性和可维护性，将严格按照“Plan Harness”工程规范推进。后续开发将由文档（`spec.md`, `tasks.md`, `checklist.md`）驱动。
- **前后端分离架构**：前端项目 `ymd-app` 和后端项目 `ymd-server` 分别在独立目录管理。
- **身份验证机制**：采用 JWT (JSON Web Token) 进行会话管理，并优先集成微信小程序的静默登录及用户信息授权。
- **开发环境**：使用 Docker Compose 统一管理本地依赖服务（如 PostgreSQL, Redis）。

## 4. 建议变更与实施步骤 (Proposed Changes & Implementation Steps)

### 阶段 1: 基础设施与 Harness 文档初始化 (Infrastructure & Docs)
- **What**: 初始化项目目录，创建工程规范文档。
- **Why**: 落实 Harness 工程规范，确保开发目标和进度可视化。
- **How**:
  - 在 `.trae/documents/` 目录下生成 `spec.md` (详细业务逻辑与 API 规格)、`tasks.md` (开发任务拆解)、`checklist.md` (测试与验收清单)。
  - 创建 `.gitignore` 和基础 README。
  - 编写 `docker-compose.yml` 配置文件。

### 阶段 2: 后端基础架构 (Backend Setup - `ymd-server`)
- **What**: 搭建 FastAPI 后端框架。
- **Why**: 为前端提供稳定、高性能的 API 接口支持。
- **How**:
  - 使用 Poetry 或 pip 初始化 Python 环境。
  - 搭建标准目录结构：`app/api` (路由), `app/models` (数据库模型), `app/schemas` (Pydantic 验证模型), `app/core` (配置与安全), `app/crud` (数据库操作)。
  - 配置 SQLAlchemy 2.0 (异步) 和 Alembic 进行数据库迁移。
  - 实现基础的用户认证模块。

### 阶段 3: 前端基础架构 (Frontend Setup - `ymd-app`)
- **What**: 搭建 UniApp (Vue 3) 前端框架。
- **Why**: 提供跨平台的用户界面交互。
- **How**:
  - 使用 Vite/Vue CLI 创建 UniApp + Vue 3 + TS 项目。
  - 配置全局状态管理 (Pinia) 和网络请求拦截器。
  - 配置 `pages.json`，实现底部导航栏 (TabBar)，划分四大核心模块的入口页面：
    - 首页/活动 (Events)
    - 社区 (Community)
    - 共居 (Co-living)
    - 我的 (Profile)

### 阶段 4: 核心业务功能开发 (Core Features Implementation)
- **What**: 按照 MVP 要求实现四大核心业务模块。
- **Why**: 交付项目的核心价值，满足用户基本使用场景。
- **How**:
  - **社区/帖子模块**：实现动态发布（图文）、点赞、评论列表、话题分类。
  - **活动报名模块**：实现活动日历/列表展示、活动详情、报名支付/登记、活动签到。
  - **共居空间模块**：实现空间列表过滤（按城市等）、房型与设施展示、预订意向提交。
  - **个人中心与积分模块**：实现用户资料编辑、数字游民身份认证、“情感账本”（社区积分）的获取与消费流水记录。

## 5. 验证步骤 (Verification Steps)
- [ ] 确认所有 Harness 规范文档 (`spec.md`, `tasks.md`, `checklist.md`) 已正确生成并包含合理内容。
- [ ] 确认 `docker-compose up -d` 能够成功启动本地数据库服务。
- [ ] 确认后端 FastAPI 服务能正常启动，Swagger UI (`http://localhost:8000/docs`) 能够访问且 API 文档清晰。
- [ ] 确认前端 UniApp 项目能成功编译到微信小程序端，且 TabBar 页面切换正常。
- [ ] 确认后续开发的所有功能通过 `checklist.md` 中的验收测试。
