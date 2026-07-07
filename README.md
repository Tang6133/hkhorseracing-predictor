# HKHorseRacing-Predictor v6.3.1

**Production ML for Hong Kong horse racing — place ranking, calibrated probabilities, and race-day intelligence**

[![Predictions](https://img.shields.io/badge/predictions-public%20archive-blue)](predictions/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**What this repo is:** A public transparency archive — system documentation and downloadable race-day prediction CSVs.  
**What this repo is not:** Source code, trained models, feature pipelines, or live API access. Those remain private.


[Predictions archive](predictions/) · [tangttjason@gmail.com](mailto:tangttjason@gmail.com) · *Last updated: July 2026*

---

## Contents

- [Overview](#overview)
- [What Problem This Solves](#what-problem-this-solves)
- [What Makes This Project Different](#what-makes-this-project-different)
- [Performance](#performance)
- [Performance Limitations](#performance-limitations)
- [Product View](#product-view)
- [Frontend](#frontend)
- [Why The Modeling Approach Looks Like This](#why-the-modeling-approach-looks-like-this)
- [Technical Architecture](#technical-architecture)
- [Race-Day Intelligence Layer](#race-day-intelligence-layer)
- [Track Bias Research](#track-bias-research)
- [Performance by Distance](#performance-by-distance)
- [Repository Contents](#repository-contents)
- [Internal System Layout](#internal-system-layout)
- [Research Foundations](#research-foundations)
- [Repository Scope](#repository-scope)
- [License](#license)

---

## Overview

HKHorseRacing-Predictor is an end-to-end ML platform that predicts **place probability**, ranks contenders, and surfaces **race-day betting context** for Hong Kong horse racing.

Unlike notebook-only racing experiments, this project is built as a **full prediction product**:

- a **time-safe feature pipeline**
- a **stacked ensemble model**
- **odds-bucket probability calibration**
- a **FastAPI backend**
- and a **single-file frontend** for live race-day use

The goal is not just to train a model with a good AUC, but to build a system that is:

- reliable under time-series evaluation
- interpretable on race day
- useful for shortlist generation
- honest about market efficiency and betting limits

Built over **12 months** as a production-focused ML system, not a one-off notebook experiment.  
Improved through many iterative cycles of feature engineering, model stacking, calibration tuning, and race-day validation.  
Only changes that survived strict time-series testing were kept and deployed.

---

## What Problem This Solves

Hong Kong horse racing is a difficult prediction problem:

- races are small, noisy, and highly competitive
- closing odds already reflect a large amount of market information
- many public racing models suffer from **data leakage**, poor calibration, or weak race-day usability

This project was built to solve those issues directly.

It focuses on three practical objectives:

1. **Rank horses better than naive baselines**
2. **Produce calibrated place probabilities across odds ranges**
3. **Turn model output into race-day tools**, including track bias analysis, pattern tags, model hints, and structured recommendations

---

## What Makes This Project Different

Most horse racing ML repos stop at feature engineering and offline modeling.

This system goes further by combining:

| Capability | What it does |
|-----------|--------------|
| **Time-safe pipeline** | All historical features are computed using only information available before race time |
| **Production inference** | Models are served through FastAPI for live prediction |
| **Probability calibration** | Different odds buckets are calibrated separately to reduce bias |
| **Race-day UI** | Predictions are presented in a usable frontend instead of notebooks only |
| **Track-bias intelligence** | Historical draw bias is quantified and matched to the specific race configuration |
| **Research discipline** | Ideas are tested, rejected, and documented rather than added blindly |

> This makes the project closer to a **real forecasting product** than a one-off machine learning experiment.

---

## Performance

Hold-out test set · 415 races · 5,151 runners · 141 features

| Metric | Value | Benchmark |
|--------|-------|-----------|
| Place AUC | **0.773** | >0.70 (pass) |
| Top-3 Coverage (≥2) | **51.3%** | >30% (pass) |
| Top-5 Coverage (≥2) | **80.0%** | >50% (pass) |
| Coverage Stability | **95.6%** | >85% (pass) |
| Training Data | 46,737 rows · >3,000 races | 2022–2026 |
| Features | 141 | — |

---

## Performance Limitations

Strong offline metrics do **not** imply profitable betting. On the same hold-out set:

| Comparison | Model | Market (closing odds) |
|------------|-------|----------------------|
| Place AUC | 0.770 | **0.786** |
| Win AUC | 0.714 | **0.786** |

Tested value strategies against closing odds produced **negative ROI** (e.g. place-value edge >0.35: −41% ROI). Hong Kong parimutuel takeout (~17.5%) is a structural barrier.

**Where the model still adds value:**

- shortlist generation (Top-3 ≥2 at ~51%)
- complementary winner identification vs market alone
- stronger discrimination in extreme longshot segments (>50x odds)
- race-day context: tags, track bias, pace hints

The system is positioned as a **decision-support and ranking tool**, not a guaranteed profit engine against closing odds.

---

## Product View

The system is designed as a race-day decision tool, not just a modeling benchmark.

### Core outputs

- **Place probability** for each horse
- **Shortlist ranking** for Top-3 / Top-5 coverage
- **QPQ / value analysis**
- **Track bias context** by venue / distance / configuration
- **Pattern tags** such as `內檔反彈`
- **Model disagreement hints** when LGB ranker and stacked ensemble diverge

---

## Frontend

The project includes a lightweight single-file frontend for race-day usage.

| Page | Description |
|------|-------------|
| Today's Predictions | Horse ranking, place%, QPQ recommendations, model hints |
| Track Environment | Official track notes + historical draw bias analysis |
| Advanced Analysis | Betting simulator, quartet ideas, value analysis |
| Results | Predicted vs actual results |
| About | Model summary, system notes, performance overview |

---

## Why The Modeling Approach Looks Like This

The system uses a stacked ensemble because horse racing prediction has **two different requirements**:

- strong **ranking quality**
- stable **probability calibration**

A single model rarely does both equally well.

| Component | Role |
|----------|------|
| **LightGBM (lambdarank)** | Optimized for ranking horses within each race |
| **XGBoost / CatBoost** | Capture complementary binary place signals |
| **Ridge stacking** | Learns model weights from out-of-fold predictions |
| **Odds-bucket calibration** | Corrects overconfidence across different market segments |

> This design reflects the practical reality that **ranking** and **probability estimation** are related, but not identical, tasks.

---

## Technical Architecture

### Data Pipeline

| Stage | Tool | Description |
|-------|------|-------------|
| Raw Collection | - | CSV + SQLite |
| Feature Engineering | `TimeSafeFeatureEngineer` | 141 features with strict `< race_date` isolation |
| Feature Storage | `Parquet` | 46,737 rows, compressed & versioned |
| Model Training | `ModelTrainer` | 80/10/10 time split, 5-fold OOF stacking |
| Calibration | `OddsCalibratorBundle` | Per-odds-bucket Platt + MinMax |
| Inference | `RacePredictor` | Load models → predict → calibrate |
| Serving | `FastAPI + Uvicorn` | Online predict |

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| LightGBM as lambdarank | Better ranking for Top-3 prediction |
| XGBoost/CB as binary classifiers | Strong probability calibration |
| Ridge stacking (not averaging) | Learns optimal model weights from OOF |
| Odds-bucket calibration | Different odds ranges have different reliability |
| 3-5x cap at 0.55 | Fixes overconfidence in this range (+11.4% → +1.3% bias) |
| Time-series split (not random) | Prevents future data leakage |
| Single-file frontend | Zero dependencies, instant deployment |
| Trial data only for new/layoff horses | Avoids noise for horses with sufficient race history |

### Feature Engineering Principles

1. **Time-safe**: All historical features computed using only data strictly before the race date
2. **No target leakage**: `is_place`, `is_win`, `placing` never used as features
3. **Versioned cache**: Parquet files versioned (`FEATURE_CACHE_VERSION = "6.3"`) for reproducibility
4. **Modular**: Each feature group in its own module (trials, sectionals, pedigree, etc.)

### Performance Characteristics

| Component | Latency | Throughput |
|-----------|---------|------------|
| Feature computation (1 race) | ~50ms | — |
| Model inference (1 race) | ~10ms | — |
| Full response (11 races) | ~200ms | ~5 req/s |
| Model training (full) | ~8 minutes | — |
| Feature building (full) | ~9 minutes | — |

### Feature Categories

| Category | Examples | Count |
|----------|----------|-------|
| Speed Figures | SF_last1, SF_avg_last3, SF_trend | 8 |
| Recent Form | avg_pla_last3, form_score, improvement_trend | 10 |
| Jockey/Trainer | win_30d, place_30d, combo_win_rate | 12 |
| Sectional Times | final_section_time_last, hist_final_vs_par | 6 |
| Pedigree | sire/dam win rates by distance | 8 |
| Pace Prediction | pace_scenario_code, leader_count | 5 |
| Track Configuration | track_A/B/C/C+3 dummies | 5 |
| Trial Data | trial_days_ago, trial_finish_time | 4 |
| Weight Changes | weight_change, weight_trend_3 | 6 |
| Risk Factors | hot_horse_* series | 8 |
| + 97 more | going, country, stamina, running style... | 97 |

---

## Race-Day Intelligence Layer

The project includes a lightweight rules-and-insight layer on top of model output to make predictions more usable.

### Tag System

The system automatically tags horses with identifiable patterns to help users spot value:

| Tag | Trigger | Historical Impact |
|-----|---------|-------------------|
| `內檔反彈` | Last run >6th + Inside draw (1-3) this race | +15% place rate |
| `條件改善` | Last run >8th + Class drop / Weight drop / Recent trial | +15% place rate |
| `雙信號` | Both tags triggered | +16% place rate |

> Tags are **UI-only** — they don't modify model probabilities. They highlight horses where historical patterns suggest the model may be conservative.

### LGB Model Hint

When the LightGBM (lambdarank) model disagrees with the Ridge ensemble on Top-3 picks, a hint card appears:

```text
LGB Model Hint
辣得金 (31%)
1200m sprint — LGB ranking historically more accurate at this distance
```

> This only appears for 1200m races where LGB and Ridge diverge. Historical data shows LGB performs better on sprint distances (47% vs 32% Top-3 coverage).

---

## Track Bias Research

The system analyzed **3,857 historical races** to quantify draw bias across different track configurations. Results are dynamically served via `/api/track-bias` and displayed on the frontend.

### Methodology

- **Data**: 46,737 rows from 2022–2026, filtered to combinations with ≥30 samples
- **Metric**: Actual place rate per draw group vs field baseline
- **Draw Groups**: Inside (1-3), Middle (4-6), Outside (7-10), Wide (11+)
- **Track Configs**: A, B, C, C+3 for both Sha Tin (ST) and Happy Valley (HV)

### Key Findings

#### Sha Tin — Grass

| Distance | Track | Inside (1-3) | Middle (4-6) | Outside (7-10) | Wide (11+) | Baseline | Bias |
|----------|-------|-------------|-------------|----------------|------------|----------|------|
| 1200m | C+3 | **33.5%** | 22.6% | 22.0% | 25.2% | 26.0% | **+29%** |
| 1200m | C | **33.5%** | 22.6% | 22.0% | 25.2% | 26.0% | **+29%** |
| 1400m | C+3 | 26.5% | **26.7%** | 19.6% | 19.4% | 22.8% | +17% |
| 1800m | C+3 | N/A | N/A | N/A | N/A | N/A | Neutral |

> **Finding**: C/C+3 1200m shows the strongest inside bias. Inside-drawn horses place 29% more often than the field average. Outside and wide draws are disadvantaged.  
> *Note: C and C+3 rows share identical aggregates in this dataset because the analysis pools configurations with equivalent effective width for those meeting dates.*

#### Sha Tin — Dirt (All-Weather)

| Distance | Inside (1-3) | Middle (4-6) | Outside (7-10) | Wide (11+) | Baseline | Bias |
|----------|-------------|-------------|----------------|------------|----------|------|
| 1200m | 30.5% | 28.7% | 22.3% | 22.0% | 26.0% | +17% |
| 1650m | N/A | N/A | N/A | N/A | N/A | Mild |

> **Finding**: Dirt track is more fair than grass, but inside still has a mild advantage. Front-runners benefit on dirt.

#### Happy Valley — Grass

| Distance | Track | Inside (1-3) | Middle (4-6) | Outside (7-10) | Wide (11+) | Baseline | Bias |
|----------|-------|-------------|-------------|----------------|------------|----------|------|
| 1200m | C+3 | **35.2%** | 25.8% | 20.0% | 19.0% | 25.8% | **+36%** |
| 1200m | C | **35.2%** | 25.8% | 20.0% | 19.0% | 25.8% | **+36%** |
| 1650m | B | 28.5% | 27.0% | 22.0% | 21.5% | 25.0% | +14% |

> **Finding**: Happy Valley has the strongest draw bias overall. C/C+3 1200m inside bias (+36%) is the most extreme in Hong Kong racing. The tight turns and short straight amplify the inside advantage.

### Official HKJC Track Knowledge Integration

The system combines statistical findings with official HKJC track notes:

| Factor | Impact |
|--------|--------|
| **Sha Tin 1000m straight** | Exception: outside draws favored (crown of the track at ~2/3 width) |
| **C/C+3 configuration** | Narrowest track width (18.3m ST, 19.5m HV), sharpest turns |
| **Rain effect (HV)** | Track slopes outward → outside drier in rain |
| **Season-end wear** | Grass wear favors closers at Sha Tin |
| **Dirt after rain + harrowing** | Strong front-runner bias |

### Sample Size by Configuration

| Venue | Config | Distance | Sample Races |
|-------|--------|----------|-------------|
| ST | C+3 | 1200m | 346 |
| ST | C | 1200m | 346 |
| HV | C+3 | 1200m | 280 |
| HV | C | 1200m | 280 |
| ST | A | 1200m | 520 |
| ST | Dirt | 1650m | 180 |

> All statistics require ≥30 samples per combination. Configurations with insufficient data fall back to the nearest available configuration or general track knowledge.

### Real-time Application

The track bias data is served live via the API and displayed on the frontend **per race, per distance, per configuration** — not as static text. Each race card shows only the relevant bias for that specific race.

---

## Performance by Distance

| Distance | Races | AUC | Top-3 ≥2 | Notes |
|----------|-------|-----|----------|-------|
| 1000m (Straight) | Small sample | N/A | 100% | Outside bias on straight course |
| 1200m (Sprint) | 206 | 0.746 | 44% | Most common, weakest performance |
| 1400m (Mile) | — | 0.804 | 75% | Best performing distance |
| 1650m (Dirt) | Small sample | N/A | 33% | Dirt track |
| 1800m+ (Long) | — | 0.708 | N/A | Weakest AUC, needs improvement |

> **Finding**: 1200m sprints are the most common race type (50% of all races) but have the weakest model performance. Mile races (1400m) show the strongest AUC at 0.804. Long distance races (1800m+) remain challenging due to smaller sample sizes and different race dynamics (pace control > raw speed).

---

## Repository Contents

What is **actually in this GitHub repository**:

```text
hkhorseracing-predictor/
├── README.md
├── LICENSE
└── predictions/
    └── YYYY-MM-DD_VENUE_predictions.csv
```

### Predictions Archive

Race-day exports uploaded after each meeting for public auditability.

| Date | Venue | File |
|------|-------|------|
| 2026-07-08 | HV (Happy Valley) | [2026-07-08_HV_predictions.csv](predictions/2026-07-08_HV_predictions.csv) |

**Format:** `YYYY-MM-DD_VENUE_predictions.csv` where `VENUE` is `ST` (Sha Tin) or `HV` (Happy Valley).

> Published predictions are for research and analysis only — not betting advice and not guaranteed profit.

---

## Internal System Layout

The production system runs in a private codebase. Layout below is documented for methodology transparency — **these paths are not in this repository**.

```text
hkjc_predictor_v5/
├── server.py
├── src/hkjc_v5/
│   ├── features/
│   │   ├── engineer.py        # Main feature pipeline
│   │   ├── trials.py          # Trial-based features
│   │   ├── sectional_store.py # Sectional time features
│   │   └── ...
│   ├── training/
│   │   ├── trainer.py         # LGB + XGB + CB + stacking
│   │   └── calibration.py     # Odds-bucket calibration
│   ├── inference/
│   │   └── predictor.py       # RacePredictor
│   └── analysis/              # Track bias / market gap analysis
├── scripts/                   # Build / train / evaluate scripts
├── models/                    # Trained models (not published)
├── data/                      # Parquet / SQLite / raw data (not published)
└── index.html                 # Single-file frontend
```

---

## Research Foundations

This system is informed by prior work in:

- tabular ML for structured data
- horse racing market efficiency
- ensemble forecasting
- probability calibration
- track-bias analysis

In practice, our experiments confirmed three consistent findings:

1. Gradient-boosted trees outperform deep learning on this dataset size
2. Ranking quality and probability calibration should be optimized separately
3. Beating closing odds markets is much harder than improving offline AUC

---

## Repository Scope

This repository is a **public research and transparency archive**, not a full open-source code release.

### Why the full source code is not shared

The system was built as a personal production project. I publish documentation and prediction outputs, but not the complete codebase, for these reasons:

- **Commercial misuse risk**: Without the full data pipeline and model lifecycle context, partial code can be repackaged and sold as a “prediction product.”
- **Attribution and control**: I invested significant time in feature engineering, calibration, and race-day validation, and I do not want third parties to monetize this work without authorization.
- **Data/licensing constraints**: The project depends on external racing datasets and live market feeds that are not redistributable.
- **Operational complexity**: Trained models, feature caches, and serving infrastructure are environment-specific and not practical to open-source as a turnkey package.

### What I do share publicly

- System methodology and design decisions
- Performance summaries and research notes
- **Race-day prediction exports** in [`predictions/`](predictions/)

### Ongoing prediction uploads

I will continue uploading prediction CSV files after each meeting:

- Format: `YYYY-MM-DD_VENUE_predictions.csv`
- Purpose: public auditability and transparent tracking of model outputs
- Disclaimer: published predictions are for analysis only, not guaranteed betting profit

> If you are interested in collaboration, licensing, or consulting, please contact me directly at **tangttjason@gmail.com**.

---

## License

This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for details.
