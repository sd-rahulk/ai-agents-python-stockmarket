# SimTrade AI - Multi-Agent Backend

This is the Python-based backend for SimTrade AI, an autonomous trading platform designed for the Indian stock market (NSE). It uses a multi-agent architecture to scan, analyze, and execute trades in a simulated environment.

## 🏗 Architecture

The backend is built with **FastAPI** and **SQLAlchemy (SQLite)**. It features a pipeline of AI agents:

1.  **Market Scanner**: Scans the Nifty 50 universe and ranks stocks by momentum.
2.  **Analyst Agent**: Computes EMA crossovers, RSI, and trend strength to generate buy/sell signals.
3.  **Risk Agent**: Validates trades against capital exposure and confidence thresholds.
4.  **Allocator Agent**: Determines the optimal position size based on portfolio balance.
5.  **Execution Engine**: Simulates trade execution with real-time market data.
6.  **Sell Engine**: Manages exits based on Stop Loss, Take Profit, and trend reversals.
7.  **Learning Agent**: Analyzes past trade performance to adjust internal strategy weights.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   python main.py
   ```
   The API will be available at `http://localhost:8000`.

## 📡 API Endpoints
- `GET /api/system`: System health and AI metrics.
- `GET /api/portfolio`: Current balance and PnL.
- `GET /api/positions`: Active open trades.
- `GET /api/history`: Closed trade history.
- `POST /api/run`: Start the autonomous bot.
- `POST /api/pause`: Stop the autonomous bot.
- `POST /api/config`: Update trading parameters (balance, risk, etc.).

## 🛠 Tech Stack
- **Framework**: FastAPI
- **Database**: SQLite (via SQLAlchemy)
- **Data Source**: yfinance (Yahoo Finance API)
- **Scheduler**: APScheduler
