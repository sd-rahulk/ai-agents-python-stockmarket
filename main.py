from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database.db import SessionLocal, init_db, Trade, Portfolio, PortfolioHistory, Config, ModelMetrics
from core.engine import TradingEngine
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import datetime

app = FastAPI(title="SimTrade AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Trading Engine
engine = TradingEngine()
scheduler = AsyncIOScheduler()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
async def startup_event():
    init_db()
    # Add trading cycle to scheduler
    scheduler.add_job(engine.run_cycle, 'interval', minutes=5, id='trading_job')
    scheduler.start()
@app.post("/api/run-cycle")
async def run_manual_cycle():
    await engine.run_cycle()
    return {"message": "Cycle triggered manually"}

@app.get("/api/system")
def get_system_status():
    return {
        "status": "RUNNING" if engine.is_running else "PAUSED",
        "uptime": "99.9%",
        "latency": "45ms",
        "inferences_per_second": 12.5
    }

@app.post("/api/run")
async def start_engine():
    engine.start()
    # Trigger an immediate run in the background
    asyncio.create_task(engine.run_cycle())
    return {"message": "Trading engine started and initial cycle triggered"}

@app.post("/api/pause")
def pause_engine():
    engine.stop()
    return {"message": "Trading engine paused"}

@app.get("/api/portfolio")
def get_portfolio(db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).first()
    return portfolio

@app.get("/api/positions")
def get_positions(db: Session = Depends(get_db)):
    positions = db.query(Trade).filter(Trade.status == "OPEN").all()
    return positions

@app.get("/api/history")
def get_history(db: Session = Depends(get_db)):
    history = db.query(Trade).filter(Trade.status == "CLOSED").order_by(Trade.exit_timestamp.desc()).all()
    return history

@app.get("/api/portfolio/history")
def get_portfolio_history(db: Session = Depends(get_db)):
    history = db.query(PortfolioHistory).order_by(PortfolioHistory.timestamp.desc()).limit(100).all()
    return history

@app.get("/api/config")
def get_config(db: Session = Depends(get_db)):
    return db.query(Config).first()

@app.post("/api/config")
def update_config(new_config: dict, db: Session = Depends(get_db)):
    config = db.query(Config).first()
    portfolio = db.query(Portfolio).first()
    
    # Exclude internal fields from update
    exclude_fields = ["id", "last_updated"]
    for key, value in new_config.items():
        if hasattr(config, key) and key not in exclude_fields:
            setattr(config, key, value)
            
            # If initial capital changes, we update the current portfolio balance as well
            if key == "initial_capital":
                portfolio.cash_balance = float(value)
                portfolio.total_value = float(value)
                portfolio.total_pnl = 0.0
    
    config.last_updated = datetime.datetime.utcnow()
    db.commit()
    db.refresh(config)
    db.refresh(portfolio)
    return config

@app.get("/api/weights")
def get_weights(db: Session = Depends(get_db)):
    metrics = db.query(ModelMetrics).order_by(ModelMetrics.timestamp.desc()).first()
    if not metrics:
        return {
            "trend_weight": 0.3,
            "momentum_weight": 0.4,
            "risk_weight": 0.15,
            "reward_weight": 0.15
        }
    return metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
