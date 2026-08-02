# OA新闻代理 — Java版生产部署包

**用途**：将老OA（SharePoint）新闻接口通过Nginx代理注入Cookie，同步新闻数据到智能门户。  
**版本**：Java版（零外部依赖，JDK自带库实现）  
**编制**：王昭 | **日期**：2026-07-16  
**适用环境**：银河麒麟 V10 / CentOS 7+，JDK 8+

---

## 文件结构

```
oa-news-proxy-java/
├── build.sh                       # 编译打包脚本（本地执行）
├── deploy.sh                      # 一键部署脚本（在接入机执行）
├── verify.sh                      # 部署验证脚本
├── README.md                      # 本文档
├── oa-proxy.properties            # 配置文件（需修改账号密码）
├── nginx/
│   └── oa-news-proxy.conf         # Nginx配置文件
└── src/
    └── OaProxyServer.java         # Java源码（单文件，零依赖）
```

---

## 技术特点

| 特性 | 说明 |
|------|------|
| **零外部依赖** | 仅使用JDK自带的 `com.sun.net.httpserver` + `java.net`，无需Maven/Gradle |
| **单文件** | 核心代码一个Java文件，便于审查和维护 |
| **自动Cookie管理** | 启动时登录OA获取Cookie，过期自动刷新 |
| **线程安全** | 10线程池处理并发请求 |
| **开机自启** | systemd托管，崩溃自动重启 |
| **轻量级** | JAR约30KB，内存占用~64MB |

---

## 快速部署（3步）

### 第1步：填OA账号

编辑 `oa-proxy.properties`：

```properties
oa.username=OA服务账号
oa.password=密码
```

### 第2步：编译打包（本地）

```bash
cd oa-news-proxy-java
bash build.sh
# 生成 oa-proxy.jar
```

### 第3步：部署到门户应用服务器

将 `oa-proxy.jar` + `oa-proxy.properties` + `nginx/` + `deploy.sh` + `verify.sh` 传到门户应用服务器(10.0.63.11)，执行：

```bash
sudo bash deploy.sh
```

部署脚本会自动：编译JAR → 部署到 `/opt/oa-news-proxy/` → 配置Nginx → 注册systemd服务。

---

## 服务管理

```bash
# 启动/停止/重启
systemctl start   oa-proxy
systemctl stop    oa-proxy
systemctl restart oa-proxy

# 查看状态和日志
systemctl status  oa-proxy
journalctl -u oa-proxy -f          # 实时日志
journalctl -u oa-proxy -n 100      # 最近100行

# 手动运行（调试用）
java -jar /opt/oa-news-proxy/oa-proxy.jar /opt/oa-news-proxy/oa-proxy.properties
```

---

## 验证部署

```bash
bash /opt/oa-news-proxy/verify.sh portal.oa.gyzq.com
```

验证通过后，在门户后台配置新闻数据源URL。

---

## 门户数据源配置

验证通过后，配置门户「门户装修 → 首页编辑 → 新闻组件 → HTTP数据源」：

| 配置项 | 值 |
|--------|-----|
| 数据源类型 | HTTP / REST API |
| 请求方式 | GET |
| 认证方式 | **无需认证** |
| 刷新频率 | 10分钟 |

**各分类数据源URL**：

