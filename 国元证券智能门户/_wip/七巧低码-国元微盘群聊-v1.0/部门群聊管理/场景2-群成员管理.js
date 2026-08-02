// ===== 部门群聊管理 — 场景2：群成员管理 =====
// 脚本位置：流程表单「群成员管理」→ 审批流程 → 执行后脚本
// ⚠️ 前置：将公共函数/下的 getAppChatToken.js 复制到本脚本顶部，并替换 secret 占位符

(function() {
    var doc = $.context.getCurrentDocument();
    var currentUserId = $.context.getCurrentUserId();
    
    var chatId = doc.getElementByName("选择群").getValue();
    var operationType = doc.getElementByName("操作类型").getValue(); // "添加成员" or "移除成员"
    var members = doc.getElementByName("选择成员").getValue();
    var reason = doc.getElementByName("操作原因").getValue();
    
    if (chatId == null || members == null || operationType == null) {
        $.log.error("必填字段为空");
        return;
    }
    
    var memberList = members.split(",");
    
    // 获取token
    var token = getAppChatToken();
    if (token == null) return;
    
    // 构造请求
    var updateUrl = "https://qw.oa.gyzq.com/cgi-bin/appchat/update?access_token=" + token;
    var body = {"chatid": chatId};
    
    if (operationType.indexOf("添加") >= 0) {
        body["add_user_list"] = memberList;
    } else {
        body["del_user_list"] = memberList;
    }
    
    var headers = {"Content-Type": "application/json"};
    
    try {
        var resp = $.httpclient.sendPost(updateUrl, null, headers, $.json.objectToJsonString(body));
        var respObj = $.json.stringToJsonObject(resp);
        var errcode = respObj.getInt("errcode");
        
        if (errcode == 42001) {
            token = getAppChatToken();
            updateUrl = "https://qw.oa.gyzq.com/cgi-bin/appchat/update?access_token=" + token;
            resp = $.httpclient.sendPost(updateUrl, null, headers, $.json.objectToJsonString(body));
            respObj = $.json.stringToJsonObject(resp);
            errcode = respObj.getInt("errcode");
        }
        
        var success = (errcode == 0);
        $.log.info("群成员管理结果: " + (success ? "成功" : "失败 ercode=" + errcode));
        
        $.message.sendGeneralStationMessage(
            "群成员管理" + (success ? "成功" : "失败"),
            "操作：" + operationType + "\n" +
            "成员：" + members + "\n" +
            "结果：" + (success ? "成功" : respObj.getString("errmsg")),
            currentUserId
        );
    } catch (e) {
        $.log.error("群成员管理异常: " + e.toString());
    }
})();
