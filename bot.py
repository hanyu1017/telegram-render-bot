import os
import json
import logging
import asyncio
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)

# Telegram Bot Token
TOKEN = os.getenv("BOT_TOKEN")

# Firebase 初始化
if not firebase_admin._apps:
    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if not cred_json:
        raise ValueError("找不到 FIREBASE_CREDENTIALS_JSON 環境變數")
    cred_data = json.loads(cred_json)
    cred = credentials.Certificate(cred_data)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 設定 log
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# 指令處理器: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 歡迎使用碳排放監控機器人！\n輸入 /carbon 來查詢碳排資料。")

# 指令處理器: /carbon
async def carbon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        doc = db.collection("carbon_data").document("summary").get()
        if doc.exists:
            data = doc.to_dict()
            response = (
                f"📊 最新碳排資訊：\n"
                f"🏭 工廠：{data.get('plant', '未提供')}\n"
                f"🌿 排放量：{data.get('co2e', 'N/A')} kg\n"
                f"🕒 時間：{data.get('timestamp', '未知')}"
            )
        else:
            response = "⚠️ Firebase 中尚未有 summary 資料。"
    except Exception as e:
        logging.error(f"查詢 Firebase 發生錯誤：{e}")
        response = "❌ 發生錯誤，請稍後再試。"

    await update.message.reply_text(response)

# 主執行函數
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("carbon", carbon))

    await app.run_polling()

if __name__ == "__main__":
    import sys
    if sys.platform.startswith("win") or sys.platform == "darwin":
        asyncio.run(main())
    else:
        # for environments that already run an event loop (e.g. Railway)
        loop = asyncio.get_event_loop()
        loop.create_task(main())
        loop.run_forever()
