// ===== 微盘共享空间管理 — 场景2：共享空间扩容 =====
// 脚本位置：流程表单「共享空间扩容」→ 审批流程 → 执行后脚本
// ⚠️ 前置：将公共函数/下的 getWeDriveToken.js 复制到本脚本顶部
// 说明：微盘扩容无API，审批后通知企微管理员（程文斐）手动操作
// ⚠️ 程文斐userid需确认：目前使用占位值 "chengwenfei"

(function() {
    var doc = $.context.getCurrentDocument();
    var currentUserId = $.context.getCurrentUserId();
    
    var spaceName = doc.getElementByName("选择空间").getValue();
    var targetCapacity = doc.getElementByName("扩容至（GB）").getValue();
    var reason = doc.getElementByName("扩容原因").getValue();
    
    // 企微管理员 = 程文斐 (userid需确认)
    var adminUserId = "chengwenfei"; // ⚠️ 需确认程文斐的企微userid
    
    var msgContent = "【微盘扩容申请已批准】\n" +
        "空间：" + spaceName + "\n" +
        "扩容至：" + targetCapacity + "GB\n" +
        "原因：" + reason + "\n" +
        "\n请企微管理员在后台手动扩容，完成后在此单据中标记处理状态。";
    
    // 通知企微管理员
    $.message.sendGeneralStationMessage("微盘扩容通知", msgContent, adminUserId);
    
    // 同时通知申请人
    $.message.sendGeneralStationMessage(
        "扩容申请已批准",
        "您申请的【" + spaceName + "】扩容至" + targetCapacity + "GB已审批通过，已通知企微管理员处理。",
        currentUserId
    );
    
    doc.getElementByName("处理状态").setValue("待处理");
    $.log.info("扩容通知已发送: " + spaceName);
})();
