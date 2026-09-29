# CANDAL — Institutional Strategy Analysis Report

**Generated:** 2026-09-28 23:52:18

**Assets analyzed:** 4
**Per-asset candles:** ~43,200 (30 days M1)
**Win-rate target:** ≥65%
**Forward-looking requirement:** signal must print ≥1 minute before the move

---

## ⏰ Executive Summary: Time Patterns Across All Assets

Below are the strongest recurring time-of-day biases detected for each asset.
These are minutes-of-day that historically produce same-direction moves ≥60% of the time.

### Recurring Minute-of-Day Patterns (bias ≥ 0.60)

| Asset | Minute-of-Day (UTC) | Direction | Bias | Samples |
|-------|---------------------|-----------|------|---------|
| BRLUSD_otc | 16:36 | Bear | -0.633 | 30 |
| BRLUSD_otc | 20:21 | Bear | -0.600 | 30 |
| USDARS_otc | 14:55 | Bull | +0.600 | 30 |
| USDDZD_otc | 04:39 | Bull | +0.600 | 30 |
| USDPKR_otc | 18:06 | Bull | +0.600 | 30 |

### Kill Zone Bias Summary

| Asset | Asian (00-07) | London (07-10) | NY AM (12-15) | NY PM (15-18) | Off (18-24) |
|-------|---------------|-----------------|---------------|---------------|-------------|
| BRLUSD_otc | ⚪ -0.007 | 🟢 +0.023 | ⚪ -0.003 | ⚪ +0.004 | ⚪ -0.006 |
| USDARS_otc | ⚪ +0.001 | ⚪ +0.007 | 🔴 -0.026 | ⚪ +0.005 | ⚪ -0.003 |
| USDDZD_otc | ⚪ +0.010 | 🟢 +0.035 | ⚪ +0.001 | ⚪ -0.001 | ⚪ -0.001 |
| USDPKR_otc | ⚪ +0.003 | ⚪ -0.013 | 🔴 -0.027 | ⚪ -0.002 | ⚪ +0.000 |

> Legend: 🟢 = bullish bias (BUY friendly), 🔴 = bearish bias (SELL friendly), ⚪ = neutral

---

## 🎯 Top Winning Strategies (Win Rate ≥65%, ATR-based TP/SL)

**Methodology:**
- TP = 1.0 × ATR(14) at signal bar (asset-adaptive)
- SL = 1.0 × ATR(14) (1:1 risk/reward, conservative)
- Forward window: 1 to 5 minutes (signal must print ≥1 min before the move)
- Min trades for inclusion: 50

