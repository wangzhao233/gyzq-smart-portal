# 审批流 02：待办详情页

## 你在哪里

已在 `01-todo-list.md` 中点击待办条目，打开了流程审批详情弹窗。你可以看到表单内容、审批操作按钮、审批意见区、流转明细等。

## 本节点分叉

从待办详情页出发，有 **3 个去向**：

| 去向 | 场景 | 目标节点 |
|------|------|---------|
| **编辑表单** | 用户要修改表单字段（调整金额/内容等） | 修改后留本节点或继续审批 |
| **审批操作** | 用户要办理/驳回/加签/终止等 | `03-approval-action.md` |
| **评论操作** | 用户要发送评论 | `04-comment.md` |

---

## 查看表单数据（只读）

**第一步：滚动待办详情到底部，加载全部字段（必做）**

打开待办详情弹窗后，必须先将内容滚动到底部，触发延迟渲染的字段全部加载。

```
bsk evaluate "document.querySelector('.workflow_layout_inner.no_scroll').scrollTo({ top: document.querySelector('.workflow_layout_inner.no_scroll').scrollHeight, behavior: 'smooth' })"
```

> 滚动容器为 `.workflow_layout_inner.no_scroll`。

**第二步：获取字段和表单元素**

```
bsk evaluate → window.$ai.getFormFields() → 字段列表
bsk evaluate → window.$ai.findDom({action:'filling'})[0] → elementData（供 __qiqiaoFormAPI 使用）
```

如果上述两个 API 均无返回数据 → 降级用 `bsk snapshot`。

获取字段后**只读展示**给用户，不执行 `fillingForm`。

---

## 编辑表单字段（分叉 B）

> ⚠️ **涉及表单字段增删改的操作，必须获取字段、修改值、提交。禁止跳过。**

### 获取可编辑字段

**第一步：滚动到底部（同查看表单数据）**

```
bsk evaluate "document.querySelector('.workflow_layout_inner.no_scroll').scrollTo({ top: document.querySelector('.workflow_layout_inner.no_scroll').scrollHeight, behavior: 'smooth' })"
```

**第二步：获取表单元素和字段**

```
bsk evaluate → window.$ai.getFormFields() → 字段列表
bsk evaluate → window.$ai.findDom({action:'filling'})[0] → elementData（供 __qiqiaoFormAPI 使用）
```

### 修改字段值并保存

参考 `core/04-field-handling.md` 中的字段分类（A~E），使用 `window.$ai.fillingForm` 填充。
修改后点击保存按钮提交。

> ⚠️ **必须读取 `core/04-field-handling.md`，不可跳过。**

---

## 查看审批意见及流转明细

| 查看内容 | 操作 |
|---------|------|
| 审批意见及评论 | Tab 默认为此页，可直接查看 |
| 流转明细 | `bsk click @eN "流转明细"` 切换 Tab |
| 流程图 | 查找流程图按钮/链接并点击 |

---

## 关闭详情

`bsk click @eN` 关闭按钮 或 `bsk evaluate → i.iconclose?.click()` → **`01-todo-list.md`**

## 下一节点

编辑表单 → 修改保存后留本节点（或继续进入 `03-approval-action.md`）
审批操作 → **`03-approval-action.md`（审批操作）**
评论操作 → **`04-comment.md`（评论）**
关闭详情 → **`01-todo-list.md`（待办列表页）**
