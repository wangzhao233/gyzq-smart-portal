# 填单流 02：应用详情页

## 你在哪里

已在 `01-app-list.md` 中选择了应用，进入该应用内部。左侧展示该应用的列表树形菜单（Element UI el-tree 组件）。你可以选择一个列表进入。

## 本节点产出

- 找到并点击了目标列表，进入了列表视图

## 可执行操作

| # | 操作名 | 前置条件 | 执行方式 | 下一节点 |
|---|--------|---------|---------|---------|
| 1 | 选择列表 | 用户指定了列表名 | 优先 `window.$ai.findDom`，失败则 `bsk snapshot` + `bsk click @eN` | → `03-list-view.md` |
| 2 | 确认后选择列表 | 搜索到多个匹配列表 | 展示让用户确认 | 确认后 → `03-list-view.md` |
| 3 | 返回应用列表 | 用户想换应用 | 点击返回或 `bsk navigate` | → `01-app-list.md` |
| 4 | 返回首页 | 用户想回到起点 | `bsk navigate` 回首页 | → `../common/30-home.md`（节点 30） |

### 操作 1：选择列表

**点击树形菜单优先用 `window.$ai.findDom`，不行再用 `@eN`：**

**方式一（优先）：`window.$ai.findDom`**

```
bsk evaluate → window.$ai.findDom('列表关键词')[0]?.click()
```

- **无结果**：提示用户没有找到该列表
- **唯一结果**：直接点击（`window.$ai.findDom` 内部已处理 Vue 组件事件冒泡）
- **多个结果**：进入操作 2

**方式二（降级）：`bsk snapshot → bsk click @eN`**

```
bsk snapshot → 找列表名的 @eN (通常是 StaticText)
bsk click @eN
```

> ⚠️ **关键：树形菜单的精准点击方式**
>
> Element UI 的 `el-tree` 组件中，事件绑定在 `el-tree-node__content` 内部的文本节点上，
> **不能**用 `querySelectorAll('[class*="treeitem"], li, [class*="tree"]')` 这类通用选择器——
> 它们会点到组件的外层容器，事件不会正确冒泡到 Vue 组件，导致 `bsk click` 返回成功但页面无变化。
>
> 正确做法：找到 `el-tree-node__content` 内部的文本节点触发点击。

### 操作 2：多个结果 — 用户确认

> ⚠️ **数据安全：** 匹配到多条数据时，必须让用户确认，**禁止**自行猜测。

```
bsk evaluate →
  const refs = window.$ai.findDom('列表关键词');
  refs.map(ref => window.$ai.getMetadata(ref));  // 展示 name/desc/id 给用户选择
```

**禁止**默认选第一个。用户确认后点击对应项。

### 操作 3：返回应用列表

```
bsk navigate "{PLATFORM_DOMAIN}/qiqiao2/runtime/"
→ 节点 30（首页）→ 重新进入 01-app-list.md
```

### 操作 4：返回首页

```
bsk navigate "{PLATFORM_DOMAIN}/qiqiao2/runtime/"
```

## 操作失败处理

| 失败场景 | 处理方式 | 回退 |
|----------|---------|------|
| 找不到目标列表 | 询问列表的准确名称 | 留本节点 |
| `window.$ai.findDom` 找到但点击无效 | 降级用 `bsk snapshot` + `@eN` 点击（确保点到内层文本节点） | 留本节点 |
| `bsk click @eN` 返回成功但页面无变化 | 可能点到外层容器，用 `bsk evaluate` 定位 `el-tree-node__content` 内文本来点击 | 留本节点 |

## 下一节点

操作 1/2 成功 → **`03-list-view.md`（列表视图）**
操作 3 → **`01-app-list.md`（应用列表页）**
操作 4 → **`../common/30-home.md`（节点 30：首页）**
