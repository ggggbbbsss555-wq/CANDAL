# CANDAL v8 — Cycle Signal Engine Report

**Generated:** 2026-09-29 23:53:40

**Assets analyzed:** 17
**Total minutes passing filter:** 1118
**Schedule signals (every 5 min):** 284

## Methodology

Inspired by analysis of competitor bot (88% win rate, 3-min cycle):

1. For each asset, scan every minute-of-day on historical data
2. For each minute, compute:
   - L1 win rate (predict next bar direction)
   - Combined win rate (L1 + martingale if L1 loses)
3. Filter: L1 ≥ 60%, p < 0.05, samples ≥ 80
4. Build 3-minute cycle: every 5 minutes, emit 1 signal
   (best available minute, rotating assets to avoid same-asset repeat)

---

## 🎯 Top 100 Minute Patterns (by combined win rate)

| # | Asset | Time (UTC) | Direction | L1 % | Combined % | Samples | p-value |
|---|-------|-----------|-----------|------|------------|---------|---------|
| 1 | USDNGN_otc | 08:06 | CALL | 65.0% | 89.0% | 100 | 0.0013 ✓ |
| 2 | USDCOP_otc | 13:10 | CALL | 64.0% | 89.0% | 100 | 0.0026 ✓ |
| 3 | USDCOP_otc | 11:41 | PUT | 63.0% | 89.0% | 100 | 0.0047 ✓ |
| 4 | USDMXN_otc | 20:47 | PUT | 62.0% | 89.0% | 100 | 0.0082 ✓ |
| 5 | USDARS_otc | 00:04 | CALL | 60.0% | 89.0% | 100 | 0.0228 ✓ |
| 6 | USDINR_otc | 12:25 | PUT | 69.0% | 88.0% | 100 | 0.0001 ✓ |
| 7 | USDBDT_otc | 10:13 | PUT | 64.0% | 88.0% | 100 | 0.0026 ✓ |
| 8 | USDCOP_otc | 08:35 | PUT | 64.0% | 88.0% | 100 | 0.0026 ✓ |
| 9 | USDARS_otc | 19:51 | CALL | 63.0% | 88.0% | 100 | 0.0047 ✓ |
| 10 | USDINR_otc | 22:07 | CALL | 63.0% | 88.0% | 100 | 0.0047 ✓ |
| 11 | BRLUSD_otc | 01:00 | PUT | 62.0% | 88.0% | 100 | 0.0082 ✓ |
| 12 | USDARS_otc | 08:09 | PUT | 62.0% | 88.0% | 100 | 0.0082 ✓ |
| 13 | USDEGP_otc | 12:21 | PUT | 62.0% | 88.0% | 100 | 0.0082 ✓ |
| 14 | USDINR_otc | 03:15 | PUT | 61.0% | 88.0% | 100 | 0.0139 ✓ |
| 15 | USDPHP_otc | 07:20 | PUT | 61.0% | 88.0% | 100 | 0.0139 ✓ |
| 16 | USDPKR_otc | 13:31 | PUT | 61.0% | 88.0% | 100 | 0.0139 ✓ |
| 17 | USDEGP_otc | 08:30 | PUT | 60.0% | 88.0% | 100 | 0.0228 ✓ |
| 18 | USDPHP_otc | 13:04 | PUT | 60.0% | 88.0% | 100 | 0.0228 ✓ |
| 19 | USDEGP_otc | 06:03 | PUT | 66.0% | 87.0% | 100 | 0.0007 ✓ |
| 20 | USDBDT_otc | 05:05 | PUT | 65.0% | 87.0% | 100 | 0.0013 ✓ |
| 21 | USDEGP_otc | 02:56 | PUT | 65.0% | 87.0% | 100 | 0.0013 ✓ |
| 22 | USDZAR_otc | 02:14 | CALL | 65.0% | 87.0% | 100 | 0.0013 ✓ |
| 23 | USDIDR_otc | 10:09 | PUT | 64.0% | 87.0% | 100 | 0.0026 ✓ |
| 24 | BRLUSD_otc | 08:07 | PUT | 63.0% | 87.0% | 100 | 0.0047 ✓ |
| 25 | BRLUSD_otc | 16:06 | PUT | 63.0% | 87.0% | 100 | 0.0047 ✓ |
| 26 | USDIDR_otc | 05:54 | PUT | 63.0% | 87.0% | 100 | 0.0047 ✓ |
| 27 | USDIDR_otc | 21:11 | PUT | 63.0% | 87.0% | 100 | 0.0047 ✓ |
| 28 | USDINR_otc | 03:12 | PUT | 63.0% | 87.0% | 100 | 0.0047 ✓ |
| 29 | USDMXN_otc | 19:27 | CALL | 63.0% | 87.0% | 100 | 0.0047 ✓ |
| 30 | USDPHP_otc | 03:51 | CALL | 63.0% | 87.0% | 100 | 0.0047 ✓ |
| 31 | USDZAR_otc | 21:49 | PUT | 63.0% | 87.0% | 100 | 0.0047 ✓ |
| 32 | BRLUSD_otc | 04:05 | PUT | 62.0% | 87.0% | 100 | 0.0082 ✓ |
| 33 | BRLUSD_otc | 16:14 | PUT | 62.0% | 87.0% | 100 | 0.0082 ✓ |
| 34 | USDARS_otc | 23:28 | PUT | 62.0% | 87.0% | 100 | 0.0082 ✓ |
| 35 | USDDZD_otc | 07:51 | PUT | 62.0% | 87.0% | 100 | 0.0082 ✓ |
| 36 | BRLUSD_otc | 10:11 | CALL | 61.0% | 87.0% | 100 | 0.0139 ✓ |
| 37 | USDARS_otc | 03:34 | PUT | 61.0% | 87.0% | 100 | 0.0139 ✓ |
| 38 | USDBDT_otc | 20:42 | PUT | 61.0% | 87.0% | 100 | 0.0139 ✓ |
| 39 | USDEGP_otc | 19:25 | PUT | 61.0% | 87.0% | 100 | 0.0139 ✓ |
| 40 | USDINR_otc | 20:15 | CALL | 61.0% | 87.0% | 100 | 0.0139 ✓ |
| 41 | USDARS_otc | 12:39 | CALL | 60.0% | 87.0% | 100 | 0.0228 ✓ |
| 42 | USDBDT_otc | 09:57 | PUT | 60.0% | 87.0% | 100 | 0.0228 ✓ |
| 43 | USDCOP_otc | 23:00 | PUT | 60.0% | 87.0% | 100 | 0.0228 ✓ |
| 44 | USDINR_otc | 12:22 | PUT | 60.0% | 87.0% | 100 | 0.0228 ✓ |
| 45 | USDBDT_otc | 00:22 | PUT | 68.0% | 86.0% | 100 | 0.0002 ✓ |
| 46 | BRLUSD_otc | 02:04 | CALL | 66.0% | 86.0% | 100 | 0.0007 ✓ |
| 47 | USDARS_otc | 17:55 | CALL | 66.0% | 86.0% | 100 | 0.0007 ✓ |
| 48 | USDDZD_otc | 18:23 | PUT | 66.0% | 86.0% | 100 | 0.0007 ✓ |
| 49 | USDARS_otc | 16:37 | PUT | 65.0% | 86.0% | 100 | 0.0013 ✓ |
| 50 | USDARS_otc | 19:28 | PUT | 65.0% | 86.0% | 100 | 0.0013 ✓ |
| 51 | USDZAR_otc | 19:04 | PUT | 65.0% | 86.0% | 100 | 0.0013 ✓ |
| 52 | USDEGP_otc | 00:16 | PUT | 64.0% | 86.0% | 100 | 0.0026 ✓ |
| 53 | USDEGP_otc | 19:26 | PUT | 63.0% | 86.0% | 100 | 0.0047 ✓ |
| 54 | USDZAR_otc | 02:31 | CALL | 63.0% | 86.0% | 100 | 0.0047 ✓ |
| 55 | USDBDT_otc | 23:14 | PUT | 62.0% | 86.0% | 100 | 0.0082 ✓ |
| 56 | USDIDR_otc | 02:00 | PUT | 62.0% | 86.0% | 100 | 0.0082 ✓ |
| 57 | USDPKR_otc | 11:47 | PUT | 62.0% | 86.0% | 100 | 0.0082 ✓ |
| 58 | USDZAR_otc | 16:01 | CALL | 62.0% | 86.0% | 100 | 0.0082 ✓ |
| 59 | USDBDT_otc | 15:11 | PUT | 61.0% | 86.0% | 100 | 0.0139 ✓ |
| 60 | USDBDT_otc | 18:10 | PUT | 61.0% | 86.0% | 100 | 0.0139 ✓ |
| 61 | USDCOP_otc | 12:47 | PUT | 61.0% | 86.0% | 100 | 0.0139 ✓ |
| 62 | USDEGP_otc | 18:35 | PUT | 61.0% | 86.0% | 100 | 0.0139 ✓ |
| 63 | USDNGN_otc | 17:46 | PUT | 61.0% | 86.0% | 100 | 0.0139 ✓ |
| 64 | USDNGN_otc | 21:40 | PUT | 61.0% | 86.0% | 100 | 0.0139 ✓ |
| 65 | USDPHP_otc | 01:44 | PUT | 61.0% | 86.0% | 100 | 0.0139 ✓ |
| 66 | USDPKR_otc | 06:28 | PUT | 61.0% | 86.0% | 100 | 0.0139 ✓ |
| 67 | BRLUSD_otc | 03:45 | PUT | 60.0% | 86.0% | 100 | 0.0228 ✓ |
| 68 | BRLUSD_otc | 09:54 | PUT | 60.0% | 86.0% | 100 | 0.0228 ✓ |
| 69 | USDIDR_otc | 23:17 | PUT | 60.0% | 86.0% | 100 | 0.0228 ✓ |
| 70 | USDINR_otc | 02:18 | CALL | 60.0% | 86.0% | 100 | 0.0228 ✓ |
| 71 | USDINR_otc | 11:49 | PUT | 60.0% | 86.0% | 100 | 0.0228 ✓ |
| 72 | USDINR_otc | 22:24 | PUT | 60.0% | 86.0% | 100 | 0.0228 ✓ |
| 73 | USDNGN_otc | 10:21 | PUT | 60.0% | 86.0% | 100 | 0.0228 ✓ |
| 74 | USDPKR_otc | 09:28 | PUT | 60.0% | 86.0% | 100 | 0.0228 ✓ |
| 75 | BRLUSD_otc | 14:02 | PUT | 66.0% | 85.0% | 100 | 0.0007 ✓ |
| 76 | USDBDT_otc | 09:58 | PUT | 65.0% | 85.0% | 100 | 0.0013 ✓ |
| 77 | USDIDR_otc | 12:38 | PUT | 65.0% | 85.0% | 100 | 0.0013 ✓ |
| 78 | USDMXN_otc | 06:40 | PUT | 65.0% | 85.0% | 100 | 0.0013 ✓ |
| 79 | USDNGN_otc | 15:57 | PUT | 65.0% | 85.0% | 100 | 0.0013 ✓ |
| 80 | USDPHP_otc | 19:08 | CALL | 65.0% | 85.0% | 100 | 0.0013 ✓ |
| 81 | USDARS_otc | 14:21 | PUT | 64.0% | 85.0% | 100 | 0.0026 ✓ |
| 82 | USDBDT_otc | 23:43 | PUT | 64.0% | 85.0% | 100 | 0.0026 ✓ |
| 83 | USDINR_otc | 00:20 | PUT | 64.0% | 85.0% | 100 | 0.0026 ✓ |
| 84 | USDNGN_otc | 21:08 | PUT | 64.0% | 85.0% | 100 | 0.0026 ✓ |
| 85 | USDPKR_otc | 13:09 | PUT | 64.0% | 85.0% | 100 | 0.0026 ✓ |
| 86 | USDEGP_otc | 12:42 | CALL | 63.0% | 85.0% | 100 | 0.0047 ✓ |
| 87 | USDEGP_otc | 23:05 | PUT | 63.0% | 85.0% | 100 | 0.0047 ✓ |
| 88 | USDINR_otc | 08:14 | PUT | 63.0% | 85.0% | 100 | 0.0047 ✓ |
| 89 | USDMXN_otc | 11:57 | CALL | 63.0% | 85.0% | 100 | 0.0047 ✓ |
| 90 | USDNGN_otc | 06:47 | PUT | 63.0% | 85.0% | 100 | 0.0047 ✓ |
| 91 | USDNGN_otc | 16:53 | PUT | 63.0% | 85.0% | 100 | 0.0047 ✓ |
| 92 | USDPHP_otc | 09:11 | PUT | 63.0% | 85.0% | 100 | 0.0047 ✓ |
| 93 | USDPHP_otc | 20:01 | PUT | 63.0% | 85.0% | 100 | 0.0047 ✓ |
| 94 | USDZAR_otc | 07:22 | PUT | 63.0% | 85.0% | 100 | 0.0047 ✓ |
| 95 | BRLUSD_otc | 06:50 | PUT | 62.0% | 85.0% | 100 | 0.0082 ✓ |
| 96 | USDBDT_otc | 17:09 | PUT | 62.0% | 85.0% | 100 | 0.0082 ✓ |
| 97 | USDEGP_otc | 14:20 | PUT | 62.0% | 85.0% | 100 | 0.0082 ✓ |
| 98 | USDEGP_otc | 17:00 | CALL | 62.0% | 85.0% | 100 | 0.0082 ✓ |
| 99 | USDNGN_otc | 02:05 | PUT | 62.0% | 85.0% | 100 | 0.0082 ✓ |
| 100 | USDNGN_otc | 02:56 | PUT | 62.0% | 85.0% | 100 | 0.0082 ✓ |

