import os
import asyncio
import pytz
import json
import random
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import firebase_admin
from firebase_admin import credentials, firestore

# 環境變數
TOKEN = os.getenv("BOT_TOKEN", "")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://cfmcloud.web.app")
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON", "")

# Firebase 初始化
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(FIREBASE_CREDENTIALS_JSON))
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Firebase 路徑
SUBSCRIBERS_REF = db.collection("bot_subscribers")

# 加入訂閱
async def subscribe_user(chat_id):
    SUBSCRIBERS_REF.document(str(chat_id)).set({"subscribed": True})

# 取消訂閱
async def unsubscribe_user(chat_id):
    SUBSCRIBERS_REF.document(str(chat_id)).delete()

# 取得所有訂閱者
def get_all_subscribers():
    docs = SUBSCRIBERS_REF.stream()
    return [doc.id for doc in docs]

# /start 訂閱並顯示按鈕
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await subscribe_user(chat_id)

    keyboard = [[InlineKeyboardButton("打開 Mini App", web_app={"url": WEB_APP_URL})]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ 你已訂閱碳排通知。可輸入 /cancel 取消通知。", reply_markup=reply_markup)

# /cancel 取消訂閱
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await unsubscribe_user(chat_id)
    await update.message.reply_text("❌ 你已取消訂閱碳排通知。")

# /list 顯示所有訂閱者 chat_id
async def list_subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subs = get_all_subscribers()
    await update.message.reply_text("🧾 訂閱者清單：\n" + "\n".join(subs) if subs else "目前沒有任何訂閱者。")

# /broadcast <msg> 手動推播訊息給所有訂閱者
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("請輸入訊息，例如：/broadcast 測試訊息")
        return

    sent_count = 0
    for chat_id in get_all_subscribers():
        try:
            await context.bot.send_message(chat_id=int(chat_id), text=f"📢 管理員公告：\n{msg}")
            sent_count += 1
        except Exception as e:
            print(f"❌ 傳送失敗 chat_id={chat_id}: {e}")
    await update.message.reply_text(f"✅ 已發送給 {sent_count} 位訂閱者")

# 定時任務：模擬資料並推播
async def scheduled_task(application):
    data = {
        "plant": random.choice(["台中廠", "台南廠", "桃園廠"]),
        "co2e": round(random.uniform(1300, 2500), 2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db.collection("carbon_data").document("summary").set(data)

    text = (
        f"📡 自動上傳碳排資料：\n"
        f"🏭 {data['plant']}\n"
        f"🌿 {data['co2e']} kg CO₂e\n"
        f"🕒 {data['timestamp']}"
    )
    for chat_id in get_all_subscribers():
        try:
            await application.bot.send_message(chat_id=int(chat_id), text=text)
        except Exception as e:
            print(f"❌ 傳送失敗 chat_id={chat_id}: {e}")

# 主函數
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("list", list_subscribers))
    app.add_handler(CommandHandler("broadcast", broadcast))

    scheduler = AsyncIOScheduler(timezone=pytz.UTC)
    scheduler.add_job(lambda: asyncio.create_task(scheduled_task(app)), "interval", hours=1)
    scheduler.start()

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("✅ Bot 已啟動，支援 /start /cancel /list /broadcast")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
