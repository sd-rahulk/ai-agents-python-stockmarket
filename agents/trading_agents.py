import yfinance as yf
import pandas as pd
import numpy as np

class BaseAgent:
    def __init__(self, name):
        self.name = name

    def log(self, message):
        print(f"[{self.name}] {message}")

class ScannerAgent(BaseAgent):
    def __init__(self):
        super().__init__("MarketScanner")
        # Larger universe: Nifty 50 Stocks
        self.universe = [
            "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "BHARTIARTL.NS", "SBI.NS", "LICI.NS", "ITC.NS", "HINDUNILVR.NS",
            "LT.NS", "BAJFINANCE.NS", "HCLTECH.NS", "MARUTI.NS", "SUNPHARMA.NS", "ADANIENT.NS", "KOTAKBANK.NS", "TITAN.NS", "AXISBANK.NS", "ULTRACEMCO.NS",
            "ASIANPAINT.NS", "WIPRO.NS", "NTPC.NS", "M&M.NS", "POWERGRID.NS", "ADANIPORTS.NS", "JSWSTEEL.NS", "TATASTEEL.NS", "ONGC.NS", "COALINDIA.NS",
            "HINDALCO.NS", "GRASIM.NS", "SBILIFE.NS", "BAJAJ-AUTO.NS", "HDFCLIFE.NS", "NESTLEIND.NS", "TECHM.NS", "BRITANNIA.NS", "CIPLA.NS", "EICHERMOT.NS",
            "TATACONSUM.NS", "INDUSINDBK.NS", "APOLLOHOSP.NS", "DRREDDY.NS", "DIVISLAB.NS", "BPCL.NS", "HEROMOTOCO.NS", "UPL.NS", "BAJAJFINSV.NS"
        ]

    def scan(self, universe_size=10):
        self.log(f"Scanning the market for the best {universe_size} opportunities...")
        # In a real app, we'd fetch 1-day change for all
        # To keep it fast for simulation, we'll pick a random subset and 'rank' them
        selected = np.random.choice(self.universe, size=min(20, len(self.universe)), replace=False)
        
        ranked_stocks = []
        for symbol in selected:
            try:
                # Simulate a performance scan
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                if len(hist) < 2: continue
                
                perf = (hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]
                ranked_stocks.append({"symbol": symbol, "performance": perf})
            except:
                continue
        
        # Sort by performance (momentum)
        ranked_stocks.sort(key=lambda x: x['performance'], reverse=True)
        return [s['symbol'] for s in ranked_stocks[:universe_size]]

class AnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__("AnalystAgent")

    def analyze(self, symbol, data=None):
        self.log(f"Deep analysis of {symbol}...")
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1mo")
            if len(hist) < 20:
                return {"symbol": symbol, "score": 0, "confidence": 0, "recommended_action": "HOLD"}

            # Calculate basic indicators
            close = hist['Close']
            ema_9 = close.ewm(span=9).mean().iloc[-1]
            ema_21 = close.ewm(span=21).mean().iloc[-1]
            
            # Simple RSI approximation
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
            rs = gain / loss if loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            
            # Decision logic
            confidence = 0.5
            action = "HOLD"
            
            if ema_9 > ema_21:
                confidence += 0.2
            if rsi < 70 and rsi > 40:
                confidence += 0.15
            if close.iloc[-1] > close.iloc[-5]: # Momentum
                confidence += 0.1
                
            if confidence > 0.75:
                action = "BUY"
            
            return {
                "symbol": symbol,
                "score": confidence * 100,
                "confidence": confidence,
                "recommended_action": action,
                "regime": "Trending" if ema_9 > ema_21 else "Consolidating"
            }
        except Exception as e:
            self.log(f"Error analyzing {symbol}: {e}")
            return {"symbol": symbol, "score": 0, "confidence": 0, "recommended_action": "HOLD"}

class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__("RiskAgent")

    def validate(self, decision, portfolio_state):
        self.log(f"Validating risk for {decision['symbol']}...")
        if decision['confidence'] < 0.6:
            return False, "Low confidence"
        # Check exposure etc.
        return True, "Passed"

class AllocatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("AllocatorAgent")

    def allocate(self, decision, cash_balance, max_exposure):
        self.log(f"Allocating capital for {decision['symbol']}...")
        amount = cash_balance * max_exposure * decision['confidence']
        return amount

class ExecutionAgent(BaseAgent):
    def __init__(self):
        super().__init__("ExecutionEngine")

    def execute(self, symbol, quantity, price, action):
        self.log(f"Executing {action} for {quantity} shares of {symbol} at {price}...")
        return {
            "status": "SUCCESS",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "action": action
        }

class SellAgent(BaseAgent):
    def __init__(self):
        super().__init__("SellEngine")

    def check_exits(self, position, current_price, config):
        # Stop loss / Take profit logic
        entry_price = position['price']
        pnl_pct = (current_price - entry_price) / entry_price
        
        if pnl_pct <= -config.stop_loss_pct:
            return True, "Stop Loss"
        if pnl_pct >= config.take_profit_pct:
            return True, "Take Profit"
        return False, None

class LearningAgent(BaseAgent):
    def __init__(self):
        super().__init__("LearningAgent")

    def learn(self, trade_history):
        self.log(f"Analyzing {len(trade_history)} recent trades to optimize weights...")
        
        # Simple reinforcement learning logic
        avg_pnl = sum([t.pnl for t in trade_history]) / len(trade_history)
        
        # Current weights (default if no history)
        weights = {
            "trend_weight": 0.35,
            "momentum_weight": 0.45,
            "risk_weight": 0.1,
            "reward_weight": 0.1
        }
        
        # If we are losing money, increase the Risk Weight
        if avg_pnl < 0:
            weights["risk_weight"] += 0.05
            weights["momentum_weight"] -= 0.05
            self.log("Detected losses: Increasing Risk Weight for more conservative entries.")
        else:
            # If winning, reward the Momentum agent
            weights["momentum_weight"] += 0.02
            weights["risk_weight"] -= 0.02
            self.log("Detected profits: Increasing Momentum Weight to capture more gains.")
            
        # Ensure total weight stays balanced (normalization placeholder)
        return weights