| Asset | Strategy | Forward (min) | Trades | Win Rate | Expectancy (ATR) | Expectancy (pips) |
|-------|----------|---------------|--------|----------|------------------|--------------------|
| USDDZD_otc | BOS_Confluence_Bear | 5 | 88 | 80.7% | +0.210 | +0.62 |
| BRLUSD_otc | NY_KZ_CHoCH_Bear | 5 | 113 | 79.6% | +0.195 | +4.84 |
| USDPKR_otc | BOS_Continuation_Bear | 5 | 4857 | 79.1% | +0.187 | +0.55 |
| USDARS_otc | BOS_Confluence_Bull | 5 | 57 | 78.9% | +0.184 | +10.63 |
| USDDZD_otc | NY_KZ_CHoCH_Bull | 5 | 113 | 78.8% | +0.181 | +0.54 |
| USDDZD_otc | BOS_Continuation_Bear | 5 | 4425 | 78.3% | +0.175 | +0.51 |
| BRLUSD_otc | BOS_Continuation_Bear | 5 | 4515 | 78.2% | +0.173 | +4.31 |
| USDARS_otc | BOS_Continuation_Bull | 5 | 5082 | 77.9% | +0.169 | +9.45 |
| BRLUSD_otc | BOS_Continuation_Bull | 5 | 4885 | 77.8% | +0.167 | +4.15 |
| USDPKR_otc | BOS_Continuation_Bull | 5 | 4692 | 77.7% | +0.165 | +0.49 |
| USDDZD_otc | BOS_Continuation_Bull | 5 | 5265 | 77.7% | +0.165 | +0.50 |
| USDARS_otc | BOS_Confluence_Bull | 3 | 57 | 77.2% | +0.158 | +9.11 |
| USDPKR_otc | BOS_Confluence_Bear | 5 | 78 | 76.9% | +0.154 | +0.48 |
| USDARS_otc | BOS_Continuation_Bear | 5 | 4585 | 76.8% | +0.152 | +8.57 |
| USDPKR_otc | BOS_Continuation_Bear | 3 | 4857 | 75.5% | +0.133 | +0.39 |
| BRLUSD_otc | NY_KZ_CHoCH_Bear | 3 | 113 | 75.2% | +0.128 | +3.19 |
| USDDZD_otc | BOS_Continuation_Bear | 3 | 4425 | 74.8% | +0.122 | +0.36 |
| USDPKR_otc | BOS_Confluence_Bear | 3 | 78 | 74.4% | +0.115 | +0.36 |
| USDDZD_otc | NY_KZ_CHoCH_Bull | 3 | 113 | 74.3% | +0.115 | +0.34 |
| BRLUSD_otc | BOS_Continuation_Bear | 3 | 4515 | 74.3% | +0.115 | +2.87 |
| USDPKR_otc | NY_KZ_CHoCH_Bull | 5 | 116 | 74.1% | +0.112 | +0.32 |
| USDPKR_otc | BOS_Continuation_Bull | 3 | 4692 | 74.0% | +0.110 | +0.33 |
| USDDZD_otc | BOS_Continuation_Bull | 3 | 5265 | 73.9% | +0.108 | +0.33 |
| USDARS_otc | BOS_Continuation_Bull | 3 | 5082 | 73.7% | +0.106 | +5.93 |
| BRLUSD_otc | BOS_Continuation_Bull | 3 | 4885 | 73.7% | +0.105 | +2.60 |
| USDPKR_otc | NY_KZ_CHoCH_Bear | 5 | 125 | 73.6% | +0.104 | +0.30 |
| USDPKR_otc | CHoCH_Reversal_Bear | 5 | 977 | 73.6% | +0.104 | +0.30 |
| USDARS_otc | BOS_Continuation_Bear | 3 | 4585 | 73.2% | +0.098 | +5.53 |
| BRLUSD_otc | BOS_Confluence_Bear | 5 | 67 | 73.1% | +0.097 | +2.46 |
| BRLUSD_otc | CHoCH_Reversal_Bear | 5 | 1054 | 73.1% | +0.096 | +2.37 |
| USDDZD_otc | BOS_Confluence_Bear | 3 | 88 | 72.7% | +0.091 | +0.27 |
| USDARS_otc | CHoCH_Reversal_Bear | 5 | 1117 | 72.5% | +0.088 | +4.96 |
| BRLUSD_otc | BOS_Confluence_Bull | 5 | 65 | 72.3% | +0.085 | +2.13 |
| USDDZD_otc | CHoCH_Reversal_Bear | 5 | 1014 | 72.3% | +0.084 | +0.25 |
| USDDZD_otc | CHoCH_Reversal_Bull | 5 | 1014 | 71.9% | +0.078 | +0.23 |
| USDPKR_otc | NY_KZ_CHoCH_Bull | 3 | 116 | 70.7% | +0.060 | +0.17 |
| USDDZD_otc | London_KZ_Sweep_Bull | 5 | 146 | 70.5% | +0.058 | +0.17 |
| USDDZD_otc | BOS_Confluence_Bull | 5 | 78 | 70.5% | +0.058 | +0.18 |
| BRLUSD_otc | CHoCH_Reversal_Bull | 5 | 1054 | 70.3% | +0.055 | +1.35 |
| USDARS_otc | BOS_Confluence_Bull | 2 | 57 | 70.2% | +0.053 | +3.04 |
| USDPKR_otc | CHoCH_Reversal_Bull | 5 | 977 | 70.1% | +0.052 | +0.15 |
| USDDZD_otc | NY_KZ_CHoCH_Bear | 5 | 110 | 70.0% | +0.050 | +0.15 |
| USDDZD_otc | CHoCH_Reversal_Bear | 3 | 1014 | 69.9% | +0.049 | +0.14 |
| USDPKR_otc | CHoCH_Reversal_Bear | 3 | 977 | 69.9% | +0.049 | +0.14 |
| USDPKR_otc | NY_KZ_CHoCH_Bear | 3 | 125 | 69.6% | +0.044 | +0.13 |
| BRLUSD_otc | CHoCH_Reversal_Bear | 3 | 1054 | 69.4% | +0.040 | +1.00 |
| USDDZD_otc | SMC_Triple_Bull(OB+Sweep) | 3 | 88 | 69.3% | +0.040 | +0.12 |
| USDDZD_otc | SMC_Triple_Bull(OB+Sweep) | 5 | 88 | 69.3% | +0.040 | +0.12 |
| USDPKR_otc | BB_Squeeze_Breakout_Bear | 5 | 81 | 69.1% | +0.037 | +0.11 |
| USDDZD_otc | NY_KZ_CHoCH_Bear | 3 | 110 | 69.1% | +0.036 | +0.11 |


