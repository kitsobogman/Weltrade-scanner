import time
import requests
import MetaTrader5 as mt5

# --- CONFIGURATION ---
TELEGRAM_BOT_TOKEN = 8906817779:AAHjSlPaahCSCk_5xvuiwy66Ur-uLs3cr4c
TELEGRAM_CHAT_ID = "1649855198"

# --- WELTRADE CREDENTIALS ---
WELTRADE_LOGIN = 19206989         
WELTRADE_PASSWORD = cU6^9t&N  
WELTRADE_SERVER = "Weltrade-Demo"             

# --- SYNTX SYMBOLS TO SCAN ---
SYMBOLS = ["BreakX", "TrendX", "FX_Vol_75", "PainX", "GainX"]
TIMEFRAME = mt5.TIMEFRAME_M15
RISK_REWARD_RATIO = 3.0  # Strict 1:3 Target

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram dispatch error: {e}")

def initialize_mt5():
    if not mt5.initialize():
        print("MT5 Initialization failed.")
        return False
    
    authorized = mt5.login(WELTRADE_LOGIN, password=WELTRADE_PASSWORD, server=WELTRADE_SERVER)
    if authorized:
        print("Connected to Weltrade MT5 successfully!")
        return True
    else:
        print(f"Weltrade login failed: {mt5.last_error()}")
        return False

def scan_markets():
    for symbol in SYMBOLS:
        mt5.symbol_select(symbol, True)
        rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 4)
        if rates is None or len(rates) < 4:
            continue

        current_close = rates[-1]['close']
        last_body = abs(rates[-2]['close'] - rates[-2]['open'])
        avg_body = (abs(rates[-3]['close'] - rates[-3]['open']) + abs(rates[-4]['close'] - rates[-4]['open'])) / 2.0

        if avg_body > 0 and last_body >= (avg_body * 2.2):
            is_bullish = rates[-2]['close'] > rates[-2]['open']
            action = "BUY SETUP" if is_bullish else "SELL SETUP"
            
            entry_price = current_close
            sl_price = rates[-2]['low'] if is_bullish else rates[-2]['high']
            risk_distance = abs(entry_price - sl_price)
            
            if risk_distance == 0:
                continue
                
            tp_price = entry_price + (risk_distance * RISK_REWARD_RATIO) if is_bullish else entry_price - (risk_distance * RISK_REWARD_RATIO)

            alert_msg = (
                f"🚨 *WELTRADE 1:3 SETUP DETECTED* 🚨\n\n"
                f"📊 *Symbol:* `{symbol}`\n"
                f"⚡ *Signal:* *{action}*\n"
                f"💵 *Entry:* `{entry_price:.2f}`\n"
                f"🛡️ *Stop Loss:* `{sl_price:.2f}`\n"
                f"🎯 *Take Profit (1:3):* `{tp_price:.2f}`\n"
                f"⚖️ *Risk/Reward:* `1 : {RISK_REWARD_RATIO}`\n\n"
                f"📱 *Action:* Open mobile MT5 and place manual order."
            )
            send_telegram_alert(alert_msg)

if __name__ == "__main__":
    if initialize_mt5():
        print("Scanner active. Monitoring SyntX symbols for 1:3 setups...")
        while True:
            scan_markets()
            time.sleep(20)
