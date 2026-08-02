# 国元元信 · 统一下载门户 — 架构设计

> 架构师：Hermes（龙虾小厨）| 日期：2026-07-28
> 项目：国元证券智能门户 — 子项目

---

## 1. 业务背景

国元证券定制 App「国元元信」通过 ABM（Apple Business Manager）向 iOS 用户分发。
现有 4000 个 Apple 兑换链接需要分发给用户，无法逐一手动发送。

**核心诉求**：
- 用户访问下载页面 → 扫码/点击 → 获得一个 ABM 兑换链接 → 完成兑换
- 每个链接一次性消耗，系统自动从池中分配
- 管理员可上传新链接补充池子，自行管控
- **Phase 2**：扩展 PC / 安卓 / Linux 客户端直接下载

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户访问流程                            │
│                                                          │
│  用户手机/PC                                            │
│      │                                                   │
│      ▼                                                   │
│  https://download.xxx.com/ios                            │
│      │                                                   │
│      ├── 页面展示：动态二维码 + 使用说明                    │
│      │    QR 编码: https://download.xxx.com/r/{code_id}   │
│      │                                                   │
│      ▼ (用户扫码)                                         │
│  GET /r/{code_id}                                        │
│      │                                                   │
│      ├── ① 记录消耗（IP/时间/UA）                         │
│      ├── ② 标记该 code 为 used                            │
│      └── ③ 302 Redirect → Apple 兑换 URL                  │
│                                                          │
│  用户跳转到 App Store 完成兑换                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    管理员流程                             │
│                                                          │
│  管理员访问 /admin (密码保护)                              │
│      │                                                   │
│      ├── 仪表盘：剩余/已用/总量统计                        │
│      ├── 上传：粘贴/导入兑换链接（支持批量）                 │
│      ├── 链接池：查看所有链接状态                           │
│      └── 消耗日志：谁、什么时候、什么设备用了什么码          │
└─────────────────────────────────────────────────────────┘
```

### 2.1 技术选型

| 组件 | 选型 | 原因 |
|------|------|------|
| 运行时 | Node.js 18+ | 简洁，npm 生态丰富 |
| 框架 | Express | 最成熟稳定的 Node 框架 |
| 数据库 | better-sqlite3 | 零配置，单文件，适合中小规模 |
| 模板引擎 | EJS | 简单，适合后端渲染 |
| 二维码 | qrcode (npm) | 服务端生成，支持 Data URL |
| 密码保护 | express-basic-auth | 最小化的管理后台鉴权 |
| 前端 | 原生 HTML/CSS/JS | 单页面，无需框架 |

### 2.2 数据库设计

```sql
-- codes 表：兑换链接池
CREATE TABLE codes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    apple_url   TEXT NOT NULL,              -- 完整的 Apple 兑换 URL
    status      TEXT NOT NULL DEFAULT 'available',  -- available | used | revoked
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    used_at     TEXT,                       -- 消耗时间
    access_ip   TEXT,                       -- 消耗者 IP
    user_agent  TEXT                        -- 消耗者 UA（判断设备类型）
);

CREATE INDEX idx_codes_status ON codes(status);
CREATE INDEX idx_codes_created ON codes(created_at);
```

### 2.3 API 路由

| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET | `/` | 统一下载首页（列出所有平台） | 无 |
| GET | `/ios` | iOS 下载页（动态 QR 码） | 无 |
| GET | `/r/:id` | 兑换跳转（消耗 + 重定向） | 无 |
| GET | `/admin` | 管理后台仪表盘 | 密码 |
| POST | `/admin/upload` | 批量导入兑换链接 | 密码 |
| GET | `/api/stats` | JSON 统计数据 | 无 |
| GET | `/api/code/current` | 当前可用兑换链接（不消耗） | 无 |

### 2.4 安全设计

- 管理后台：HTTP Basic Auth，密码通过环境变量 `ADMIN_PASSWORD` 配置
- 兑换链接不直接暴露在页面 HTML 中（通过中间页跳转）
- 同一 IP 短时间多次请求加频率限制（防止恶意消耗）
- SQLite 文件放在 `data/` 目录，不允许 Web 访问

### 2.5 Phase 2 扩展预留

Phase 2 添加 PC/安卓/Linux 客户端下载：
- `/pc` — PC 客户端下载页
- `/android` — 安卓 APK 下载页
- `/linux` — Linux 客户端下载页
- 文件存储在 `public/downloads/` 目录
- 管理后台增加「客户端版本管理」Tab

---

## 3. 部署方案

| 项目 | 说明 |
|------|------|
| 服务器 | 待定（独立于国元门户的服务器，或复用现有 DMZ Nginx） |
| 域名 | 待定（推荐 download.oa.gyzq.com） |
| 端口 | 3100（内部），Nginx 反向代理到 443 |
| 进程管理 | PM2 或 systemd |
| 日志 | stdout → PM2/systemd journal |

```nginx
# Nginx 配置示例
server {
    listen 443 ssl;
    server_name download.oa.gyzq.com;

    location / {
        proxy_pass http://127.0.0.1:3100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 4. 项目结构

```
download-portal/
├── server.js              # 主入口
├── package.json
├── .env.example           # 环境变量模板
├── data/                  # SQLite 数据库（gitignore）
│   └── codes.db
├── public/                # 静态资源
│   ├── style.css
│   └── downloads/         # Phase 2：客户端安装包
├── views/                 # EJS 模板
│   ├── index.ejs          # 统一下载首页
│   ├── ios.ejs            # iOS ABM 下载页（含 QR）
│   ├── redeem.ejs         # 兑换跳转中间页
│   ├── admin.ejs          # 管理后台
│   └── error.ejs          # 错误页
├── admin/                 # 管理后台路由
│   └── admin.js
├── deploy.sh              # 部署脚本
├── ARCHITECTURE.md        # 本文件
└── SPEC.md                # 开发规格书
```
