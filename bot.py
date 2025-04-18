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
    ContextTypes
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import firebase_admin
from firebase_admin import credentials, firestore

# 環境變數
TOKEN = os.getenv("BOT_TOKEN", "")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://cfmcloud.web.app")
FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON", "")

# 初始化 Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(json.loads(FIREBASE_CREDENTIALS_JSON))
    firebase_admin.initialize_app(cred)
db = firestore.client()

# Firestore 路徑
SUBSCRIBERS_REF = db.collection("bot_subscribers")

# 用戶訂閱/取消訂閱邏輯
async def subscribe_user(chat_id):
    SUBSCRIBERS_REF.document(str(chat_id)).set({"subscribed": True})

async def unsubscribe_user(chat_id):
    SUBSCRIBERS_REF.document(str(chat_id)).delete()

def get_all_subscribers():
    docs = SUBSCRIBERS_REF.stream()
    return [doc.id for doc in docs]

# Bot 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await subscribe_user(chat_id)
    keyboard = [[InlineKeyboardButton("打開 Mini App", web_app={"url": WEB_APP_URL})]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ 你已訂閱碳排通知。可輸入 /cancel 取消通知。", reply_markup=reply_markup)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await unsubscribe_user(chat_id)
    await update.message.reply_text("❌ 你已取消訂閱碳排通知。")

async def list_subscribers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subs = get_all_subscribers()
    text = "📋 訂閱者 chat_id 清單：\n" + "\n".join(subs) if subs else "目前沒有任何訂閱者。"
    await update.message.reply_text(text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("請輸入訊息，例如：/broadcast 測試訊息")
        return

    count = 0
    for chat_id in get_all_subscribers():
        try:
            await context.bot.send_message(chat_id=int(chat_id), text=f"📢 管理員公告：\n{msg}")
            count += 1
        except Exception as e:
            print(f"❌ 傳送失敗 chat_id={chat_id}: {e}")
    await update.message.reply_text(f"✅ 已發送給 {count} 位訂閱者")

# ✅ /carbon 查詢最新碳排資料
async def carbon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        docs = (
            db.collection("carbon_data")
            .document("logs")
            .collection("entries")
            .order_by("timestamp", direction=firestore.Query.DESCENDING)
            .limit(1)
            .stream()
        )
        latest = next(docs, None)
        if latest:
            data = latest.to_dict()
            text = (
                f"📊 最新碳排資料：\n"
                f"🏭 工廠：{data['plant']}\n"
                f"🌿 CO₂e：{data['co2e']} kg\n"
                f"🕒 時間：{data['timestamp']}"
            )
        else:
            text = "⚠️ 尚無碳排放資料。"
    except Exception as e:
        text = f"❌ 發生錯誤：{e}"
    await update.message.reply_text(text)

# 定時任務
async def scheduled_task(application):
    data = {
        "plant": random.choice(["台中廠", "台南廠", "桃園廠"]),
        "co2e": round(random.uniform(1300, 2500), 2),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db.collection("carbon_data").document("logs").collection("entries").add(data)

    for chat_id in get_all_subscribers():
        try:
            await application.bot.send_message(
                chat_id=int(chat_id),
                text=(
                    f"📡 自動上傳碳排資料：\n"
                    f"🏭 {data['plant']}\n🌿 {data['co2e']} kg CO₂e\n🕒 {data['timestamp']}"
                )
            )
        except Exception as e:
            print(f"❌ 傳送失敗 chat_id={chat_id}: {e}")

# 主程式
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("list", list_subscribers))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("carbon", carbon))

    scheduler = AsyncIOScheduler(timezone=pytz.UTC)
    scheduler.add_job(lambda: asyncio.create_task(scheduled_task(app)), "interval", hours=1)
    scheduler.start()

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("✅ Bot is running with /carbon 指令與定時任務。")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
