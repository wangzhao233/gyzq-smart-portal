# 全局规则（唯一权威）

> **读取阶段：** 阶段二（主会话登录后、进入节点 30 前）
>
> 本文定义「跨节点成立」的规则，对主会话执行的所有节点均生效。
> 节点内仅引用，不重复展开同义正文。引用格式：`见 core/01-global-rules.md GR-XX`。

## GR-01 执行纪律

1. **严格按节点执行** — 先定位你在哪个节点，再看该节点支持什么操作。**禁止**跳过节点、发明文档中没有的操作。
2. **每步必须有结果** — 执行完一个操作后，必须确认得到了预期结果（成功/失败），才能决定下一步。**禁止**"假装执行"。
3. **检测顺序命中即停** — 快速定位时按编号依次检查，第一个命中就停止，**禁止**把所有检测项都跑一遍。
4. **文件路径统一** — 本技能涉及的所有文件路径**必须**使用以下写法：
   - 站点记忆：`~/browser-data/site-memory.json`
   - **禁止**自行转换路径，直接使用 `~/browser-data/` 前缀
5. **环境检测方式** — 检查 `bsk` CLI 是否可用，用 Bash 执行 `which bsk`。若不存在则引导安装 browser-skill。
6. **引导用户操作的步骤必须完整展示在回复中** — 引导安装扩展、设置 Chrome 标志、运行命令、复制粘贴密钥等场景，**必须把完整步骤直接展示给用户**（加粗标记关键步骤），不能只写在思考/工具调用里然后回一句"请安装"或"请按提示操作"。详见 `runbooks/common/10-env-detect.md`。
7. **`$ai` 不可用时立即执行 `window.$ai.init()`** — 在填单流程中，如果发现 `$ai` 不可用（如 `window.$ai.findDom` 报错、`$ai` 对象不存在、`getFormFields` 返回异常），**必须先执行 `window.$ai.init()`**，然后重试操作。不要跳过初始化步骤。
   - ⚠️ **登录场景（节点 20）例外：** `$ai` 不可用说明用户还未登录，应提示手动登录，无需执行 `window.$ai.init()`。
8. **涉及表单字段修改的操作必须走填单节点** — 应用列表编辑数据行、待办列表审批中修改表单内容等所有涉及表单字段增删改的场景，**必须先进入填单节点（表单填写页）** 获取字段、修改值、提交，再回到原节点继续。**禁止**跳过填单节点直接在列表或审批详情页执行字段修改。
9. **获取列表/待办数据必须用最新快照** — 用户要求查看应用列表数据、待办列表数据时，**必须用 `bsk snapshot` 获取最新实时快照**，禁止使用此前会话中缓存的上下文数据（如之前工具调用输出中残留的快照文本）。每次数据查询请求都重新 snapshot，确保数据实时准确。

## GR-02 交互方式：bsk snapshot 优先，window.$ai.fillingForm 辅助

### 定位与交互原则

- **语义定位（优先）→ `window.$ai.findDom('文本')`**：按文本内容查找元素，自动处理 Vue 组件事件冒泡。适用于导航文字、按钮、列表项、树形菜单等场景
- **精确点击（降级）→ `bsk snapshot` + `bsk click @eN`**：当 `window.$ai.findDom` 找不到目标时，用 snapshot 获取 ref 后点击
- **表单字段获取 → 用 `window.$ai.getFormFields()`（首选），`findDom({action:'filling'})[0]` 供 `__qiqiaoFormAPI` 使用**：`bsk snapshot` 输出会截断（长表单后面字段看不到），必须优先用 `$ai` API 获取完整字段列表。两者均无返回数据时才降级 `bsk snapshot`
- **表单普通字段批量填充 → 用 `window.$ai.fillingForm`**：获取字段列表后批量填充，快速准确
- **弹窗、复杂交互 → 用 bsk snapshot 识别**：dialog 弹窗中的按钮通过 snapshot 定位后 `bsk click @eN`
- **禁止**直接用 `bsk evaluate` 执行任意 JS 来绕过交互（如直接设 input.value），需通过 bsk CLI 标准命令操作
- 若 `window.$ai.findDom` 和 `bsk snapshot` 都无法定位目标，**直接询问用户**

