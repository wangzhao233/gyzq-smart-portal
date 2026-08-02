// ===== 公共函数：获取微盘 access_token =====
// 用途：微盘共享空间管理应用的3个场景共用
// 位置：复制到每个脚本的顶部

function getWeDriveToken() {
    var corpid = "ww3a805f9cde3da4c2";
    var secret = "IcJJQnQJKXGPIdtu_-HSzTZpawKtliVmrZs7iB1SlCo";
    var url = "https://qw.oa.gyzq.com/cgi-bin/gettoken";
    var params = new Packages.java.util.HashMap();
    params.put("corpid", corpid);
    params.put("corpsecret", secret);
    var headers = new Packages.java.util.HashMap();
    headers.put("Content-Type", "application/json;charset=UTF-8");
    var resp = $.httpclient.sendGet(url, params, headers);
    var obj = $.json.stringToJsonObject(resp);
    var token = obj.getString("access_token");
    if (token == null || token == "") {
        $.log.error("获取access_token失败: " + resp);
        return null;
    }
    $.log.info("获取access_token成功: " + token.substring(0, 10) + "...");
    return token;
}
