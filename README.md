# 多功能AI助理 Telegram Bot

## ✨ 功能特色
- **身份切換系統**：支援三種不同身份的專業AI助理
- **智能問答**：基於OpenAI GPT的專業回答系統
- **Web App整合**：可開啟儀表板頁面

## 🎯 三種服務模式

### 🏢 管理者模式 - ESG政策專家
- 碳排放目標查詢與政策說明
- ESG策略與實施建議
- 碳足跡數據分析與報告
- 永續發展相關諮詢

### 🚗 消費者模式 - 客戶服務經理
- 汽車訂單狀態即時查詢
- 交車時間預估與進度追蹤
- 訂單問題處理與客戶關懷
- 車輛相關服務諮詢

### 🤝 經銷商模式 - 業務支援助理
- 各車型等候時間查詢
- 交車預估時間計算
- 庫存與配額狀況說明
- 銷售支援與客戶期望管理

## 🚀 部署到 Render

1. 前往 https://render.com 登入並建立新的 Web Service
2. 選擇 GitHub 並匯入此專案
3. 設定建構指令：`pip install -r requirements.txt`
4. 設定執行指令：`python bot.py`
5. 添加環境變數：
   - `BOT_TOKEN`：從 BotFather 獲得的機器人Token
   - `WEB_APP_URL`：前端頁面網址 (選填)
   - `OPENAI_API_KEY`：OpenAI API金鑰

## 📱 使用方式

1. **開始使用**：發送 `/start` 選擇身份
2. **AI問答**：發送 `/ask [問題]` 獲得專業回答

### 範例問題

**管理者模式：**
- `/ask 我們公司的碳排放目標是什麼？`
- `/ask ESG報告中應該包含哪些指標？`
- `/ask 如何制定有效的減碳策略？`

**消費者模式：**
- `/ask 我的訂單T001現在狀況如何？`
- `/ask 什麼時候可以交車？`
- `/ask 我的Tesla Model 3生產進度如何？`

**經銷商模式：**
- `/ask Tesla Model 3現在要等多久？`
- `/ask BYD車系的交車時間預估？`
- `/ask 目前哪款車交車最快？`

## 📊 內建資料

### 汽車模型等候時間
- Tesla Model 3/Y/S/X
- BYD Han/Tang
- BMW iX, Audi e-tron

### 客戶訂單範例
- 包含訂單編號、客戶資訊、車型、狀態等
- 支援即時狀態查詢與進度追蹤

### ESG與碳排放資料
- 公司減碳目標與時程
- ESG政策與實施方案
- 碳足跡三大範疇數據

## 🔧 技術架構
- **框架**：python-telegram-bot 20.6
- **AI引擎**：OpenAI GPT-3.5-turbo
- **部署平台**：Render雲端服務
- **前端整合**：Telegram Web App

## 📂 專案結構
```
├── bot.py              # 主程式
├── requirements.txt    # 依賴套件
└── README.md          # 說明文件
```

