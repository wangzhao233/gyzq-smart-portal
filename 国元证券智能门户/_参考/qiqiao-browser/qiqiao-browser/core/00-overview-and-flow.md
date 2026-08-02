# 总览与主流程（唯一权威）

## 本技能解决什么

通过**主会话单线程节点流**在七巧Plus 平台上执行浏览器自动化操作。环境检测、登录、意图识别、流程执行、结果展示全部在主会话中按节点顺序完成，不派发子代理。

技术栈：**browser-skill (bsk CLI)** + **`window.$ai.fillingForm`**。仅支持 PC 运行端。

## 核心设计：主会话单线程节点流

```
═══════════════════════════════════════════════════════════════
                       主会话（唯一执行者）
═══════════════════════════════════════════════════════════════

[10-环境检测] → [20-登录] → [30-首页/意图识别与导航]
                                  │
         ┌────────────────────────┼────────────────────────┐
         ▼                        ▼                        ▼
  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐
  │   填单流     │          │   审批流     │          │  发起流程    │
  │ form-filling │          │  approval    │          │start-process│
  │             │          │             │          │             │
  │ 01→02→03    │          │ 01→02→03    │          │ 01→02→03    │
  │ →04→05→06   │          │ →04/05→06   │          │ →04→05      │
  └──────┬──────┘          └──────┬──────┘          └──────┬──────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                    [任务完成 → 展示结果给用户]
```

**关键约束：**
- 主会话是**唯一执行者**，所有节点（公共节点 + 流程节点）都由主会话按顺序执行
- 每个节点对应一个 runbook 文件，**按节点顺序逐个读取**，执行完一个再读下一个
- 节点之间按各 runbook 文件末尾的"下一节点"声明流转，不跳节点、不并行
- 需要用户输入时，主会话直接在会话中询问并等待回复，随后从中断点继续执行

## 主会话执行顺序总览

1. **公共节点**（`runbooks/common/`）：环境检测 → 登录 → 首页意图识别与导航
2. **流程节点**（对应流程文件夹）：按流程路径逐个读取节点文件并执行
3. **结果展示**：任务完成后向用户展示结果（附固定 tips，见 `../SKILL.md`）

## 流程路径说明

进入流程节点前，主会话必须先读取 `core/` 全部文档（01-global-rules.md / 02-state-model.md / 03-error-handling.md / 04-field-handling.md / 05-commands-reference.md），然后按指定流程路径执行。

### 填单流

**流程路径：** `form-filling/01` → `02` → `03` → `04` → `05` → `06`

**起始状态：** 已在应用列表页（主会话已从首页点击"应用列表"）

**执行逻辑：** 搜索应用 → 选择应用 → 选择列表 → 填单 → 提交弹窗确认 → 站点记忆写入

**完成后必须执行站点记忆写入（`06-site-memory.md`）。**

### 审批流

**流程路径：** `approval/01` → `02` → `03` → `04`/`05` → `06`

**起始状态：** 已在待办列表页（主会话已从首页点击"待办列表"）

**执行逻辑：** 搜索/筛选待办 → 打开审批详情 → 办理/驳回/加签/终止/抄送/委托/暂存/标记 → 弹窗确认 → 选人/意见弹窗

**审批流完成后不走站点记忆。**

### 发起流程

**流程路径：** `start-process/01` → `02` → `03` → `04` → `05`

**起始状态：** 流程选择弹窗已打开（主会话已从首页点击"发起流程"）

**执行逻辑：** 搜索流程 → 选择流程 → 表单弹窗初始化 → 填单 → 选人/意见弹窗

**发起流程完成后不走站点记忆。**

## 节点与文件对照表

