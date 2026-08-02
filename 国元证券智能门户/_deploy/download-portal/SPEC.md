# 国元元信统一下载门户 — 开发规格书 (SPEC)

> 给 Claude 开发用 | 制作者：Hermes | 日期：2026-07-28
> **输出语言要求**：所有 UI 文字使用中文，代码注释使用中文

---

## ⚠️ 前置要求

1. **必须本地测试通过**：所有端点必须用 curl 验证
2. **必须包含测试数据**：初始化脚本生成 10 条模拟兑换链接
3. **不要编造测试结果**：每个功能都要实际运行验证
4. **交付物检查清单**：全部代码 + 测试结果截图 + 启动说明

---

## Phase 1：ABM 兑换码分发（本次交付）

### 一、项目初始化

```bash
mkdir download-portal && cd download-portal
npm init -y
npm install express better-sqlite3 ejs qrcode express-basic-auth dotenv
```

### 二、功能清单

#### F1：iOS 下载页面 (`GET /ios`)

- 展示页面标题：「国元元信 · iOS 下载」
- 展示 App Logo（占位即可，后续替换）
- 动态生成一个 QR 码：
  - 从 `codes` 表中取**一条** status=available 的链接
  - 取该链接的 `id`
  - QR 编码的内容为：`{BASE_URL}/r/{id}`（BASE_URL 从环境变量读取）
  - **不要直接在页面上显示 Apple 兑换链接**（防止直接复制走）
- 展示使用步骤说明：
  1. 使用 iPhone 相机扫描二维码
  2. 跳转后自动前往 App Store 兑换
  3. 下载安装「国元元信」
  4. 如遇问题，联系 IT 管理员
- 页面底部显示：「剩余兑换次数：{available_count}」
- 如果可用链接为 0，显示「兑换码已用完，请联系管理员补充」
- 移动端优先设计，自适应

#### F2：兑换跳转 (`GET /r/:id`)

- 根据 `id` 查找 codes 表中的记录
- 如果 status != 'available'，显示错误页「此兑换码已被使用」
- 如果 status = 'available'：
  1. 更新 status = 'used'
  2. 记录 used_at = 当前时间
  3. 记录 access_ip = req.ip
  4. 记录 user_agent = req.headers['user-agent']
- 302 重定向到原始的 `apple_url`
- **注意**：重定向前先更新数据库，再返回 302

#### F3：统一下载首页 (`GET /`)

- 页面标题：「国元元信 · 下载中心」
- 展示 App 名称 + Logo
- 展示下载入口卡片：
  - iOS 版：图标 + 「iOS 版下载」→ 链接到 `/ios`
  - 安卓版：图标 + 「安卓版下载」→ 显示「即将上线」（Phase 2）
  - PC 版：图标 + 「PC 版下载」→ 显示「即将上线」
  - Linux 版：图标 + 「Linux 版下载」→ 显示「即将上线」
- 页面底部公司信息：「道一云 · 国元证券智能门户项目」

#### F4：管理后台 (`GET /admin`)

- HTTP Basic Auth 保护（密码从 `ADMIN_PASSWORD` 环境变量读取，默认 `admin123`）
- 页面顶部导航：仪表盘 | 导入兑换码 | 链接池 | 消耗日志
- **仪表盘 Tab**：
  - 总量 / 已用 / 可用 三个卡片（大数字）
  - 今日消耗数
  - 最近 7 天消耗趋势（简单柱状图，纯 HTML/CSS 实现，不需要图表库）
- **导入兑换码 Tab**：
  - 文本框（textarea），每行一个 Apple 兑换链接
  - 支持粘贴批量导入
  - 导入时去重（检查 `apple_url` 是否已存在）
  - 导入结果显示：成功 X 条，跳过 X 条（重复）
- **链接池 Tab**：
  - 表格展示所有链接：ID | 状态 | 创建时间 | 消耗时间 | 消耗IP
  - 分页（每页 50 条）
  - 支持按状态筛选（全部/可用/已用）
  - 可用链接显示前 60 字符 + 「...」
- **消耗日志 Tab**：
  - 最近消耗记录表格：时间 | IP | 设备信息（简化 UA）
  - 分页（每页 20 条）

#### F5：统计 API (`GET /api/stats`)

返回 JSON：
```json
{
  "total": 4000,
  "used": 156,
  "available": 3844,
  "today_used": 23
}
```

#### F6：当前兑换码 API (`GET /api/code/current`)

- 返回当前页面显示的兑换码信息（仅用于 AJAX 刷新，不消耗）
- 返回 JSON：`{ "id": 123, "remaining": 3844 }`
- 前端页面每 30 秒自动 AJAX 刷新剩余数量

---

### 三、页面视觉规范

- 主色调：`#1F4E79`（国元证券深蓝）→ 与现有门户一致
- 按钮色：`#2B7CD3`
- 背景色：`#F5F7FA`
- 卡片背景：白色 + 圆角 12px + 阴影
- 字体：系统默认（`-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`）
- 移动端：最大宽度 480px 居中
- QR 码尺寸：200x200 px

### 四、初始化脚本

创建 `scripts/init-db.js`：
- 创建 SQLite 数据库和 codes 表
- 插入 10 条模拟兑换链接（用 `https://apps.apple.com/redeem?ctx=offercodes&id=123456789&code=TEST{序号}` 格式）
- 确保 `data/` 目录存在

### 五、部署脚本 (`deploy.sh`)

```bash
#!/bin/bash
# 一键部署到 /opt/download-portal/
# 1. 安装 Node 依赖
# 2. 初始化数据库
# 3. 配置 systemd 服务
# 4. 配置 Nginx（如果存在）
```

### 六、测试清单（交付前必须验证）

| # | 测试项 | 验证方式 |
|---|--------|---------|
| 1 | 首页 `/` 正常渲染 | curl -s http://localhost:3100/ \| grep "下载中心" |
| 2 | `/ios` 页 QR 码可扫描 | 检查页面含 `<img src="data:image/png;base64,..."` |
| 3 | `/r/:id` 正确跳转 | curl -v http://localhost:3100/r/1 检查 302 + Location |
| 4 | 同一 id 二次访问报错 | curl 后再 curl 同一 r/:id，应显示"已被使用" |
| 5 | 剩余数量递减 | curl /api/stats 前后对比 |
| 6 | 管理后台密码保护 | curl http://localhost:3100/admin 返回 401 |
| 7 | 管理后台登录后正常 | 带 Authorization header 访问 /admin 返回 200 |
| 8 | 批量导入去重 | POST /admin/upload 重复链接，看 skip 计数 |
| 9 | 全部用完后 `/ios` 提示 | 把所有测试码用完，访问 /ios 看到提示 |
| 10 | 响应式移动端 | 页面在 375px 宽度下正常显示 |

---

## Phase 2（预留，本次不开发）

- PC 客户端下载页：`/pc` — 静态文件下载
- 安卓 APK 下载页：`/android`
- Linux 客户端下载页：`/linux`
- 管理后台「客户端版本管理」Tab：上传安装包、更新版本号
- 下载统计（各平台下载次数）

---

## 环境变量

```bash
# .env 文件
PORT=3100
BASE_URL=http://localhost:3100    # 生产环境改为实际域名
ADMIN_PASSWORD=admin123           # 生产环境改为强密码
NODE_ENV=development
```