> **关于 bsk snapshot 截断：** `bsk snapshot` 的输出有大小限制（会显示 `[truncated ... bytes]`），对话框/表单内容太长时只显示开头部分。**获取字段列表必须优先用 `window.$ai.getFormFields()`，不可用 snapshot 的输出来判断有哪些字段。** snapshot 仅用于验证页面状态、定位按钮位置，以及 API 均无返回数据时的兜底。
>
> **关于 Element UI 树形菜单（el-tree）：** 点击树节点时，`window.$ai.findDom('列表名')` 优先使用，它内部已处理 Vue 组件的事件冒泡。不要用 `querySelectorAll('[class*="tree"]')` 等通用选择器——它们会点到外层容器，事件无法冒泡到 Vue 组件，点击后页面无变化。降级时用 `bsk snapshot` 找到文本节点 @eN 再点击。

### $ai API 速查（仅填单场景使用）

| API | 用途 | 返回值 |
|-----|------|--------|
| `window.$ai.init()` | 初始化（弹窗后调用） | `undefined` 表示成功 |
| `window.$ai.getFormFields()` | ⭐ **获取所有字段信息（填单/发起流程/审批弹窗通用，首选）** | 字段数组 |
| `window.$ai.findDom({action:'filling'})[0]` | 获取表单容器元素，供 `__qiqiaoFormAPI` 函数使用 | 元素引用 |
| `element.__qiqiaoFormAPI.getFormInfoData().fields` | Vue API，降级获取完整字段信息 | 字段数组（含 type/subForms/title 等） |
| `window.$ai.fillingForm(element, data)` | 自动填充普通字段 | `true` 表示成功。支持：**普通字段**、**人员单选/多选**（传姓名）、**部门单选/多选**（传部门名）、**子表字段**、**在线链接上传字段**、**外键值（fieldValue）**。<br><br>**⚠️ 严重警告：禁止用于子表关联、多表关联！** 这两类字段必须通过弹窗 checkbox 选择，`fillingForm` 填充会破坏关联关系，导致最严重的数据错误。<br><br>子表：`{ "子表名": [{ "列1": "值1" }] }`<br>人员/部门：字符串=单选，数组=多选 |
| `window.$ai.getMetadata(element)` | 获取元素的 AI 元数据（仅字段对比时用） | `{ name, desc, id, action, ... }` |
| `window.$ai.findDom({id:'__canEdit'})` | 按元数据 id 定位（行操作按钮） | 返回匹配元素数组。索引 0=第1行 |

**行操作按钮元数据 id 对照表：**

| 场景 | 按钮 | id | type | 定位方式 |
|------|------|-----|------|---------|
| 列表行 | 详情 | `按钮id` | `detailbtn` | `window.$ai.findDom({type:'detailbtn'})[N]` |
| 列表行 | 编辑 | `按钮id` | `editbtn` | `window.$ai.findDom({type:'editbtn'})[N]` |
| 关联表行 | 查看 | `__canViewForm` | `formDetail` | `window.$ai.findDom({id:'__canViewForm'})[N]` |
| 关联表行 | 编辑 | `__canEdit` | `formEdit` | `window.$ai.findDom({id:'__canEdit'})[N]` |
| 关联表行 | 更多操作 | `more` | `null` | `window.$ai.findDom({id:'more'})[N]` |
| 关联表行 | 删除 | `__canDel` | `formDel` | `window.$ai.findDom({id:'__canDel'})[N]` |
| 关联表行 | 复制 | `__canCopy` | `formCopy` | `window.$ai.findDom({id:'__canCopy'})[N]` |

> 操作第 N 行（从 0 开始）：`window.$ai.findDom({type:'detailbtn'})[N]?.click()`。找不到时降级用 `bsk snapshot` + `@eN`。
>
> ⚠️ **意图约束**：`detailbtn`（type 为 `detailbtn`）只能用于"查看/详情"场景，`editbtn`（type 为 `editbtn`）只能用于"编辑/修改"场景。禁止混用。

