# 中断恢复协议

> 本文件**仅在**技能被触发时执行，用于快速定位当前处于哪个节点。

## 目的

技能触发后，不要从头走完整流程。先快速判断用户当前处于哪个状态，直接跳到对应节点，由主会话读取该节点文件继续执行。

## 前置检测：browser-skill 是否就绪

在执行恢复协议之前，先确认 bsk CLI 可用：

1. 用 Bash 执行 `which bsk` 检查 bsk 是否在 PATH 上
2. 如果不存在 → **节点 10（环境检测）**，主会话引导安装 browser-skill
3. 如果存在 → 继续执行恢复协议

## 检测流程（按编号依次执行，命中一个即停，禁止跳号）

### 检测 1：浏览器是否已在七巧平台？

**操作：** 调用 `bsk snapshot --session <SESSION_ID>` 查看当前页面内容

**判断：** 页面 URL 是否包含 `/runtime/`？

| 结果 | 处理 |
|------|------|
| 是 — URL 包含 `/runtime/` | 进入检测 2 |
| 否 — 浏览器未打开或不在七巧平台 | 进入检测 4 |

### 检测 2：用户是否已登录？

**操作：** 用 `bsk evaluate 'window.$ai.init()' --session <SESSION_ID>`

| 结果 | 含义 | 处理 |
|------|------|------|
| 返回 `undefined` | ✅ 已登录 | 进入检测 3（判断当前节点） |
| 报错 / 不存在 | ❌ 未登录或页面未加载 | → 跳到 **节点 20（登录）**，读取 `runbooks/common/20-login.md` 执行 |

### 检测 3：已登录 — 判断当前在哪个节点

已登录且在七巧平台上，根据 URL 和页面内容判断。节点文件按流程文件夹组织：

- 公共节点：`runbooks/common/{编号}-*.md`
- 填单流节点：`runbooks/form-filling/{编号}-*.md`
- 审批流节点：`runbooks/approval/{编号}-*.md`
- 发起流程节点：`runbooks/start-process/{编号}-*.md`

**根据页面特征判断当前节点：**

| 当前页面特征 | 节点位置 | 主会话处理 |
|-------------|---------|-----------|
| URL 是首页 `/index/home` | `common/30-home.md` | 读取节点 30，识别意图 → 导航 |
| 看到应用列表页、搜索框 | `form-filling/01-app-list.md` | 读取该节点文件，继续填单流 |
| 看到待办列表、有搜索框和筛选条件 | `approval/01-todo-list.md` | 读取该节点文件，继续审批流 |
| 看到某个应用的左侧菜单树 | `form-filling/02-app-detail.md` | 读取该节点文件，继续填单流 |
| 看到审批详情页（dialog 弹窗）、有办理/驳回等按钮 | `approval/02-todo-detail.md` 或 `approval/03-approval-action.md` | 读取该节点文件，继续审批流 |
| 看到数据列表、有新增/删除/导出按钮 | `form-filling/03-list-view.md` | 读取该节点文件，继续填单流 |
| 看到表单填写页面（dialog 弹窗内有表单字段） | `form-filling/04-form-fill.md` 或 `start-process/04-form-fill.md` | 根据上下文读取对应节点文件 |
| 看到弹窗（确认/取消/下载） | 对应流程的弹窗处理节点 | 读取对应节点文件继续执行 |
| 看到流程选择弹窗 | `start-process/01-process-search.md` | 读取该节点文件，继续发起流程 |

**判断方法：** 用 `bsk snapshot --session <SESSION_ID>` 查看页面内容来确定。

### 检测 4：不在七巧平台 — 检查 bsk 环境

浏览器未打开或不在七巧平台 → 需要从头开始。

先检查是否有 bsk 会话可以复用：

| 结果 | 处理 |
|------|------|
| 有 bsk 会话（`bsk session list` 有活跃会话） | → **节点 20（登录）**，读取 `runbooks/common/20-login.md` 执行 |
| 无活跃会话 | → **节点 10（环境检测）**，读取 `runbooks/common/10-env-detect.md` 执行 |

## 检测完成后主会话的行为

根据检测到的节点位置，主会话**直接读取对应节点文件并执行**：

1. **节点 10/20/30** → 读取 `runbooks/common/{编号}-*.md` 执行
2. **节点位于 form-filling/** → 读取 `runbooks/form-filling/{编号}-*.md`，从当前节点按顺序继续执行填单流
3. **节点位于 approval/** → 读取 `runbooks/approval/{编号}-*.md`，从当前节点按顺序继续执行审批流
4. **节点位于 start-process/** → 读取 `runbooks/start-process/{编号}-*.md`，从当前节点按顺序继续执行发起流程

> 进入流程节点前，确认已读取 `core/` 全部文档（01/02/03/04/05）；runbook 节点文件随流程推进逐个加载，按各文件末尾"下一节点"声明流转。

## 检测完成的标志

你已经明确知道了用户当前处于哪个流程的哪个节点，并且知道接下来要读取哪个节点文件继续执行。如果没得到这个结论，**不要**继续往下走。
