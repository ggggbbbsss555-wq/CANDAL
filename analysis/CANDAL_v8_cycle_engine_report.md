# CANDAL v8 — Variable-Gap Signal Schedule (Obfuscation Mode)

**Generated:** 2026-09-30 00:17:03

**Assets analyzed:** 17
**Total eligible minutes (passing all filters):** 65
**Today's schedule:** 21 signals (random in [20, 40])

## Methodology

Inspired by competitor bot analysis + obfuscation requirements:

1. **Filter**: L1 ≥ 60% (no martingale needed), p < 0.05, samples ≥ 80, martingale use ≤ 35%
2. **Daily count**: Random 20-40 signals (different each day)
3. **Gap**: Variable 3-6 min normal, 10 min after martingale
4. **Asset rotation**: No same-asset in consecutive signals
5. **Obfuscation**: Different minutes + assets each day (no fixed pattern)
6. **Martingale**: ONE retry only (no MTG2)

---

## 📅 Today's Schedule (21 signals)

| # | Time (UTC) | Asset | Direction | L1 % | Combined % | Mart Use % | Samples |
|---|-----------|-------|-----------|------|------------|------------|---------|
| 1 | 00:22 | USDBDT_otc | PUT | 68.0% | 86.0% | 32.0% | 100 |
| 2 | 02:04 | BRLUSD_otc | CALL | 66.0% | 86.0% | 34.0% | 100 |
| 3 | 02:14 | USDZAR_otc | CALL | 65.0% | 87.0% | 35.0% | 100 |
| 4 | 04:36 | BRLUSD_otc | PUT | 67.0% | 84.0% | 33.0% | 100 |
| 5 | 05:05 | USDBDT_otc | PUT | 65.0% | 87.0% | 35.0% | 100 |
| 6 | 05:51 | USDZAR_otc | PUT | 66.0% | 84.0% | 34.0% | 100 |
| 7 | 06:03 | USDEGP_otc | PUT | 66.0% | 87.0% | 34.0% | 100 |
| 8 | 06:40 | USDMXN_otc | PUT | 65.0% | 85.0% | 35.0% | 100 |
| 9 | 08:06 | USDNGN_otc | CALL | 65.0% | 89.0% | 35.0% | 100 |
| 10 | 09:58 | USDBDT_otc | PUT | 65.0% | 85.0% | 35.0% | 100 |
| 11 | 11:05 | USDPKR_otc | CALL | 67.0% | 84.0% | 33.0% | 100 |
| 12 | 12:25 | USDINR_otc | PUT | 69.0% | 88.0% | 31.0% | 100 |
| 13 | 12:27 | USDZAR_otc | CALL | 67.0% | 84.0% | 33.0% | 100 |
| 14 | 12:38 | USDIDR_otc | PUT | 65.0% | 85.0% | 35.0% | 100 |
| 15 | 14:02 | BRLUSD_otc | PUT | 66.0% | 85.0% | 34.0% | 100 |
| 16 | 15:57 | USDNGN_otc | PUT | 65.0% | 85.0% | 35.0% | 100 |
| 17 | 16:37 | USDARS_otc | PUT | 65.0% | 86.0% | 35.0% | 100 |
| 18 | 17:55 | USDARS_otc | CALL | 66.0% | 86.0% | 34.0% | 100 |
| 19 | 18:23 | USDDZD_otc | PUT | 66.0% | 86.0% | 34.0% | 100 |
| 20 | 19:04 | USDZAR_otc | PUT | 65.0% | 86.0% | 35.0% | 100 |
| 21 | 19:08 | USDPHP_otc | CALL | 65.0% | 85.0% | 35.0% | 100 |

### Gap Distribution (minutes between consecutive signals)

| Gap (min) | Count |
|-----------|-------|
| 2 | 1 |
| 4 | 1 |
| 10 | 1 |
| 11 | 1 |
| 12 | 1 |
| 28 | 1 |
| 29 | 1 |
| 37 | 1 |
| 40 | 1 |
| 41 | 1 |
| 46 | 1 |
| 67 | 1 |
| 78 | 1 |
| 80 | 1 |
| 84 | 1 |
| 86 | 1 |
| 102 | 1 |
| 112 | 1 |
| 115 | 1 |
| 142 | 1 |

