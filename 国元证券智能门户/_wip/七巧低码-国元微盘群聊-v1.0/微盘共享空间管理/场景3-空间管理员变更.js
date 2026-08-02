// ===== 微盘共享空间管理 — 场景3：空间管理员变更 =====
// 脚本位置：流程表单「空间管理员变更」→ 审批流程 → 执行后脚本
// ⚠️ 前置：将公共函数/下的 getWeDriveToken.js 复制到本脚本顶部
// ⚠️ 程文斐userid需确认：目前使用占位值 "chengwenfei"

(function() {
    var doc = $.context.getCurrentDocument();
    var currentUserId = $.context.getCurrentUserId();
    
    var spaceId = doc.getElementByName("选择空间").getValue();
    var newAdmin = doc.getElementByName("新管理员").getValue();
    var reason = doc.getElementByName("变更原因").getValue();
    
    if (spaceId == null || newAdmin == null) {
        doc.getElementByName("新管理员添加结果").setValue("失败：空间或管理员为空");
        return;
    }
    
    // 1. 获取token
    var token = getWeDriveToken();
    if (token == null) {
        doc.getElementByName("新管理员添加结果").setValue("失败：获取token失败");
        return;
    }
    
    // 2. 调用space_acl_add添加新管理员
    var apiUrl = "https://qw.oa.gyzq.com/cgi-bin/wedrive_new/space_acl_add?access_token=" + token;
    var body = {
        "spaceid": spaceId,
        "auth_info": [
            {"type": 1, "userid": newAdmin, "auth": 7}
        ]
    };
    var headers = {"Content-Type": "application/json"};
    
    try {
        var resp = $.httpclient.sendPost(apiUrl, null, headers, $.json.objectToJsonString(body));
        var respObj = $.json.stringToJsonObject(resp);
        var errcode = respObj.getInt("errcode");
        
        if (errcode == 42001) {
            token = getWeDriveToken();
            apiUrl = "https://qw.oa.gyzq.com/cgi-bin/wedrive_new/space_acl_add?access_token=" + token;
            resp = $.httpclient.sendPost(apiUrl, null, headers, $.json.objectToJsonString(body));
            respObj = $.json.stringToJsonObject(resp);
            errcode = respObj.getInt("errcode");
        }
        
        if (errcode == 0) {
            doc.getElementByName("新管理员添加结果").setValue("成功");
            
            // 通知新管理员
            $.message.sendGeneralStationMessage(
                "微盘管理员变更通知",
                "您已被添加为共享空间的管理员（空间ID：" + spaceId + "）。",
                newAdmin
            );
            
            // 通知企微管理员移除旧管理员
            var adminUserId = "chengwenfei"; // ⚠️ 需确认
            $.message.sendGeneralStationMessage(
                "微盘管理员变更 — 需移除旧管理员",
                "空间ID：" + spaceId + "已添加新管理员" + newAdmin + "。请手动移除旧管理员的微盘权限。变更原因：" + reason,
                adminUserId
            );
            
            doc.getElementByName("通知结果").setValue("已通知企微管理员移除旧管理员");
            $.log.info("管理员变更成功: spaceid=" + spaceId + ", newAdmin=" + newAdmin);
        } else {
            var errmsg = respObj.getString("errmsg");
            doc.getElementByName("新管理员添加结果").setValue("失败：" + errmsg);
            $.log.error("添加管理员失败: " + errmsg);
        }
    } catch (e) {
        doc.getElementByName("新管理员添加结果").setValue("失败：脚本异常 " + e.toString());
        $.log.error("脚本异常: " + e.toString());
    }
})();
