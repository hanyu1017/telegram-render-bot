import os
import json
import logging
import asyncio
import random
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 初始化 Telegram Bot Token
TOKEN = os.getenv("BOT_TOKEN")

# Firebase 初始化
if not firebase_admin._apps:
    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    cred_data = json.loads(cred_json)
    cred = credentials.Certificate(cred_data)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Logging 設定
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# 定時任務：每小時寫入模擬資料
def write_fake_data():
    data = {
        "plant": random.choice(["台中廠", "台南廠", "林口廠"]),
        "co2e": round(random.uniform(1200, 2500), 2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db.collection("carbon_data").document("summary").set(data)
    logging.info(f"✅ 定時寫入碳排資料：{data}")

# /start 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 歡迎使用碳排放監控機器人！\n輸入 /carbon 查詢碳排資料。")

# /carbon 指令
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

# 主函數
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("carbon", carbon))

    # 定時排程
    scheduler = AsyncIOScheduler()
    scheduler.add_job(write_fake_data, "interval", hours=1)
    scheduler.start()

    await app.initialize()
    await app.start()
    logging.info("✅ Bot is running with hourly Firestore updates.")
    await asyncio.Event().wait()

# Railway 執行方式
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
