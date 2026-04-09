# 配置地图 Key 解决 Map key not configured 问题

## 摘要
解决 `ymd-app`（H5 端）在个人资料页（`profile.vue`）调用 `uni.chooseLocation` 时出现 `Map key not configured.` 报错的问题。需要在项目的 `manifest.json` 文件中添加 H5 的地图 SDK 密钥配置。

## 当前状态分析
- **报错定位**：在 `ymd-app/src/pages/user/profile.vue` 的第 344 行附近，前端调用了 `uni.chooseLocation` API 来唤起地图选点。
- **配置现状**：在 `ymd-app/src/manifest.json` 中，目前缺少 `h5` 节点及地图相关的 `sdkConfigs`，导致在浏览器端（H5）运行时无法加载地图 SDK。

## 提议的更改
**目标文件**：`c:\Users\brian\projects\ymd\ymd-app\src\manifest.json`

**1. 配置 H5 端的腾讯地图 Key**
在 `manifest.json` 的顶层（与 `app-plus`、`mp-weixin` 同级）新增 `h5` 节点，并配置腾讯地图的 Key：
```json
  "h5": {
    "sdkConfigs": {
      "maps": {
        "qqmap": {
          "key": "这里替换为你申请的腾讯地图 Key"
        }
      }
    }
  }
```
*(注：前往 [腾讯位置服务](https://lbs.qq.com/) 注册并申请一个 Web 端的 Key)*

**2. 微信小程序的额外配置（如有需要）**
如果是编译到微信小程序端，需要声明相关的隐私接口权限，在 `mp-weixin` 节点中增加：
```json
  "mp-weixin": {
    "appid": "",
    "setting": {
      "urlCheck": false
    },
    "usingComponents": true,
    "requiredPrivateInfos": [
      "chooseLocation",
      "getLocation"
    ]
  }
```

## 假设与决策
- **平台假设**：由于报错为“Map key not configured.”，这是典型的 UniApp H5 端由于缺失 SDK Key 导致的报错。
- **地图服务商**：UniApp H5 端默认并推荐使用腾讯地图，因此使用 `qqmap` 作为配置项。

## 验证步骤
1. 开发者自行申请并获取腾讯地图 Key。
2. 修改 `ymd-app/src/manifest.json` 填入该 Key。
3. 重新运行前端项目（如 `npm run dev:h5`）。
4. 在页面点击“设置位置”，验证地图选点面板是否能够正常加载与显示。
