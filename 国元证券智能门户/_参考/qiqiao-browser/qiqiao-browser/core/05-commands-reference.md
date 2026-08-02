# 指令速查

> 主会话在节点 30 执行前读取，流程执行中随时查阅。优先用 `window.$ai.*`，降级才用 `bsk`。

---

## window.$ai（优先）

| 指令 | 作用 |
|------|------|
| `window.$ai.init()` | 初始化 API。进入表单弹窗后必须调 |
| `window.$ai.getFormFields()` | ⭐ **获取所有字段列表（填单/发起流程/审批弹窗通用，首选）** |
| `window.$ai.findDom({action:'filling'})[0]` | 获取表单容器元素引用，供 `__qiqiaoFormAPI` 函数使用 |
| `window.$ai.fillingForm(element, data)` | 批量填充字段。键=字段中文名，值=字段值。子表用 `[{列名:值}]` |
| `window.$ai.getMetadata(element)` | 获取元素元数据（name/desc/id），多结果时展示给用户确认 |
| `window.$ai.findDom('文本')` | 按文本找元素，自动处理 Vue 事件冒泡 |
| `window.$ai.findDom({type:'detailbtn'})` | 定位行详情按钮 |
| `window.$ai.findDom({type:'editbtn'})` | 定位行编辑按钮 |
| `window.$ai.findDom({type:'confirmbtn'})` | 定位弹窗确认按钮 |
| `window.$ai.findDom({type:'cancelbtn'})` | 定位弹窗取消按钮 |
| `window.$ai.findDom({type:'downloadExport'})` | 定位导出下载按钮 |
| `window.$ai.findDom({id:'__canEdit'})` | 关联行编辑 |
| `window.$ai.findDom({id:'__canDel'})` | 关联行删除 |
| `window.$ai.findDom({id:'__canCopy'})` | 关联行复制 |
| `window.$ai.findDom({id:'more'})` | 关联行更多操作 |
| `window.$ai.findDom({id:'index-startProcess'})` | 首页发起流程按钮 |
| `window.$ai.findDom({id:'atUser'})` | 评论 @提及 |
| `window.$ai.findDom({id:'uploadImage'})` | 评论上传图片 |
| `window.$ai.findDom({id:'uploadFile'})` | 评论上传文件 |
| `window.$ai.findDom({id:'emoji'})` | 评论表情 |

**关键约束：**
- `findDom('文本')` 优先，找不到再降级 `bsk snapshot` + `bsk click @eN`
- `fillingForm` 禁止用于子表关联(B5)和多表关联(B6)——必须弹窗 checkbox 勾选
- `fillingForm` 对子表是追加行为，禁止重复调用
- **字段获取标准顺序：** `getFormFields()` → `findDom({action:'filling'})[0]`（供 `__qiqiaoFormAPI`）→ 均无数据才降级 `bsk snapshot`

---

## bsk（降级）

| 指令 | 作用 |
|------|------|
| `bsk snapshot` | 页面文本快照，每个元素带 @eN ref。用于验证页面、定位按钮 |
| `bsk click @eN` | 点击 @eN 对应元素 |
| `bsk evaluate 'js代码'` | 在浏览器执行 JS。用于调 window.$ai、滚动、检查接口 |

> ⚠️ **Shell 引号规则（Windows Git Bash / Linux / macOS）：** JS 代码中含 `$` 符号（如 `$ai`、`${}`）时，**必须用单引号** `'...'` 包裹，否则 bash 会把 `$` 当作变量展开导致代码错误（如 `bsk evaluate "window.$ai.init()"` → bash 展开 `$ai` 为空 → 实际执行 `bsk evaluate "window."` → SyntaxError）。**正确写法：** `bsk evaluate 'window.$ai.init()'`。不含 `$` 的 JS 可用双引号或单引号。当 JS 内层含单引号（如 `findDom('文本')`）时，内层改用双引号、外层用单引号：`bsk evaluate 'window.$ai.findDom("应用列表")[0].click()'`。
| `bsk navigate "URL"` | 导航到 URL。仅限 PLATFORM_DOMAIN 域名内 |
| `bsk fill @eN --value "值"` | 向输入框填值。搜索框用，填完跟 `bsk press Enter` |
| `bsk press Enter --ref @eN` | 按键 |
| `bsk wait-ms` | 等待毫秒。等弹窗出现或 toast 消失 |
| `bsk doctor` | 诊断扩展连接状态 |
| `bsk session start` / `bsk session list` | 管理浏览器会话 |
| `which bsk` | 检查 bsk CLI 是否可用 |

---

## 滚动（获取字段前必须执行）

