# 审批流 04：评论

> ⚠️ 开始前先读取 `core/06-discipline-check.md`。

## 你在哪里

已在 `02-todo-detail.md` 中打开了审批详情弹窗，评论区域在底部。

## 评论工具栏图标

| 图标 | ai-id | 定位 |
|------|-------|------|
| @提及 | `atUser` | `window.$ai.findDom({id:'atUser'})[0].click()` |
| 上传图片 | `uploadImage` | `window.$ai.findDom({id:'uploadImage'})[0].click()` |
| 上传文件 | `uploadFile` | `window.$ai.findDom({id:'uploadFile'})[0].click()` |
| 表情 | `emoji` | `window.$ai.findDom({id:'emoji'})[0].click()` |

## 发送纯文字评论

### 步骤 1：聚焦 iframe 编辑区

```
bsk snapshot → 找到评论编辑区 iframe 的 @eN
bsk click @eN → 聚焦 iframe
```

> ⚠️ **不能**用 `bsk fill @eN` 对 iframe 填值，必须在 evaluate 中操作。

### 步骤 2：通过 contenteditable 填入内容

```
bsk evaluate →
  var ifr = document.querySelector('iframe');
  var doc = ifr.contentDocument || ifr.contentWindow.document;
  var editable = doc.querySelector('[contenteditable]') || doc.body;
  editable.innerHTML = '';
  var p = doc.createElement('p');
  p.textContent = '评论内容';
  editable.appendChild(p);
  var evt = new Event('input', { bubbles: true });
  editable.dispatchEvent(evt);
```

**关键点：**
- 用 `[contenteditable]` 找到富文本编辑器的实际可编辑元素
- **必须 dispatch `input` 事件**，否则编辑器框架不会感知内容变更，发送按钮保持不可用
- 不能仅设置 `innerHTML`（不触发编辑器响应），也不能用 `execCommand`（不可靠）

### 步骤 3：点击发送

**优先：**

```
bsk evaluate → window.$ai.findDom('发送')[0].click()
```

**降级：**

```
bsk snapshot → 找发送按钮 @eN
bsk click @eN
```

### 步骤 4：验证

```
bsk snapshot → 检查评论区是否出现刚发布的内容
```

验证标准：评论时间戳显示"刚刚"，内容文本匹配。

## @提及人员（可选，在填文字之前操作）

**1. 点 @ 图标 → 搜索 → 选择：**
```
window.$ai.findDom({id:'atUser'})[0].click()
bsk fill @eN --value "姓名"
bsk evaluate →
  document.querySelectorAll('.el-select-dropdown__item')
    .forEach(i => i.textContent.includes('姓名') && i.click())
bsk snapshot → 确认已选 → bsk click @eN "确 定"
```

> 搜索后 `.el-select-dropdown__item` 弹出，匹配文本后 `.click()`。

**2. 追加文字（用 createTextNode，不要覆盖 innerHTML）：**
```
bsk evaluate '
  var doc = (document.querySelector("iframe").contentDocument);
  doc.querySelector("p").appendChild(doc.createTextNode(" 文字"));
  doc.querySelector("[contenteditable]").dispatchEvent(new Event("input", {bubbles: true}));
'
```

> ⚠️ **严禁以下做法（会导致追加的文字丢失）：**
> 
> **禁止1 — 使用 `contentWindow.document` 降级：**
> ```js
> // ❌ 错误：contentWindow.document 在部分浏览器返回外层包装对象，
> //    text node 挂到了非 TinyMCE 内部 Document 上，序列化保存时被丢弃
> var doc = ifr.contentDocument || ifr.contentWindow.document;
> ```
> 
> **禁止2 — 用 `editable.querySelector("p")` 降级到 body：**
> ```js
> // ❌ 错误：@mention 后 TinyMCE 已有 <p> 节点，
> //   querySelector("p") || editable 降级到 body 时文字位置错误
> var p = editable.querySelector("p") || editable;
> ```
> 
> **核心原则：** 必须用 `document.querySelector("iframe").contentDocument`（不加降级），
> 必须用 `doc.querySelector("p")`（不加 || 降级）。

## 发送图片/文件

绕开 el-upload（files 只读），注入 TinyMCE 的 file input（`inputs[2]`，parentClass `dy-rich-text`）。注入后直接发送，不要修改编辑器内容。

```bash
B64=$(base64 -w 0 "/path/to/文件")
```
```
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
```
```
window.$ai.findDom('发送')[0].click()
bsk snapshot → 验证附件显示
```

> `inputs[2]` 可能随页面变化，不确定时用 `inputs[i].parentElement.className.includes('dy-rich-text')` 动态定位。支持所有文件类型。

## 错误处理

| 失败场景 | 处理方式 |
|---------|---------|
| iframe 找不到 | `bsk snapshot` 确认评论区是否可见 |
| `[contenteditable]` 返回 null | 降级用 `doc.body` |
| 发送按钮不可用 | 检查是否 dispatch 了 `input` 事件 |
| @ 图标点击无反应 | 先 click iframe 聚焦 |
| 搜索后无下拉选项 | 确认输入了足够关键字 |

## 下一节点

> ⚠️ 评论发布后，读取 `core/06-discipline-check.md`。

评论发布后 → 留本节点（详情弹窗保持打开）
关闭详情 → **`01-todo-list.md`（待办列表页）**
