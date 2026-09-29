# CANDAL v4 — Enhanced Future Signals Report

**Generated:** 2026-09-29 01:32:18

**Assets analyzed:** 17
**Total surviving signals (validated + beat breakeven):** 1910

## Methodology

- **Train/Test split:** 70/30 chronological (no shuffling, prevents overfitting)
- **Breakeven:** 55.6% (at 80.0% payout)
- **Min train samples:** 15
- **Min test samples:** 5
- **Min train accuracy:** 65.0%
- **Time buckets tested:** [5, 15, 30, 60] minutes + timeless
- **Patterns tested:** 11

---

## 🎯 Top 100 Surviving Signals (by test accuracy)

These signals PASSED the train phase AND validated on unseen test data AND beat breakeven.

| Asset | Time (UTC) | Pattern | Direction | Train % | Test % | Test Samples | Bucket |
|-------|-----------|---------|-----------|---------|--------|---------------|--------|
| EURUSD_otc | 12:15-12:20 | Momentum | BUY | 74.3% | 100.0% | 12 | 5min |
| USDARS_otc | 14:35-14:40 | Momentum | SELL | 71.4% | 100.0% | 10 | 5min |
| USDEGP_otc | 00:00-00:05 | Heavy | SELL | 66.7% | 100.0% | 6 | 5min |
| USDPKR_otc | 07:40-07:45 | Momentum | SELL | 75.8% | 100.0% | 14 | 5min |
| USDZAR_otc | 12:25-12:30 | Momentum | BUY | 84.8% | 100.0% | 6 | 5min |
| USDPKR_otc | 23:20-23:25 | Heavy | SELL | 71.0% | 100.0% | 5 | 5min |
| USDBDT_otc | 19:00-19:05 | Momentum | SELL | 80.0% | 100.0% | 10 | 5min |
| USDDZD_otc | 23:05-23:10 | Momentum | SELL | 65.5% | 100.0% | 5 | 5min |
| USDNGN_otc | 21:45-22:00 | LiquiditySweep | SELL | 67.9% | 100.0% | 6 | 15min |
| USDEGP_otc | 16:30-16:35 | Heavy | SELL | 74.1% | 100.0% | 6 | 5min |
| USDEGP_otc | 08:00-08:15 | LiquiditySweep | BUY | 66.7% | 100.0% | 9 | 15min |
| BRLUSD_otc | 21:25-21:30 | Momentum | SELL | 84.6% | 100.0% | 14 | 5min |
| EURGBP_otc | 07:10-07:15 | Momentum | SELL | 69.2% | 100.0% | 10 | 5min |
| USDZAR_otc | 09:05-09:10 | Momentum | BUY | 73.1% | 100.0% | 6 | 5min |
| EURGBP_otc | 17:05-17:10 | Momentum | SELL | 68.0% | 100.0% | 8 | 5min |
| USDDZD_otc | 23:00-23:05 | Momentum | SELL | 68.0% | 100.0% | 9 | 5min |
| USDEGP_otc | 22:00-22:05 | Momentum | SELL | 66.7% | 100.0% | 8 | 5min |
| USDEGP_otc | 17:15-17:30 | LiquiditySweep | BUY | 66.7% | 100.0% | 6 | 15min |
| EURCAD_otc | 10:00-11:00 | RSIExtreme | BUY | 65.2% | 100.0% | 8 | 60min |
| EURGBP_otc | 19:30-19:35 | Heavy | SELL | 69.6% | 100.0% | 8 | 5min |
| USDEGP_otc | 02:35-02:40 | Heavy | SELL | 65.2% | 100.0% | 5 | 5min |
| USDEGP_otc | 16:55-17:00 | Momentum | BUY | 65.2% | 100.0% | 7 | 5min |
| USDINR_otc | 19:45-20:00 | LiquiditySweep | BUY | 69.6% | 100.0% | 6 | 15min |
| BRLUSD_otc | 13:35-13:40 | Momentum | SELL | 77.3% | 100.0% | 5 | 5min |
| USDCOP_otc | 01:15-01:20 | Momentum | BUY | 68.2% | 100.0% | 11 | 5min |
| USDZAR_otc | 22:30-23:00 | ColorBurst | BUY | 90.9% | 100.0% | 8 | 30min |
| USDDZD_otc | 23:00-23:15 | LiquiditySweep | BUY | 66.7% | 100.0% | 13 | 15min |
| USDIDR_otc | 06:00-06:15 | LiquiditySweep | BUY | 71.4% | 100.0% | 5 | 15min |
| USDINR_otc | 13:10-13:15 | Engulfing | BUY | 66.7% | 100.0% | 6 | 5min |
| USDZAR_otc | 15:00-15:30 | ColorBurst | SELL | 66.7% | 100.0% | 5 | 30min |
| EURGBP_otc | 08:30-08:45 | InsideBarBreakout | BUY | 75.0% | 100.0% | 8 | 15min |
| USDBDT_otc | 10:15-10:30 | LiquiditySweep | BUY | 80.0% | 100.0% | 6 | 15min |
| USDMXN_otc | 14:00-14:05 | Momentum | SELL | 65.0% | 100.0% | 6 | 5min |
| EURUSD_otc | 21:30-21:45 | LiquiditySweep | BUY | 68.4% | 100.0% | 6 | 15min |
| USDDZD_otc | 18:30-19:00 | ColorBurst | BUY | 68.4% | 100.0% | 6 | 30min |
| USDEGP_otc | 11:00-12:00 | RSIExtreme | BUY | 94.7% | 100.0% | 7 | 60min |
| USDIDR_otc | 22:25-22:30 | Momentum | BUY | 78.9% | 100.0% | 10 | 5min |
| BRLUSD_otc | 02:00-02:15 | LiquiditySweep | SELL | 66.7% | 100.0% | 7 | 15min |
| BRLUSD_otc | 20:30-21:00 | ColorBurst | BUY | 77.8% | 100.0% | 5 | 30min |
| USDDZD_otc | 12:45-13:00 | LiquiditySweep | SELL | 66.7% | 100.0% | 7 | 15min |
| USDEGP_otc | 10:15-10:20 | Heavy | SELL | 66.7% | 100.0% | 7 | 5min |
| USDEGP_otc | 07:10-07:15 | Engulfing | BUY | 66.7% | 100.0% | 5 | 5min |
| USDINR_otc | 15:00-15:30 | ColorBurst | SELL | 94.1% | 100.0% | 7 | 30min |
| USDMXN_otc | 12:30-12:45 | LiquiditySweep | SELL | 76.5% | 100.0% | 5 | 15min |
| USDMXN_otc | 16:15-16:30 | LiquiditySweep | BUY | 76.5% | 100.0% | 6 | 15min |
| EURUSD_otc | 20:30-21:00 | ColorBurst | SELL | 93.8% | 100.0% | 7 | 30min |
| USDBDT_otc | 11:00-12:00 | RSIExtreme | SELL | 73.3% | 100.0% | 7 | 60min |
| USDIDR_otc | 07:30-07:45 | ColorBurst | SELL | 66.7% | 100.0% | 6 | 15min |
| USDNGN_otc | 16:00-16:15 | InsideBarBreakout | SELL | 66.7% | 100.0% | 5 | 15min |
| USDZAR_otc | 07:10-07:15 | Momentum | BUY | 80.0% | 94.4% | 18 | 5min |
| USDZAR_otc | 21:00-22:00 | RSIExtreme | SELL | 95.2% | 94.1% | 17 | 60min |
| USDBDT_otc | 09:05-09:10 | Momentum | BUY | 80.0% | 93.3% | 15 | 5min |
| USDEGP_otc | 12:30-12:45 | LiquiditySweep | SELL | 66.7% | 93.3% | 15 | 15min |
| EURGBP_otc | 18:10-18:15 | Momentum | SELL | 67.7% | 92.9% | 14 | 5min |
| USDARS_otc | 20:40-20:45 | Momentum | BUY | 87.1% | 92.9% | 14 | 5min |
| USDPHP_otc | 07:00-07:05 | Momentum | SELL | 66.7% | 92.9% | 14 | 5min |
| USDDZD_otc | 07:15-07:30 | LiquiditySweep | SELL | 66.7% | 92.9% | 14 | 15min |
| USDZAR_otc | 22:00-23:00 | ColorBurst | BUY | 78.0% | 92.3% | 13 | 60min |
| BRLUSD_otc | 11:00-11:05 | Momentum | SELL | 70.0% | 92.3% | 13 | 5min |
| USDZAR_otc | 21:00-21:30 | RSIExtreme | SELL | 100.0% | 92.3% | 13 | 30min |
| EURCAD_otc | 19:00-19:05 | Momentum | BUY | 68.8% | 91.7% | 12 | 5min |
| USDDZD_otc | 13:15-13:30 | LiquiditySweep | BUY | 66.7% | 91.7% | 12 | 15min |
| EURUSD_otc | 11:30-11:45 | LiquiditySweep | BUY | 82.6% | 91.7% | 12 | 15min |
| USDIDR_otc | 06:30-07:00 | ColorBurst | BUY | 66.7% | 91.7% | 12 | 30min |
| USDPKR_otc | 00:05-00:10 | Momentum | SELL | 70.6% | 90.9% | 11 | 5min |
| USDCOP_otc | 06:00-07:00 | RSIExtreme | SELL | 100.0% | 90.9% | 11 | 60min |
| USDPHP_otc | 09:55-10:00 | Reversal | SELL | 66.7% | 90.9% | 11 | 5min |
| USDMXN_otc | 20:00-20:15 | LiquiditySweep | SELL | 69.2% | 90.9% | 11 | 15min |
| USDMXN_otc | 06:40-06:45 | Momentum | SELL | 75.0% | 90.9% | 11 | 5min |
| USDPKR_otc | 01:20-01:25 | Momentum | BUY | 65.2% | 90.9% | 11 | 5min |
| EURGBP_otc | 01:20-01:25 | Heavy | BUY | 68.2% | 90.9% | 11 | 5min |
| USDCOP_otc | 01:20-01:25 | Heavy | SELL | 71.4% | 90.9% | 11 | 5min |
| EURGBP_otc | 09:50-09:55 | Momentum | SELL | 80.0% | 90.9% | 11 | 5min |
| USDCOP_otc | 18:20-18:25 | Momentum | SELL | 75.0% | 90.9% | 11 | 5min |
| USDNGN_otc | 09:25-09:30 | Momentum | BUY | 70.0% | 90.9% | 11 | 5min |
| USDEGP_otc | 02:30-02:35 | Momentum | SELL | 70.6% | 90.9% | 11 | 5min |
| USDMXN_otc | 16:30-17:00 | ColorBurst | BUY | 68.8% | 90.9% | 11 | 30min |
| USDBDT_otc | 04:20-04:25 | Momentum | BUY | 79.3% | 90.0% | 10 | 5min |
| BRLUSD_otc | 20:55-21:00 | Momentum | BUY | 72.0% | 90.0% | 10 | 5min |
| USDARS_otc | 05:15-05:20 | Momentum | SELL | 66.7% | 90.0% | 10 | 5min |
| USDEGP_otc | 07:15-07:20 | Momentum | BUY | 70.8% | 90.0% | 20 | 5min |
| EURCAD_otc | 08:15-08:30 | LiquiditySweep | SELL | 65.2% | 90.0% | 10 | 15min |
| USDPHP_otc | 09:35-09:40 | Momentum | SELL | 66.7% | 90.0% | 10 | 5min |
| USDEGP_otc | 00:00-00:15 | LiquiditySweep | BUY | 77.8% | 90.0% | 10 | 15min |
| USDPHP_otc | 02:40-02:45 | Momentum | BUY | 69.4% | 88.9% | 9 | 5min |
| EURCAD_otc | 23:35-23:40 | Momentum | SELL | 67.7% | 88.9% | 9 | 5min |
| USDPHP_otc | 04:25-04:30 | Momentum | BUY | 82.8% | 88.9% | 9 | 5min |
| EURNZD_otc | 02:40-02:45 | Momentum | BUY | 75.0% | 88.9% | 9 | 5min |
| USDDZD_otc | 04:25-04:30 | Momentum | BUY | 78.6% | 88.9% | 9 | 5min |
| USDEGP_otc | 15:20-15:25 | Momentum | SELL | 74.1% | 88.9% | 18 | 5min |
| EURNZD_otc | 23:05-23:10 | Engulfing | BUY | 65.4% | 88.9% | 9 | 5min |
| EURUSD_otc | 17:30-17:35 | Momentum | SELL | 69.2% | 88.9% | 9 | 5min |
| USDPHP_otc | 12:25-12:30 | Momentum | BUY | 73.1% | 88.9% | 9 | 5min |
| USDNGN_otc | 17:50-17:55 | Momentum | SELL | 68.0% | 88.9% | 9 | 5min |
| EURUSD_otc | 08:50-08:55 | Momentum | SELL | 79.2% | 88.9% | 9 | 5min |
| USDINR_otc | 12:50-12:55 | Momentum | BUY | 79.2% | 88.9% | 9 | 5min |
| USDINR_otc | 19:10-19:15 | Engulfing | BUY | 66.7% | 88.9% | 9 | 5min |
| USDPHP_otc | 23:00-23:05 | Heavy | BUY | 68.2% | 88.9% | 9 | 5min |
| EURCAD_otc | 02:20-02:25 | Momentum | SELL | 66.7% | 88.9% | 9 | 5min |
| USDBDT_otc | 19:00-19:15 | LiquiditySweep | BUY | 81.0% | 88.9% | 9 | 15min |

