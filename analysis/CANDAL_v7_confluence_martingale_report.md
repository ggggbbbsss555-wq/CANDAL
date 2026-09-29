# CANDAL v7 — Triple Confluence + Martingale Report

**Generated:** 2026-09-29 02:01:47
**Assets analyzed:** 17
**Total exploits found:** 16

## Methodology

Each exploit combines 3 conditions that must all be TRUE at the current bar:
1. **Shape** (candle shape): hammer, doji, wick rejection, big/small body, color bar
2. **Context** (sequence before): 2-5 same-color candles BEFORE
3. **Momentum/Indicator**: body behavior, range expansion, RSI, MACD, BB, EMA

Each exploit predicts the color of the NEXT 1-minute candle.

**Martingale**: if first prediction loses, re-enter same direction at the very next bar. **Only ONE retry.**

**Validation (70/30 chronological split):**
- Train L1 win rate ≥ 65% (without martingale)
- Train Combined win rate ≥ 85% (with martingale)
- Test Combined win rate ≥ 85% (out-of-sample)
- Min train samples: 15
- Min test samples: 5
- Statistical significance: p < 0.05

---

## 🏆 ELITE Exploits (Test Combined ≥ 90%)

**5 exploits with combined win rate ≥ 90%** (close to 1 loss per 20 trades).

| # | Asset | Direction | Shape | Context | Momentum | Train L1% | Train Comb% | Test L1% | Test Comb% | Test Samples | p-value |
|---|-------|-----------|-------|---------|----------|-----------|-------------|----------|------------|---------------|---------|
| 1 | USDZAR_otc | SELL | red_bar | 5greens | bb_upper_breach | 73.1% | 88.5% | 71.4% | 100.0% | 7 | 0.0093 ✓ |
| 2 | BRLUSD_otc | SELL | star | 2greens | bb_upper_breach | 70.6% | 94.1% | 60.0% | 100.0% | 5 | 0.0448 ✓ |
| 3 | USDIDR_otc | SELL | star | 3greens | bb_upper_breach | 70.6% | 94.1% | 80.0% | 100.0% | 5 | 0.0448 ✓ |
| 4 | BRLUSD_otc | SELL | star | 4greens | body_shrinking | 75.0% | 85.0% | 54.5% | 90.9% | 11 | 0.0127 ✓ |
| 5 | USDPHP_otc | SELL | doji | 5greens | body_growing | 68.0% | 88.0% | 63.6% | 90.9% | 11 | 0.0359 ✓ |

---

## 🎯 Top 100 Exploits (Test Combined ≥ 85%)

| # | Asset | Direction | Shape | Context | Momentum | Train L1% | Train Comb% | Test L1% | Test Comb% | Test Samples | p-value |
|---|-------|-----------|-------|---------|----------|-----------|-------------|----------|------------|---------------|---------|
| 1 | USDZAR_otc | SELL | red_bar | 5greens | bb_upper_breach | 73.1% | 88.5% | 71.4% | 100.0% | 7 | 0.0093 ✓ |
| 2 | BRLUSD_otc | SELL | star | 2greens | bb_upper_breach | 70.6% | 94.1% | 60.0% | 100.0% | 5 | 0.0448 ✓ |
| 3 | USDIDR_otc | SELL | star | 3greens | bb_upper_breach | 70.6% | 94.1% | 80.0% | 100.0% | 5 | 0.0448 ✓ |
| 4 | BRLUSD_otc | SELL | star | 4greens | body_shrinking | 75.0% | 85.0% | 54.5% | 90.9% | 11 | 0.0127 ✓ |
| 5 | USDPHP_otc | SELL | doji | 5greens | body_growing | 68.0% | 88.0% | 63.6% | 90.9% | 11 | 0.0359 ✓ |
| 6 | EURUSD_otc | SELL | red_bar | 3greens | macd_cross_down | 65.6% | 87.5% | 52.6% | 89.5% | 19 | 0.0385 ✓ |
| 7 | USDIDR_otc | SELL | star | 2greens | bb_upper_breach | 71.4% | 90.5% | 62.5% | 87.5% | 8 | 0.0248 ✓ |
| 8 | USDMXN_otc | SELL | red_bar | 4greens | macd_cross_down | 77.8% | 94.4% | 25.0% | 87.5% | 8 | 0.0092 ✓ |
| 9 | USDINR_otc | BUY | small_green | 5reds | rsi_oversold | 69.7% | 90.9% | 71.4% | 85.7% | 21 | 0.0118 ✓ |
| 10 | USDINR_otc | BUY | hammer | 4reds | rsi_oversold | 75.0% | 100.0% | 71.4% | 85.7% | 7 | 0.0228 ✓ |
| 11 | USDMXN_otc | SELL | wick_rej_up | 3greens | body_shrinking | 65.6% | 87.5% | 58.3% | 83.3% | 12 | 0.0385 ✓ |
| 12 | USDZAR_otc | SELL | red_bar | 4greens | bb_upper_breach | 66.7% | 87.2% | 58.3% | 83.3% | 12 | 0.0187 ✓ |
| 13 | USDINR_otc | BUY | wick_rej_down | 2reds | rsi_oversold | 73.3% | 93.3% | 66.7% | 83.3% | 6 | 0.0354 ✓ |
| 14 | EURNZD_otc | SELL | small_red | 3greens | body_growing | 66.7% | 88.9% | 60.0% | 80.0% | 10 | 0.0416 ✓ |
| 15 | USDPHP_otc | SELL | doji | 5greens | ema_below | 66.7% | 92.6% | 40.0% | 80.0% | 10 | 0.0416 ✓ |
| 16 | USDARS_otc | SELL | star | 5greens | body_shrinking | 70.6% | 94.1% | 40.0% | 80.0% | 5 | 0.0448 ✓ |

---

## 📊 Per-Asset Summary

| Asset | Total | Elite (≥95%) | Super (≥90%) | Best Test Comb% |
|-------|-------|--------------|--------------|------------------|
| BRLUSD_otc | 2 | 2 | 2 | 100.0% |
| EURNZD_otc | 1 | 0 | 0 | 80.0% |
| EURUSD_otc | 1 | 0 | 1 | 89.5% |
| USDARS_otc | 1 | 0 | 0 | 80.0% |
| USDIDR_otc | 2 | 1 | 2 | 100.0% |
| USDINR_otc | 3 | 0 | 2 | 85.7% |
| USDMXN_otc | 2 | 0 | 1 | 87.5% |
| USDPHP_otc | 2 | 1 | 1 | 90.9% |
| USDZAR_otc | 2 | 1 | 1 | 100.0% |