---

## 📊 BRLUSD_otc

- Total candles: **43,198**
- Pip size: **1e-05**

### ⏰ Time Patterns

**Kill Zone Performance:**

| Kill Zone | Bias | Sample | Avg Range (pips) |
|-----------|------|--------|------------------|
| Asian | -0.007 | 12600 | 24.6 |
| London | +0.023 | 5400 | 24.9 |
| NY_AM | -0.003 | 5400 | 24.3 |
| NY_PM | +0.004 | 5400 | 24.1 |
| Off-hours | -0.006 | 14398 | 24.7 |

**Recurring minute-of-day patterns (high-confidence):**

| Minute-of-Day | Bias | Sample |
|---------------|------|--------|
| 16:36 | Bear (-0.633) | 30 |
| 20:21 | Bear (-0.600) | 30 |

### 📈 All Strategies Ranked by Win Rate (at fwd=2 min)

| Strategy | Trades | Win Rate | Win@fwd=1 | Win@fwd=2 | Win@fwd=3 | Win@fwd=5 | Expectancy (fwd=2) |
|----------|--------|----------|-----------|-----------|-----------|-----------|---------------------|
| BOS_Continuation_Bear | 4515 | 67.4% | 50.7% | 67.4% | 74.3% | 78.2% | +0.27 |
| BOS_Continuation_Bull | 4885 | 67.1% | 49.5% | 67.1% | 73.7% | 77.8% | +0.17 |
| ICT_LondonOpen_WithAsian | 30 | 66.7% | 40.0% | 66.7% | 66.7% | 70.0% | -0.00 |
| NY_KZ_CHoCH_Bear | 113 | 65.5% | 48.7% | 65.5% | 75.2% | 79.6% | -0.44 |
| CHoCH_Reversal_Bear | 1054 | 63.9% | 49.3% | 63.9% | 69.4% | 73.1% | -1.04 |
| London_KZ_Sweep_Bull | 189 | 60.3% | 40.2% | 60.3% | 63.5% | 67.2% | -2.37 |
| RecurringMinute_Bear | 60 | 60.0% | 48.3% | 60.0% | 60.0% | 61.7% | -2.39 |
| SMC_Triple_Bull(OB+Sweep) | 82 | 59.8% | 46.3% | 59.8% | 67.1% | 68.3% | -2.69 |
| CHoCH_Reversal_Bull | 1054 | 59.7% | 45.3% | 59.7% | 66.7% | 70.3% | -2.60 |
| BOS_Confluence_Bear | 67 | 58.2% | 46.3% | 58.2% | 68.7% | 73.1% | -3.22 |
| NY_KZ_CHoCH_Bull | 116 | 57.8% | 44.8% | 57.8% | 65.5% | 68.1% | -3.28 |
| RSI_Divergence_Bull | 3878 | 56.3% | 41.4% | 56.3% | 62.3% | 65.7% | -3.84 |
| Confluence_Bear | 523 | 56.2% | 43.6% | 56.2% | 61.6% | 66.1% | -4.12 |
| RSI_Divergence_Bear | 3747 | 55.6% | 41.3% | 55.6% | 61.5% | 65.2% | -4.06 |
| FVG_BearOnly | 5596 | 55.0% | 41.0% | 55.0% | 60.9% | 64.6% | -4.38 |

