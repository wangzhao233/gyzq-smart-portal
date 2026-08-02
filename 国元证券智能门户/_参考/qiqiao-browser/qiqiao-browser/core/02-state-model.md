# 状态模型与变量字典（唯一权威）

> **读取阶段：** 阶段二（主会话登录后、进入节点 30 前）

## 当前节点

| 变量 | 含义 | 判定方式 |
|------|------|---------|
| `CURRENT_NODE` | 当前所处的节点（如 `common/30`、`form-filling/03` 等） | 由 `recovery/00-resume-protocol.md` 快速定位后确定 |

**规则：** 任何时候你都必须清楚自己在哪个节点。如果不确定，重新执行 `recovery/00-resume-protocol.md`。

## 平台域名

| 变量 | 值 | 判定方式 |
|------|-----|---------|
| `PLATFORM_DOMAIN` | 平台域名（含协议） | 根据用户是否提到"测试环境"判定 |

**域名选择规则：**

| 用户说法 | `PLATFORM_DOMAIN`（基础域名） | 完整首页 URL | 说明 |
|----------|-------------------|-------------|------|
| 未提及环境 / 默认 | `https://qy.do1.com.cn` | `https://qy.do1.com.cn/qiqiao2/runtime/` | 正式环境（**默认**） |
| "测试环境"、"测试服"、"QA环境" 等 | `https://qiqiao-tcb-qa.qiweioa.com.cn` | `https://qiqiao-tcb-qa.qiweioa.com.cn/qiqiao2/runtime/` | 测试环境 |

**规则：**
- **默认使用正式环境，禁止询问用户选择环境**。只有用户明确说"测试环境"/"测试服"/"QA环境"时才切换到测试域名。用户没说=正式环境，直接打开，不要问。
- `PLATFORM_DOMAIN` 是基础域名，拼接 `/qiqiao2/runtime/` 得到完整首页 URL
- 站点记忆中存储的 URL 也使用完整路径 `{PLATFORM_DOMAIN}/qiqiao2/runtime/...`

## 用户意图拆解

技能触发后，根据用户输入的完整度，分为三种场景：

| 场景 | 条件 | 处理方式 |
|------|------|---------|
| A — 意图明确 | 用户已提供具体应用名、字段值；或用户已说明要发起的流程名称 | 直接执行，不重复确认 |
| B — 口语化 | 用户说"帮我填个单"、"提个XX申请"但未指定应用和列表；或用户说"发起XX流程"但未说明流程名称 | **必须先询问**：填单流问"哪个应用？哪个列表？做什么操作？"；发起流程问"要发起哪个流程？" |
| C — 意图模糊 | 用户只给了关键词如"人事管理的应用填单" | 先用 `bsk snapshot` 查看页面 → 展示结果 → 让用户确认选择。**禁止**凭空编造 |

**核心原则：口语化表达先询问，模糊关键词先探索。**

> 例：用户说"帮我填个请假单" → 询问"请问要去哪个应用里填单？应用里哪个列表？"，**不要**直接用"请假"去搜索

## 操作上下文变量

以下变量在操作过程中逐步确定：

| 变量 | 含义 | 确定时机 |
|------|------|---------|
| `APP_NAME` | 目标应用名称 | `form-filling/01-app-list.md` 搜索/选择后确定 |
| `LIST_NAME` | 目标列表名称 | `form-filling/02-app-detail.md` 选择后确定 |
| `FORM_FIELDS` | 表单字段结构 | 表单填写节点（`form-filling/04` / `start-process/04`）获取 |
| `FORM_DATA` | 已填写的字段值 | 表单填写节点组装 |
| `FLOW_NAME` | 目标流程名称（发起流程时使用） | `start-process/01-process-search.md` 或 `start-process/02-process-select.md` 确定 |
| `FILLED_URL` | 当前操作完成后的页面 URL | `form-filling/06-site-memory.md` 写入站点记忆时获取 |

## 站点记忆

| 变量 | 说明 |
|------|------|
| 记忆文件 | `~/browser-data/site-memory.json` |
| 数据结构 | 扁平数组 `{"entries": [{ appName, listName, url, verifiedAt }]}` |
| 匹配方式 | 精确匹配 `appName + listName` |
| 过期规则 | `verifiedAt` 超过 30 天视为过期 |
| 过期处理 | 打开 URL 后验证页面是否仍然有效，失败则重新导航 |
| 文件不存在 | 视为未命中，自动创建 `{"entries":[]}` |

完整数据结构见 `references/site-memory-template.md`。