---

## 🎯 Top 100 Eligible Minutes (sorted by L1 then Combined)

These are the pool from which each day's schedule is drawn.

| # | Asset | Time (UTC) | Direction | L1 % | Combined % | Mart Use % | Samples | p-value |
|---|-------|-----------|-----------|------|------------|------------|---------|---------|
| 1 | USDNGN_otc | 08:06 | CALL | 65.0% | 89.0% | 35.0% | 100 | 0.0013 ✓ |
| 2 | USDINR_otc | 12:25 | PUT | 69.0% | 88.0% | 31.0% | 100 | 0.0001 ✓ |
| 3 | USDEGP_otc | 06:03 | PUT | 66.0% | 87.0% | 34.0% | 100 | 0.0007 ✓ |
| 4 | USDBDT_otc | 05:05 | PUT | 65.0% | 87.0% | 35.0% | 100 | 0.0013 ✓ |
| 5 | USDEGP_otc | 02:56 | PUT | 65.0% | 87.0% | 35.0% | 100 | 0.0013 ✓ |
| 6 | USDZAR_otc | 02:14 | CALL | 65.0% | 87.0% | 35.0% | 100 | 0.0013 ✓ |
| 7 | USDBDT_otc | 00:22 | PUT | 68.0% | 86.0% | 32.0% | 100 | 0.0002 ✓ |
| 8 | BRLUSD_otc | 02:04 | CALL | 66.0% | 86.0% | 34.0% | 100 | 0.0007 ✓ |
| 9 | USDARS_otc | 17:55 | CALL | 66.0% | 86.0% | 34.0% | 100 | 0.0007 ✓ |
| 10 | USDDZD_otc | 18:23 | PUT | 66.0% | 86.0% | 34.0% | 100 | 0.0007 ✓ |
| 11 | USDARS_otc | 16:37 | PUT | 65.0% | 86.0% | 35.0% | 100 | 0.0013 ✓ |
| 12 | USDARS_otc | 19:28 | PUT | 65.0% | 86.0% | 35.0% | 100 | 0.0013 ✓ |
| 13 | USDZAR_otc | 19:04 | PUT | 65.0% | 86.0% | 35.0% | 100 | 0.0013 ✓ |
| 14 | BRLUSD_otc | 14:02 | PUT | 66.0% | 85.0% | 34.0% | 100 | 0.0007 ✓ |
| 15 | USDBDT_otc | 09:58 | PUT | 65.0% | 85.0% | 35.0% | 100 | 0.0013 ✓ |
| 16 | USDIDR_otc | 12:38 | PUT | 65.0% | 85.0% | 35.0% | 100 | 0.0013 ✓ |
| 17 | USDMXN_otc | 06:40 | PUT | 65.0% | 85.0% | 35.0% | 100 | 0.0013 ✓ |
| 18 | USDNGN_otc | 15:57 | PUT | 65.0% | 85.0% | 35.0% | 100 | 0.0013 ✓ |
| 19 | USDPHP_otc | 19:08 | CALL | 65.0% | 85.0% | 35.0% | 100 | 0.0013 ✓ |
| 20 | BRLUSD_otc | 04:36 | PUT | 67.0% | 84.0% | 33.0% | 100 | 0.0003 ✓ |
| 21 | USDPKR_otc | 11:05 | CALL | 67.0% | 84.0% | 33.0% | 100 | 0.0003 ✓ |
| 22 | USDZAR_otc | 12:27 | CALL | 67.0% | 84.0% | 33.0% | 100 | 0.0003 ✓ |
| 23 | USDZAR_otc | 05:51 | PUT | 66.0% | 84.0% | 34.0% | 100 | 0.0007 ✓ |
| 24 | USDCOP_otc | 15:54 | PUT | 65.0% | 84.0% | 35.0% | 100 | 0.0013 ✓ |
| 25 | USDBDT_otc | 14:35 | PUT | 69.0% | 83.0% | 31.0% | 100 | 0.0001 ✓ |
| 26 | USDNGN_otc | 07:32 | PUT | 69.0% | 83.0% | 31.0% | 100 | 0.0001 ✓ |
| 27 | USDPKR_otc | 10:57 | PUT | 67.0% | 83.0% | 33.0% | 100 | 0.0003 ✓ |
| 28 | USDZAR_otc | 19:00 | CALL | 67.0% | 83.0% | 33.0% | 100 | 0.0003 ✓ |
| 29 | USDBDT_otc | 03:25 | PUT | 66.0% | 83.0% | 34.0% | 100 | 0.0007 ✓ |
| 30 | USDDZD_otc | 22:46 | PUT | 66.0% | 83.0% | 34.0% | 100 | 0.0007 ✓ |
| 31 | USDNGN_otc | 17:09 | PUT | 66.0% | 83.0% | 34.0% | 100 | 0.0007 ✓ |
| 32 | USDNGN_otc | 21:31 | PUT | 66.0% | 83.0% | 34.0% | 100 | 0.0007 ✓ |
| 33 | BRLUSD_otc | 06:41 | PUT | 65.0% | 83.0% | 35.0% | 100 | 0.0013 ✓ |
| 34 | BRLUSD_otc | 12:54 | PUT | 65.0% | 83.0% | 35.0% | 100 | 0.0013 ✓ |
| 35 | USDDZD_otc | 07:48 | PUT | 65.0% | 83.0% | 35.0% | 100 | 0.0013 ✓ |
| 36 | USDZAR_otc | 17:28 | PUT | 65.0% | 83.0% | 35.0% | 100 | 0.0013 ✓ |
| 37 | USDBDT_otc | 20:01 | PUT | 67.0% | 82.0% | 33.0% | 100 | 0.0003 ✓ |
| 38 | USDIDR_otc | 22:09 | CALL | 66.0% | 82.0% | 34.0% | 100 | 0.0007 ✓ |
| 39 | BRLUSD_otc | 11:07 | PUT | 65.0% | 82.0% | 35.0% | 100 | 0.0013 ✓ |
| 40 | BRLUSD_otc | 21:07 | PUT | 65.0% | 82.0% | 35.0% | 100 | 0.0013 ✓ |
| 41 | USDCOP_otc | 07:04 | PUT | 65.0% | 82.0% | 35.0% | 100 | 0.0013 ✓ |
| 42 | USDINR_otc | 16:29 | PUT | 65.0% | 82.0% | 35.0% | 100 | 0.0013 ✓ |
| 43 | USDMXN_otc | 19:07 | PUT | 65.0% | 82.0% | 35.0% | 100 | 0.0013 ✓ |
| 44 | USDCOP_otc | 17:41 | PUT | 68.0% | 81.0% | 32.0% | 100 | 0.0002 ✓ |
| 45 | USDDZD_otc | 03:34 | PUT | 67.0% | 81.0% | 33.0% | 100 | 0.0003 ✓ |
| 46 | USDNGN_otc | 14:44 | PUT | 66.0% | 81.0% | 34.0% | 100 | 0.0007 ✓ |
| 47 | USDZAR_otc | 12:21 | PUT | 66.0% | 81.0% | 34.0% | 100 | 0.0007 ✓ |
| 48 | USDDZD_otc | 19:09 | PUT | 65.0% | 81.0% | 35.0% | 100 | 0.0013 ✓ |
| 49 | USDEGP_otc | 00:34 | PUT | 65.0% | 81.0% | 35.0% | 100 | 0.0013 ✓ |
| 50 | USDPHP_otc | 13:01 | PUT | 65.0% | 81.0% | 35.0% | 100 | 0.0013 ✓ |
| 51 | USDBDT_otc | 16:28 | CALL | 67.0% | 80.0% | 33.0% | 100 | 0.0003 ✓ |
| 52 | BRLUSD_otc | 15:39 | PUT | 66.0% | 80.0% | 34.0% | 100 | 0.0007 ✓ |
| 53 | USDPHP_otc | 22:16 | PUT | 66.0% | 80.0% | 34.0% | 100 | 0.0007 ✓ |
| 54 | USDZAR_otc | 06:19 | PUT | 66.0% | 80.0% | 34.0% | 100 | 0.0007 ✓ |
| 55 | USDZAR_otc | 07:46 | PUT | 66.0% | 80.0% | 34.0% | 100 | 0.0007 ✓ |
| 56 | BRLUSD_otc | 16:10 | PUT | 65.0% | 80.0% | 35.0% | 100 | 0.0013 ✓ |
| 57 | USDCOP_otc | 08:36 | PUT | 65.0% | 80.0% | 35.0% | 100 | 0.0013 ✓ |
| 58 | USDPHP_otc | 13:05 | PUT | 65.0% | 80.0% | 35.0% | 100 | 0.0013 ✓ |
| 59 | USDDZD_otc | 23:21 | PUT | 67.0% | 79.0% | 33.0% | 100 | 0.0003 ✓ |
| 60 | USDARS_otc | 18:40 | PUT | 65.0% | 79.0% | 35.0% | 100 | 0.0013 ✓ |
| 61 | USDMXN_otc | 19:47 | PUT | 65.0% | 79.0% | 35.0% | 100 | 0.0013 ✓ |
| 62 | USDZAR_otc | 23:15 | PUT | 65.0% | 79.0% | 35.0% | 100 | 0.0013 ✓ |
| 63 | USDPHP_otc | 21:09 | PUT | 66.0% | 78.0% | 34.0% | 100 | 0.0007 ✓ |
| 64 | USDIDR_otc | 04:15 | CALL | 67.0% | 77.0% | 33.0% | 100 | 0.0003 ✓ |
| 65 | BRLUSD_otc | 22:07 | PUT | 65.0% | 77.0% | 35.0% | 100 | 0.0013 ✓ |

