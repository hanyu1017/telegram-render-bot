import os
import asyncio
import json
import random
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from openai import OpenAI

# === 環境變數 ===
TOKEN = os.getenv("BOT_TOKEN", "")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://cfmcloud.vercel.app")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# === 初始化 OpenAI 客戶端 ===
client = OpenAI(api_key=OPENAI_API_KEY)

# === 模擬汽車訂單資料 ===
CAR_MODELS = {
    "Tesla Model 3": {"wait_time": "2-3個月", "delivery_estimate": "預計2025年9-10月交車"},
    "Tesla Model Y": {"wait_time": "3-4個月", "delivery_estimate": "預計2025年10-11月交車"},
    "Tesla Model S": {"wait_time": "4-5個月", "delivery_estimate": "預計2025年11-12月交車"},
    "Tesla Model X": {"wait_time": "5-6個月", "delivery_estimate": "預計2026年1-2月交車"},
    "BYD Han": {"wait_time": "1-2個月", "delivery_estimate": "預計2025年8-9月交車"},
    "BYD Tang": {"wait_time": "2-3個月", "delivery_estimate": "預計2025年9-10月交車"},
    "BMW iX": {"wait_time": "6-8個月", "delivery_estimate": "預計2026年1-3月交車"},
    "Audi e-tron": {"wait_time": "4-6個月", "delivery_estimate": "預計2025年11月-2026年1月交車"},
}

# 模擬客戶訂單資料
CUSTOMER_ORDERS = {
    "T001": {
        "customer_name": "王小明",
        "model": "Tesla Model 3",
        "order_date": "2025-05-15",
        "status": "生產中",
        "estimated_delivery": "2025-09-20",
        "current_progress": "車輛已進入最終組裝階段"
    },
    "T002": {
        "customer_name": "李美華",
        "model": "Tesla Model Y",
        "order_date": "2025-04-20",
        "status": "準備出貨",
        "estimated_delivery": "2025-08-15",
        "current_progress": "車輛品質檢測完成，準備發送"
    },
    "B001": {
        "customer_name": "陳志偉",
        "model": "BYD Han",
        "order_date": "2025-06-01",
        "status": "排程生產",
        "estimated_delivery": "2025-08-30",
        "current_progress": "訂單已確認，排入生產排程"
    },
    "B002": {
        "customer_name": "張雅婷",
        "model": "BYD Tang",
        "order_date": "2025-05-10",
        "status": "生產中",
        "estimated_delivery": "2025-09-10",
        "current_progress": "電池系統安裝中"
    }
}

# === ESG與碳排放相關資料 ===
ESG_DATA = {
    "carbon_reduction_targets": {
        "2025": "減少25%碳排放",
        "2030": "減少50%碳排放", 
        "2050": "達成淨零排放"
    },
    "esg_policies": [
        "循環經濟推動計畫",
        "綠色供應鏈管理",
        "員工多元化與包容性政策",
        "社區投資與社會責任",
        "透明度與公司治理"
    ],
    "carbon_footprint": {
        "scope1": "直接排放：12,500噸CO2e/年",
        "scope2": "能源間接排放：8,300噸CO2e/年",
        "scope3": "其他間接排放：45,200噸CO2e/年"
    }
}

# === 身份識別系統 ===
USER_ROLES = {}  # 儲存用戶身份

def get_user_role(chat_id):
    """獲取用戶身份，預設為消費者"""
    return USER_ROLES.get(chat_id, "consumer")

def set_user_role(chat_id, role):
    """設定用戶身份"""
    USER_ROLES[chat_id] = role

