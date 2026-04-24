import requests

class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.token = token
        self.chat_id = chat_id

    def send_message(self, message):
        if not self.token or not self.chat_id:
            print(f"[Notifier] Telegram not configured. Message: {message}")
            return False
            
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }
        
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print(f"[Notifier] Telegram alert sent successfully.")
                return True
            else:
                print(f"[Notifier] Failed to send Telegram alert: {response.text}")
                return False
        except Exception as e:
            print(f"[Notifier] Error sending Telegram alert: {e}")
            return False

    def notify_trade(self, trade_type, symbol, quantity, price, pnl=None):
        emoji = "🚀" if trade_type == "BUY" else "💰"
        action = "BOUGHT" if trade_type == "BUY" else "SOLD"
        
        msg = f"<b>{emoji} SimTrade AI Alert</b>\n\n"
        msg += f"<b>Action:</b> {action}\n"
        msg += f"<b>Symbol:</b> {symbol}\n"
        msg += f"<b>Quantity:</b> {quantity}\n"
        msg += f"<b>Price:</b> ₹{price:,.2f}\n"
        
        if pnl is not None:
            pnl_emoji = "✅" if pnl >= 0 else "❌"
            msg += f"<b>PnL:</b> {pnl_emoji} ₹{pnl:,.2f}\n"
            
        msg += f"\n<i>Keep growing your capital!</i>"
        return self.send_message(msg)
