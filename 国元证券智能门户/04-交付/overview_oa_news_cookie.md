# 老OA新闻数据源同步 — Cookie认证方案摘要

**日期**：2026-07-16 | **编制**：王昭

---

## 结论：可以同步！✅

老OA（SharePoint on-premises）提供了27个REST API接口覆盖8个新闻分类，可以通过**Nginx反向代理+Cookie注入**实现数据同步到智能门户。

## 为什么不能直接调

- OA Cookie属于 `home.oa.gyzq.com` 域
- 门户在 `portal.oa.gyzq.com` 域
- 浏览器跨域安全策略禁止前端携带OA Cookie

## 怎么做（三步走）

```
获取OA Cookie → Nginx注入代理 → 门户配置同域数据源
```

1. **获取Cookie**：向客户要一个OA服务账号，登录拿到`FedAuth`/`rtFa` Cookie
2. **部署代理**：在门户应用服务器(10.0.63.11)部署代理服务，注入Cookie并转发到OA
3. **配置门户**：数据源URL改为 `https://portal.oa.gyzq.com/oa-news/gsdt/_api/...`

## Cookie过期怎么办

部署Python刷新脚本，定时（每2小时）模拟登录获取新Cookie写入文件，Nginx动态读取。

## 需要客户配合

- 提供一个OA服务账号（新闻阅读权限即可）
- 确认门户应用服务器到OA的网络已通

## 详细方案

见 `output/新闻数据源配置方案.md`（已更新至V2.0）