| 新闻分类 | 门户数据源URL |
|---------|--------------|
| 公司动态 | `https://portal.oa.gyzq.com/oa-news/gsdt/_api/lists/getbytitle('页面')/items?$select=Created,Title,Id,ArticleStartDate,FileRef,Modified&$top=20&$orderby=ArticleStartDate%20desc&$filter=OData__ModerationStatus%20eq%200` |
| 部门简报 | `https://portal.oa.gyzq.com/oa-news/bmjb/_api/lists/getbytitle('页面')/items?$select=Created,Title,Id,ArticleStartDate,FileRef,Modified,OData__x005f_x9644__x005f_x4ef6_ID,OData__x005f_x6765__x005f_x6e90_&$top=20&$orderby=ArticleStartDate%20desc&$filter=OData__ModerationStatus%20eq%200` |
| 创新发展 | `https://portal.oa.gyzq.com/oa-news/cxfz/zcdt/_api/lists/getbytitle('页面')/items?$select=Created,Title,Id,ArticleStartDate,FileRef,Modified&$orderby=Created%20desc&$filter=OData__ModerationStatus%20eq%200&$top=20` |
| 监管动态 | `https://portal.oa.gyzq.com/oa-news/hggl/jgdt/_api/lists/getbytitle('页面')/items?...` |
| 党建群团 | `https://portal.oa.gyzq.com/oa-news/djqt/_api/lists/getbytitle('页面')/items?...` |
| 子公司及分支机构 | `https://portal.oa.gyzq.com/oa-news/zgs/_api/lists/getbytitle('页面')/items?...` |
| 党建指南 | `https://portal.oa.gyzq.com/oa-news/lxyz/_api/lists/getbytitle('页面')/items?...` |
| 服务台 | `https://portal.oa.gyzq.com/oa-news/fwt/{子站名}/_api/lists/getbytitle('页面')/items?...` |
| 部门公告 | `https://portal.oa.gyzq.com/oa-news/bmgg/_api/search/query?...` |

---

## 工作原理

```
浏览器(门户) → GET https://portal.oa.gyzq.com/oa-news/gsdt/_api/...
    ↓
Nginx(DMZ服务器 172.16.19.1) → proxy_pass http://10.0.63.11:8899
    ↓
OaProxyServer(本地) → 自动注入OA Cookie → GET http://home.oa.gyzq.com/gsdt/_api/...
    ↓
SharePoint返回JSON → 代理透传 → 门户组件渲染
```

- Java代理监听 `127.0.0.1:8899`（仅本机，不对外暴露）
- 启动时自动登录OA获取FedAuth/rtFa Cookie
- Cookie过期前30分钟自动刷新（默认4小时有效期）
- 10线程并发处理，支持门户多组件同时请求

---

## 配置说明

```properties
# OA认证
oa.base.url=http://home.oa.gyzq.com         # OA地址
oa.username=服务账号                           # OA账号
oa.password=密码                               # OA密码
oa.auth.type=cookie_form                       # cookie_form 或 ntlm

# 代理
proxy.listen.port=8899                         # 监听端口（仅本地）

# 会话
session.cookie.max.age.hours=4                 # Cookie有效期（小时）
session.retry.count=3                          # 登录重试次数
session.request.timeout.seconds=15             # 请求超时

# 日志
logging.file=/var/log/oa-proxy/proxy.log       # 日志路径
```

---

## 故障排查

| 现象 | 可能原因 | 解决方法 |
|------|---------|---------|
| 验证脚本报 401 | Cookie过期/账号密码错误 | 检查 oa-proxy.properties，重启服务 |
| 验证脚本报 502 | Java代理未启动 | `systemctl status oa-proxy`，查看日志 |
| 服务启动失败 | Java版本过低/配置错误 | `journalctl -u oa-proxy -n 50` |
| 登录失败 | auth_type不匹配 | 尝试把 `cookie_form` 改为 `ntlm` |
| Nginx 502 | 端口未监听 | `netstat -tlnp \| grep 8899` 确认 |

---

## 安全说明

- `oa-proxy.properties` 权限已设为 `600`（仅root可读）
- 代理仅监听 `127.0.0.1`，不对外暴露端口
- OA Cookie不写入浏览器或日志文件
- 生产部署后建议定期更换OA密码

---

## 附：JDK安装参考（银河麒麟 V10）

```bash
# 检查是否已安装
java -version

# 安装 OpenJDK 8（推荐，兼容性最好）
yum install java-1.8.0-openjdk java-1.8.0-openjdk-devel -y

# 或安装 OpenJDK 11
yum install java-11-openjdk java-11-openjdk-devel -y

# 验证
javac -version
```
