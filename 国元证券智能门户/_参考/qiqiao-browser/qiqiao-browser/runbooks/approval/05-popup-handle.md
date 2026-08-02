# 审批流 05：弹窗处理

## 你在哪里

页面上出现了弹窗。弹窗可能是：提交确认、删除确认、导出确认、导入选择、下载提示等。你需要根据弹窗类型执行确认或取消操作。

## 本节点产出

- 弹窗已正确处理（确认/取消/下载）

## 可执行操作

| # | 操作名 | 弹窗类型 | 执行方式 | 下一节点 |
|---|--------|---------|---------|---------|
| 1 | 确认 | 提交确认 / 删除确认 / 导出确认 / 导入确认 | `bsk snapshot` 找 `@eN "确 定"`，找不到则 `window.$ai.findDom({type:'confirmbtn'})` | 视来源节点 |
| 2 | 取消 | 任何弹窗 | `bsk snapshot` 找 `@eN "取 消"`，找不到则 `window.$ai.findDom({type:'cancelbtn'})` | 视来源节点 |
| 3 | 下载文件 | 导出确认后的下载提示 | `bsk evaluate` → `window.$ai.findDom({type:'downloadExport'})` | → 完成（审批流不走站点记忆） |

### 弹窗按钮规则

优先用 `bsk snapshot` 查找弹窗中的按钮（通过文字匹配 `"确 定"`、`"取 消"`），找不到时降级使用 `window.$ai.findDom({type:'confirmbtn'})` 备用。

> 弹窗按钮**不优先用文字搜索**是因为 `window.$ai.findDom` 的 type 参数更可靠，不易受页面文字变化影响。

```
确定：bsk evaluate → window.$ai.findDom({ type: 'confirmbtn' })[0].click()
取消：bsk evaluate → window.$ai.findDom({ type: 'cancelbtn' })[0].click()
```

### 操作 1：确认

> ⚠️ **数据安全：** 如果是删除确认弹窗，**必须**已在待办列表（`01-todo-list.md`）中让用户确认过即将删除的数据。如果还没确认过，回到 `01-todo-list.md`。

**特殊情况：同名按钮** — 如果 `confirmbtn` 返回 2 个元数据完全相同的按钮，只点击第一个可能无效，需要两个都点击：

```
bsk evaluate → 
  const btns = window.$ai.findDom({type:'confirmbtn'});
  btns.forEach(btn => btn.click());
```

### 操作 2：取消

```
bsk evaluate → window.$ai.findDom({ type: 'cancelbtn' })[0].click()
```

### 操作 3：下载文件（导出场景专用）

导出流程：`01-todo-list.md` 点击导出按钮 → 本节点确认弹窗 → **等待下载提示出现** → 下载

> ⚠️ 确认弹窗点击后不会立即出现下载提示，需等待一段加载时间。

```
bsk evaluate → 
  // 确认弹窗后等待下载提示出现
  window.$ai.findDom({type:'downloadExport'}).forEach(btn => btn.click());
```

### 各来源场景的弹窗处理

| 来源节点 | 触发操作 | 弹窗类型 | 确认后去向 |
|----------|---------|---------|-----------|
| `01-todo-list.md` | 批量处理/批量转交 | 批量操作确认 | 完成 |
| `03-approval-action.md` | 办理/驳回 | 审批确认 | → `06-post-action.md` |
| `03-approval-action.md` | 终止 | 审批确认 | 完成 |
| `03-approval-action.md` | 加签/抄送/委托 | 审批操作弹窗 | → `06-post-action.md` |

## 操作失败处理

| 失败场景 | 处理方式 | 回退 |
|----------|---------|------|
| 文字搜索找到按钮但点击无效 | 弹窗按钮必须用 type 参数，不要用文字搜索 | 用 type 重试 |
| 同名 confirmbtn 只点一个无效 | 两个都点击 | `forEach(btn => btn.click())` |
| 导出确认后未出现下载提示 | 等待更长时间；`bsk snapshot` 检查页面状态 | 留本节点 |

## 下一节点

弹窗处理完成：
- 审批流来源 — 办理/驳回/加签/抄送/委托 → **`06-post-action.md`（选人/意见弹窗）**
- 审批流来源 — 终止 → **完成**
- 批量操作来源 → **完成**
