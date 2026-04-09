# 一键启动（动态端口）

## 前置要求
- 已安装 Node.js（含 npm）
- 已安装 Python（能运行 `python`）
- 已在各目录安装依赖：
  - `ymd-admin`: `npm install`
  - `ymd-app`: `npm install`
  - `ymd-server`: 安装 `requirements.txt`（需包含 `uvicorn`）

## 启动
在仓库根目录执行：

```powershell
pwsh ./dev-start.ps1
```

启动后脚本会输出 3 个地址（端口会自动选择未占用的）：
- API：`http://localhost:<API_PORT>/api/v1`
- Admin：`http://localhost:<ADMIN_PORT>/`
- H5：`http://localhost:<H5_PORT>/`

脚本会保持运行以维持三个服务进程；在该窗口按 `Ctrl+C` 停止并清理后台进程。

## 常见问题
- 提示 uvicorn 缺失：先安装 `ymd-server/requirements.txt`
- 端口被占用：脚本会自动换端口；若仍失败，检查是否有安全软件阻止监听端口
- H5 端口不一致：如果 uni dev server 不接受 `--port`，请以 H5 启动窗口日志显示的 URL 为准
