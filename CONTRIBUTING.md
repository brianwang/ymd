# Contributing
欢迎参与共建游牧岛（Nomad Island）。本仓库默认使用 GitHub Issues + Pull Requests 协作。

## 参与方式
- 报 Bug：开 Issue，提供复现步骤、期望行为与实际行为、环境信息（系统/浏览器/Node/Python/PostgreSQL 版本等）。
- 提需求/讨论方案：开 Issue，先描述问题与目标，再给出可选方案与取舍。
- 提交代码：优先关联 Issue，再提交 PR，方便追踪动机与验收标准。

## 本地开发（跑起来再改）
优先使用仓库的一键启动脚本（动态端口）：

```powershell
pwsh ./dev-start.ps1
```

更完整的说明见 [scripts/README-dev-start.md](scripts/README-dev-start.md)。

## 提交规范（最小约定）
- 分支命名建议：
  - `feature/<short-name>`
  - `fix/<short-name>`
  - `chore/<short-name>`
- PR 描述建议包含：
  - 改动动机：解决什么问题/实现什么目标
  - 改动范围：涉及哪些模块/接口/页面
  - 验证方式：你如何确认它可用（启动、手工回归、脚本、测试等）

## 代码风格
- 尽量遵循各子项目已有的代码风格与项目结构，不强行引入新的框架/大范围重构。
- 如需引入新依赖或调整结构，请先在 Issue 里讨论动机与替代方案。

## 自检清单（提交前）
- 能在本地启动相关服务（至少覆盖你改动涉及的端）。
- 核心路径手工验证通过（例如：登录、列表/详情、提交表单等与本次改动相关的路径）。
- 不提交真实密钥、账号、Access Token 等敏感信息；使用各端的 `.env.example` 作为示例。

