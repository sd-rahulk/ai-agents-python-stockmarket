from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

Base = declarative_base()

class Config(Base):
    __tablename__ = "config"
    id = Column(Integer, primary_key=True)
    initial_capital = Column(Float, default=100000.0)
    max_trades = Column(Integer, default=10)
    max_exposure = Column(Float, default=0.2) # Max 20% per trade
    stop_loss_pct = Column(Float, default=0.02)
    take_profit_pct = Column(Float, default=0.05)
    scanner_universe_size = Column(Integer, default=50)
    scan_frequency = Column(Integer, default=30) # minutes
    trading_frequency = Column(Integer, default=5) # minutes
    risk_profile = Column(String, default="Balanced") # Safe, Balanced, Aggressive
    telegram_token = Column(String, nullable=True)
    telegram_chat_id = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class Portfolio(Base):
    __tablename__ = "portfolio"
    id = Column(Integer, primary_key=True)
    cash_balance = Column(Float, default=100000.0)
    total_value = Column(Float, default=100000.0)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    active_positions_count = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    action = Column(String) # BUY, SELL
    quantity = Column(Integer)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String) # OPEN, CLOSED
    pnl = Column(Float, default=0.0)
    exit_price = Column(Float, nullable=True)
    exit_timestamp = Column(DateTime, nullable=True)
    strategy = Column(String)
    confidence = Column(Float)

class PortfolioHistory(Base):
    __tablename__ = "portfolio_history"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    total_value = Column(Float)
    cash_balance = Column(Float)
    pnl = Column(Float)

class ModelMetrics(Base):
    __tablename__ = "model_metrics"
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    trend_weight = Column(Float)
    momentum_weight = Column(Float)
    risk_weight = Column(Float)
    reward_weight = Column(Float)
    ml_accuracy = Column(Float)

import os

# Database Setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./simtrade.db")

# Render fix for postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Ensure default Config exists
        if not db.query(Config).first():
            db.add(Config(
                initial_capital=100000.0,
                max_trades=10,
                max_exposure=0.2,
                stop_loss_pct=0.02,
                take_profit_pct=0.05
            ))
        
        # Ensure default Portfolio exists
        if not db.query(Portfolio).first():
            db.add(Portfolio(
                cash_balance=100000.0,
                total_value=100000.0,
                total_pnl=0.0,
                active_positions_count=0
            ))
        
        db.commit()
    except Exception as e:
        print(f"Error during DB initialization: {e}")
        db.rollback()
    finally:
        db.close()
