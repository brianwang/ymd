## Summary
- 小程序端“我的/个人页”移除“编辑个人资料”入口与独立编辑页。
- 将“编辑资料”能力迁移到用户详情页（pages/user/profile）且在该页内完成编辑与保存（不再跳转到单独页面）。

## Current State Analysis
- “我的”tab 页为 [pages/profile/index.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/index.vue)。
  - 顶部头像卡片右侧存在“编辑”按钮，点击会 `navigateTo('/pages/profile/edit')`，见 [index.vue:L6-L13](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/index.vue#L6-L13)、[index.vue:L196-L202](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/index.vue#L196-L202)。
  - “功能入口”菜单内存在“编辑个人资料”菜单项，同样走 `goEditProfile()`，见 [index.vue:L49-L66](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/index.vue#L49-L66)。
- 独立编辑页为 [pages/profile/edit.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/edit.vue)，包含头像上传(`/media/upload`)与资料更新(`PUT /users/me`)逻辑。
- 用户详情页为 [pages/user/profile.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/user/profile.vue)，当前用于查看他人主页与动态；当 `isMe` 时仅隐藏关注按钮，没有资料编辑能力。
- 路由定义在 [pages.json](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages.json)：
  - “我的”页：`pages/profile/index`，见 [pages.json:L74-L79](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages.json#L74-L79)
  - “编辑个人资料”页：`pages/profile/edit`，见 [pages.json:L81-L85](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages.json#L81-L85)
  - 用户详情页：`pages/user/profile`，见 [pages.json:L52-L59](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages.json#L52-L59)

## Goal & Success Criteria
- “我的/个人页”不再出现任何“编辑个人资料/编辑”入口。
- 用户资料编辑仅在用户详情页（pages/user/profile）完成：
  - 当查看自己（isMe）时，页面提供头像/昵称/手机号编辑与保存。
  - 保存成功后：更新服务端 `PUT /users/me`，并同步更新 `userStore.userInfo`，返回到查看态（仍在同页）。
- 移除旧编辑页（路由与页面文件），项目可正常 type-check/构建。

## Proposed Changes

### 1) 移除“我的页”编辑入口，并提供进入“我的用户详情”的路径
- 修改 [profile/index.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/index.vue)
  - 删除头像卡片右侧“编辑”按钮（`@click="goEditProfile"`）。
  - 删除“功能入口”里的“编辑个人资料”菜单项。
  - 删除 `goEditProfile()` 方法及其引用。
  - 新增进入个人用户详情页的入口（不包含“编辑个人资料”字样），推荐两种做法（二选一，按 UI 更自然的方式落地）：
    - 让顶部个人信息 Card 可点击：登录后跳转 `/pages/user/profile?id=<myId>`。
    - 或在“功能入口”添加“个人主页/个人资料”菜单项：登录后跳转同上。
  - 导航前确保拿到 `myId`：
    - 优先从 `userStore.userInfo?.id` 读取；
    - 若不存在但已登录，则先 `GET /users/me` 刷新 store 后再跳转。

### 2) 在用户详情页内实现“编辑资料”（仅 isMe）
- 修改 [user/profile.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/user/profile.vue)
  - 当 `isMe` 为 true：
    - AppBar 标题改为“我的主页”（或保持“用户主页”，以产品期望为准；默认改为“我的主页”）。
    - 在顶部 profile Card 下方增加“我的资料”编辑区（同页编辑，不跳转）：
      - 头像选择：`uni.chooseImage` 选择本地图片；预览优先用本地路径；
      - 头像上传：复用现有 `BASE_URL + /media/upload` + `uni.uploadFile` 方式；
      - 昵称/手机号输入与校验：复用 edit.vue 中校验规则；
      - 保存：`PUT /users/me`，成功后：
        - `userStore.setUserInfo(updated)`，并刷新页面展示（头像/昵称等）；
        - 退出编辑态（例如收起编辑区/回到查看态）。
  - 当 `isMe` 为 false：保持现有“关注/动态列表”逻辑不变。
  - 数据来源：
    - 为 isMe 增加一次 `GET /users/me` 用于填充编辑表单与展示更完整字段（昵称/头像/手机号等），避免 `/users/:id` 返回字段不全。
    - 动态列表仍按 `user_id` 拉取，不改变分页/下拉刷新/触底加载逻辑。

### 3) 删除旧编辑页（含路由）
- 修改 [pages.json](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages.json)
  - 删除 `pages/profile/edit` 路由段。
- 删除文件：
  - [profile/edit.vue](file:///c:/Users/brian/projects/ymd/ymd-app/src/pages/profile/edit.vue)
- 确认仓库内不再存在对 `/pages/profile/edit` 的跳转引用（仅在 `profile/index.vue` 发现引用，删除后应为 0）。

## Assumptions & Decisions (Locked)
- “个人用户详情”明确为 `pages/user/profile`（用户主页页）。
- 编辑方式为“详情页内直接编辑”，不再跳转独立编辑页。
- 旧编辑页 `pages/profile/edit` 需要彻底删除（路由 + 文件）。

## Verification
- 静态检查：
  - 在 `ymd-app/` 运行 `npm run type-check`，确保 TS 与 SFC 类型检查通过。
  - 全局搜索确认无 `/pages/profile/edit` 残留引用。
- 手动验收（mp-weixin 或 h5 均可）：
  - 进入“我的”tab：不展示“编辑/编辑个人资料”入口。
  - 登录后从“我的”进入个人用户详情页：可在详情页内编辑头像/昵称/手机号并保存成功。
  - 保存成功后返回查看态，且“我的”页展示同步更新（昵称/头像等）。
