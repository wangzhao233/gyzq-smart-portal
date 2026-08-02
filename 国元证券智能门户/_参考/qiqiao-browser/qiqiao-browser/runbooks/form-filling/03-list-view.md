# 填单流 03：列表视图

> ⚠️ 查询列表数据后，读取 `core/06-discipline-check.md`。

## 你在哪里

已在 `02-app-detail.md` 中选择列表，进入了数据列表页面。页面上有添加、删除、导入、导出等操作按钮，以及每行的详情/编辑按钮。

## 本节点分叉

本节点有 **3 个分叉**：

| 分叉 | 场景 | 涉及操作 | 去向 |
|------|------|---------|------|
| **A — 查看列表数据** | 用户想看当前列表有哪些数据 | 搜索/浏览 snapshot → 展示结果 | 留本节点 |
| **B — 列表操作按钮** | 删除/导出/导入（非填单操作） | 操作 2/3/4 | `05-popup-handle.md` |
| **C — 添加/编辑/详情** | 打开填单弹窗，走填单节点 | 操作 1/5/6 | `04-form-fill.md` |

---

## 本节点产出

- 完成了用户要求的列表操作，或导航到了填单节点

## 可执行操作

> ⚠️ 数据查询规则（GR-01-9）：查看列表数据必须用 `bsk snapshot` 获取最新快照，禁止使用缓存上下文。

| # | 操作名 | 分叉 | 执行方式 | 下一节点 |
|---|--------|------|---------|---------|
| 1 | 新增填单 | **C** | `bsk snapshot` → `bsk click @eN "添加"` | → `04-form-fill.md` |
| 2 | 删除数据 | **B** | `bsk snapshot` 展示数据 → 勾选 → `bsk click @eN` | → `05-popup-handle.md` |
| 3 | 导出数据 | **B** | `bsk click @eN` → 下拉菜单选类型 → 弹窗 → 下载 | → `05-popup-handle.md` |
| 4 | 导入数据 | **B** | `bsk click @eN` → 导入弹窗 | → `05-popup-handle.md` |
| 5 | 查看详情 | **C** | `window.$ai.findDom({type:'detailbtn'})` + 行索引 | → `04-form-fill.md`（只读） |
| 6 | 编辑数据 | **C** | `window.$ai.findDom({type:'editbtn'})` + 行索引 | → `04-form-fill.md`（编辑） |
| 7 | 返回应用详情 | **A** | 面包屑导航或 `bsk navigate` 重导航 | → `02-app-detail.md` |
| 8 | 返回首页 | **A** | `bsk navigate` 回首页 | → `../common/30-home.md`（节点 30） |

> 所有按钮操作：先 `bsk snapshot` 查看列表页，找到目标按钮的 @eN ref，然后 `bsk click @eN` 点击。

### 操作 5/6：查看详情 / 编辑数据行

> ⚠️ **意图约束：用户说"查看/看详情/打开详情" → 用 `detailbtn`；用户说"编辑/修改/更新" → 用 `editbtn`。禁止混淆两者。**

每行数据有「详情」和「编辑」两个独立按钮，必须在定位按钮时明确区分：

**方式一（优先）：`window.$ai.findDom` 按 type 定位**

```
// 查看第 1 行详情
bsk evaluate → window.$ai.findDom({type:'detailbtn'})[0]?.click();

// 编辑第 2 行数据
bsk evaluate → window.$ai.findDom({type:'editbtn'})[1]?.click();
```

> `window.$ai.findDom({type:'detailbtn'})` 返回所有行详情按钮的数组，索引 0=第1行，1=第2行…
> `window.$ai.findDom({type:'editbtn'})` 同理匹配编辑按钮。

**方式二（降级）：`bsk snapshot` + `bsk click @eN`**

```
bsk snapshot → 找到第 N 行的「详情」或「编辑」按钮的 @eN → bsk click @eN
```

**行操作结果去向：**

