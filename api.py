# 导入第三方库：requests用于发送HTTP请求，uuid生成唯一消息ID，random生成随机数，base64用于编码
import requests
import uuid
import random
import base64
global api_post
# ==================== 工具函数 ====================
def random_wechat_uin():
    """
    uint32字符串Base64
    """
    # 生成32位无符号整数（uint32范围：0 ~ 4294967295）
    uint32_num = random.randint(0, 4294967295)
    # 转十进制字符串 → 转字节 → Base64编码 → 解码为字符串
    return base64.b64encode(str(uint32_num).encode('utf-8')).decode('utf-8')

def build_headers(token=None):
    """
    构建接口请求的通用请求头
    参数：
        token (str, 可选): 接口鉴权的Bearer Token，不传则不添加Authorization头
    返回值：
        dict: 构造完成的请求头字典
    """
    # 基础请求头：固定客户端版本、网络类型，随机UIN
    headers = {
        "Content-Type": "application/json",  # 显式声明
        "AuthorizationType": "ilink_bot_token",  # 补充协议要求的鉴权类型
        "X-WECHAT-UIN": random_wechat_uin(),  # 修正为协议要求的字段名
        "iLink-App-ClientVersion": "1",
        "iLink-App-NetType": "wifi",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers
# ==================== 通用 POST 请求封装 ====================
def api_post(url, data, token=None, timeout=15):
    """
    封装接口通用的POST请求逻辑，统一处理请求头、异常、响应解析
    参数：
        url (str): 接口完整URL
        data (dict): POST请求的JSON参数
        token (str, 可选): 接口鉴权token
        timeout (int, 可选): 请求超时时间，默认15秒
    返回值：
        dict: 接口响应的JSON数据；若异常，返回空消息+空缓冲区的默认字典
    异常处理：
        1. 超时异常：返回空消息列表+空缓冲区
        2. 其他异常（连接失败、JSON解析失败等）：返回空消息列表+空缓冲区
    """
    try:
        # 构建请求头（含随机UIN、鉴权token）
        headers = build_headers(token)
        # 发送POST请求：JSON格式传参，自定义超时时间
        resp = requests.post(url, json=data, headers=headers, timeout=timeout)
        # 主动触发HTTP状态码异常（如401鉴权失败、500服务端错误）
        resp.raise_for_status()
        # 解析响应为JSON并返回
        return resp.json()
    except requests.exceptions.Timeout:
        # 超时异常：返回默认空数据，避免业务代码崩溃
        return {"msgs": [], "get_updates_buf": ""}
    except Exception:
        # 其他所有异常（连接失败、JSON解析失败等）：返回默认空数据
        return {"msgs": [], "get_updates_buf": ""}

# ==================== 拉取微信消息（核心接口） ====================
def get_updates(base_url, token, get_updates_buf):
    """
    拉取微信/iLink机器人的新消息（增量拉取）
    核心逻辑：通过get_updates_buf实现增量拉取，只获取上次拉取后的新消息
    参数：
        base_url (str): 接口基础域名（如https://xxx.com）
        token (str): 接口鉴权token
        get_updates_buf (str): 消息更新缓冲区，首次传空字符串，后续用接口返回的新值
    返回值：
        dict: 接口响应数据，结构如下：
            {
                "msgs": [消息列表],  # 新消息数组，每条消息包含发送人、内容、类型等
                "get_updates_buf": str  # 新的缓冲区，下次拉取需传入该值
            }
    """
    # 拼接拉取消息的完整接口URL
    url = f"{base_url}/ilink/bot/getupdates"
    # 构造请求参数：传入缓冲区实现增量拉取
    data = {"get_updates_buf": get_updates_buf}
    # 调用通用POST函数，返回接口响应
    return api_post(url, data, token, timeout=35)  # 拉取消息超时设为35秒（需等待服务端返回新消息）

# ==================== 发送文本消息 ====================
def send_text_message(base_url, token, to_user_id, content, context_token):
    """
    修复：context_token 从可选改为必传（协议强制要求）
    补充：参数校验 + 错误日志，便于定位 ret:-2 问题
    """
    # 1. 必传参数校验（缺失直接返回错误）
    if not context_token:
        print(f"[错误] context_token 不能为空（ret:-2 核心原因）")
        return {"ret": -2, "msg": "context_token is required"}
    if not to_user_id:
        print(f"[错误] to_user_id 不能为空")
        return {"ret": -2, "msg": "to_user_id is required"}
    if not content:
        content = " "  # 兜底：避免空内容
    
    # 2. 确认接口域名是官方固定值（防止传错）
    if base_url != "https://ilinkai.weixin.qq.com":
        print(f"[警告] 非官方域名，可能导致 ret:-2，建议使用：https://ilinkai.weixin.qq.com")
    
    # 3. 拼接正确的接口 URL
    url = f"{base_url}/ilink/bot/sendmessage"
    
    # 4. 构造合规的请求参数（严格按协议）
    data = {
        "msg":{
            "from_user_id": "",
            "to_user_id": to_user_id,           # 接收方ID（用户/群聊）
            "client_id": str(uuid.uuid4()), # 唯一消息ID（UUID格式）
            "message_type": 2,                  # 固定值：Bot消息
            "message_state": 2,                 # 固定值：发送完成
            "item_list": [
                {"type": 1, "text_item": {"text": content}}
            ],
        },
        "base_info": {"channel_version": "1.0.3"},  # 必须包含的基础信息
    }
    
    # 5. 发送请求并打印日志（便于排查）
    print(f"[发送消息请求] URL: {url}")
    print(f"[发送消息请求头] {build_headers(token)}")
    print(f"[发送消息参数] {data}")
    
    response = api_post(url, data, token)
    print(f"[发送消息响应] {response}")
    
    return response
# ==================== 消息文本提取工具函数 ====================
def extract_text_from_message(msg):
    """
    从拉取的消息结构体中提取文本内容（适配实际接口返回的字段）
    参数：
        msg (dict): 单条消息结构体（来自get_updates的msgs数组）
    返回值：
        str: 提取到的文本内容；若提取失败/无文本，返回空字符串
    """
    try:
        # 遍历消息中的item_list（替代原items）
        for item in msg.get("item_list", []):
            # 文本类型仍为1，提取text_item.text（替代原content）
            if item.get("type") == 1:
                return item.get("text_item", {}).get("text", "")
    except Exception as e:
        # 打印异常便于调试（可选）
        print(f"提取消息文本失败：{e}")
        return ""
# ==================== 独立运行逻辑 ====================
import time  # 用于循环间隔，避免高频请求

if __name__ == "__main__":
    # 配置项：请替换为实际的接口域名和鉴权token
    BASE_URL = "https://ilinkai.weixin.qq.com"  # 接口基础域名
    TOKEN = "a7fb3379e10e@im.bot:0600006ed6d2261f623126f12c0cc806695b9b"  # 接口鉴权token
    
    # 初始化消息缓冲区（增量拉取用）
    get_updates_buf = ""
    
    print("===== 微信机器人消息监听启动 =====")
    print(f"接口地址: {BASE_URL}")
    print("开始拉取消息（按Ctrl+C停止）...\n")
    
    try:
        while True:
            # 1. 拉取新消息（调用原有get_updates函数）
            # 重写get_updates内部的api_post逻辑，增加响应打印
            def api_post_with_print(url, data, token=None, timeout=15):
                try:
                    headers = build_headers(token)
                    resp = requests.post(url, json=data, headers=headers, timeout=timeout)
                    resp.raise_for_status()
                    response_json = resp.json()
                    # 打印HTTP响应核心信息
                    print(f"\n===== HTTP响应信息 =====")
                    print(f"请求URL: {url}")
                    print(f"响应状态码: {resp.status_code}")
                    print(f"响应内容: {response_json}")
                    return response_json
                except requests.exceptions.Timeout:
                    print(f"\n===== HTTP请求超时 =====")
                    print(f"请求URL: {url}")
                    return {"msgs": [], "get_updates_buf": ""}
                except Exception as e:
                    print(f"\n===== HTTP请求异常 =====")
                    print(f"请求URL: {url}")
                    print(f"异常信息: {str(e)}")
                    return {"msgs": [], "get_updates_buf": ""}
            
            # 临时替换api_post为带打印的版本
            
            original_api_post = api_post
            api_post = api_post_with_print
            
            # 拉取消息
            response = get_updates(BASE_URL, TOKEN, get_updates_buf)
            
            # 恢复原api_post函数
            api_post = original_api_post
            
            # 2. 更新缓冲区（用于下次增量拉取）
            get_updates_buf = response.get("get_updates_buf", "")
            
            # 3. 提取并打印微信用户输入的文本消息
            if response.get("msgs"):
                print(f"\n===== 拉取到新消息 =====")
                for idx, msg in enumerate(response["msgs"], 1):
                    sender_id = msg.get("from_user_id", "未知发送人")
                    text_content = extract_text_from_message(msg)
                    
                    print(f"消息{idx} - 发送人ID: {sender_id} | 内容: {text_content}")
            
            # 4. 间隔1秒，避免高频请求
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n===== 监听停止 =====")