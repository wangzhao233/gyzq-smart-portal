// ===== 部门群聊管理 — 场景1：创建部门群 =====
// 脚本位置：流程表单「创建部门群」→ 审批流程 → 执行后脚本
// ⚠️ 前置：将公共函数/下的 getAppChatToken.js 复制到本脚本顶部，并替换 secret 占位符
// ⚠️ 群聊secret待补充

(function() {
    var appId = $.context.getCurrentApplicationId();
    var doc = $.context.getCurrentDocument();
    var currentUserId = $.context.getCurrentUserId();
    
    var groupName = doc.getElementByName("群名称").getValue();
    var deptId = doc.getElementByName("所属部门").getValue();
    var ownerUserId = doc.getElementByName("群主").getValue();
    var extraMembers = doc.getElementByName("额外成员").getValue(); // 可能为空
    
    if (groupName == null || deptId == null || ownerUserId == null) {
        doc.getElementByName("创建结果").setValue("失败：必填字段为空");
        return;
    }
    
    // 1. 获取部门全部成员
    var userlist = new Packages.java.util.ArrayList();
    
    try {
        var deptUsers = $.contact.queryDepartmentUserList(parseInt(deptId));
        if (deptUsers != null) {
            for (var i = 0; i < deptUsers.size(); i++) {
                var user = deptUsers.get(i);
                var userId = user.getAccount();
                if (!userlist.contains(userId)) {
                    userlist.add(userId);
                }
            }
        }
    } catch (e) {
        $.log.warn("获取部门成员出错: " + e.toString() + "，继续创建群聊");
    }
    
    // 确保群主在列表里
    if (!userlist.contains(ownerUserId)) {
        userlist.add(ownerUserId);
    }
    
    // 添加额外成员
    if (extraMembers != null && extraMembers != "") {
        var extras = extraMembers.split(",");
        for (var j = 0; j < extras.length; j++) {
            var member = extras[j].trim();
            if (member != "" && !userlist.contains(member)) {
                userlist.add(member);
            }
        }
    }
    
    var memberCount = userlist.size();
    $.log.info("群聊成员数: " + memberCount + " (群主: " + ownerUserId + ")");
    
    // 2. 获取token
    var token = getAppChatToken();
    if (token == null) {
        doc.getElementByName("创建结果").setValue("失败：获取access_token失败");
        return;
    }
    
    // 3. 调用appchat/create
    var createUrl = "https://qw.oa.gyzq.com/cgi-bin/appchat/create?access_token=" + token;
    var body = {
        "name": groupName,
        "owner": ownerUserId,
        "userlist": userlist,
        "chatid": ""
    };
    var headers = {"Content-Type": "application/json"};
    
    try {
        var resp = $.httpclient.sendPost(createUrl, null, headers, $.json.objectToJsonString(body));
        var respObj = $.json.stringToJsonObject(resp);
        var errcode = respObj.getInt("errcode");
        
        if (errcode == 42001) {
            token = getAppChatToken();
            createUrl = "https://qw.oa.gyzq.com/cgi-bin/appchat/create?access_token=" + token;
            resp = $.httpclient.sendPost(createUrl, null, headers, $.json.objectToJsonString(body));
            respObj = $.json.stringToJsonObject(resp);
            errcode = respObj.getInt("errcode");
        }
        
        if (errcode == 0) {
            var chatId = respObj.getString("chatid");
            doc.getElementByName("群ID（chatid）").setValue(chatId);
            doc.getElementByName("创建结果").setValue("成功");
            doc.getElementByName("群成员数").setValue(memberCount);
            
            // 发送欢迎消息（让群在客户端显示）
            var sendUrl = "https://qw.oa.gyzq.com/cgi-bin/appchat/send?access_token=" + token;
            var msgBody = {
                "chatid": chatId,
                "msgtype": "text",
                "text": {"content": "欢迎加入【" + groupName + "】！本群由部门群聊管理系统自动创建。"},
                "safe": 0
            };
            $.httpclient.sendPost(sendUrl, null, headers, $.json.objectToJsonString(msgBody));
            
            $.message.sendGeneralStationMessage(
                "部门群创建成功",
                "【" + groupName + "】已创建成功，群成员" + memberCount + "人",
                currentUserId
            );
            $.log.info("部门群创建成功: " + groupName + " (chatid=" + chatId + ")");
        } else {
            var errmsg = respObj.getString("errmsg");
            doc.getElementByName("创建结果").setValue("失败：" + errmsg);
            $.log.error("创建群聊失败: " + errmsg);
            $.message.sendGeneralStationMessage(
                "部门群创建失败",
                "【" + groupName + "】创建失败：" + errmsg + "（错误码：" + errcode + "）",
                currentUserId
            );
        }
    } catch (e) {
        doc.getElementByName("创建结果").setValue("失败：脚本异常 " + e.toString());
        $.log.error("脚本异常: " + e.toString());
    }
})();
