# Telegram Mini App Bot (Render 雲端部署版)

## ✅ 功能簡述
- 一個可與 Telegram 整合並可開啟 Web App 的機器人
- 專為 Render 雲端環境設計
- 搭配 Firebase Hosting 作為前端展示頁

## 🚀 如何部署到 Render

1. 到 https://render.com 登入並建立新 Web Service
2. 選擇 GitHub 並匯入此專案
3. 設定建構指令為：`pip install -r requirements.txt`
4. 設定執行指令為：`python bot.py`
5. 加入環境變數：
   - `BOT_TOKEN`：你從 BotFather 拿到的 Token
   - `WEB_APP_URL`：你的 Firebase Hosting 網址，例如 https://20250501.web.app

6. 部署完成後，Telegram 輸入 /start，就會看到 Mini App 按鈕！

## 📂 專案結構
- `bot.py`：Telegram Bot 主程式
- `requirements.txt`：安裝需求
- `README.md`：說明檔

