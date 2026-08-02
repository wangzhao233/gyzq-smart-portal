// ===== 微盘共享空间管理 — 场景1：共享空间新建 =====
// 脚本位置：流程表单「共享空间新建」→ 审批流程 → 执行后脚本
// ⚠️ 前置：将公共函数/下的 getWeDriveToken.js 和 handleTokenExpired.js 复制到本脚本顶部
// 对应搭建指南：七巧低码-微盘群聊-搭建指南.md → 一 → 1.2

(function() {
    var appId = $.context.getCurrentApplicationId();
    var doc = $.context.getCurrentDocument();
    var currentUserId = $.context.getCurrentUserId();
    
    // 1. 获取表单字段值
    var spaceName = doc.getElementByName("空间名称").getValue();
    var departmentId = doc.getElementByName("申请部门").getValue();
    var extraAdmins = doc.getElementByName("空间管理员（可选）").getValue(); // 可能为空
    
    if (spaceName == null || departmentId == null) {
        $.log.error("必填字段为空：空间名称或申请部门");
        doc.getElementByName("创建结果").setValue("失败：必填字段为空");
        return;
    }
    
    // 2. 构造auth_info：部门负责人(auth=7) + 可选管理员(auth=7) + 部门全员(auth=1)
    var authInfo = new Packages.java.util.ArrayList();
    
    // 部门负责人（申请人）— type=1 个人, auth=7 管理员
    var adminObj = new Packages.java.util.HashMap();
    adminObj.put("type", 1);
    adminObj.put("userid", currentUserId);
    adminObj.put("auth", 7);
    authInfo.add(adminObj);
    
    // 可选管理员
    if (extraAdmins != null && extraAdmins != "") {
        var adminList = extraAdmins.split(",");
        for (var i = 0; i < adminList.length && i < 2; i++) {
            var extraObj = new Packages.java.util.HashMap();
            extraObj.put("type", 1);
            extraObj.put("userid", adminList[i].trim());
            extraObj.put("auth", 7);
            authInfo.add(extraObj);
        }
    }
    
    // 申请部门全员 — type=2 部门, auth=1 仅下载
    var deptObj = new Packages.java.util.HashMap();
    deptObj.put("type", 2);
    deptObj.put("departmentid", parseInt(departmentId));
    deptObj.put("auth", 1);
    authInfo.add(deptObj);
    
    // 3. 获取token
    var token = getWeDriveToken();
    if (token == null) {
        doc.getElementByName("创建结果").setValue("失败：获取access_token失败");
        $.message.sendGeneralStationMessage("共享空间创建失败", "获取企微access_token失败，请联系管理员", currentUserId);
        return;
    }
    
    // 4. 调用space_create API
    var createUrl = "https://qw.oa.gyzq.com/cgi-bin/wedrive_new/space_create?access_token=" + token;
    var body = {
        "space_name": spaceName,
        "auth_info": authInfo,
        "space_sub_type": 0
    };
    var headers = {"Content-Type": "application/json"};
    
    try {
        var resp = $.httpclient.sendPost(createUrl, null, headers, $.json.objectToJsonString(body));
        var respObj = $.json.stringToJsonObject(resp);
        var errcode = respObj.getInt("errcode");
        
        if (errcode == 42001) {
            token = getWeDriveToken();
            if (token == null) {
                doc.getElementByName("创建结果").setValue("失败：token过期后重新获取失败");
                return;
            }
            createUrl = "https://qw.oa.gyzq.com/cgi-bin/wedrive_new/space_create?access_token=" + token;
            resp = $.httpclient.sendPost(createUrl, null, headers, $.json.objectToJsonString(body));
            respObj = $.json.stringToJsonObject(resp);
            errcode = respObj.getInt("errcode");
        }
        
        if (errcode == 0) {
            var spaceId = respObj.getString("spaceid");
            doc.getElementByName("空间ID（spaceid）").setValue(spaceId);
            doc.getElementByName("创建结果").setValue("成功");
            doc.getElementByName("创建时间").setValue($.date.getCurrentDate());
            
            $.message.sendGeneralStationMessage(
                "共享空间创建成功",
                "您申请的【" + spaceName + "】共享空间已创建完成，空间ID：" + spaceId + "。部门成员已自动加入空间（仅下载权限）。",
                currentUserId
            );
            $.log.info("共享空间创建成功: " + spaceName + " (spaceid=" + spaceId + ")");
        } else {
            var errmsg = respObj.getString("errmsg");
            doc.getElementByName("创建结果").setValue("失败：" + errmsg + " (errcode=" + errcode + ")");
            $.log.error("创建空间失败: errcode=" + errcode + ", errmsg=" + errmsg);
            $.message.sendGeneralStationMessage(
                "共享空间创建失败",
                "【" + spaceName + "】创建失败：" + errmsg + "（错误码：" + errcode + "）",
                currentUserId
            );
        }
    } catch (e) {
        doc.getElementByName("创建结果").setValue("失败：脚本异常 " + e.toString());
        $.log.error("脚本异常: " + e.toString());
    }
})();
