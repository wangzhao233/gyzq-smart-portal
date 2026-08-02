# 国元元信 · 统一下载门户 — 版本记录

## v1.1 (2026-07-28)
- 🔒 检测微信/企微内置浏览器，引导用户使用系统浏览器打开
- 🔒 iOS ABM 兑换改为原子抢占（`/r/claim`），解决并发冲突
- 📱 Android 下载页优化

## v1.0 (2026-07-28)

### 功能清单

| 模块 | 功能 |
|------|------|
| 🏠 下载首页 | 6 平台入口（iOS/Android/PC×2/Mac×2/Linux），移动端自适应 |
| 📱 iOS ABM | 动态 QR 码分发兑换链接，扫码消耗，自动跳转 App Store |
| 🤖 Android | QR 码 → 云端下载，备用内网直链 |
| ⊞ PC 64/32位 | 内网下载 + 云端下载，双通道 |
| ⌘ Mac Apple/Intel | 内网下载 + 云端下载 |
| 🐧 Linux | Deb 包直链下载 |
| 🔧 管理后台 | 仪表盘（7天趋势）+ 兑换码导入（去重）+ 链接池（筛选/分页/统计卡片）+ 消耗日志 |

### 技术栈

- Node.js + Express + EJS + better-sqlite3 + qrcode
- SQLite 单文件数据库，零外部依赖
- HTTP Basic Auth 管理后台保护

### 部署

- 端口：3100（Nginx 反代到 443）
- 进程：PM2 / systemd
- 推荐域名：download.oa.gyzq.com

### 文件清单

```
server.js db.js admin/admin.js deploy.sh package.json .env.example
views/{index,ios,android,admin,error}.ejs
public/style.css
scripts/{init-db,force-reset}.js
```
