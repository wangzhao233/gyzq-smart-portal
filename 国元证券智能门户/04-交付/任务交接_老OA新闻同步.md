# 任务交接：老OA新闻同步到智能门户

**交接人**：王昭
**日期**：2026-07-18
**任务状态**：方案V3.0已完成，代理代码已更新，待上机部署测试

---

## 一、任务目标

将老OA（SharePoint on-premises）的新闻数据，通过智能门户数据源同步到首页展示。覆盖8个新闻分类：公司动态、部门简报、创新发展、监管动态、党建群团、子公司及分支机构、党建指南、服务台。

## 二、已确认的前提

| 项 | 状态 | 说明 |
|----|------|------|
| OA系统 | ✅ | SharePoint on-premises，`http://home.oa.gyzq.com` |
| 接口清单 | ✅ | 27个SP REST API，客户已提供 `官网SP接口.xlsx` |
| 认证方式 | ✅ | 需Cookie认证（FedAuth/rtFa） |
| OA服务账号 | ✅ | 已有 |
| 网络 | ✅ | 门户应用服务器10.0.63.11双网卡，可访问OA内网 |
| 门户数据源能力 | ✅ | 主动拉取模式：POST请求，消息列表组件，需特定JSON格式 |
| SSO | ℹ️ | 老OA+新门户都接Keycloak，但SSO不能替代代理（SP API只认Cookie） |

## 三、技术方案（V3.0 定稿）

**方案**：代理服务 + 门户主动拉取 + JSON格式转换

```
门户后端(POST) → http://10.0.63.11:8899/api/news
                      ↓
              OaProxyServer V2.0
                 ├─ 接收: typeId(分类)/maxCount(条数)/currentPage(页码)
                 ├─ 映射typeId→SharePoint站点路径
                 ├─ 注入Cookie → GET SharePoint REST API
                 ├─ 转换: OData JSON → 门户消息列表JSON
                 └─ 返回门户格式JSON
```

**关键变化（V2→V3.0）**：
- V2.0 假设门户发GET请求+透传JSON → **错误**
- V3.0 门户发POST请求+代理做格式转换 → **正确**
- 不再需要Nginx额外代理层，代理直接在应用服务器上接受门户后端请求

## 四、已完成的交付物

### 4.1 方案文档

| 文件 | 路径 | 说明 |
|------|------|------|
| 新闻数据源配置方案 V3.0 | `output/新闻数据源配置方案.md` | 完整技术方案，含字段映射、门户配置步骤 |
| 任务交接文件 | `output/任务交接_老OA新闻同步.md` | 本文档 |

### 4.2 代理服务 V2.0

| 文件 | 路径 | 说明 |
|------|------|------|
| Java代理源码 | `_deploy/oa-news-proxy-java/src/OaProxyServer.java` | V2.0，新增`/api/news`端点+格式转换 |
| 配置文件 | `_deploy/oa-news-proxy-java/oa-proxy.properties` | OA账号密码配置 |
| 编译脚本 | `_deploy/oa-news-proxy-java/build.sh` | `javac`编译为oa-proxy.jar |
| 部署脚本 | `_deploy/oa-news-proxy-java/deploy.sh` | 一键部署到10.0.63.11 |
| 验证脚本 | `_deploy/oa-news-proxy-java/verify.sh` | 部署后验证 |
| 部署说明 | `_deploy/oa-news-proxy-java/README.md` | 部署文档 |

### 4.3 参考文档

| 文件 | 来源 |
|------|------|
| `智能门户数据源对接指南2.14.pdf` | 道一云官方 |
| `智能门户数据源API文档--主动拉取-v608.pdf` | 道一云官方 |
| `智能门户数据源API文档--数据推送-v608.pdf` | 道一云官方 |
| `官网SP接口.xlsx` | 客户提供 |
| SSO三份接入文档 | 客户提供 |

## 五、部署步骤

### 第1步：准备
1. 确认门户应用服务器(10.0.63.11)的Java版本：`java -version`（需JDK 8+）
2. 如无Java，安装：`yum install java-1.8.0-openjdk-devel -y`

### 第2步：配置OA账号
编辑 `oa-proxy.properties`，填入OA服务账号：
```properties
oa.username=OA服务账号
oa.password=密码
```

### 第3步：编译+部署
```bash
cd _deploy/oa-news-proxy-java
bash build.sh              # 本地编译 → oa-proxy.jar
# 将 oa-proxy.jar + oa-proxy.properties + deploy.sh 传到10.0.63.11
sudo bash deploy.sh        # 在服务器上执行
```

### 第4步：验证
```bash
# 健康检查
curl http://10.0.63.11:8899/health

# 测试主动拉取（模拟门户POST）
curl -X POST http://10.0.63.11:8899/api/news \
  -d "typeId=gsdt&maxCount=5&currentPage=1" \
  -H "Content-Type: application/x-www-form-urlencoded"
```
应返回JSON包含`"code":0`和`"data":{"value":[...]}`。

### 第5步：门户后台配置数据源

管理员登录门户后台 → 门户中心 → 数据源设置 → 消息列表 → 创建数据源：

| 配置项 | 值 |
|--------|-----|
| 数据源名称 | OA公司动态 |
| 获取数据方式 | 主动拉取 |
| API地址 | `http://10.0.63.11:8899/api/news` |
| 自定义参数 | 固定参数：`typeId=gsdt` |

**每个分类创建独立数据源**：

| 数据源 | typeId | 对应SP站点 |
|--------|--------|-----------|
| OA公司动态 | `gsdt` | `/gsdt/` |
| OA部门简报 | `bmjb` | `/bmjb/` |
| OA创新发展 | `cxfz` | `/cxfz/zcdt/` |
| OA监管动态 | `jgdt` | `/hggl/jgdt/` |
| OA党建群团 | `djqt` | `/gsdt/djqt/` |
| OA子公司 | `zgs` | `/gsdt/zgsfzjg/` |
| OA党建指南 | `lxyz` | `/jdlm/lxyz/` |

配置后在门户首页编辑中绑定这些数据源到消息列表组件，预览效果后发布。

## 六、待办

| # | 事项 | 优先级 | 说明 |
|---|------|--------|------|
| 1 | 部署代理到10.0.63.11 | P0 | 编译→传文件→run |
| 2 | 门户后台创建8个数据源 | P0 | 每个新闻分类一个 |
| 3 | 门户首页绑定组件并发布 | P0 | 预览→确认→发布 |
| 4 | 确认OA Cookie有效期 | P1 | 影响自动刷新频率 |
| 5 | 审查同事提供的JAR包（如有） | P1 | — |

## 七、已知风险

| 风险 | 应对 |
|------|------|
| SharePoint表单认证方式不确定 | 支持`cookie_form`和`ntlm`两种，失败时切换 |
| Cookie过期导致新闻中断 | 代理每30分钟自动刷新Cookie |
| 门户`/api/news`端口被防火墙拦截 | 代理部署在应用服务器上，门户后端直连内网无防火墙问题 |

---

**文档版本**：V1.1
**交接日期**：2026-07-18
**交接人**：王昭