| 场景 | 指令 |
|------|------|
| 添加/编辑/详情表单 | `bsk evaluate "document.querySelector('.business_drawer .drawer .drawer_content').scrollTo({ top: document.querySelector('.business_drawer .drawer .drawer_content').scrollHeight, behavior: 'smooth' })"` |
| 发起流程表单 | `bsk evaluate "document.querySelector('.process_content .drawer_content').scrollTo({ top: document.querySelector('.process_content .drawer_content').scrollHeight, behavior: 'smooth' })"` |
| 审批详情弹窗 | `bsk evaluate "document.querySelector('.workflow_layout_inner.no_scroll').scrollTo({ top: document.querySelector('.workflow_layout_inner.no_scroll').scrollHeight, behavior: 'smooth' })"` |

---

## Iframe / 评论编辑器（TinyMCE）

评论区是 iframe 内的 TinyMCE，`bsk fill` 无效。通过 contenteditable + dispatch `input` 事件操作：

```
# 聚焦 + 填文字
bsk click @eN (Iframe) → 聚焦
bsk evaluate →
  var doc = (document.querySelector('iframe').contentDocument);
  var ed = doc.querySelector('[contenteditable]') || doc.body;
  ed.innerHTML = ''; var p = doc.createElement('p');
  p.textContent = '内容'; ed.appendChild(p);
  ed.dispatchEvent(new Event('input', {bubbles: true}));

# 发送
bsk evaluate → window.$ai.findDom('发送')[0].click()
```

**@mention 后追加文字：** 用 `createTextNode` + `appendChild`，禁止覆盖 innerHTML（会丢失 mention 节点）。

```
bsk evaluate '
  var doc = (document.querySelector("iframe").contentDocument);
  doc.querySelector("p").appendChild(doc.createTextNode(" 文字"));
  doc.querySelector("[contenteditable]").dispatchEvent(new Event("input", {bubbles: true}));
'
```

> ⚠️ 禁止 `contentWindow.document` 降级（非 TinyMCE 内部 Document，text node 会丢失），
> 禁止 `querySelector("p") || editable` 降级到 body（文字位置错误）。不加保护性 if/降级，出错让它报出来。

**文件上传（图片/附件）：** 绕过 el-upload，注入 TinyMCE 的 file input（`inputs[2]`，parentClass `dy-rich-text`）。注入后直接发送，不要修改编辑器内容。

```bash
B64=$(base64 -w 0 "/path/to/文件")
```
```
# 清空编辑器
bsk evaluate →
  var ifr = document.querySelector('iframe');
  if (ifr) {
    var doc = ifr.contentDocument || ifr.contentWindow.document;
    doc.body.innerHTML = '<p><br data-mce-bogus="1"></p>';
    (doc.querySelector('[contenteditable]') || doc.body)
      .dispatchEvent(new Event('input', {bubbles: true}));
  }

# 注入文件
bsk evaluate →
  var t = document.querySelectorAll('input[type="file"]')[2];
  var b64 = '${B64}'; var bin = atob(b64);
  var bytes = new Uint8Array(bin.length);
  for (var j = 0; j < bin.length; j++) bytes[j] = bin.charCodeAt(j);
  var dt = new DataTransfer();
  dt.items.add(new File([bytes], '文件名.docx', {type: 'MIME类型'}));
  Object.defineProperty(t, 'files', {value: dt.files, writable: false});
  t.dispatchEvent(new Event('change', {bubbles: true}));
  'ok';

# 直接发送
bsk evaluate → window.$ai.findDom('发送')[0].click()
```

> `inputs[2]` 可能随页面变化，不确定时用 `inputs[i].parentElement.className.includes('dy-rich-text')` 动态定位。支持所有文件类型。

**@mention 选人：** `window.$ai.findDom({id:'atUser'})[0].click()` → `bsk fill` 搜索 → `document.querySelectorAll('.el-select-dropdown__item')` 匹配点击 → `bsk click @eN "确 定"`

---

## 复选框勾选

**点击行不会选中复选框**，必须 snapshot 找准 checkbox 的 @eN 再 click：

```
bsk snapshot
bsk click @eN
```

禁止 `querySelector('input[type=checkbox]')`（先命中表头全选框）。

---

## 禁止操作

| 禁止 | 原因 |
|------|------|
| `querySelector('input[type=checkbox]')` | 命中表头全选框 |
| `querySelectorAll('[class*="tree"]')` | 命中 el-tree 外层，Vue 事件不响应 |
| `fillingForm` 填子表关联/多表关联 | 破坏关联关系 |
| 对同一子表重复 `fillingForm` | 会产生重复行 |
| 用 `bsk snapshot` 看字段列表 | 输出截断，字段不全 |