### 🏆 Winning Strategies for this asset (≥65%)

- **NY_KZ_CHoCH_Bear** @ fwd=5min — win rate 79.6% over 113 trades, expectancy +4.84 pips
- **BOS_Continuation_Bear** @ fwd=5min — win rate 78.2% over 4515 trades, expectancy +4.31 pips
- **BOS_Continuation_Bull** @ fwd=5min — win rate 77.8% over 4885 trades, expectancy +4.15 pips
- **NY_KZ_CHoCH_Bear** @ fwd=3min — win rate 75.2% over 113 trades, expectancy +3.19 pips
- **BOS_Continuation_Bear** @ fwd=3min — win rate 74.3% over 4515 trades, expectancy +2.87 pips
- **BOS_Continuation_Bull** @ fwd=3min — win rate 73.7% over 4885 trades, expectancy +2.60 pips
- **BOS_Confluence_Bear** @ fwd=5min — win rate 73.1% over 67 trades, expectancy +2.46 pips
- **CHoCH_Reversal_Bear** @ fwd=5min — win rate 73.1% over 1054 trades, expectancy +2.37 pips
- **BOS_Confluence_Bull** @ fwd=5min — win rate 72.3% over 65 trades, expectancy +2.13 pips
- **CHoCH_Reversal_Bull** @ fwd=5min — win rate 70.3% over 1054 trades, expectancy +1.35 pips


---

## 📊 USDARS_otc

- Total candles: **43,200**
- Pip size: **0.01**

### ⏰ Time Patterns

**Kill Zone Performance:**

| Kill Zone | Bias | Sample | Avg Range (pips) |
|-----------|------|--------|------------------|
| Asian | +0.001 | 12600 | 55.5 |
| London | +0.007 | 5400 | 55.9 |
| NY_AM | -0.026 | 5400 | 56.5 |
| NY_PM | +0.005 | 5400 | 56.9 |
| Off-hours | -0.003 | 14400 | 55.6 |

**Recurring minute-of-day patterns (high-confidence):**

| Minute-of-Day | Bias | Sample |
|---------------|------|--------|
| 14:55 | Bull (+0.600) | 30 |

### 📈 All Strategies Ranked by Win Rate (at fwd=2 min)

