# Cloud Cost Observability & Intelligent Archival

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Teja-Jan/Cloud-Cost-Observability-Intelligent-Archival/blob/main/app.ipynb)

An enterprise-grade, platform-agnostic intelligence platform for cloud cost observability, predictive forecasting, and intelligent data archival governance.

## Overview

This application provides a unified three-tab dashboard for cloud platform teams to:

- **Observe** current cost, storage, compute, and memory metrics across cloud platforms
- **Forecast** 1-year and 5-year resource cost projections using a Linear Trend Analysis (OLS) model
- **Optimize** data estates by identifying inactive assets, reviewing governance context, and executing governed archival workflows

## Supported Platforms

Snowflake · Databricks · BigQuery · AWS · Azure · Google Cloud Platform · Oracle Cloud Infrastructure · IBM Cloud

## Features

### Observability
- 4-category KPI dashboard: Cost, Storage, Compute, Memory
- Hierarchical drill-down: Database → Schema → Table/View level
- Storage distribution charts

### Forecasting
- Simultaneous 4-card forecast display (Cost, Storage, Compute, Memory)
- Current Cost, 1-Year Forecast, 5-Year Forecast per card
- Week-over-Week, Month-over-Month, Year-over-Year trend indicators
- 4 separate historical + projection charts
- Forecast Rationalization narrative
- Model: Linear Trend Analysis (Ordinary Least Squares)

### Optimization & Governance
- Total Assets, Active Assets, Inactive Assets KPI cards with drill-downs
- Enterprise Database Hierarchy explorer
- Asset Filter Panel (Platform, Database, Schema, Type, Format, Status)
- 21-column scalable Inactive Asset Grid with governance context:
  - Last accessed by, last access date, access granted date
  - Service accounts, report dependencies, upstream/downstream lineage
  - Archival justification narrative
- Excel export for Total / Active / Inactive assets and Archival Reports
- SendGrid email integration for report distribution
- Approval workflow with rollback retention policy selection
- Floating AI Assistant for natural language queries

## Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
git clone https://github.com/Teja-Jan/Cloud-Cost-Observability-Intelligent-Archival.git
cd Cloud-Cost-Observability-Intelligent-Archival

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Key settings:
- `SENDGRID_API_KEY` — for email report distribution
- `SENDGRID_FROM_EMAIL` — sender address

### Run

```bash
streamlit run src/app.py
```

App will open at [http://localhost:8501](http://localhost:8501)

## Project Structure

```
├── src/
│   ├── app.py                          # Main Streamlit application
│   ├── agent/
│   │   └── analyzers/
│   │       ├── forecaster.py           # OLS Linear Trend forecasting engine
│   │       ├── pricing_engine.py       # Multi-platform cost calculation
│   │       └── hoarding_analyzer.py    # Data hoarding detection
│   ├── utils/
│   │   ├── mock_data.py                # Realistic enterprise data generator
│   │   ├── env_manager.py              # .env management
│   │   └── governance_service.py       # Governance metadata service
│   └── agent/fixers/
│       └── archival_executor.py        # Archival action executor
├── data/raw/                           # Auto-generated on first run
├── requirements.txt
├── .env.example
└── technical_architecture_spec.md
```

## Architecture

- **Frontend**: Streamlit with custom CSS (Inter + Outfit fonts, glassmorphism cards)
- **Forecasting Model**: Ordinary Least Squares (OLS) Linear Regression via `numpy.polyfit`
- **Cost Engine**: Platform-specific pricing per compute unit, storage GB, and data transfer GB
- **Data Layer**: Realistic deterministic mock data (4,500+ enterprise assets across 8 platforms × 5 domains)
- **Email**: SendGrid API with Excel attachment support

## License

MIT