| 节点 | 名称 | 文件 |
|------|------|------|
| 10 | 环境检测 | `runbooks/common/10-env-detect.md` |
| 20 | 登录 | `runbooks/common/20-login.md` |
| 30 | 首页（意图识别与导航） | `runbooks/common/30-home.md` |
| — | **填单流** | `runbooks/form-filling/` |
| 01 | 应用列表页 | `runbooks/form-filling/01-app-list.md` |
| 02 | 应用详情页 | `runbooks/form-filling/02-app-detail.md` |
| 03 | 列表视图（含3分叉） | `runbooks/form-filling/03-list-view.md` |
| 04 | 表单填写页 | `runbooks/form-filling/04-form-fill.md` |
| 05 | 弹窗处理 | `runbooks/form-filling/05-popup-handle.md` |
| 06 | 站点记忆写入 | `runbooks/form-filling/06-site-memory.md` |
| — | **审批流** | `runbooks/approval/` |
| 01 | 待办列表页（含4分叉） | `runbooks/approval/01-todo-list.md` |
| 02 | 待办详情页 | `runbooks/approval/02-todo-detail.md` |
| 03 | 审批操作 | `runbooks/approval/03-approval-action.md` |
| 04 | 评论 | `runbooks/approval/04-comment.md` |
| 05 | 弹窗处理 | `runbooks/approval/05-popup-handle.md` |
| 06 | 审批后弹窗 | `runbooks/approval/06-post-action.md` |
| — | **发起流程** | `runbooks/start-process/` |
| 01 | 流程搜索 | `runbooks/start-process/01-process-search.md` |
| 02 | 流程选择 | `runbooks/start-process/02-process-select.md` |
| 03 | 表单弹窗 | `runbooks/start-process/03-process-form.md` |
| 04 | 表单填写页 | `runbooks/start-process/04-form-fill.md` |
| 05 | 发起后弹窗 | `runbooks/start-process/05-post-action.md` |

## 节点流转规范

主会话在每个节点内：

1. **读取节点文件** — 按当前节点读取对应 runbook 文件（如 `form-filling/03-list-view.md`）
2. **按操作表执行** — 根据前置条件选择操作，逐项执行
3. **确认执行结果** — 每步操作后确认得到预期结果（见 GR-08 操作后结果检测）
4. **按"下一节点"声明流转** — 读取目标节点文件继续执行；遇到"完成"则任务结束
5. **用户交互直接进行** — 需要用户输入时在会话中询问，等待回复后从当前节点继续，不中断、不重启流程

## 文档读取阶段

**本技能按阶段加载文档，不在启动时一次读完所有文件：**

### 阶段一：技能加载时

1. `../SKILL.md`（导航入口）
2. 本文（总览与流程路径）
3. `../recovery/00-resume-protocol.md`（中断恢复协议）

### 阶段二：登录成功、进入首页后（节点 30 执行前）

4. `01-global-rules.md`（全局规则 GR-01 至 GR-09）
5. `02-state-model.md`（状态变量字典）
6. `05-commands-reference.md`（指令参考手册）

### 阶段三：进入流程节点时

7. `03-error-handling.md`（故障处理矩阵，进入首个流程节点前读取）
8. `04-field-handling.md`（字段分类与处理规则，进入表单填写节点前必读）
9. `runbooks/{流程}/{编号}-*.md`（流程节点文件，按节点顺序逐个读取）

> core/ 全部文档都由主会话按需读取；runbook 节点文件随流程推进逐个加载，避免上下文膨胀。

## 运行时顺序

技能触发后，先执行 `recovery/00-resume-protocol.md` 快速定位当前节点：

- 定位到公共节点（环境检测/登录/首页）→ 读取 `runbooks/common/{编号}-*.md` 执行
- 定位到流程节点（form-filling/approval/start-process）→ 读取对应流程的节点文件，从当前节点继续执行

## 平台地址

| 环境 | URL |
|------|-----|
| 正式环境（默认） | `https://qy.do1.com.cn/qiqiao2/runtime/` |
| 测试环境 | `https://qiqiao-tcb-qa.qiweioa.com.cn/qiqiao2/runtime/` |

域名由 `core/02-state-model.md` 中 `PLATFORM_DOMAIN` 变量控制。
