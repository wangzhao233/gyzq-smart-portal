# 七巧平台站点记忆模板

此文件存储用户访问过的应用和列表，后续可直接跳转到列表页面，省去搜索和导航步骤。

## 存储位置

`~/browser-data/site-memory.json`

## 数据结构

```json
{
  "entries": [
    {
      "appName": "请假应用",
      "listName": "请假列表",
      "url": "{PLATFORM_DOMAIN}/qiqiao2/runtime/#/index/...",
      "verifiedAt": "2026-04-30"
    },
    {
      "appName": "请假应用",
      "listName": "审批列表",
      "url": "{PLATFORM_DOMAIN}/qiqiao2/runtime/#/index/...",
      "verifiedAt": "2026-04-30"
    }
  ]
}
```

## 字段说明

| 字段 | 说明 |
|------|------|
| `appName` | 应用名称 |
| `listName` | 列表名称 |
| `url` | 该应用+列表对应的完整页面 URL（导航目标） |
| `verifiedAt` | 最后验证日期，超过 30 天视为过期 |

**结构特点：** 扁平数组，每条记录就是 `appName + listName + url` 一一对应。相同应用的不同列表是独立条目，直接追加到数组末尾，不需要分组。

## 使用规则

- 文件不存在时自动创建 `{"entries":[]}`
- 每次成功进入列表页面后，在 `entries` 数组末尾追加一条记录
- 匹配时精确匹配 `appName + listName`
- `verifiedAt` 超过 30 天的记录不直接跳转，而是打开 URL 后验证页面是否仍然有效