---

## 📊 Per-Asset Summary (eligible minutes only)

| Asset | Eligible Minutes | Avg L1 % | Avg Combined % | Avg Mart Use % | Best Combined % |
|-------|-----------------|----------|-----------------|-----------------|------------------|
| USDZAR_otc | 10 | 65.8% | 82.7% | 34.2% | 87.0% |
| BRLUSD_otc | 10 | 65.5% | 82.2% | 34.5% | 86.0% |
| USDBDT_otc | 7 | 66.7% | 83.7% | 33.3% | 87.0% |
| USDNGN_otc | 6 | 66.2% | 84.0% | 33.8% | 89.0% |
| USDDZD_otc | 6 | 66.0% | 82.2% | 34.0% | 86.0% |
| USDPHP_otc | 5 | 65.4% | 80.8% | 34.6% | 85.0% |
| USDARS_otc | 4 | 65.3% | 84.2% | 34.8% | 86.0% |
| USDCOP_otc | 4 | 65.8% | 81.8% | 34.2% | 84.0% |
| USDEGP_otc | 3 | 65.3% | 85.0% | 34.7% | 87.0% |
| USDIDR_otc | 3 | 66.0% | 81.3% | 34.0% | 85.0% |
| USDMXN_otc | 3 | 65.0% | 82.0% | 35.0% | 85.0% |
| USDINR_otc | 2 | 67.0% | 85.0% | 33.0% | 88.0% |
| USDPKR_otc | 2 | 67.0% | 83.5% | 33.0% | 84.0% |

---

## 📈 Schedule Statistics

- Total signals today: **21**
- Average L1 win rate: **65.9%**
- Average Combined win rate: **85.7%**
- Average Martingale use rate: **34.1%** (rare)
- Min combined: 84.0%
- Max combined: 89.0%
- Unique assets in schedule: 12
- Gap min/max/avg: 2/142/56.3 min

