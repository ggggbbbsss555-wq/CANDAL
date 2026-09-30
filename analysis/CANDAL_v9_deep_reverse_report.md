# CANDAL v9 — Deep Reverse Engineering Report

**Generated:** 2026-09-30 00:26:10

**Total eligible minutes (after deep filters):** 524
**Today's schedule:** 28 signals

## 🔍 Discoveries from Competitor Analysis (998 signals)

### Discovery 1: MTG is 100% Successful
- Competitor uses MTG in 27% of trades
- ALL 269 MTG signals won (100% success rate)
- **Insight**: MTG should only fire when L1 loss is followed by high-confidence recovery

### Discovery 2: PUT is 4% Safer than CALL
- PUT loss rate: 9.9%
- CALL loss rate: 13.7%
- **Action**: when L1 tie, prefer PUT

### Discovery 3: Best/Worst Hours (UTC)
| Hour | Loss Rate | Status |
|------|-----------|--------|
| 11:00 | 5.6% | ✅ BEST |
| 17:00 | 6.9% | ✅ BEST |
| 20:00 | 8.3% | ✅ BEST |
| 15:00 | 9.9% | ✅ BEST |
| 18:00 | 11.7% | ✅ BEST |
| 12:00 | 13.0% | ⚠️ NEUTRAL |
| 13:00 | 12.6% | ⚠️ NEUTRAL |
| 14:00 | 10.6% | ⚠️ NEUTRAL |
| 19:00 | 12.5% | ⚠️ NEUTRAL |
| 22:00 | 13.3% | ⚠️ NEUTRAL |
| 10:00 | 25.0% | ❌ AVOID |
| 16:00 | 19.2% | ❌ AVOID |
| 21:00 | 16.3% | ❌ AVOID |
| 23:00 | 16.3% | ❌ AVOID |

### Discovery 4: Best/Worst Assets
| Asset | Loss Rate | Status |
|-------|-----------|--------|
| USDCOP_otc | 7.1% | ✅ BEST |
| USDDZD_otc | 9.2% | ✅ BEST |
| USDBDT_otc | 10.0% | ✅ BEST |
| USDIDR_otc | 10.4% | ✅ BEST |
| USDARS_otc | 10.7% | ✅ BEST |
| USDNGN_otc | 10.9% | ⚠️ NEUTRAL |
| USDINR_otc | 11.3% | ⚠️ NEUTRAL |
| USDZAR_otc | 12.3% | ⚠️ NEUTRAL |
| USDPHP_otc | 11.1% | ⚠️ NEUTRAL |
| USDMXN_otc | 12.8% | ⚠️ NEUTRAL |
| USDPKR_otc | 14.5% | ⚠️ NEUTRAL |
| BRLUSD_otc | 16.8% | ❌ AVOID |

---

## 📅 Today's Schedule (obfuscation: random gaps + asset rotation)