---

## 📊 Per-Asset Summary

| Asset | Train Candles | Test Candles | Validated Signals | Top Test Accuracy |
|-------|---------------|--------------|-------------------|-------------------|
| BRLUSD_otc | 30238 | 12960 | 115 | 100.0% |
| EURCAD_otc | 30239 | 12960 | 94 | 100.0% |
| EURGBP_otc | 30237 | 12959 | 128 | 100.0% |
| EURNZD_otc | 30237 | 12960 | 102 | 88.9% |
| EURUSD_otc | 30239 | 12960 | 122 | 100.0% |
| USDARS_otc | 30239 | 12961 | 106 | 100.0% |
| USDBDT_otc | 30238 | 12960 | 108 | 100.0% |
| USDCOP_otc | 30239 | 12961 | 98 | 100.0% |
| USDDZD_otc | 30239 | 12961 | 110 | 100.0% |
| USDEGP_otc | 30238 | 12960 | 133 | 100.0% |
| USDIDR_otc | 30239 | 12960 | 150 | 100.0% |
| USDINR_otc | 30237 | 12959 | 120 | 100.0% |
| USDMXN_otc | 30238 | 12960 | 93 | 100.0% |
| USDNGN_otc | 30239 | 12961 | 112 | 100.0% |
| USDPHP_otc | 30237 | 12960 | 113 | 92.9% |
| USDPKR_otc | 30237 | 12960 | 101 | 100.0% |
| USDZAR_otc | 30237 | 12960 | 105 | 100.0% |

