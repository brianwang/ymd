# 计划：登录/鉴权失败直接跳转登录页（小程序端）

## Summary
- 目标：在小程序端（`ymd-app`）任意接口返回鉴权失败（401/403）时，立即跳转到登录页，避免停留在需要登录的页面。
- 成功标准：当 token 失效/缺失导致后端返回 401/403 时，前端会清理登录态并 `reLaunch` 到 `/pages/auth/login`；若当前已在登录页则不重复跳转。

## Current State Analysis
- 小程序全局请求封装在 [request.ts](file:///c:/Users/brian/projects/ymd/ymd-app/src/utils/request.ts)：
  - 遇到 `401/403` 仅 `toast` + `uni.removeStorageSync('token')`，不做页面跳转。
  - 这会导致用户仍停留在原页面，需要页面自行处理或用户手动进入登录页。
- 登录页路径已在 [pages.json](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages.json) 注册为 `pages/auth/login`，页面内已有登录成功后跳转逻辑。
- 用户登录态在 [user.ts](file:///c:/Users/brian/projects/ymd/ymd-app/src/store/user.ts) 中集中管理（`token/userInfo/logout()`），当前请求层未调用 `logout()`，可能导致 Pinia 内存态与 storage 不一致。

## Assumptions & Decisions
- 范围：仅修改小程序端（`ymd-app`），不改后台管理端（`ymd-admin`）。用户已明确选择“只改小程序”。
- 跳转方式：`401/403` 时使用 `uni.reLaunch({ url: '/pages/auth/login' })`（用户选择）。
- 清理登录态：优先调用 `useUserStore().logout()`，保证 Pinia 与本地缓存一致；如运行环境在极早期无法获取 Pinia active 实例，则回退到移除 storage（实现时以可运行性为准）。
- 防抖/防循环：增加模块级跳转锁，且当当前页面已是登录页时不重复 `reLaunch`。
- 状态码覆盖：同时覆盖 `401` 与 `403`（后端 JWT 校验失败可能返回 `403`）。

## Proposed Changes
### 1) 全局请求封装在 401/403 时统一跳转
- 修改文件：[request.ts](file:///c:/Users/brian/projects/ymd/ymd-app/src/utils/request.ts)
- 改动点：
  - 在 `res.statusCode === 401 || 403` 分支中：
    - 清理登录态：调用 `useUserStore().logout()`（或等效逻辑）。
    - 获取当前页面路径（通过 `getCurrentPages()` 最后一项的 `route`/`$page?.fullPath` 兼容读取）。
    - 若不在登录页且未处于跳转中：`uni.reLaunch({ url: '/pages/auth/login' })`。
  - 保持现有 `toast` 行为，但避免在已处于登录页时重复弹出/重复跳转。

## Verification
- 静态检查：
  - 在 `ymd-app` 下运行 `npm run type-check`，确认 TS 类型无报错。
- 手动验证（任一端即可）：
  - 本地写入一个无效 token（例如在存储里设置 `token` 为随机字符串），打开任一会调用受保护接口的页面，触发请求后应直接进入登录页。
  - 在登录页停留时再次触发 401/403（如有相关请求）不应造成无限跳转。

## Out of Scope
- 不调整后端对无效 token 返回 `401`/`403` 的策略。
- 不新增“登录后回跳原页面”的参数与逻辑（若后续需要，可单独规划实现）。 