---

## ⏰ 3-Minute Cycle Schedule (24-hour rotation)

Each row is one 3-minute slot. Pick the signal at that time.

| # | Time (UTC) | Asset | Direction | L1 % | Combined % | Samples |
|---|-----------|-------|-----------|------|------------|---------|
| 1 | 00:04 | USDARS_otc | CALL | 60.0% | 89.0% | 100 |
| 2 | 00:08 | USDDZD_otc | CALL | 60.0% | 85.0% | 100 |
| 3 | 00:13 | USDARS_otc | PUT | 61.0% | 85.0% | 100 |
| 4 | 00:16 | USDEGP_otc | PUT | 64.0% | 86.0% | 100 |
| 5 | 00:22 | USDBDT_otc | PUT | 68.0% | 86.0% | 100 |
| 6 | 00:25 | USDEGP_otc | PUT | 62.0% | 84.0% | 100 |
| 7 | 00:32 | BRLUSD_otc | PUT | 60.0% | 84.0% | 100 |
| 8 | 00:37 | USDNGN_otc | PUT | 61.0% | 81.0% | 100 |
| 9 | 00:40 | USDIDR_otc | PUT | 63.0% | 83.0% | 100 |
| 10 | 00:48 | USDARS_otc | PUT | 60.0% | 81.0% | 100 |
| 11 | 00:54 | USDINR_otc | CALL | 60.0% | 82.0% | 100 |
| 12 | 00:57 | USDDZD_otc | CALL | 60.0% | 82.0% | 100 |
| 13 | 01:00 | BRLUSD_otc | PUT | 62.0% | 88.0% | 100 |
| 14 | 01:13 | USDEGP_otc | CALL | 61.0% | 82.0% | 100 |
| 15 | 01:16 | USDIDR_otc | CALL | 60.0% | 81.0% | 100 |
| 16 | 01:24 | USDCOP_otc | CALL | 61.0% | 84.0% | 100 |
| 17 | 01:27 | BRLUSD_otc | PUT | 62.0% | 82.0% | 100 |
| 18 | 01:30 | USDMXN_otc | PUT | 62.0% | 84.0% | 100 |
| 19 | 01:37 | USDIDR_otc | CALL | 61.0% | 78.0% | 100 |
| 20 | 01:44 | USDPHP_otc | PUT | 61.0% | 86.0% | 100 |
| 21 | 01:47 | USDDZD_otc | PUT | 62.0% | 80.0% | 100 |
| 22 | 01:50 | USDPHP_otc | PUT | 61.0% | 82.0% | 100 |
| 23 | 01:59 | USDZAR_otc | CALL | 63.0% | 81.0% | 100 |
| 24 | 02:04 | BRLUSD_otc | CALL | 66.0% | 86.0% | 100 |
| 25 | 02:05 | USDNGN_otc | PUT | 62.0% | 85.0% | 100 |
| 26 | 02:14 | USDZAR_otc | CALL | 65.0% | 87.0% | 100 |
| 27 | 02:18 | USDINR_otc | CALL | 60.0% | 86.0% | 100 |
| 28 | 02:24 | BRLUSD_otc | PUT | 60.0% | 81.0% | 100 |
| 29 | 02:26 | USDCOP_otc | PUT | 61.0% | 80.0% | 100 |
| 30 | 02:31 | USDZAR_otc | CALL | 63.0% | 86.0% | 100 |
| 31 | 02:37 | USDINR_otc | CALL | 60.0% | 83.0% | 100 |
| 32 | 02:44 | BRLUSD_otc | PUT | 60.0% | 82.0% | 100 |
| 33 | 02:48 | USDDZD_otc | CALL | 60.0% | 84.0% | 100 |
| 34 | 02:54 | USDINR_otc | CALL | 62.0% | 82.0% | 100 |
| 35 | 02:56 | USDEGP_otc | PUT | 65.0% | 87.0% | 100 |
| 36 | 03:01 | USDPHP_otc | CALL | 60.0% | 79.0% | 100 |
| 37 | 03:08 | USDEGP_otc | PUT | 61.0% | 82.0% | 100 |
| 38 | 03:12 | USDINR_otc | PUT | 63.0% | 87.0% | 100 |
| 39 | 03:19 | USDPKR_otc | PUT | 62.0% | 85.0% | 100 |
| 40 | 03:23 | BRLUSD_otc | PUT | 60.0% | 83.0% | 100 |
| 41 | 03:29 | USDCOP_otc | PUT | 60.0% | 85.0% | 100 |
| 42 | 03:34 | USDARS_otc | PUT | 61.0% | 87.0% | 100 |
| 43 | 03:36 | USDPHP_otc | CALL | 60.0% | 81.0% | 100 |
| 44 | 03:43 | USDDZD_otc | PUT | 60.0% | 82.0% | 100 |
| 45 | 03:45 | BRLUSD_otc | PUT | 60.0% | 86.0% | 100 |
| 46 | 03:51 | USDPHP_otc | CALL | 63.0% | 87.0% | 100 |
| 47 | 03:57 | USDNGN_otc | PUT | 62.0% | 83.0% | 100 |
| 48 | 04:03 | BRLUSD_otc | CALL | 61.0% | 82.0% | 100 |
| 49 | 04:06 | USDZAR_otc | CALL | 60.0% | 82.0% | 100 |
| 50 | 04:14 | USDEGP_otc | PUT | 60.0% | 85.0% | 100 |
| 51 | 04:19 | USDDZD_otc | PUT | 60.0% | 85.0% | 100 |
| 52 | 04:21 | USDEGP_otc | CALL | 61.0% | 85.0% | 100 |
| 53 | 04:27 | USDCOP_otc | PUT | 61.0% | 82.0% | 100 |
| 54 | 04:30 | USDINR_otc | PUT | 62.0% | 82.0% | 100 |
| 55 | 04:36 | BRLUSD_otc | PUT | 67.0% | 84.0% | 100 |
| 56 | 04:41 | USDNGN_otc | CALL | 60.0% | 76.0% | 100 |
| 57 | 04:45 | USDBDT_otc | PUT | 60.0% | 84.0% | 100 |
| 58 | 04:51 | USDPHP_otc | PUT | 64.0% | 84.0% | 100 |
| 59 | 04:58 | USDARS_otc | PUT | 60.0% | 83.0% | 100 |
| 60 | 05:04 | USDNGN_otc | PUT | 60.0% | 85.0% | 100 |
| 61 | 05:05 | USDBDT_otc | PUT | 65.0% | 87.0% | 100 |
| 62 | 05:11 | USDARS_otc | PUT | 60.0% | 81.0% | 100 |
| 63 | 05:18 | USDMXN_otc | PUT | 62.0% | 82.0% | 100 |
| 64 | 05:22 | BRLUSD_otc | PUT | 60.0% | 85.0% | 100 |
| 65 | 05:26 | USDINR_otc | PUT | 62.0% | 84.0% | 100 |
| 66 | 05:31 | USDPHP_otc | PUT | 61.0% | 79.0% | 100 |
| 67 | 05:37 | USDEGP_otc | CALL | 61.0% | 83.0% | 100 |
| 68 | 05:40 | USDNGN_otc | PUT | 60.0% | 81.0% | 100 |
| 69 | 05:49 | USDEGP_otc | PUT | 61.0% | 84.0% | 100 |
| 70 | 05:54 | USDIDR_otc | PUT | 63.0% | 87.0% | 100 |
| 71 | 05:59 | USDZAR_otc | PUT | 61.0% | 81.0% | 100 |
| 72 | 06:03 | USDEGP_otc | PUT | 66.0% | 87.0% | 100 |
| 73 | 06:07 | USDIDR_otc | PUT | 64.0% | 83.0% | 100 |
| 74 | 06:14 | USDARS_otc | CALL | 61.0% | 81.0% | 100 |
| 75 | 06:16 | USDEGP_otc | PUT | 60.0% | 83.0% | 100 |
| 76 | 06:23 | USDBDT_otc | PUT | 61.0% | 78.0% | 100 |
| 77 | 06:28 | USDPKR_otc | PUT | 61.0% | 86.0% | 100 |
| 78 | 06:34 | USDDZD_otc | PUT | 63.0% | 83.0% | 100 |
| 79 | 06:35 | USDNGN_otc | PUT | 60.0% | 82.0% | 100 |
| 80 | 06:40 | USDMXN_otc | PUT | 65.0% | 85.0% | 100 |
| 81 | 06:47 | USDNGN_otc | PUT | 63.0% | 85.0% | 100 |
| 82 | 06:50 | BRLUSD_otc | PUT | 62.0% | 85.0% | 100 |
| 83 | 06:57 | USDMXN_otc | CALL | 61.0% | 81.0% | 100 |
| 84 | 07:04 | USDCOP_otc | PUT | 65.0% | 82.0% | 100 |
| 85 | 07:06 | USDPKR_otc | CALL | 60.0% | 82.0% | 100 |
| 86 | 07:12 | USDARS_otc | CALL | 60.0% | 82.0% | 100 |
| 87 | 07:15 | USDEGP_otc | CALL | 62.0% | 82.0% | 100 |
| 88 | 07:20 | USDPHP_otc | PUT | 61.0% | 88.0% | 100 |
| 89 | 07:32 | USDNGN_otc | PUT | 69.0% | 83.0% | 100 |
| 90 | 07:35 | USDZAR_otc | CALL | 61.0% | 81.0% | 100 |
| 91 | 07:40 | USDPKR_otc | PUT | 63.0% | 84.0% | 100 |
| 92 | 07:46 | USDINR_otc | PUT | 61.0% | 84.0% | 100 |
| 93 | 07:51 | USDDZD_otc | PUT | 62.0% | 87.0% | 100 |
| 94 | 07:59 | USDINR_otc | CALL | 60.0% | 80.0% | 100 |
| 95 | 08:03 | USDMXN_otc | PUT | 62.0% | 84.0% | 100 |
| 96 | 08:06 | USDNGN_otc | CALL | 65.0% | 89.0% | 100 |
| 97 | 08:14 | USDINR_otc | PUT | 63.0% | 85.0% | 100 |
| 98 | 08:17 | USDPHP_otc | CALL | 61.0% | 85.0% | 100 |
| 99 | 08:22 | BRLUSD_otc | PUT | 60.0% | 81.0% | 100 |
| 100 | 08:27 | USDEGP_otc | PUT | 64.0% | 83.0% | 100 |
| 101 | 08:33 | USDPHP_otc | PUT | 60.0% | 81.0% | 100 |
| 102 | 08:35 | USDCOP_otc | PUT | 64.0% | 88.0% | 100 |
| 103 | 08:40 | USDINR_otc | CALL | 61.0% | 84.0% | 100 |
| 104 | 08:53 | USDBDT_otc | PUT | 61.0% | 83.0% | 100 |
| 105 | 08:55 | BRLUSD_otc | PUT | 63.0% | 84.0% | 100 |
| 106 | 09:01 | USDDZD_otc | CALL | 62.0% | 83.0% | 100 |
| 107 | 09:06 | USDPHP_otc | PUT | 63.0% | 82.0% | 100 |
| 108 | 09:12 | USDNGN_otc | PUT | 60.0% | 82.0% | 100 |
| 109 | 09:18 | USDCOP_otc | CALL | 61.0% | 83.0% | 100 |
| 110 | 09:23 | USDINR_otc | PUT | 62.0% | 84.0% | 100 |
| 111 | 09:28 | USDPKR_otc | PUT | 60.0% | 86.0% | 100 |
| 112 | 09:34 | USDEGP_otc | PUT | 62.0% | 80.0% | 100 |
| 113 | 09:38 | USDPKR_otc | CALL | 62.0% | 83.0% | 100 |
| 114 | 09:42 | USDNGN_otc | PUT | 61.0% | 77.0% | 100 |
| 115 | 09:45 | BRLUSD_otc | PUT | 61.0% | 82.0% | 100 |
| 116 | 09:54 | USDARS_otc | PUT | 62.0% | 80.0% | 100 |
| 117 | 09:57 | USDBDT_otc | PUT | 60.0% | 87.0% | 100 |
| 118 | 10:02 | USDPKR_otc | CALL | 62.0% | 80.0% | 100 |
| 119 | 10:09 | USDIDR_otc | PUT | 64.0% | 87.0% | 100 |
| 120 | 10:13 | USDBDT_otc | PUT | 64.0% | 88.0% | 100 |
| 121 | 10:17 | USDMXN_otc | PUT | 62.0% | 82.0% | 100 |
| 122 | 10:21 | USDNGN_otc | PUT | 60.0% | 86.0% | 100 |
| 123 | 10:29 | USDIDR_otc | CALL | 62.0% | 82.0% | 100 |
| 124 | 10:34 | USDMXN_otc | PUT | 63.0% | 82.0% | 100 |
| 125 | 10:36 | USDDZD_otc | PUT | 60.0% | 82.0% | 100 |
| 126 | 10:43 | USDARS_otc | CALL | 63.0% | 83.0% | 100 |
| 127 | 10:45 | USDCOP_otc | PUT | 60.0% | 80.0% | 100 |
| 128 | 10:53 | USDINR_otc | CALL | 63.0% | 80.0% | 100 |
| 129 | 10:57 | USDPKR_otc | PUT | 67.0% | 83.0% | 100 |
| 130 | 11:00 | USDIDR_otc | CALL | 64.0% | 81.0% | 100 |
| 131 | 11:06 | USDZAR_otc | PUT | 61.0% | 85.0% | 100 |
| 132 | 11:11 | USDPHP_otc | CALL | 60.0% | 83.0% | 100 |
| 133 | 11:15 | USDMXN_otc | PUT | 61.0% | 78.0% | 100 |
| 134 | 11:21 | USDPHP_otc | PUT | 62.0% | 81.0% | 100 |
| 135 | 11:27 | USDARS_otc | PUT | 60.0% | 85.0% | 100 |
| 136 | 11:30 | USDPKR_otc | PUT | 61.0% | 80.0% | 100 |
| 137 | 11:36 | USDNGN_otc | PUT | 60.0% | 85.0% | 100 |
| 138 | 11:41 | USDCOP_otc | PUT | 63.0% | 89.0% | 100 |
| 139 | 11:47 | USDPKR_otc | PUT | 62.0% | 86.0% | 100 |
| 140 | 11:52 | USDMXN_otc | CALL | 64.0% | 84.0% | 100 |
| 141 | 11:57 | USDCOP_otc | PUT | 61.0% | 82.0% | 100 |
| 142 | 12:04 | USDBDT_otc | PUT | 61.0% | 81.0% | 100 |
| 143 | 12:07 | BRLUSD_otc | CALL | 62.0% | 84.0% | 100 |
| 144 | 12:12 | USDDZD_otc | PUT | 61.0% | 83.0% | 100 |
| 145 | 12:15 | USDMXN_otc | CALL | 62.0% | 84.0% | 100 |
| 146 | 12:21 | USDEGP_otc | PUT | 62.0% | 88.0% | 100 |
| 147 | 12:25 | USDINR_otc | PUT | 69.0% | 88.0% | 100 |
| 148 | 12:33 | USDZAR_otc | PUT | 61.0% | 84.0% | 100 |
| 149 | 12:39 | USDARS_otc | CALL | 60.0% | 87.0% | 100 |
| 150 | 12:42 | USDEGP_otc | CALL | 63.0% | 85.0% | 100 |
| 151 | 12:47 | USDCOP_otc | PUT | 61.0% | 86.0% | 100 |
| 152 | 12:54 | BRLUSD_otc | PUT | 65.0% | 83.0% | 100 |
| 153 | 12:57 | USDARS_otc | PUT | 60.0% | 83.0% | 100 |
| 154 | 13:04 | USDPHP_otc | PUT | 60.0% | 88.0% | 100 |
| 155 | 13:09 | USDPKR_otc | PUT | 64.0% | 85.0% | 100 |
| 156 | 13:10 | USDCOP_otc | CALL | 64.0% | 89.0% | 100 |
| 157 | 13:16 | USDIDR_otc | CALL | 61.0% | 85.0% | 100 |
| 158 | 13:21 | USDPHP_otc | CALL | 60.0% | 82.0% | 100 |
| 159 | 13:28 | USDPKR_otc | PUT | 60.0% | 84.0% | 100 |
| 160 | 13:34 | USDNGN_otc | PUT | 60.0% | 78.0% | 100 |
| 161 | 13:36 | USDZAR_otc | PUT | 60.0% | 83.0% | 100 |
| 162 | 13:42 | USDARS_otc | CALL | 61.0% | 81.0% | 100 |
| 163 | 13:49 | USDBDT_otc | PUT | 60.0% | 83.0% | 100 |
| 164 | 13:53 | USDINR_otc | PUT | 62.0% | 82.0% | 100 |
| 165 | 13:57 | USDNGN_otc | CALL | 62.0% | 85.0% | 100 |
| 166 | 14:02 | BRLUSD_otc | PUT | 66.0% | 85.0% | 100 |
| 167 | 14:09 | USDINR_otc | PUT | 60.0% | 79.0% | 100 |
| 168 | 14:13 | USDIDR_otc | CALL | 60.0% | 85.0% | 100 |
| 169 | 14:19 | USDZAR_otc | CALL | 62.0% | 83.0% | 100 |
| 170 | 14:21 | USDARS_otc | PUT | 64.0% | 85.0% | 100 |
| 171 | 14:25 | USDBDT_otc | CALL | 60.0% | 82.0% | 100 |
| 172 | 14:31 | USDEGP_otc | CALL | 64.0% | 83.0% | 100 |
| 173 | 14:35 | USDBDT_otc | PUT | 69.0% | 83.0% | 100 |
| 174 | 14:44 | USDNGN_otc | PUT | 66.0% | 81.0% | 100 |
| 175 | 14:49 | USDMXN_otc | PUT | 63.0% | 84.0% | 100 |
| 176 | 14:51 | USDZAR_otc | CALL | 63.0% | 81.0% | 100 |
| 177 | 14:58 | BRLUSD_otc | PUT | 60.0% | 80.0% | 100 |
| 178 | 15:01 | USDARS_otc | CALL | 60.0% | 85.0% | 100 |
| 179 | 15:06 | USDZAR_otc | PUT | 60.0% | 84.0% | 100 |
| 180 | 15:11 | USDBDT_otc | PUT | 61.0% | 86.0% | 100 |
| 181 | 15:15 | USDINR_otc | PUT | 60.0% | 81.0% | 100 |
| 182 | 15:22 | USDCOP_otc | PUT | 61.0% | 81.0% | 100 |
| 183 | 15:25 | USDEGP_otc | CALL | 60.0% | 80.0% | 100 |
| 184 | 15:31 | USDNGN_otc | PUT | 61.0% | 82.0% | 100 |
| 185 | 15:36 | USDARS_otc | CALL | 62.0% | 82.0% | 100 |
| 186 | 15:43 | USDDZD_otc | PUT | 61.0% | 81.0% | 100 |
| 187 | 15:46 | USDBDT_otc | PUT | 61.0% | 76.0% | 100 |
| 188 | 15:54 | USDCOP_otc | PUT | 65.0% | 84.0% | 100 |
| 189 | 15:57 | USDNGN_otc | PUT | 65.0% | 85.0% | 100 |
| 190 | 16:01 | USDZAR_otc | CALL | 62.0% | 86.0% | 100 |
| 191 | 16:06 | BRLUSD_otc | PUT | 63.0% | 87.0% | 100 |
| 192 | 16:13 | USDZAR_otc | PUT | 60.0% | 81.0% | 100 |
| 193 | 16:15 | USDBDT_otc | CALL | 61.0% | 83.0% | 100 |
| 194 | 16:24 | USDCOP_otc | CALL | 62.0% | 82.0% | 100 |
| 195 | 16:29 | USDINR_otc | PUT | 65.0% | 82.0% | 100 |
| 196 | 16:30 | USDIDR_otc | PUT | 60.0% | 75.0% | 100 |
| 197 | 16:37 | USDARS_otc | PUT | 65.0% | 86.0% | 100 |
| 198 | 16:43 | BRLUSD_otc | CALL | 60.0% | 80.0% | 100 |
| 199 | 16:47 | USDEGP_otc | PUT | 60.0% | 85.0% | 100 |
| 200 | 16:53 | USDNGN_otc | PUT | 63.0% | 85.0% | 100 |