| # | Time (UTC) | Asset | Dir | L1% | Comb% | MTG Use% | MTG Succ% | Samples |
|---|-----------|-------|-----|-----|-------|----------|-----------|---------|
| 1 | 00:04 | USDARS_otc | CALL | 60.0% | 89.0% | 40.0% | 72.5% | 100 |
| 2 | 02:14 | USDZAR_otc | CALL | 65.0% | 87.0% | 35.0% | 62.9% | 100 |
| 3 | 02:56 | USDEGP_otc | PUT | 65.0% | 87.0% | 35.0% | 62.9% | 100 |
| 4 | 03:12 | USDINR_otc | PUT | 63.0% | 87.0% | 37.0% | 64.9% | 100 |
| 5 | 03:15 | USDINR_otc | PUT | 61.0% | 88.0% | 39.0% | 69.2% | 100 |
| 6 | 03:51 | USDPHP_otc | CALL | 63.0% | 87.0% | 37.0% | 64.9% | 100 |
| 7 | 05:05 | USDBDT_otc | PUT | 65.0% | 87.0% | 35.0% | 62.9% | 100 |
| 8 | 05:54 | USDIDR_otc | PUT | 63.0% | 87.0% | 37.0% | 64.9% | 100 |
| 9 | 06:03 | USDEGP_otc | PUT | 66.0% | 87.0% | 34.0% | 61.8% | 100 |
| 10 | 07:20 | USDPHP_otc | PUT | 61.0% | 88.0% | 39.0% | 69.2% | 100 |
| 11 | 08:06 | USDNGN_otc | CALL | 65.0% | 89.0% | 35.0% | 68.6% | 100 |
| 12 | 08:09 | USDARS_otc | PUT | 62.0% | 88.0% | 38.0% | 68.4% | 100 |
| 13 | 08:30 | USDEGP_otc | PUT | 60.0% | 88.0% | 40.0% | 70.0% | 100 |
| 14 | 08:35 | USDCOP_otc | PUT | 64.0% | 88.0% | 36.0% | 66.7% | 100 |
| 15 | 11:27 | USDBDT_otc | CALL | 58.0% | 88.0% | 42.0% | 71.4% | 100 |
| 16 | 12:21 | USDEGP_otc | PUT | 62.0% | 88.0% | 38.0% | 68.4% | 100 |
| 17 | 12:25 | USDINR_otc | PUT | 69.0% | 88.0% | 31.0% | 61.3% | 100 |
| 18 | 13:04 | USDPHP_otc | PUT | 60.0% | 88.0% | 40.0% | 70.0% | 100 |
| 19 | 13:10 | USDCOP_otc | CALL | 64.0% | 89.0% | 36.0% | 69.4% | 100 |
| 20 | 13:31 | USDPKR_otc | PUT | 61.0% | 88.0% | 39.0% | 69.2% | 100 |
| 21 | 18:08 | USDINR_otc | PUT | 58.0% | 88.0% | 42.0% | 71.4% | 100 |
| 22 | 18:33 | USDDZD_otc | CALL | 59.0% | 89.0% | 41.0% | 73.2% | 100 |
| 23 | 19:03 | USDIDR_otc | CALL | 59.0% | 90.0% | 41.0% | 75.6% | 100 |
| 24 | 19:27 | USDMXN_otc | CALL | 63.0% | 87.0% | 37.0% | 64.9% | 100 |
| 25 | 19:51 | USDARS_otc | CALL | 63.0% | 88.0% | 37.0% | 67.6% | 100 |
| 26 | 20:47 | USDMXN_otc | PUT | 62.0% | 89.0% | 38.0% | 71.1% | 100 |
| 27 | 22:07 | USDINR_otc | CALL | 63.0% | 88.0% | 37.0% | 67.6% | 100 |
| 28 | 22:24 | USDARS_otc | PUT | 58.0% | 88.0% | 42.0% | 71.4% | 100 |

## 📊 Per-Asset Summary (filtered)

| Asset | Eligible Minutes | Avg L1% | Avg Comb% | Avg MTG Use% | Best Comb% |
|-------|-----------------|---------|-----------|--------------|-------------|
| USDNGN_otc | 51 | 60.0% | 84.0% | 40.0% | 89.0% |
| USDPHP_otc | 51 | 59.6% | 83.7% | 40.4% | 88.0% |
| USDBDT_otc | 48 | 59.9% | 83.8% | 40.1% | 88.0% |
| USDINR_otc | 45 | 59.9% | 84.5% | 40.1% | 88.0% |
| USDEGP_otc | 45 | 60.3% | 84.3% | 39.7% | 88.0% |
| USDARS_otc | 44 | 60.0% | 84.3% | 40.0% | 89.0% |
| USDZAR_otc | 42 | 59.7% | 83.7% | 40.3% | 87.0% |
| USDDZD_otc | 41 | 59.8% | 83.5% | 40.2% | 89.0% |
| USDPKR_otc | 41 | 59.8% | 83.7% | 40.2% | 88.0% |
| USDMXN_otc | 40 | 59.7% | 83.9% | 40.3% | 89.0% |
| USDCOP_otc | 38 | 59.7% | 83.7% | 40.3% | 89.0% |
| USDIDR_otc | 38 | 59.3% | 84.0% | 40.7% | 90.0% |

---

## 📈 Schedule Statistics

- Signals today: **28**
- Avg L1 win rate: **62.2%**
- Avg Combined win rate: **88.0%**
- Avg MTG use rate: **37.8%** (target: 45%)
- Avg MTG success rate: **67.9%**
- Unique assets: 12
- Gap: min=3, max=277, avg=49.6 min

