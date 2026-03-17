# Quant-Lab

[![Tests](https://github.com/alfredcho91-ux/Quant-Lab/actions/workflows/test.yml/badge.svg)](https://github.com/alfredcho91-ux/Quant-Lab/actions/workflows/test.yml)
![React](https://img.shields.io/badge/Frontend-React_18-blue)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688)
![Python](https://img.shields.io/badge/Quant-Python_3.9-3776AB)
![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178C6)

Quant-Lab is a quantitative research and strategy analysis platform for crypto markets. The project turns raw hypothesis testing into an operable product: typed APIs, modular quant logic, reusable indicator pipelines, multi-page React workflows, and documentation that makes implementation decisions traceable.

> Portfolio lens: this repository is intentionally positioned as an Implementation PM case study. It demonstrates how quant research is translated into a maintainable software system with delivery structure, architecture boundaries, execution artifacts, and a clear roadmap.

## Executive Snapshot

- Product scope: 15 frontend pages, 11 backend modules, and 19 backend test files supporting research, scanning, backtesting, and AI-assisted exploration.
- Quant focus: streak analysis, hybrid filters, MTF trend judgment, pattern scanning, and AI-assisted strategy drafting.
- Engineering focus: React + TypeScript frontend, FastAPI backend, pure indicator/core layers, and explicit documentation for architecture, install flow, and feature-to-backend mapping.

## What This Repository Proves

- I can decompose a quant product into bounded modules instead of growing a monolithic script pile.
- I can move from research logic to implementation artifacts: API contracts, UI workflows, startup scripts, and validation docs.
- I can manage technical execution as an Implementation PM, not just write isolated code, by making system decisions explicit and repeatable.

## Core Capabilities

### 1. Streak And Conditional Probability Analysis
- Evaluates bullish and bearish streak behavior with follow-through statistics.
- Surfaces confidence intervals, conditional splits, and significance-aware reporting rather than raw hit rates alone.

### 2. Multi-Timeframe Trend Judgment
- Aggregates directional evidence across multiple intervals to reduce single-timeframe bias.
- Uses indicators such as EMA, MACD, Supertrend, and stochastic context to frame regime-level decisions.

### 3. Hybrid Strategy And Pattern Workflows
- Supports combined indicator filters, scan-first workflows, and backtest-ready parameterization.
- Organizes strategy-specific logic under bounded backend modules so features can evolve independently.

### 4. AI Quant Lab
- Converts natural-language research prompts into structured analysis conditions.
- Separates LLM parsing, rule normalization, statistical evaluation, and frontend presentation so AI features remain auditable.

## Architecture Decisions

- `core/`: Pure quant primitives and indicator pipelines with no HTTP or UI awareness.
- `backend/strategy/`: Strategy-specific business logic for streak, hybrid, combo filter, and related domains.
- `backend/modules/`: API-facing orchestration, schemas, and service boundaries.
- `frontend/src/features/`: Feature-sliced UI modules that keep complex workflows localized instead of spreading logic across generic components.

Architecture details live in [ARCHITECTURE.md](./ARCHITECTURE.md).

## Implementation PM Evidence

- [Implementation PM Case Study](./docs/IMPLEMENTATION_PM_CASE_STUDY.md)
- [Portfolio Release Notes](./docs/PORTFOLIO_RELEASE_NOTES.md)
- [System Architecture](./ARCHITECTURE.md)
- [API Specification](./API_SPEC.md)
- [Install And Recovery Guide](./INSTALL.md)
- [Page To Backend Mapping](./docs/PAGE_BACKEND_MAPPING.md)
- [Streak Analysis Flow](./docs/STREAK_ANALYSIS_FLOW.md)
- [Complex Mode Flow](./docs/COMPLEX_MODE_FLOW.md)

## Quality Gates

- GitHub Actions runs backend tests, frontend lint/build, and architecture guard scripts on every push to `main`.
- The repository includes explicit import guards to prevent `core/` and router layers from accumulating cross-layer coupling.
- Public repo hygiene is enforced via ignore rules that exclude logs, local caches, agent artifacts, and large market data files.

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Optional local Binance CSV cache under `binance_klines/`

### Run Locally

```bash
git clone https://github.com/alfredcho91-ux/Quant-Lab.git
cd Quant-Lab
chmod +x start.sh
./start.sh
```

## Delivery Principles

- Quant logic is isolated from transport and presentation layers.
- New features are documented with implementation maps so the repository stays understandable as scope grows.
- Local startup and recovery are scripted to reduce friction when onboarding or restoring the project.

## Public Release

- Repository: [alfredcho91-ux/Quant-Lab](https://github.com/alfredcho91-ux/Quant-Lab)
- Current CI workflow: [Tests](https://github.com/alfredcho91-ux/Quant-Lab/actions/workflows/test.yml)
- Portfolio release notes: [docs/PORTFOLIO_RELEASE_NOTES.md](./docs/PORTFOLIO_RELEASE_NOTES.md)

## Roadmap

- [x] Phase 1: Core analytics, backtesting workflows, and architectural modularization
- [ ] Phase 2: Execution-ready live trading integration and portfolio state management
- [ ] Phase 3: Strategy optimization and ML-assisted ranking
- [ ] Phase 4: CI/CD, containerization, and cloud deployment hardening

Designed and implemented by Geunwoo Cho, focused on the intersection of Quant Finance and Software Implementation.