| 操作 | 下一节点 |
|------|---------|
| 详情 | → `04-form-fill.md`（只读查看，不执行 fillingForm）→ 关闭返回列表 |
| 编辑 | → **`04-form-fill.md`（修改表单字段）** → 修改后提交/保存 → 回列表 |

> ⚠️ **涉及表单字段增删改的操作，必须先走 `04-form-fill.md` 获取字段、修改值、提交。禁止跳过。**（见 GR-01-8）

### 操作 1：新增填单

`bsk click @eN "添加"` → 打开表单填写页 → **`04-form-fill.md`**。

表单打开后先滚动到底部加载全部字段，再初始化并进入填单流程。详见 `04-form-fill.md` 操作 1。

### 操作 2：删除数据

> ⚠️ **数据安全：** 删除前必须展示即将删除的数据让用户确认。**严禁自动删除**。

1. `bsk snapshot` 获取列表数据，展示给用户确认要删除的数据
2. **勾选目标数据行 checkbox：**
   - ⚠️ **点击行不会选中复选框，必须精准点击 checkbox 元素**
   - 先用 `bsk snapshot` 找到目标行对应的 checkbox 的 @eN ref
   - 再用 `bsk click @eN` 精准点击该 checkbox
   - ⚠️ **禁止**用 `querySelector('input[type=checkbox]')`，会命中表头全选框
3. `bsk click @eN "删除"` → 弹出确认弹窗
4. 确认弹窗内容：「确定删除X条数据吗？若存在关联的流程数据将一并被删除，删除的数据不可恢复。」
5. `bsk click @eN "取消"` 或 `bsk click @eN "删除"` → **`05-popup-handle.md`**

### 操作 3：导出数据

导出是**下拉菜单 + 选择弹窗**组合流程：

1. `bsk click @eN "导出"` → 弹出**下拉菜单**（不是直接确认）
2. `bsk snapshot` 查看下拉菜单，通常有 2 个选项：
   - **导出明细内容** — 含全部字段的详细导出
   - **导出图片/附件** — 仅图片/附件导出
3. 选择一项后弹出「选择导出字段」弹窗（两类都走此弹窗）
4. `bsk click @eN "确 定"` → 触发后台导出任务
5. 等待下载提示出现后下载：
   ```
   bsk evaluate → window.$ai.findDom({type:'downloadExport'}).forEach(btn => btn.click())
   ```

### 操作 4：导入数据

`bsk click @eN "导入"` → 弹出「导入」弹窗：
- **导入类型**（radio）：仅新增数据 / 仅更新数据 / 新增和更新数据
- **导入匹配**（radio）：姓名 / 账号 / 工号
- **选择数据**：文件选择区域（上传 Excel/CSV 文件）

选择文件 + 配置导入规则后确认触发导入 → **`05-popup-handle.md`**。

## 操作失败处理

| 失败场景 | 处理方式 | 回退 |
|----------|---------|------|
| 找不到目标按钮 | `bsk snapshot` 检查页面；`bsk evaluate` 尝试 `window.$ai.findDom({type:'btn类型'})` | 留本节点 |
| 导出后未下载 | 等待下载提示出现后，用 `window.$ai.findDom({type:'downloadExport'})` | 留本节点 |
| 导入弹窗无标准按钮 | 用 Close 图标关闭 | 留本节点 |

## 操作完成后的必做步骤

**无论执行了哪个操作，完成后都必须执行站点记忆写入（`06-site-memory.md`）。** 这是必做步骤，不是可选的。

## 下一节点

分叉 A（查看数据）→ 留本节点或返回上级
分叉 B（操作 2/3/4）→ **`05-popup-handle.md`（弹窗处理）**
分叉 C（操作 1/5/6）→ **`04-form-fill.md`（表单填写页）**
返回 → **`02-app-detail.md`** 或 **`../common/30-home.md`（节点 30：首页）**