# === AI回應功能 ===
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_role = get_user_role(chat_id)
    prompt = " ".join(context.args)
    
    if not prompt:
        role_examples = {
            "manager": "例如：/ask 我們公司的碳排放目標是什麼？",
            "consumer": "例如：/ask 我的訂單T001現在狀況如何？",
            "dealer": "例如：/ask Tesla Model 3現在要等多久？"
        }
        await update.message.reply_text(f"請輸入你想問的問題，{role_examples.get(user_role, role_examples['consumer'])}")
        return

    await update.message.reply_text("🤖 正在為您查詢，請稍候...")

    try:
        # 根據身份設定不同的AI角色
        system_prompts = {
            "manager": f"""你是一位對碳排放政策及ESG非常了解的公司助理。你可以回答關於：
            - 碳排放目標：{ESG_DATA['carbon_reduction_targets']}
            - ESG政策：{', '.join(ESG_DATA['esg_policies'])}
            - 碳足跡資料：{ESG_DATA['carbon_footprint']}
            請以專業、詳細的方式回答管理層的問題。""",
            
            "consumer": f"""你是一位專業的汽車客戶服務經理，可以幫助客戶查詢訂單狀態。
            目前的訂單資料：{json.dumps(CUSTOMER_ORDERS, ensure_ascii=False, indent=2)}
            
            當客戶詢問訂單狀態時，請提供：
            1. 訂單當前狀態
            2. 預計交車時間
            3. 目前進度說明
            4. 任何需要注意的事項
            
            請以親切、專業的語調回答客戶問題。""",
            
            "dealer": f"""你是一位汽車經銷商助理，專門回答關於車輛等候時間和交車預估的問題。
            目前可供應的車型資訊：{json.dumps(CAR_MODELS, ensure_ascii=False, indent=2)}
            
            請提供準確的等候時間、交車預估，並給予客戶合理的期望管理。
            回答要包含具體的時間範圍和可能影響交車的因素。"""
        }
        
        system_prompt = system_prompts.get(user_role, system_prompts["consumer"])
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        answer = response.choices[0].message.content
        
        # 根據身份添加角色標識
        role_icons = {
            "manager": "🏢 ESG管理助理",
            "consumer": "🚗 客戶服務",
            "dealer": "🤝 經銷商服務"
        }
        
        role_name = role_icons.get(user_role, "🤖 AI助理")
        await update.message.reply_text(f"{role_name}：\n\n{answer}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ 系統回應失敗：{e}")

# === 開始指令 ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    # 身份選擇按鈕
    keyboard = [
        [
            InlineKeyboardButton("🏢 管理者 (ESG助理)", callback_data="role_manager"),
            InlineKeyboardButton("🚗 消費者 (客戶服務)", callback_data="role_consumer")
        ],
        [
            InlineKeyboardButton("🤝 經銷商 (業務支援)", callback_data="role_dealer"),
            InlineKeyboardButton("📊 前往儀表板", web_app={"url": WEB_APP_URL})
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = """🎯 歡迎使用多功能AI助理系統！

請選擇您的身份以獲得專業服務：

🏢 **管理者模式**：ESG政策與碳排放專家
🚗 **消費者模式**：汽車訂單查詢客服
🤝 **經銷商模式**：車輛交期與等候時間查詢

💡 選擇身份後，使用 /ask [問題] 來獲得專業回答"""

    await update.message.reply_text(welcome_message, reply_markup=reply_markup)

# === 處理身份選擇的回調 ===
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.from_user.id
    
    role_mapping = {
        "role_manager": ("manager", "🏢 ESG管理助理"),
        "role_consumer": ("consumer", "🚗 客戶服務經理"), 
        "role_dealer": ("dealer", "🤝 經銷商業務助理")
    }
    
    if query.data in role_mapping:
        role, role_name = role_mapping[query.data]
        set_user_role(chat_id, role)
        
        await query.answer()
        await query.edit_message_text(
            f"✅ 身份設定完成！您現在是 {role_name}\n\n"
            f"使用 /ask [問題] 來獲得專業回答\n"
            f"如需更換身份，請重新執行 /start"
        )

# === 主程式 ===
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    # 添加指令處理器
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ask", ask))
    
    # 添加按鈕回調處理器
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(button_callback))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("✅ 多功能AI助理Bot已啟動！")
    print("📋 功能：/start (選擇身份) + /ask (AI問答)")

if __name__ == "__main__":
    asyncio.run(main())