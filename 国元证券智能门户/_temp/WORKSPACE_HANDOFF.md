# 工作空间交接文件 — 国元证券智能门户

**交接人**: 王昭（昭哥） | **日期**: 2026-07-20 | **接收方**: 新应用的AI/开发者

---

## 一、这是什么项目

国元证券智能门户项目（合同金额 ¥387万），为客户部署企业微信私有化 + 智能门户 V2.1.6 + 七巧低代码。

**当前阶段**: 一期已上线（PC/安卓/鸿蒙 7/18上线，iOS待8/1），二期信创适配+定制需求进行中。老OA（SharePoint）与门户长期并行。

---

## 二、工作空间结构

```
国元证券智能门户/
├── CONTEXT.md              ← 项目上下文（每次任务前读这个）
├── PROJECT.md              ← 项目概览
├── output/                 ← 所有交付物、报告、文档
│   ├── 上线文档/           ← D1-D10上线文档（含Word版）
│   ├── 新闻数据源配置方案.md  ← OA新闻同步方案 V3.0
│   ├── 任务交接_老OA新闻同步.md ← OA新闻专题交接
│   └── ...
├── _deploy/                ← 生产部署包
│   ├── oa-news-proxy-java/ ← Java版新闻代理（推荐）
│   └── oa-news-proxy/      ← Python版新闻代理
├── 00-全局/                ← 全项目共享资源
├── .workbuddy/
│   ├── memory/             ← 记忆系统
│   │   ├── MEMORY.md       ← 项目长期记忆（项目事实）
│   │   └── YYYY-MM-DD.md   ← 每日工作日志
│   ├── skills/             ← 项目级技能
│   └── memory/MEMORY.md    ← 项目长期记忆
└── _临时/                  ← 临时文件
```

---

## 三、记忆系统规则（P0 强制）

### 3.1 两套记忆的分工

| 记忆层 | 路径 | 存什么 |
|--------|------|--------|
| **全局记忆** | `~/.workbuddy/MEMORY.md` | 规则、角色、方法论、全局路径（跨项目通用） |
| **项目记忆** | `.workbuddy/memory/MEMORY.md` | 项目事实、历史、文件路径、项目约定 |

### 3.2 每日日志规则

1. 每天工作完成后，**必须**在 `.workbuddy/memory/YYYY-MM-DD.md` 写日志
2. 日志末尾**必须**追加 `## 今日模型使用` 表格（原子操作，不可分开）
3. 格式：
```markdown
## 今日模型使用
| 模型 | 次数 | 任务 |
|------|:---:|------|
| Pro | N | 任务描述 |
| Flash | N | 任务描述 |
```

### 3.3 开工流程

1. 读 `CONTEXT.md`
2. 读 `.workbuddy/memory/MEMORY.md`
3. 读最近几天的 `.workbuddy/memory/YYYY-MM-DD.md`
4. 开始工作

---

## 四、当前进行中的任务

### 🎯 主任务：老OA新闻同步到智能门户

**目标**: 将老OA（SharePoint `home.oa.gyzq.com`）的新闻数据通过门户数据源展示到智能门户首页。

**状态**: 方案V3.0已完成，代理代码V2.0已就绪，**待部署测试**。

**技术方案（关键！已踩过的坑）**:

1. ❌ 不能直接在前端调OA API → 跨域+Cookie跨域问题
2. ❌ SSO不能替代代理 → SSO给JWT Token，SharePoint API只认Cookie
3. ❌ 不能简单透传 → 门户主动拉取是**POST请求**，且要求**特定JSON格式**
4. ✅ 正确方案：代理服务 + 格式转换

```
门户后端(POST) → http://10.0.63.11:8899/api/news
                      ↓
              OaProxyServer V2.0
                 ├─ 接收: typeId/maxCount/currentPage
                 ├─ 映射typeId→SharePoint站点路径
                 ├─ 注入Cookie → GET SharePoint REST API
                 ├─ 转换: OData JSON → 门户消息列表JSON
                 └─ 返回门户格式JSON
```

**部署目标**: 门户应用服务器 `10.0.63.11`（双网卡，可访问内网OA）

**部署包位置**: `_deploy/oa-news-proxy-java/`
- `src/OaProxyServer.java` — Java代理源码（零外部依赖）
- `oa-proxy.properties` — 填OA账号密码
- `build.sh` — 编译
- `deploy.sh` — 一键部署

**待办**:
1. 编译部署到10.0.63.11
2. 门户后台创建8个主动拉取数据源（每个新闻分类一个，typeId映射见方案文档）
3. 门户首页绑定消息列表组件 → 验证 → 发布

**参考文档**:
- `output/新闻数据源配置方案.md`（完整V3.0技术方案）
- `output/任务交接_老OA新闻同步.md`（专题交接，含部署步骤）
- `output/WORKSPACE_HANDOFF.md`（本文档）

---

## 五、关键文件索引

### 项目文档
| 文件 | 说明 |
|------|------|
| `CONTEXT.md` | 项目上下文（部署架构、技术栈、人员） |
| `PROJECT.md` | 项目概览 |
| `output/新闻公告分类栏目ID对照表.md` | 11个分类栏目ID（F202607090002~0012） |
| `output/第三方应用接入跟进表.md` | 49个应用对接进度 |

### OA新闻同步相关
| 文件 | 说明 |
|------|------|
| `output/新闻数据源配置方案.md` | 技术方案 V3.0 |
| `output/任务交接_老OA新闻同步.md` | 专题交接 |
| `_deploy/oa-news-proxy-java/` | Java部署包 |
| `_deploy/oa-news-proxy/` | Python部署包 |

### 上线文档
| 文件 | 说明 |
|------|------|
| `output/上线文档/README_上线支持文档目录.md` | 文档索引 |
| `output/上线文档/D1~D10/*.md` | 10份Markdown文档 |
| `output/上线文档/Word版/*.docx` | 10份Word文档 |

### 服务器资源
| 文档 | 来源 |
|------|------|
| 企微在线表格 `AXQAlQbEAL8CNpcOVT1wSRuqM1X5N` | 生产环境资源配置（服务器IP、密码、网络策略） |
| `官网SP接口.xlsx` | 客户提供，27个SharePoint REST API |

---

## 六、部署架构（关键IP）

```
用户 → portal.oa.gyzq.com
         ↓
    DMZ负载均衡 172.16.20.253
         ↓
    DMZ应用服务器(Nginx) 172.16.19.1
         ↓
    门户应用服务器 10.0.63.11 (BES, 双网卡)
         ↓
    中间件集群 10.0.63.13~15
```

- **OA新闻代理部署目标**: 10.0.63.11
- **老OA**: home.oa.gyzq.com (SharePoint on-premises)
- **SSO**: login.oa.gyzq.com (Keycloak)

---

## 七、协作约定

1. **滴答清单单一入口**: 昭哥所有待办操作仅在滴答清单，自动化自动检测变化
2. **企微MCP**: 在线文档/表格通过 `企业微信文档` streamable-http MCP 读取
3. **文档双文件**: 所有文档同时维护 `.md` + `.html`
4. **绝对路径**: 所有路径必须使用绝对路径，禁止 `~/` 缩写
5. **模型记录**: 每日日志末尾必须追加模型使用表

---

**文档版本**: V1.0 | **编制人**: 王昭 | **日期**: 2026-07-20
