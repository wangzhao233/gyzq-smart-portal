# 故障处理矩阵（唯一权威）

> **读取阶段：** 阶段三（主会话进入首个流程节点前读取）
>
> 本文定义所有流程节点通用故障处理方案。节点内仅引用，不重复展开。

## 故障矩阵

| 卡在哪 | 现象 | 处理方案 | 回退节点 |
|--------|------|---------|---------|
| 环境检测 | bsk CLI 不存在（`which bsk` 失败） | 引导用户安装 browser-skill（见 `common/10-env-detect.md`） | — |
| 环境检测 | `bsk session start` 失败 | `bsk doctor` 执行诊断；检查浏览器扩展是否已安装并连接 | — |
| 登录 | `window.$ai` 不存在 | 确认用户已在七巧Plus平台页面，且平台版本支持 `$ai` | `common/20-login.md` |
| 登录 | `window.$ai.init()` 报错 | 刷新页面重新 `window.$ai.init()`；仍失败则可能是版本问题，询问用户 | `common/20-login.md` |
| 通用（非登录场景） | `window.$ai.findDom` / `window.$ai.getFormFields` 报错 | **先执行 `window.$ai.init()`**（见 GR-01-6），再重试 | 当前节点 |
| 导航 | `bsk snapshot` 看不到目标元素 | 等页面加载完成再 snapshot；换同义词搜索；仍找不到则询问用户 | 当前节点 |
| 搜索应用 | snapshot 中看不到搜索结果 | 换同义词重试；**先去掉"应用/系统/平台"等后缀**；仍找不到则询问用户 | `form-filling/01-app-list.md` |
| 选择应用 | snapshot 中有多个匹配 | 展示文本内容让用户确认，**禁止**默认选第一个 | `form-filling/01-app-list.md` |
| 选择列表 | snapshot 中有多个匹配 | 同上，展示让用户确认 | `form-filling/02-app-detail.md` |
| 按钮 | bsk snapshot 看不到对应按钮 | 询问用户该按钮在当前页面的位置或名称 | 当前节点 |
| 表单 | `getFormFields()` 返回 null | 降级 `bsk snapshot` | 当前流程的填单节点 |
| 表单 | `fillingForm` 填充失败（返回 false） | 检查字段 key 是否为中文名称；检查 data 值是否为字符串；尝试逐字段填充排查 | 当前流程的填单节点 |
| 子表 | 出现重复行 | `fillingForm` 对子表是追加行为，**禁止对同一子表重复调用**。需修正的字段应逐单元格点击编辑 | 当前流程的填单节点 |
| 子表 | 字段无内部列名 | 用 Vue API `elementData.__qiqiaoFormAPI.getFormInfoData().fields` 获取所有字段 → 筛选 `type === 'subform'` → 从 `subForms` 中筛选 `permission === 'MODIFY'` 提取 `title`（见 GR-07）；**禁止添加行来获取列名**；失败则询问用户 | 当前流程的填单节点 |
| 子表 | 数据填充失败 | 确认数据格式为 `[{ "列名": "值" }]`（对象数组）；列名必须与页面列头完全一致 | 当前流程的填单节点 |
| 外键弹窗 | 打开弹窗后搜索无结果 | 告知用户未找到，询问是否换关键词或手动选择 | 当前流程的填单节点 |
| 子表关联 | 子表关联弹窗无法打开 | 用 `bsk snapshot` 检查按钮位置；询问用户该按钮在页面中的位置 | 当前流程的填单节点 |
| 多表关联 | 多表关联弹窗无法打开 | 用 `bsk snapshot` 检查按钮位置；询问用户该按钮在页面中的位置 | 当前流程的填单节点 |
| 弹窗 | bsk snapshot 看不到弹窗 | `bsk wait-ms` 等待弹窗出现；或检查弹窗是否已被其他操作关闭 | 当前流程的弹窗节点 |
| 弹窗 | 弹窗中确认/取消按钮点不到 | 用 `bsk snapshot` 重新定位 dialog 内的按钮 ref；snapshot ref 可能已失效 | 当前流程的弹窗节点 |
| 导出 | 确认弹窗后未下载 | 确认后需等待下载文件提示出现，再用 bsk snapshot 定位下载按钮并点击；**不要**在确认后立即点击 | 当前流程的弹窗节点 |
| 发起流程 | snapshot 看不到"发起流程"按钮 | 尝试在首页重新定位；仍失败则询问用户 | `common/30-home.md` |
| 发起流程 | 流程搜索无结果 | 询问用户是否换关键词重新搜索 | `start-process/01-process-search.md` |
| 发起流程 | 流程表单弹窗 `init()` 失败 | 刷新页面后重新导航，从首页重新进入 | `start-process/03-process-form.md` |
| 审批 | 办理/驳回/终止按钮找不到 | 可能该流程当前节点无此操作权限；用 `bsk snapshot` 确认弹窗内按钮 | `approval/03-approval-action.md` |
| 审批 | 办理/驳回后弹窗确认失败 | 按弹窗处理规则重试 | `approval/05-popup-handle.md` |
| 审批 | 驳回后流程状态未变更 | 刷新页面检查；可能审批已过期或被他人处理 | `approval/03-approval-action.md` |
| 待办列表 | 搜索无结果 | 换同义词重试；清空筛选条件后重试 | `approval/01-todo-list.md` |
| 待办列表 | 多条同名待办无法区分 | 用 `bsk snapshot` 查看完整标题和发起人信息辅助判断 | `approval/01-todo-list.md` |
| bsk 会话 | `bsk click @eN` 报错 stale ref | ref 已失效，重新 `bsk snapshot` 获取最新 ref 后再操作 | 当前节点 |
| bsk 会话 | `bsk snapshot` 返回 timeout | 页面未加载完，增加等待时间或检查浏览器连接状态 | 当前节点 |
| bsk 会话 | `bsk session` 无响应 | `bsk doctor` 检查扩展连接状态；确认浏览器扩展已打开 | 当前节点 |

## 降级策略

当 browser-skill 完全不可用时（扩展未安装、连接断开等极端情况）：

1. **告知用户**：browser-skill 当前不可用，自动化操作无法继续
2. **引导恢复**：请用户检查浏览器扩展是否已连接（插件图标是否为绿色）
3. **可选方案**：让用户手动操作，Agent 仅提供指导