> ⚠️ **`window.$ai.findDom('文本')` 优先用于语义定位**（导航文字、按钮、树形菜单项等），失败后降级用 `bsk snapshot` 的 `@eN` ref。`window.$ai.findDom({ action: 'filling' })` 专门用于获取表单元素引用传给 `fillingForm`。

### bsk evaluate 引号安全规则

所有 `bsk evaluate` 命令**必须**根据 JS 代码内容选择合适的 shell 引号，避免 bash 变量展开导致代码错误：

| JS 代码特征 | 引号选择 | 示例 |
|-------------|---------|------|
| 含 `$`（如 `$ai`、`${}`） | **一律单引号** `'...'` | `bsk evaluate 'window.$ai.init()'` |
| 不含 `$` | 双引号或单引号均可 | `bsk evaluate "document.querySelector(...)"` |
| 含 `$` 且内层有单引号 | **外层单引号，内层双引号** | `bsk evaluate 'window.$ai.findDom("应用列表")[0].click()'` |

**⚠️ 典型错误：** `bsk evaluate "window.$ai.init()"` 在 Git Bash/Linux/macOS 中 `$ai` 会被展开为空字符串，实际执行变成 `bsk evaluate "window."` → SyntaxError。**正确写法：** `bsk evaluate 'window.$ai.init()'`。

## GR-03 多结果处理

当搜索、匹配到多个结果时：

- **多条匹配**：将 `bsk snapshot` 看到的文本内容展示给用户，让用户确认选择。**禁止**默认选第一个或自行猜测。
- **无匹配**：告知用户未找到，询问是否换关键词重试。**禁止**自行尝试其他关键词探测。
- **文本内容完全相同**：直接全部操作，无需询问。

## GR-04 数据安全

### GR-04-0 关键停检点

每次准备填值之前，先问自己：用户给具体值了吗？

- **没给** → 不能填，必须先问
- **给了** → 用用户给的值填

### GR-04 具体规则
1. **严禁在未征得用户同意的情况下自行构造数据填单**
2. **严禁未经用户确认自动提交表单** — 填单完成后必须展示已填字段值让用户核对，用户确认后才能提交
3. **严禁未经用户确认自动删除数据** — 删除前必须展示即将删除的数据让用户确认，用户确认后才能点击删除
4. **用户未提供字段值时，必须返回字段列表并询问**，由用户决定填什么值。**禁止**自行编造值填入
5. **搜索结果多条或零条时，必须让用户确认/换词** — 禁止自行探索或猜测
6. **用户没说"全部"或"都处理"时，禁止自行批量操作** — 必须逐条让用户确认
7. **需跳转到外部链接或执行高危操作（终止/驳回）前必须告知用户并取得确认**

## GR-05 日期时间格式

表单中所有日期、时间、日期时间字段，**必须使用以下格式**：

| 类型 | 正确格式 | 错误格式 |
|------|---------|---------|
| 日期时间 | `2026-05-28 11:00:25` | `2026.05.28 11:00:25` |
| 日期 | `2026-05-28` | `2026.05.28`、`2026/05/28` |
| 时间 | `11:00` | `11：00` |
| 年月 | `2026-05` | `2026.05` |

**规则：** 日期分隔符用 `-`（短横线），时间分隔符用 `:`（英文冒号）。**禁止**使用 `.`（点号）、`/`（斜杠）、`：`（中文冒号）。

填充前需检查文档中提取的日期时间值，自动转换为正确格式后再传入 `fillingForm`。

## GR-06 导航安全

- 所有页面跳转（`bsk navigate`）**仅限当前 `PLATFORM_DOMAIN` 域名内**（见 `core/02-state-model.md`），即 URL 必须包含 `/runtime/` 路径
- **严禁跳转到平台外 URL** — 如果遇到非当前 `PLATFORM_DOMAIN` 域名的链接或弹窗，立即停止导航并告知用户
- 页面中出现外部链接（广告、第三方推广、未知重定向）时，**禁止点击**，除非用户明确要求

