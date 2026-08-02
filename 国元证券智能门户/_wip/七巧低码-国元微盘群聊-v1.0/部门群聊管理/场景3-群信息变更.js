// ===== 部门群聊管理 — 场景3：群信息变更 =====
// 脚本位置：流程表单「群信息变更」→ 审批流程 → 执行后脚本
// ⚠️ 前置：将公共函数/下的 getAppChatToken.js 复制到本脚本顶部，并替换 secret 占位符
// 支持三种操作：改群名 / 改群主 / 解散群

(function() {
    var doc = $.context.getCurrentDocument();
    var currentUserId = $.context.getCurrentUserId();
    
    var chatId = doc.getElementByName("选择群").getValue();
    var operationType = doc.getElementByName("操作类型").getValue(); // "改群名" / "改群主" / "解散群"
    
    if (chatId == null || operationType == null) {
        $.log.error("必填字段为空");
        return;
    }
    
    var token = getAppChatToken();
    if (token == null) return;
    var headers = {"Content-Type": "application/json"};
    
    try {
        if (operationType.indexOf("解散") >= 0) {
            // 解散群
            var dismissUrl = "https://qw.oa.gyzq.com/cgi-bin/appchat/dismiss?access_token=" + token;
            var body = {"chatid": chatId};
            var resp = $.httpclient.sendPost(dismissUrl, null, headers, $.json.objectToJsonString(body));
            var respObj = $.json.stringToJsonObject(resp);
            
            if (respObj.getInt("errcode") == 0) {
                $.message.sendGeneralStationMessage("群聊已解散", "群聊" + chatId + "已成功解散", currentUserId);
            } else {
                $.log.error("解散群失败: " + respObj.getString("errmsg"));
            }
        } else {
            // 改群名 / 改群主
            var updateUrl = "https://qw.oa.gyzq.com/cgi-bin/appchat/update?access_token=" + token;
            var body = {"chatid": chatId};
            
            if (operationType.indexOf("群名") >= 0) {
                var newName = doc.getElementByName("新群名").getValue();
                body["name"] = newName;
            } else if (operationType.indexOf("群主") >= 0) {
                var newOwner = doc.getElementByName("新群主").getValue();
                body["owner"] = newOwner;
            }
            
            var resp = $.httpclient.sendPost(updateUrl, null, headers, $.json.objectToJsonString(body));
            var respObj = $.json.stringToJsonObject(resp);
            
            if (respObj.getInt("errcode") == 42001) {
                token = getAppChatToken();
                updateUrl = "https://qw.oa.gyzq.com/cgi-bin/appchat/update?access_token=" + token;
                resp = $.httpclient.sendPost(updateUrl, null, headers, $.json.objectToJsonString(body));
                respObj = $.json.stringToJsonObject(resp);
            }
            
            var success = (respObj.getInt("errcode") == 0);
            $.message.sendGeneralStationMessage(
                "群信息变更" + (success ? "成功" : "失败"),
                "操作：" + operationType + "\n结果：" + (success ? "成功" : respObj.getString("errmsg")),
                currentUserId
            );
        }
    } catch (e) {
        $.log.error("群信息变更异常: " + e.toString());
    }
})();