---

## 📈 Pattern Performance (across all assets)

| Pattern | # Signals | Avg Train Acc | Avg Test Acc | Best Test Acc |
|---------|-----------|---------------|--------------|---------------|
| Momentum | 672 | 71.4% | 69.7% | 100.0% |
| Heavy | 305 | 69.6% | 66.1% | 100.0% |
| LiquiditySweep | 289 | 70.8% | 68.6% | 100.0% |
| Engulfing | 231 | 69.5% | 64.4% | 100.0% |
| ColorBurst | 113 | 73.0% | 70.5% | 100.0% |
| Reversal | 109 | 68.5% | 64.7% | 90.9% |
| InsideBarBreakout | 108 | 69.9% | 65.1% | 100.0% |
| WickRejection | 58 | 70.9% | 66.2% | 88.9% |
| RSIExtreme | 14 | 85.9% | 82.3% | 100.0% |
| DoubleTopBottom | 8 | 67.0% | 65.8% | 81.5% |
| SqueezeBreakout | 3 | 77.2% | 66.7% | 80.0% |

---

## ⏰ Time Bucket Performance

| Bucket | # Signals | Avg Test Acc |
|--------|-----------|-------------|
| 5min | 1252 | 67.8% |
| 15min | 362 | 68.1% |
| 30min | 217 | 67.8% |
| 60min | 79 | 67.4% |

