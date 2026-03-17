# Quant-Lab: Algorithmic Trading & Quantitative Analysis Platform

![React](https://img.shields.io/badge/Frontend-React_18-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Python](https://img.shields.io/badge/Quant-Python_3.9-3776AB)
![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6)

> **Project Manager's Note:**
> This repository is not just a collection of scripts; it is a fully architected, production-ready quantitative analysis platform. As an Implementation PM with a background in Quant Finance, I designed this system to bridge the gap between complex financial modeling and scalable software engineering. The focus here is on **maintainability, modularity, and actionable data visualization**.

## 🎯 Executive Summary

Quant-Lab is a comprehensive cryptocurrency trading analysis platform designed to validate trading hypotheses through rigorous statistical testing and backtesting. It moves beyond simple indicator crossovers by implementing advanced conditional probability analysis, streak pattern recognition, and AI-driven strategy optimization.

### Key Business Value (ROI)
- **Data-Driven Decision Making:** Replaces intuition with 95% Wilson Confidence Intervals and Bonferroni-corrected p-values.
- **Rapid Strategy Prototyping:** The "AI Quant Lab" module allows users to test complex trading conditions using natural language, drastically reducing the time from hypothesis to backtest.
- **Risk Mitigation:** Built-in multi-timeframe (MTF) analysis and strict EMA 200 trend filters prevent trading against macro trends.

---

## 🏗️ Architecture & Implementation Strategy

As the Technical PM, I prioritized a clean separation of concerns to ensure the platform can scale from a personal research tool to a multi-user SaaS.

### 1. Domain-Driven Design (DDD)
The backend is strictly modularized. We moved away from monolithic scripts to a domain-centric approach:
- `core/`: Pure, stateless financial math and indicator pipelines (RSI, MACD, Bollinger Bands, ATR).
- `backend/strategy/`: Complex business logic for specific trading strategies (e.g., N-Streak Analysis, Hybrid Models).
- `backend/modules/`: API routing and service layers, ensuring HTTP concerns never leak into quant logic.

### 2. The "AI Quant Lab" (NLP to Quant)
A standout feature is the AI integration. Instead of writing Python code to test a new idea, users can ask:
> *"What is the probability of the next candle being green if RSI < 30 and Price touches the lower Bollinger Band on the 1H timeframe?"*

**Implementation Flow:**
1. **LLM Gateway:** Parses natural language into structured JSON conditions.
2. **Condition Parser:** Translates JSON into Pandas boolean masks.
3. **Statistical Engine:** Calculates success rates, p-values, and GATI (Custom Edge Index).
4. **UI Presentation:** Renders interactive Plotly charts and confidence bands.

### 3. Frontend Engineering
Built with React and TypeScript, the frontend is designed for high-density data visualization without sacrificing performance.
- **State Management:** Zustand for global state (Coin selection, Timeframes) to ensure UI consistency across 14+ analysis pages.
- **Component Architecture:** Feature-sliced design (`src/features/`) keeps complex logic (like the Streak Analysis tables) isolated and testable.

---

## 📊 Core Quant Features

### 1. N-Streak Analysis (연속 봉 분석)
Analyzes the statistical edge of consecutive bullish/bearish candles.
- **Conditional Breakdown:** Heatmaps showing win rates based on RSI and ATR at the time of pattern completion.
- **Statistical Rigor:** Displays 95% Confidence Intervals and flags statistically significant edges.

### 2. Multi-Timeframe (MTF) Trend Judgment
Aggregates trend data across 15m, 1H, 4H, and 1D timeframes using Supertrend, MACD, and EMA alignments to provide a single "Market Regime" score.

### 3. Strategy & Pattern Scanners
Real-time scanning of multiple assets against predefined quantitative criteria (e.g., Bollinger Band Squeeze + RSI Divergence).

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Binance API access (for live data fetching)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/your-username/quant-lab.git
cd quant-lab

# Start both Backend and Frontend concurrently
chmod +x start.sh
./start.sh
```

---

## 📈 Roadmap & Future Phases

As a PM, I manage this project in distinct phases:
- [x] **Phase 1: Core Infrastructure & Statistical Engine** (Current)
- [ ] **Phase 2: Live Trading Integration** (Execution engine via CCXT)
- [ ] **Phase 3: Machine Learning Models** (Predictive modeling using XGBoost/LSTM)
- [ ] **Phase 4: Cloud Deployment & CI/CD** (Dockerization, AWS ECS, GitHub Actions)

---
*Designed and implemented by [Your Name] - Bridging Quant Finance and Software Engineering.*
