import os
import json
import time
import requests
from pathlib import Path
from urllib.parse import quote

# ==================== 配置常量（对齐TS） ====================
BASE_URL = "https://ilinkai.weixin.qq.com"
BOT_TYPE = "3"
QR_POLL_TIMEOUT_MS = 35000
MAX_QR_REFRESH = 3  # 新增：二维码最大刷新次数
CONFIRMED_TIMEOUT = 30  # confirmed状态超时
GLOBAL_TIMEOUT = 3 * 60  # 全局登录超时设置3min
CREDENTIALS_PATH = Path("data/credentials.json")

# ==================== 核心工具函数（修复字段/超时） ====================
def fetchQRCode() -> dict:
    """获取登录二维码（对齐TS接口参数）"""
    url = f"{BASE_URL}/ilink/bot/get_bot_qrcode?bot_type={BOT_TYPE}"
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        raise Exception(f"获取二维码失败: {str(e)}")

def pollQRStatus(qrcodeStr: str) -> dict:
    """轮询二维码状态（修复超时逻辑+对齐TS请求头）"""
    url = f"{BASE_URL}/ilink/bot/get_qrcode_status?qrcode={quote(qrcodeStr)}"
    headers = {
        "iLink-App-ClientVersion": "1",
        # 补充TS里的其他头字段（如果有）
    }
    
    try:
        # 对齐TS的AbortController：用timeout实现请求超时
        res = requests.get(url, headers=headers, timeout=QR_POLL_TIMEOUT_MS / 1000)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.Timeout:
        return {"status": "wait"}
    except Exception as e:
        raise Exception(f"轮询二维码状态失败: {str(e)}")

def displayQRCode(qrcodeUrl: str):
    """控制台显示二维码"""
    print("\n" + "="*50)
    print("请用微信扫描下方二维码登录")
    print("复制链接打开：")
    print(qrcodeUrl)
    print("="*50 + "\n")

# ==================== 凭证存储（修复字段校验） ====================
def saveCredentials(creds: dict):
    """保存登录凭证（对齐TS的字段名）"""
    try:
        CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CREDENTIALS_PATH, "w", encoding="utf-8") as f:
            json.dump(creds, f, indent=2, ensure_ascii=False)
        try:
            os.chmod(CREDENTIALS_PATH, 0o600)
        except:
            pass
        print(f"💾 凭证已保存到：{CREDENTIALS_PATH.absolute()}")
    except Exception as e:
        raise Exception(f"保存凭证失败：{str(e)}")

def loadCredentials() -> dict | None:
    """加载本地凭证（对齐TS的字段校验）"""
    try:
        if not CREDENTIALS_PATH.exists():
            return None
        with open(CREDENTIALS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        # 校验TS里的核心字段：bot_token/ilink_bot_id/baseUrl
        if all(k in data for k in ["bot_token", "ilink_bot_id", "baseUrl"]):
            return data
        return None
    except:
        return None

def clearCredentials():
    """清除登录凭证"""
    try:
        if CREDENTIALS_PATH.exists():
            CREDENTIALS_PATH.unlink()
    except:
        pass

# ==================== 完整登录流程（对齐TS逻辑） ====================
def login_with_poll():
    """
    修复点：
    1. 新增scaned状态处理
    2. 对齐TS的字段名（bot_token/ilink_bot_id）
    3. 新增二维码刷新逻辑（MAX_QR_REFRESH）
    4. 新增全局8分钟超时
    5. 统一轮询间隔为1秒（对齐TS）
    """
    local = loadCredentials()
    if local:
        print("✅ 已使用本地凭证登录")
        return local

    # 初始化变量（对齐TS）
    refresh_count = 0
    global_start_time = time.time()  # 全局超时计时
    qr_resp = fetchQRCode()
    qrcode_url = qr_resp["qrcode_img_content"]
    qrcode_str = qr_resp["qrcode"]
    displayQRCode(qrcode_url)

    confirmed_start_time = None  # confirmed状态计时

    # 核心轮询逻辑（对齐TS的while循环）
    while time.time() - global_start_time < GLOBAL_TIMEOUT:
        # 检查全局超时
        if time.time() - global_start_time > GLOBAL_TIMEOUT:
            raise Exception("❌ 登录超时（8分钟）")

        # 轮询状态
        status = pollQRStatus(qrcode_str)
        current_status = status.get("status")
        print(f"🔍 扫码状态：{current_status}")

        # 状态分支（完全对齐TS：wait/scaned/expired/confirmed）
        if current_status == "confirmed":
            print("⌛ 已扫码确认，等待登录完成...")
            # 校验TS里的核心字段
            bot_token = status.get("bot_token")
            ilink_bot_id = status.get("ilink_bot_id")
            if not bot_token or not ilink_bot_id:
                # 初始化confirmed计时，超时则抛异常
                if not confirmed_start_time:
                    confirmed_start_time = time.time()
                if time.time() - confirmed_start_time > CONFIRMED_TIMEOUT:
                    raise Exception(f"❌ Confirmed状态等待超时（{CONFIRMED_TIMEOUT}秒），且未获取到凭证")
                time.sleep(1)
                continue
            # 确认状态下提取凭证（对齐TS）
            creds = {
                "bot_token": bot_token,
                "ilink_bot_id": ilink_bot_id,
                "baseUrl": status.get("baseurl") or BASE_URL
            }
            saveCredentials(creds)
            print(f"✅ 扫码登录成功！accountId={ilink_bot_id}")
            return creds

        elif current_status == "scaned":
            print("📱 已扫码，请在手机上确认...")
            confirmed_start_time = None  # 重置confirmed计时
            time.sleep(1)

        elif current_status == "expired":
            refresh_count += 1
            if refresh_count >= MAX_QR_REFRESH:
                raise Exception(f"❌ 二维码多次过期（{MAX_QR_REFRESH}次），请重试")
            print(f"⚠️ 二维码已过期，正在刷新... ({refresh_count}/{MAX_QR_REFRESH})")
            # 重新获取二维码
            qr_resp = fetchQRCode()
            qrcode_url = qr_resp["qrcode_img_content"]
            qrcode_str = qr_resp["qrcode"]
            displayQRCode(qrcode_url)
            confirmed_start_time = None
            time.sleep(1)

        elif current_status == "wait":
            confirmed_start_time = None
            time.sleep(1)

        else:
            # 未知状态，按wait处理
            confirmed_start_time = None
            time.sleep(1)

    raise Exception("❌ 登录超时")

# ==================== 测试入口 ====================
if __name__ == "__main__":
    try:
        result = login_with_poll()
        print("🎉 最终登录凭证：")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print("❌ 登录失败：", e)
        result = "登录失败"
        print(json.dumps(result, indent=2, ensure_ascii=False))
# auth.py 末尾新增
login = login_with_poll  # 新增别名，匹配ollama-engine.py的导入名