| Strategy | Trades | Win Rate | Win@fwd=1 | Win@fwd=2 | Win@fwd=3 | Win@fwd=5 | Expectancy (fwd=2) |
|----------|--------|----------|-----------|-----------|-----------|-----------|---------------------|
| BOS_Confluence_Bull | 57 | 70.2% | 40.4% | 70.2% | 77.2% | 78.9% | +3.04 |
| BOS_Continuation_Bull | 5082 | 67.1% | 50.8% | 67.1% | 73.7% | 77.9% | +0.40 |
| BOS_Continuation_Bear | 4585 | 66.5% | 49.0% | 66.5% | 73.2% | 76.8% | -0.10 |
| CHoCH_Reversal_Bear | 1117 | 62.0% | 46.8% | 62.0% | 68.8% | 72.5% | -3.92 |
| BOS_Confluence_Bear | 80 | 61.3% | 45.0% | 61.3% | 67.5% | 67.5% | -4.66 |
| CHoCH_Reversal_Bull | 1117 | 59.6% | 43.7% | 59.6% | 66.2% | 68.9% | -5.91 |
| NY_KZ_CHoCH_Bear | 146 | 59.6% | 47.3% | 59.6% | 64.4% | 67.8% | -6.04 |
| LiquiditySweep_Bull | 1401 | 59.1% | 44.3% | 59.1% | 63.7% | 66.9% | -6.42 |
| BB_Squeeze_Breakout_Bull | 79 | 58.2% | 44.3% | 58.2% | 64.6% | 68.4% | -7.07 |
| SMC_Triple_Bull(OB+Sweep) | 87 | 57.5% | 41.4% | 57.5% | 60.9% | 66.7% | -8.06 |
| RSI_Divergence_Bear | 3775 | 56.7% | 42.1% | 56.7% | 62.0% | 65.6% | -8.34 |
| ICT_LondonOpen_WithAsian | 30 | 56.7% | 40.0% | 56.7% | 63.3% | 66.7% | -8.32 |
| ICT_NYOpen_WithAsian | 30 | 56.7% | 43.3% | 56.7% | 63.3% | 66.7% | -8.42 |
| RecurringMinute_Bull | 30 | 56.7% | 46.7% | 56.7% | 56.7% | 66.7% | -8.52 |
| LiquiditySweep_Bear | 1472 | 56.6% | 42.1% | 56.6% | 62.8% | 65.0% | -8.48 |

### 🏆 Winning Strategies for this asset (≥65%)

- **BOS_Confluence_Bull** @ fwd=5min — win rate 78.9% over 57 trades, expectancy +10.63 pips
- **BOS_Continuation_Bull** @ fwd=5min — win rate 77.9% over 5082 trades, expectancy +9.45 pips
- **BOS_Confluence_Bull** @ fwd=3min — win rate 77.2% over 57 trades, expectancy +9.11 pips
- **BOS_Continuation_Bear** @ fwd=5min — win rate 76.8% over 4585 trades, expectancy +8.57 pips
- **BOS_Continuation_Bull** @ fwd=3min — win rate 73.7% over 5082 trades, expectancy +5.93 pips
- **BOS_Continuation_Bear** @ fwd=3min — win rate 73.2% over 4585 trades, expectancy +5.53 pips
- **CHoCH_Reversal_Bear** @ fwd=5min — win rate 72.5% over 1117 trades, expectancy +4.96 pips
- **BOS_Confluence_Bull** @ fwd=2min — win rate 70.2% over 57 trades, expectancy +3.04 pips
- **CHoCH_Reversal_Bull** @ fwd=5min — win rate 68.9% over 1117 trades, expectancy +1.90 pips
- **CHoCH_Reversal_Bear** @ fwd=3min — win rate 68.8% over 1117 trades, expectancy +1.85 pips


---

## 📊 USDDZD_otc

- Total candles: **43,200**
- Pip size: **0.01**

### ⏰ Time Patterns

**Kill Zone Performance:**

| Kill Zone | Bias | Sample | Avg Range (pips) |
|-----------|------|--------|------------------|
| Asian | +0.010 | 12600 | 2.9 |
| London | +0.035 | 5400 | 2.9 |
| NY_AM | +0.001 | 5400 | 3.1 |
| NY_PM | -0.001 | 5400 | 2.9 |
| Off-hours | -0.001 | 14400 | 2.9 |

**Recurring minute-of-day patterns (high-confidence):**

| Minute-of-Day | Bias | Sample |
|---------------|------|--------|
| 04:39 | Bull (+0.600) | 30 |

### 📈 All Strategies Ranked by Win Rate (at fwd=2 min)

