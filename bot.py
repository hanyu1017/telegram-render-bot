import os
import logging
import requests
import json
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)

# 配置日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 配置參數
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_TELEGRAM_BOT_TOKEN')
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL', 'http://localhost:5678/webhook/carbon-query')

# 對話狀態
WAITING_QUERY = 1

class CarbonBot:
    def __init__(self):
        self.webhook_url = N8N_WEBHOOK_URL
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /start 命令"""
        user = update.effective_user
        welcome_message = f"""
👋 你好 {user.first_name}！

🌱 歡迎使用 **碳排放智能查詢系統**

我可以幫你查詢和分析碳排放數據。你可以：

📊 **查詢功能**
• 查詢特定時間範圍的碳排放數據
• 分析碳排放趨勢
• 生成碳排放報告
• 比較不同時期的排放量

💬 **使用方式**
直接輸入你的問題，例如：
• "查詢本月的碳排放數據"
• "2024年10月的總碳排放量是多少？"
• "分析最近三個月的碳排放趨勢"
• "生成上季度的碳排放報告"

輸入 /help 查看更多幫助
輸入 /examples 查看查詢範例
        """
        
        # 創建快捷鍵盤
        keyboard = [
            [KeyboardButton("📊 查詢本月數據"), KeyboardButton("📈 查看趨勢分析")],
            [KeyboardButton("📝 生成報告"), KeyboardButton("❓ 幫助")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /help 命令"""
        help_text = """
📖 **使用指南**

**基本查詢**
• 時間查詢：指定年份、月份或日期範圍
• 數據分析：獲取統計數據和趨勢分析
• 報告生成：創建詳細的碳排放報告

**查詢語法**
• 使用自然語言提問
• 支援中文和英文
• 可以指定具體的時間範圍

**快捷按鈕**
• 📊 查詢本月數據：快速查詢當月碳排放
• 📈 查看趨勢分析：分析排放趨勢
• 📝 生成報告：創建詳細報告
• ❓ 幫助：顯示此幫助訊息

**技術支援**
如遇問題，請聯繫系統管理員。
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def examples_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理 /examples 命令"""
        examples_text = """
💡 **查詢範例**

**時間範圍查詢**
• "查詢2024年10月的碳排放數據"
• "顯示最近30天的排放量"
• "本季度的碳排放統計"

**趨勢分析**
• "分析過去6個月的碳排放趨勢"
• "比較今年和去年同期的排放量"
• "找出排放量最高的月份"

**報告生成**
• "生成2024年Q3碳排放報告"
• "創建本年度的碳排放摘要"
• "製作上個月的詳細分析報告"

**具體數據**
• "scope 1 的總排放量是多少？"
• "上個月的碳排放強度"
• "各類別排放量佔比"

直接輸入你的問題開始查詢！
        """
        await update.message.reply_text(examples_text, parse_mode='Markdown')
    
    async def handle_quick_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理快捷按鈕"""
        text = update.message.text
        
        if text == "📊 查詢本月數據":
            query = f"查詢{datetime.now().strftime('%Y年%m月')}的碳排放數據"
        elif text == "📈 查看趨勢分析":
            query = "分析最近3個月的碳排放趨勢"
        elif text == "📝 生成報告":
            query = f"生成{datetime.now().strftime('%Y年%m月')}的碳排放報告"
        elif text == "❓ 幫助":
            await self.help_command(update, context)
            return
        else:
            return
        
        await self.process_query(update, context, query)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理用戶訊息"""
        query = update.message.text
        
        # 檢查是否為快捷按鈕
        if query in ["📊 查詢本月數據", "📈 查看趨勢分析", "📝 生成報告", "❓ 幫助"]:
            await self.handle_quick_button(update, context)
            return
        
        await self.process_query(update, context, query)
    
    async def process_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
        """處理查詢並調用 n8n webhook"""
        user = update.effective_user
        
        # 發送處理中訊息
        processing_msg = await update.message.reply_text(
            "🔍 正在分析您的查詢...\n⏳ 請稍候",
            parse_mode='Markdown'
        )
        
        try:
            # 準備 webhook 請求
            payload = {
                'query': query,
                'user_id': user.id,
                'username': user.username or user.first_name,
                'chat_id': update.effective_chat.id,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Sending query to n8n: {query}")
            
            # 調用 n8n webhook
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60  # 60秒超時
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 刪除處理中訊息
            await processing_msg.delete()
            
            # 發送結果
            await self.send_result(update, result)
            
        except requests.exceptions.Timeout:
            await processing_msg.edit_text(
                "⚠️ 查詢超時，請稍後再試或簡化查詢條件。"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Webhook request error: {e}")
            await processing_msg.edit_text(
                f"❌ 查詢失敗：無法連接到分析服務\n\n錯誤：{str(e)}"
            )
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            await processing_msg.edit_text(
                f"❌ 處理查詢時發生錯誤\n\n錯誤：{str(e)}"
            )
    
    async def send_result(self, update: Update, result: dict):
        """發送查詢結果"""
        try:
            # 解析結果
            if result.get('success'):
                response_text = result.get('response', '查詢完成')
                data = result.get('data', {})
                
                # 構建回覆訊息
                message = f"✅ **查詢結果**\n\n{response_text}\n"
                
                # 添加數據摘要
                if data:
                    message += "\n📊 **數據摘要**\n"
                    if 'total_emissions' in data:
                        message += f"• 總排放量: {data['total_emissions']:,.2f} 噸CO₂e\n"
                    if 'record_count' in data:
                        message += f"• 記錄數量: {data['record_count']} 筆\n"
                    if 'date_range' in data:
                        message += f"• 時間範圍: {data['date_range']}\n"
                
                # 添加建議
                if result.get('suggestions'):
                    message += f"\n💡 **建議**\n{result['suggestions']}\n"
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
            else:
                error_message = result.get('error', '未知錯誤')
                await update.message.reply_text(
                    f"❌ 查詢失敗\n\n{error_message}"
                )
                
        except Exception as e:
            logger.error(f"Error sending result: {e}")
            await update.message.reply_text(
                "❌ 發送結果時發生錯誤，請稍後再試。"
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理錯誤"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ 系統發生錯誤，請稍後再試。"
            )

def main():
    """主程式"""
    # 檢查環境變數
    if TELEGRAM_TOKEN == 'YOUR_TELEGRAM_BOT_TOKEN':
        logger.error("請設置 TELEGRAM_BOT_TOKEN 環境變數")
        return
    
    # 創建 Bot 實例
    bot = CarbonBot()
    
    # 創建 Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # 添加處理器
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("examples", bot.examples_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # 添加錯誤處理器
    application.add_error_handler(bot.error_handler)
    
    # 啟動 Bot
    logger.info("Carbon Telegram Bot 啟動中...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
