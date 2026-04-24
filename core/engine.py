import asyncio
import datetime
from database.db import SessionLocal, Trade, Portfolio, PortfolioHistory, Config, ModelMetrics
from agents.trading_agents import ScannerAgent, AnalystAgent, RiskAgent, AllocatorAgent, ExecutionAgent, SellAgent, LearningAgent
from utils.notifier import TelegramNotifier
import yfinance as yf

class TradingEngine:
    def __init__(self):
        self.scanner = ScannerAgent()
        self.analyst = AnalystAgent()
        self.risk = RiskAgent()
        self.allocator = AllocatorAgent()
        self.execution = ExecutionAgent()
        self.sell_engine = SellAgent()
        self.learner = LearningAgent()
        self.notifier = TelegramNotifier()
        self.is_running = False

    async def run_cycle(self):
        if not self.is_running:
            return
            
        print(f"[{datetime.datetime.now()}] Starting trading cycle...")
        db = SessionLocal()
        config = db.query(Config).first()
        portfolio = db.query(Portfolio).first()

        # Update notifier credentials
        self.notifier.token = config.telegram_token
        self.notifier.chat_id = config.telegram_chat_id

        # 1. Manage existing positions
        active_positions = db.query(Trade).filter(Trade.status == "OPEN").all()
        for pos in active_positions:
            # Get current price
            ticker = yf.Ticker(pos.symbol)
            try:
                current_price = ticker.fast_info['lastPrice']
                if current_price is None:
                    continue
            except:
                continue
            
            should_exit, reason = self.sell_engine.check_exits(
                {"price": pos.price, "symbol": pos.symbol}, 
                current_price, 
                config
            )
            
            if should_exit:
                print(f"Exiting {pos.symbol} due to {reason}")
                pos.status = "CLOSED"
                pos.exit_price = current_price
                pos.exit_timestamp = datetime.datetime.utcnow()
                pos.pnl = (current_price - pos.price) * pos.quantity
                
                portfolio.cash_balance += current_price * pos.quantity
                portfolio.active_positions_count -= 1
                
                # Send Notification
                self.notifier.notify_trade("SELL", pos.symbol, pos.quantity, current_price, pos.pnl)
                db.commit()

        # 2. Scan for new opportunities
        if portfolio.active_positions_count < config.max_trades:
            symbols = self.scanner.scan(config.scanner_universe_size)
            for symbol in symbols:
                if portfolio.active_positions_count >= config.max_trades:
                    break
                    
                # Check if already holding
                if db.query(Trade).filter(Trade.symbol == symbol, Trade.status == "OPEN").first():
                    continue

                # Analysis
                # In real world, we'd pass actual data
                decision = self.analyst.analyze(symbol, None)
                
                if decision['recommended_action'] == "BUY":
                    # Risk Check
                    is_safe, reason = self.risk.validate(decision, portfolio)
                    if is_safe:
                        # Allocation
                        amount = self.allocator.allocate(decision, portfolio.cash_balance, config.max_exposure)
                        ticker = yf.Ticker(symbol)
                        try:
                            price = ticker.fast_info['lastPrice']
                            if price is None or price <= 0:
                                print(f"Could not get valid price for {symbol}, skipping...")
                                continue
                        except Exception as e:
                            print(f"Error fetching price for {symbol}: {e}")
                            continue

                        quantity = int(amount / price)
                        
                        if quantity > 0:
                            # Execution
                            result = self.execution.execute(symbol, quantity, price, "BUY")
                            if result['status'] == "SUCCESS":
                                new_trade = Trade(
                                    symbol=symbol,
                                    action="BUY",
                                    quantity=quantity,
                                    price=price,
                                    status="OPEN",
                                    strategy="AI_MOMENTUM",
                                    confidence=decision['confidence']
                                )
                                db.add(new_trade)
                                portfolio.cash_balance -= price * quantity
                                portfolio.active_positions_count += 1
                                
                                # Send Notification
                                self.notifier.notify_trade("BUY", symbol, quantity, price)
                                db.commit()
                        else:
                            print(f"[{symbol}] Skipped: Allocated ₹{amount:.2f} is not enough to buy 1 share at ₹{price:.2f}")

        # Update portfolio total value
        total_pos_value = 0
        active_positions = db.query(Trade).filter(Trade.status == "OPEN").all()
        for pos in active_positions:
             ticker = yf.Ticker(pos.symbol)
             try:
                 price = ticker.fast_info['lastPrice']
                 if price:
                     total_pos_value += price * pos.quantity
             except:
                 continue
        
        portfolio.total_value = portfolio.cash_balance + total_pos_value
        portfolio.total_pnl = portfolio.total_value - config.initial_capital
        
        # Log Portfolio History
        history = PortfolioHistory(
            total_value=portfolio.total_value,
            cash_balance=portfolio.cash_balance,
            pnl=portfolio.total_pnl
        )
        db.add(history)

        # 3. Learning Cycle
        closed_trades = db.query(Trade).filter(Trade.status == "CLOSED").order_by(Trade.exit_timestamp.desc()).limit(10).all()
        if closed_trades:
            new_weights = self.learner.learn(closed_trades)
            metrics = ModelMetrics(
                trend_weight=new_weights['trend_weight'],
                momentum_weight=new_weights['momentum_weight'],
                risk_weight=new_weights['risk_weight'],
                reward_weight=new_weights['reward_weight'],
                ml_accuracy=0.85 # Placeholder for ML model accuracy
            )
            db.add(metrics)

        db.commit()
        db.close()

    def start(self):
        self.is_running = True

    def stop(self):
        self.is_running = False