---

## 📊 Per-Asset Summary

| Asset | Total Minutes | Avg L1 % | Avg Combined % | Best Combined % |
|-------|---------------|----------|----------------|------------------|
| USDNGN_otc | 107 | 61.2% | 80.6% | 89.0% |
| USDCOP_otc | 99 | 61.3% | 80.2% | 89.0% |
| BRLUSD_otc | 99 | 61.3% | 81.3% | 88.0% |
| USDEGP_otc | 98 | 61.2% | 81.1% | 88.0% |
| USDPHP_otc | 85 | 61.6% | 80.5% | 88.0% |
| USDARS_otc | 84 | 61.3% | 80.8% | 89.0% |
| USDMXN_otc | 83 | 61.4% | 80.1% | 89.0% |
| USDBDT_otc | 82 | 61.7% | 81.1% | 88.0% |
| USDINR_otc | 80 | 61.2% | 81.1% | 88.0% |
| USDIDR_otc | 79 | 61.1% | 79.9% | 87.0% |
| USDPKR_otc | 75 | 61.2% | 80.9% | 88.0% |
| USDZAR_otc | 75 | 61.7% | 80.1% | 87.0% |
| USDDZD_otc | 72 | 61.6% | 80.7% | 87.0% |

---

## 📈 Schedule Statistics

- Total signals per 24h cycle: **284**
- Average combined win rate: **83.4%**
- Min combined: 75.0%
- Max combined: 89.0%
- Unique assets in schedule: 13
- Signal frequency: every 5 minutes