| Strategy | Trades | Win Rate | Win@fwd=1 | Win@fwd=2 | Win@fwd=3 | Win@fwd=5 | Expectancy (fwd=2) |
|----------|--------|----------|-----------|-----------|-----------|-----------|---------------------|
| NY_KZ_CHoCH_Bull | 113 | 69.0% | 53.1% | 69.0% | 74.3% | 78.8% | +0.11 |
| BOS_Continuation_Bear | 4425 | 68.1% | 50.0% | 68.1% | 74.8% | 78.3% | +0.06 |
| BOS_Continuation_Bull | 5265 | 67.1% | 49.7% | 67.1% | 73.9% | 77.7% | +0.02 |
| BOS_Confluence_Bear | 88 | 67.0% | 56.8% | 67.0% | 72.7% | 80.7% | +0.02 |
| ICT_LondonOpen_WithAsian | 30 | 66.7% | 56.7% | 66.7% | 70.0% | 70.0% | -0.00 |
| CHoCH_Reversal_Bear | 1014 | 64.9% | 50.0% | 64.9% | 69.9% | 72.3% | -0.08 |
| CHoCH_Reversal_Bull | 1014 | 63.0% | 47.3% | 63.0% | 68.6% | 71.9% | -0.16 |
| BB_Squeeze_Breakout_Bear | 71 | 62.0% | 45.1% | 62.0% | 67.6% | 67.6% | -0.21 |
| BOS_Confluence_Bull | 78 | 61.5% | 47.4% | 61.5% | 66.7% | 70.5% | -0.23 |
| NY_KZ_CHoCH_Bear | 110 | 60.9% | 48.2% | 60.9% | 69.1% | 70.0% | -0.25 |
| SMC_Triple_Bear(OB+Sweep) | 83 | 60.2% | 43.4% | 60.2% | 63.9% | 65.1% | -0.29 |
| RecurringMinute_Bull | 30 | 60.0% | 46.7% | 60.0% | 60.0% | 63.3% | -0.29 |
| London_KZ_Sweep_Bull | 146 | 59.6% | 43.2% | 59.6% | 67.8% | 70.5% | -0.31 |
| LiquiditySweep_Bear | 1334 | 59.4% | 43.5% | 59.4% | 63.8% | 67.1% | -0.32 |
| SMC_Triple_Bull(OB+Sweep) | 88 | 59.1% | 47.7% | 59.1% | 69.3% | 69.3% | -0.35 |

### 🏆 Winning Strategies for this asset (≥65%)

- **BOS_Confluence_Bear** @ fwd=5min — win rate 80.7% over 88 trades, expectancy +0.62 pips
- **NY_KZ_CHoCH_Bull** @ fwd=5min — win rate 78.8% over 113 trades, expectancy +0.54 pips
- **BOS_Continuation_Bear** @ fwd=5min — win rate 78.3% over 4425 trades, expectancy +0.51 pips
- **BOS_Continuation_Bull** @ fwd=5min — win rate 77.7% over 5265 trades, expectancy +0.50 pips
- **BOS_Continuation_Bear** @ fwd=3min — win rate 74.8% over 4425 trades, expectancy +0.36 pips
- **NY_KZ_CHoCH_Bull** @ fwd=3min — win rate 74.3% over 113 trades, expectancy +0.34 pips
- **BOS_Continuation_Bull** @ fwd=3min — win rate 73.9% over 5265 trades, expectancy +0.33 pips
- **BOS_Confluence_Bear** @ fwd=3min — win rate 72.7% over 88 trades, expectancy +0.27 pips
- **CHoCH_Reversal_Bear** @ fwd=5min — win rate 72.3% over 1014 trades, expectancy +0.25 pips
- **CHoCH_Reversal_Bull** @ fwd=5min — win rate 71.9% over 1014 trades, expectancy +0.23 pips


---

## 📊 USDPKR_otc

- Total candles: **43,197**
- Pip size: **0.01**

### ⏰ Time Patterns

**Kill Zone Performance:**

| Kill Zone | Bias | Sample | Avg Range (pips) |
|-----------|------|--------|------------------|
| Asian | +0.003 | 12600 | 2.9 |
| London | -0.013 | 5400 | 2.9 |
| NY_AM | -0.027 | 5400 | 2.9 |
| NY_PM | -0.002 | 5400 | 2.9 |
| Off-hours | +0.000 | 14397 | 2.9 |

**Recurring minute-of-day patterns (high-confidence):**