## GR-07 子表处理规则

### 子表列名获取

通过 Vue 内部 API 获取所有字段数据，从中提取子表及其列名：

```js
const inputs = elementData.__qiqiaoFormAPI.getFormInfoData().fields;
// 筛选 type === "subform" 的字段（即子表）
const subForms = inputs.filter(f => f.type === 'subform');
// 对每个子表，从 subForms 字段中筛选 permission === "MODIFY" 的列，提取 title
subForms.forEach(sf => {
  const columns = sf.subForms
    .filter(col => col.permission === 'MODIFY')
    .map(col => col.title);
  // columns 即为该子表的可填写列名数组
  // 例：["公司名称", "职位名称", "入职时间", "离职时间", "工作内容"]
});
```

> ⚠️ **禁止用"添加一行"方式获取列名**——会创建空白行污染表单。
> ⚠️ 如果 Vue API 获取失败，询问用户该子表有哪些列。

### 子表数据格式

`fillingForm` 的 data 参数中子表字段的值必须为**对象数组**：

```js
{
  "普通字段": "值",
  "子表字段名": [
    { "列1": "值1", "列2": "值2" },  // 第1行
    { "列1": "值3", "列2": "值4" }   // 第2行（可多条）
  ]
}
```

### 子表行为约束

1. **追加行，不更新**：对子表调用 `fillingForm` 会新增行，不会匹配或覆盖已有行。**禁止对同一子表重复调用 `fillingForm`**，否则会产生重复行。
### 文档提取子表数据

| 文档内容 | 处理方式 |
|----------|---------|
| 结构化表格/分节 | 按行解析为子表数组 |
| 连续文本 | 尝试识别时间线/公司名等分隔模式，拆分为多条记录 |
| 无法解析 | 标记为"需要手动补充"，告知用户 |

## GR-08 操作后结果检测

点击提交、办理、驳回、导出等操作按钮后，页面可能不会立即变化，但短暂（约 3 秒）的提示消息或接口报错可反映结果。

**所有按钮点击后必须执行以下检测流程：**

1. **点 击** → `bsk click @eN`
2. **2秒后** → `bsk snapshot` — 捕捉短提示（约 3 秒消失的 toast 消息）
3. **5秒后** → `bsk snapshot` — 再次检查页面状态变化
4. **页面无变化** → 用 `bsk evaluate` 查看最近一次接口请求的返回值：
   ```
   bsk evaluate →
     const entries = performance.getEntriesByType('resource')
       .filter(e => e.initiatorType === 'fetch' || e.initiatorType === 'xmlhttprequest');
     const last = entries[entries.length - 1];
     last ? { url: last.name, status: last.responseStatus } : 'no request'
   ```
5. **接口返回错误** → 提取错误信息告知用户
6. **接口无日志或返回正常** → 询问用户手动确认当前页面状态

> 适用于：提交表单、审批办理/驳回/终止、导出按钮、导入确认等所有需要等待结果的操作。
> 提示消息只停留 3 秒左右消失，`bsk snapshot` 不一定能截到，**不能仅靠一次 snapshot 判断操作失败**。

## GR-09 站点记忆写入（必做）

用户任务完成后（填单提交后、导出下载后、查看/编辑/删除操作完成后），**必须立即写入站点记忆**，不等用户提醒。

写入规范详见 `runbooks/form-filling/06-site-memory.md`。数据结构详见 `references/site-memory-template.md`。

## GR-10 流程完成判定

以下任一场景达成即视为一次任务完成，主会话向用户展示结果（附固定 tips），随后可等待用户下达新指令：

- 完整填单并提交成功
- 查看应用列表数据并返回给用户
- 查看审批待办列表数据并返回给用户
- 审批待办详情内容修改并完成按钮操作
- 审批待办详情完成一次评论并发送

任务完成后如需执行新任务，重新从 `recovery/00-resume-protocol.md` 开始定位节点。
