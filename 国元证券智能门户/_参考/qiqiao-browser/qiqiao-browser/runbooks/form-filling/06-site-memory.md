# 填单流 06：站点记忆写入（必做）

> ⚠️ 完成后读取 `core/06-discipline-check.md`。

## 你在哪里

用户的一项操作任务已完成（填单提交、导出下载、删除数据、查看/编辑等）。现在需要将当前页面路径缓存起来，下次可以快速直达。

## 本节点产出

- `~/browser-data/site-memory.json` 的 `entries` 数组中新增了一条记录

## 可执行操作

| # | 操作名 | 说明 |
|---|--------|------|
| 1 | 获取当前页面 URL | 用 `bsk evaluate` 获取 `window.location.href` |
| 2 | 读取站点记忆文件 | 读取 `~/browser-data/site-memory.json` |
| 3 | 追加新记录 | 在 `entries` 数组末尾追加一条 |
| 4 | 保存文件 | 写回 `site-memory.json` |

> **这是必做步骤，不是可选的。** 用户任务完成后**必须立即执行**，不等用户提醒。

### 操作 1：获取当前页面 URL

```js
// 通过 bsk evaluate 执行
window.location.href
```

### 操作 2：读取站点记忆文件

读取 `~/browser-data/site-memory.json`。

- 文件存在 → 读取 `entries` 数组
- 文件不存在 → 创建空结构 `{"entries":[]}`

> ⚠️ 文件路径：`~/browser-data/site-memory.json`。**禁止**自行转换路径。

### 操作 3：追加新记录

在 `entries` 数组末尾追加一条：

```json
{
  "appName": "应用名称（01-app-list.md 确定的 APP_NAME）",
  "listName": "列表名称（02-app-detail.md 确定的 LIST_NAME）",
  "url": "操作 1 获取到的 URL",
  "runtime": "pc",
  "verifiedAt": "今天的日期（YYYY-MM-DD 格式）"
}
```

**字段说明：**

| 字段 | 来源 | 说明 |
|------|------|------|
| `appName` | `01-app-list.md` 选择应用时确定 | 应用名称 |
| `listName` | `02-app-detail.md` 选择列表时确定 | 列表名称 |
| `url` | 操作 1 获取 | 当前页面完整 URL |
| `runtime` | 固定值 | PC 端为 `"pc"` |
| `verifiedAt` | 当前日期 | `YYYY-MM-DD` 格式，如 `"2026-06-16"` |

**结构特点：** 扁平数组，相同应用的不同列表是独立条目，直接追加到数组末尾，不需要分组。

### 操作 4：保存文件

将更新后的 `entries` 数组写回 `~/browser-data/site-memory.json`。

### 完整数据结构示例

```json
{
  "entries": [
    {
      "appName": "请假应用",
      "listName": "请假列表",
      "url": "{PLATFORM_DOMAIN}/qiqiao2/runtime/#/index/app/list/...",
      "runtime": "pc",
      "verifiedAt": "2026-06-16"
    }
  ]
}
```

> 完整数据结构规范见 `references/site-memory-template.md`。

## 写入时机

以下情况完成后**必须**执行本节点：

- ✅ 填单提交成功后
- ✅ 导出下载完成后
- ✅ 查看/编辑/删除操作完成后
- ✅ 任何列表操作完成后

## 操作失败处理

| 失败场景 | 处理方式 |
|----------|---------|
| 文件读取失败 | 创建新文件 `{"entries":[]}`，重新追加 |
| APP_NAME / LIST_NAME 不确定 | 回溯 `01-app-list.md` / `02-app-detail.md` 的选择结果；若无法确定则跳过本次写入 |
| URL 获取失败 | 用 `bsk snapshot` 检查页面，重新获取 |

## 完成标志

本节点执行完毕 = 用户的本次任务全部完成。可以告知用户操作已完成，等待下一次指令。

## 下一节点

无。本节点是任务的终点。等待用户下达新的指令后，重新从 `recovery/00-resume-protocol.md` 开始定位节点。