| Minute-of-Day | Bias | Sample |
|---------------|------|--------|
| 18:06 | Bull (+0.600) | 30 |

### 📈 All Strategies Ranked by Win Rate (at fwd=2 min)

| Strategy | Trades | Win Rate | Win@fwd=1 | Win@fwd=2 | Win@fwd=3 | Win@fwd=5 | Expectancy (fwd=2) |
|----------|--------|----------|-----------|-----------|-----------|-----------|---------------------|
| BOS_Continuation_Bear | 4857 | 68.8% | 51.4% | 68.8% | 75.5% | 79.1% | +0.10 |
| NY_KZ_CHoCH_Bull | 116 | 68.1% | 52.6% | 68.1% | 70.7% | 74.1% | +0.06 |
| BOS_Continuation_Bull | 4692 | 67.4% | 50.4% | 67.4% | 74.0% | 77.7% | +0.03 |
| BOS_Confluence_Bear | 78 | 65.4% | 43.6% | 65.4% | 74.4% | 76.9% | -0.06 |
| CHoCH_Reversal_Bear | 977 | 61.7% | 47.4% | 61.7% | 69.9% | 73.6% | -0.22 |
| NY_KZ_CHoCH_Bear | 125 | 61.6% | 46.4% | 61.6% | 69.6% | 73.6% | -0.22 |
| CHoCH_Reversal_Bull | 977 | 60.6% | 47.0% | 60.6% | 67.5% | 70.1% | -0.27 |
| RecurringMinute_Bull | 30 | 60.0% | 50.0% | 60.0% | 66.7% | 66.7% | -0.29 |
| Confluence_Bear | 499 | 58.9% | 45.1% | 58.9% | 63.9% | 68.3% | -0.36 |
| SMC_Triple_Bull(OB+Sweep) | 82 | 58.5% | 46.3% | 58.5% | 62.2% | 65.9% | -0.37 |
| BB_Squeeze_Breakout_Bear | 81 | 56.8% | 42.0% | 56.8% | 65.4% | 69.1% | -0.44 |
| Confluence_Bull | 495 | 56.6% | 43.4% | 56.6% | 61.8% | 64.8% | -0.46 |
| ICT_PowerOf3_Bear | 195 | 56.4% | 43.1% | 56.4% | 62.6% | 65.1% | -0.49 |
| RSI_Divergence_Bear | 3902 | 56.3% | 41.5% | 56.3% | 61.7% | 65.2% | -0.46 |
| BOS_Confluence_Bull | 75 | 56.0% | 42.7% | 56.0% | 61.3% | 64.0% | -0.48 |

### 🏆 Winning Strategies for this asset (≥65%)

- **BOS_Continuation_Bear** @ fwd=5min — win rate 79.1% over 4857 trades, expectancy +0.55 pips
- **BOS_Continuation_Bull** @ fwd=5min — win rate 77.7% over 4692 trades, expectancy +0.49 pips
- **BOS_Confluence_Bear** @ fwd=5min — win rate 76.9% over 78 trades, expectancy +0.48 pips
- **BOS_Continuation_Bear** @ fwd=3min — win rate 75.5% over 4857 trades, expectancy +0.39 pips
- **BOS_Confluence_Bear** @ fwd=3min — win rate 74.4% over 78 trades, expectancy +0.36 pips
- **NY_KZ_CHoCH_Bull** @ fwd=5min — win rate 74.1% over 116 trades, expectancy +0.32 pips
- **BOS_Continuation_Bull** @ fwd=3min — win rate 74.0% over 4692 trades, expectancy +0.33 pips
- **NY_KZ_CHoCH_Bear** @ fwd=5min — win rate 73.6% over 125 trades, expectancy +0.30 pips
- **CHoCH_Reversal_Bear** @ fwd=5min — win rate 73.6% over 977 trades, expectancy +0.30 pips
- **NY_KZ_CHoCH_Bull** @ fwd=3min — win rate 70.7% over 116 trades, expectancy +0.17 pips

