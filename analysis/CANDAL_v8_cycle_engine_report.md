# CANDAL v8 — Cycle Signal Engine Report

**Generated:** 2026-09-29 22:38:27

**Assets analyzed:** 17
**Total minutes passing filter:** 337
**Schedule signals (every 3 min):** 251

## Methodology

Inspired by analysis of competitor bot (88% win rate, 3-min cycle):

1. For each asset, scan every minute-of-day on historical data
2. For each minute, compute:
   - L1 win rate (predict next bar direction)
   - Combined win rate (L1 + martingale if L1 loses)
3. Filter: L1 ≥ 60%, p < 0.05, samples ≥ 80
4. Build 3-minute cycle: every 3 minutes, emit 1 signal
   (best available minute, rotating assets to avoid same-asset repeat)

---

## 🎯 Top 100 Minute Patterns (by combined win rate)

| # | Asset | Time (UTC) | Direction | L1 % | Combined % | Samples | p-value |
|---|-------|-----------|-----------|------|------------|---------|---------|
| 1 | USDARS_otc | 00:04 | CALL | 60.0% | 89.0% | 100 | 0.0228 ✓ |
| 2 | BRLUSD_otc | 01:00 | PUT | 62.0% | 88.0% | 100 | 0.0082 ✓ |
| 3 | USDARS_otc | 08:09 | PUT | 62.0% | 88.0% | 100 | 0.0082 ✓ |
| 4 | USDARS_otc | 19:51 | CALL | 63.0% | 88.0% | 100 | 0.0047 ✓ |
| 5 | USDBDT_otc | 10:13 | PUT | 64.0% | 88.0% | 100 | 0.0026 ✓ |
| 6 | BRLUSD_otc | 04:05 | PUT | 62.0% | 87.0% | 100 | 0.0082 ✓ |
| 7 | BRLUSD_otc | 08:07 | PUT | 63.0% | 87.0% | 100 | 0.0047 ✓ |
| 8 | BRLUSD_otc | 10:11 | CALL | 61.0% | 87.0% | 100 | 0.0139 ✓ |
| 9 | BRLUSD_otc | 16:06 | PUT | 63.0% | 87.0% | 100 | 0.0047 ✓ |
| 10 | BRLUSD_otc | 16:14 | PUT | 62.0% | 87.0% | 100 | 0.0082 ✓ |
| 11 | USDARS_otc | 03:34 | PUT | 61.0% | 87.0% | 100 | 0.0139 ✓ |
| 12 | USDARS_otc | 12:39 | CALL | 60.0% | 87.0% | 100 | 0.0228 ✓ |
| 13 | USDARS_otc | 23:28 | PUT | 62.0% | 87.0% | 100 | 0.0082 ✓ |
| 14 | USDBDT_otc | 05:05 | PUT | 65.0% | 87.0% | 100 | 0.0013 ✓ |
| 15 | USDBDT_otc | 09:57 | PUT | 60.0% | 87.0% | 100 | 0.0228 ✓ |
| 16 | USDBDT_otc | 20:42 | PUT | 61.0% | 87.0% | 100 | 0.0139 ✓ |
| 17 | USDDZD_otc | 07:51 | PUT | 62.0% | 87.0% | 100 | 0.0082 ✓ |
| 18 | BRLUSD_otc | 02:04 | CALL | 66.0% | 86.0% | 100 | 0.0007 ✓ |
| 19 | BRLUSD_otc | 03:45 | PUT | 60.0% | 86.0% | 100 | 0.0228 ✓ |
| 20 | BRLUSD_otc | 09:54 | PUT | 60.0% | 86.0% | 100 | 0.0228 ✓ |
| 21 | USDARS_otc | 16:37 | PUT | 65.0% | 86.0% | 100 | 0.0013 ✓ |
| 22 | USDARS_otc | 17:55 | CALL | 66.0% | 86.0% | 100 | 0.0007 ✓ |
| 23 | USDARS_otc | 19:28 | PUT | 65.0% | 86.0% | 100 | 0.0013 ✓ |
| 24 | USDBDT_otc | 00:22 | PUT | 68.0% | 86.0% | 100 | 0.0002 ✓ |
| 25 | USDBDT_otc | 15:11 | PUT | 61.0% | 86.0% | 100 | 0.0139 ✓ |
| 26 | USDBDT_otc | 18:10 | PUT | 61.0% | 86.0% | 100 | 0.0139 ✓ |
| 27 | USDBDT_otc | 23:14 | PUT | 62.0% | 86.0% | 100 | 0.0082 ✓ |
| 28 | USDDZD_otc | 18:23 | PUT | 66.0% | 86.0% | 100 | 0.0007 ✓ |
| 29 | BRLUSD_otc | 05:22 | PUT | 60.0% | 85.0% | 100 | 0.0228 ✓ |
| 30 | BRLUSD_otc | 06:50 | PUT | 62.0% | 85.0% | 100 | 0.0082 ✓ |
| 31 | BRLUSD_otc | 14:02 | PUT | 66.0% | 85.0% | 100 | 0.0007 ✓ |
| 32 | BRLUSD_otc | 21:26 | PUT | 60.0% | 85.0% | 100 | 0.0228 ✓ |
| 33 | USDARS_otc | 00:13 | PUT | 61.0% | 85.0% | 100 | 0.0139 ✓ |
| 34 | USDARS_otc | 03:35 | PUT | 60.0% | 85.0% | 100 | 0.0228 ✓ |
| 35 | USDARS_otc | 11:27 | PUT | 60.0% | 85.0% | 100 | 0.0228 ✓ |
| 36 | USDARS_otc | 14:21 | PUT | 64.0% | 85.0% | 100 | 0.0026 ✓ |
| 37 | USDARS_otc | 15:01 | CALL | 60.0% | 85.0% | 100 | 0.0228 ✓ |
| 38 | USDARS_otc | 17:41 | PUT | 60.0% | 85.0% | 100 | 0.0228 ✓ |
| 39 | USDBDT_otc | 09:58 | PUT | 65.0% | 85.0% | 100 | 0.0013 ✓ |
| 40 | USDBDT_otc | 12:22 | PUT | 61.0% | 85.0% | 100 | 0.0139 ✓ |
| 41 | USDBDT_otc | 17:09 | PUT | 62.0% | 85.0% | 100 | 0.0082 ✓ |
| 42 | USDBDT_otc | 23:43 | PUT | 64.0% | 85.0% | 100 | 0.0026 ✓ |
| 43 | USDDZD_otc | 00:08 | CALL | 60.0% | 85.0% | 100 | 0.0228 ✓ |
| 44 | USDDZD_otc | 04:19 | PUT | 60.0% | 85.0% | 100 | 0.0228 ✓ |
| 45 | USDDZD_otc | 18:59 | PUT | 61.0% | 85.0% | 100 | 0.0139 ✓ |
| 46 | USDDZD_otc | 22:12 | PUT | 60.0% | 85.0% | 100 | 0.0228 ✓ |
| 47 | BRLUSD_otc | 00:32 | PUT | 60.0% | 84.0% | 100 | 0.0228 ✓ |
| 48 | BRLUSD_otc | 04:36 | PUT | 67.0% | 84.0% | 100 | 0.0003 ✓ |
| 49 | BRLUSD_otc | 06:46 | PUT | 61.0% | 84.0% | 100 | 0.0139 ✓ |
| 50 | BRLUSD_otc | 08:55 | PUT | 63.0% | 84.0% | 100 | 0.0047 ✓ |
| 51 | BRLUSD_otc | 12:07 | CALL | 62.0% | 84.0% | 100 | 0.0082 ✓ |
| 52 | BRLUSD_otc | 16:56 | PUT | 61.0% | 84.0% | 100 | 0.0139 ✓ |
| 53 | BRLUSD_otc | 21:24 | PUT | 63.0% | 84.0% | 100 | 0.0047 ✓ |
| 54 | USDARS_otc | 06:01 | CALL | 60.0% | 84.0% | 100 | 0.0228 ✓ |
| 55 | USDARS_otc | 17:30 | CALL | 62.0% | 84.0% | 100 | 0.0082 ✓ |
| 56 | USDARS_otc | 19:13 | PUT | 60.0% | 84.0% | 100 | 0.0228 ✓ |
| 57 | USDARS_otc | 19:27 | PUT | 63.0% | 84.0% | 100 | 0.0047 ✓ |
| 58 | USDBDT_otc | 03:17 | PUT | 60.0% | 84.0% | 100 | 0.0228 ✓ |
| 59 | USDBDT_otc | 04:45 | PUT | 60.0% | 84.0% | 100 | 0.0228 ✓ |
| 60 | USDBDT_otc | 09:27 | CALL | 64.0% | 84.0% | 100 | 0.0026 ✓ |
| 61 | USDBDT_otc | 17:42 | PUT | 61.0% | 84.0% | 100 | 0.0139 ✓ |
| 62 | USDBDT_otc | 23:16 | PUT | 60.0% | 84.0% | 100 | 0.0228 ✓ |
| 63 | USDDZD_otc | 02:48 | CALL | 60.0% | 84.0% | 100 | 0.0228 ✓ |
| 64 | USDDZD_otc | 13:11 | PUT | 61.0% | 84.0% | 100 | 0.0139 ✓ |
| 65 | USDDZD_otc | 15:11 | PUT | 64.0% | 84.0% | 100 | 0.0026 ✓ |
| 66 | USDDZD_otc | 16:48 | PUT | 62.0% | 84.0% | 100 | 0.0082 ✓ |
| 67 | USDDZD_otc | 17:03 | PUT | 61.0% | 84.0% | 100 | 0.0139 ✓ |
| 68 | USDDZD_otc | 17:41 | PUT | 63.0% | 84.0% | 100 | 0.0047 ✓ |
| 69 | USDDZD_otc | 18:19 | PUT | 60.0% | 84.0% | 100 | 0.0228 ✓ |
| 70 | USDDZD_otc | 23:50 | PUT | 64.0% | 84.0% | 100 | 0.0026 ✓ |
| 71 | BRLUSD_otc | 22:00 | PUT | 60.6% | 83.8% | 99 | 0.0174 ✓ |
| 72 | BRLUSD_otc | 02:30 | PUT | 63.0% | 83.0% | 100 | 0.0047 ✓ |
| 73 | BRLUSD_otc | 03:17 | CALL | 61.0% | 83.0% | 100 | 0.0139 ✓ |
| 74 | BRLUSD_otc | 03:23 | PUT | 60.0% | 83.0% | 100 | 0.0228 ✓ |
| 75 | BRLUSD_otc | 05:29 | PUT | 60.0% | 83.0% | 100 | 0.0228 ✓ |
| 76 | BRLUSD_otc | 06:41 | PUT | 65.0% | 83.0% | 100 | 0.0013 ✓ |
| 77 | BRLUSD_otc | 07:40 | CALL | 60.0% | 83.0% | 100 | 0.0228 ✓ |
| 78 | BRLUSD_otc | 08:11 | PUT | 61.0% | 83.0% | 100 | 0.0139 ✓ |
| 79 | BRLUSD_otc | 11:37 | PUT | 60.0% | 83.0% | 100 | 0.0228 ✓ |
| 80 | BRLUSD_otc | 12:54 | PUT | 65.0% | 83.0% | 100 | 0.0013 ✓ |
| 81 | BRLUSD_otc | 16:18 | PUT | 60.0% | 83.0% | 100 | 0.0228 ✓ |
| 82 | BRLUSD_otc | 16:59 | PUT | 61.0% | 83.0% | 100 | 0.0139 ✓ |
| 83 | BRLUSD_otc | 18:08 | PUT | 61.0% | 83.0% | 100 | 0.0139 ✓ |
| 84 | BRLUSD_otc | 20:42 | PUT | 62.0% | 83.0% | 100 | 0.0082 ✓ |
| 85 | BRLUSD_otc | 21:27 | PUT | 62.0% | 83.0% | 100 | 0.0082 ✓ |
| 86 | USDARS_otc | 02:45 | PUT | 61.0% | 83.0% | 100 | 0.0139 ✓ |
| 87 | USDARS_otc | 04:58 | PUT | 60.0% | 83.0% | 100 | 0.0228 ✓ |
| 88 | USDARS_otc | 07:21 | PUT | 62.0% | 83.0% | 100 | 0.0082 ✓ |
| 89 | USDARS_otc | 10:43 | CALL | 63.0% | 83.0% | 100 | 0.0047 ✓ |
| 90 | USDARS_otc | 12:57 | PUT | 60.0% | 83.0% | 100 | 0.0228 ✓ |
| 91 | USDARS_otc | 20:35 | PUT | 60.0% | 83.0% | 100 | 0.0228 ✓ |
| 92 | USDARS_otc | 20:49 | PUT | 60.0% | 83.0% | 100 | 0.0228 ✓ |
| 93 | USDARS_otc | 22:13 | PUT | 64.0% | 83.0% | 100 | 0.0026 ✓ |
| 94 | USDBDT_otc | 00:31 | CALL | 60.0% | 83.0% | 100 | 0.0228 ✓ |
| 95 | USDBDT_otc | 03:25 | PUT | 66.0% | 83.0% | 100 | 0.0007 ✓ |
| 96 | USDBDT_otc | 05:50 | CALL | 61.0% | 83.0% | 100 | 0.0139 ✓ |
| 97 | USDBDT_otc | 08:53 | PUT | 61.0% | 83.0% | 100 | 0.0139 ✓ |
| 98 | USDBDT_otc | 11:42 | PUT | 62.0% | 83.0% | 100 | 0.0082 ✓ |
| 99 | USDBDT_otc | 13:49 | PUT | 60.0% | 83.0% | 100 | 0.0228 ✓ |
| 100 | USDBDT_otc | 14:35 | PUT | 69.0% | 83.0% | 100 | 0.0001 ✓ |

---

## ⏰ 3-Minute Cycle Schedule (24-hour rotation)

Each row is one 3-minute slot. Pick the signal at that time.

| # | Time (UTC) | Asset | Direction | L1 % | Combined % | Samples |
|---|-----------|-------|-----------|------|------------|---------|
| 1 | 00:04 | USDARS_otc | CALL | 60.0% | 89.0% | 100 |
| 2 | 00:08 | USDDZD_otc | CALL | 60.0% | 85.0% | 100 |
| 3 | 00:13 | USDARS_otc | PUT | 61.0% | 85.0% | 100 |
| 4 | 00:17 | USDBDT_otc | PUT | 61.0% | 77.0% | 100 |
| 5 | 00:22 | USDBDT_otc | PUT | 68.0% | 86.0% | 100 |
| 6 | 00:25 | USDBDT_otc | CALL | 60.0% | 76.0% | 100 |
| 7 | 00:28 | USDARS_otc | PUT | 62.0% | 79.0% | 100 |
| 8 | 00:32 | BRLUSD_otc | PUT | 60.0% | 84.0% | 100 |
| 9 | 00:33 | BRLUSD_otc | PUT | 60.0% | 78.0% | 100 |
| 10 | 00:41 | USDDZD_otc | CALL | 61.0% | 81.0% | 100 |
| 11 | 00:48 | USDARS_otc | PUT | 60.0% | 81.0% | 100 |
| 12 | 00:57 | USDDZD_otc | CALL | 60.0% | 82.0% | 100 |
| 13 | 01:00 | BRLUSD_otc | PUT | 62.0% | 88.0% | 100 |
| 14 | 01:03 | USDARS_otc | CALL | 60.0% | 80.0% | 100 |
| 15 | 01:11 | USDBDT_otc | PUT | 61.0% | 79.0% | 100 |
| 16 | 01:23 | BRLUSD_otc | CALL | 60.0% | 78.0% | 100 |
| 17 | 01:26 | BRLUSD_otc | CALL | 61.0% | 77.0% | 100 |
| 18 | 01:28 | USDBDT_otc | PUT | 62.0% | 82.0% | 100 |
| 19 | 01:33 | USDDZD_otc | PUT | 61.0% | 81.0% | 100 |
| 20 | 01:47 | USDDZD_otc | PUT | 62.0% | 80.0% | 100 |
| 21 | 01:59 | USDDZD_otc | CALL | 61.0% | 74.0% | 100 |
| 22 | 02:04 | BRLUSD_otc | CALL | 66.0% | 86.0% | 100 |
| 23 | 02:11 | USDDZD_otc | PUT | 61.0% | 77.0% | 100 |
| 24 | 02:21 | USDARS_otc | CALL | 63.0% | 77.0% | 100 |
| 25 | 02:24 | BRLUSD_otc | PUT | 60.0% | 81.0% | 100 |
| 26 | 02:29 | USDDZD_otc | CALL | 60.0% | 76.0% | 100 |
| 27 | 02:30 | BRLUSD_otc | PUT | 63.0% | 83.0% | 100 |
| 28 | 02:36 | USDDZD_otc | PUT | 64.0% | 76.0% | 100 |
| 29 | 02:40 | USDDZD_otc | CALL | 61.0% | 79.0% | 100 |
| 30 | 02:44 | BRLUSD_otc | PUT | 60.0% | 82.0% | 100 |
| 31 | 02:45 | USDARS_otc | PUT | 61.0% | 83.0% | 100 |
| 32 | 02:48 | USDDZD_otc | CALL | 60.0% | 84.0% | 100 |
| 33 | 03:17 | USDBDT_otc | PUT | 60.0% | 84.0% | 100 |
| 34 | 03:23 | BRLUSD_otc | PUT | 60.0% | 83.0% | 100 |
| 35 | 03:25 | USDBDT_otc | PUT | 66.0% | 83.0% | 100 |
| 36 | 03:27 | BRLUSD_otc | PUT | 60.0% | 82.0% | 100 |
| 37 | 03:31 | USDBDT_otc | CALL | 61.0% | 81.0% | 100 |
| 38 | 03:34 | USDARS_otc | PUT | 61.0% | 87.0% | 100 |
| 39 | 03:43 | USDDZD_otc | PUT | 60.0% | 82.0% | 100 |
| 40 | 03:45 | BRLUSD_otc | PUT | 60.0% | 86.0% | 100 |
| 41 | 04:05 | BRLUSD_otc | PUT | 62.0% | 87.0% | 100 |
| 42 | 04:19 | USDDZD_otc | PUT | 60.0% | 85.0% | 100 |
| 43 | 04:23 | USDARS_otc | CALL | 60.0% | 75.0% | 100 |
| 44 | 04:36 | BRLUSD_otc | PUT | 67.0% | 84.0% | 100 |
| 45 | 04:45 | USDBDT_otc | PUT | 60.0% | 84.0% | 100 |
| 46 | 04:50 | USDDZD_otc | PUT | 62.0% | 79.0% | 100 |
| 47 | 04:56 | BRLUSD_otc | PUT | 60.0% | 80.0% | 100 |
| 48 | 04:58 | USDARS_otc | PUT | 60.0% | 83.0% | 100 |
| 49 | 05:05 | USDBDT_otc | PUT | 65.0% | 87.0% | 100 |
| 50 | 05:08 | USDDZD_otc | PUT | 63.0% | 79.0% | 100 |
| 51 | 05:11 | USDARS_otc | PUT | 60.0% | 81.0% | 100 |
| 52 | 05:14 | BRLUSD_otc | CALL | 63.0% | 79.0% | 100 |
| 53 | 05:15 | BRLUSD_otc | PUT | 61.0% | 80.0% | 100 |
| 54 | 05:22 | BRLUSD_otc | PUT | 60.0% | 85.0% | 100 |
| 55 | 05:29 | BRLUSD_otc | PUT | 60.0% | 83.0% | 100 |
| 56 | 05:36 | USDDZD_otc | PUT | 63.0% | 81.0% | 100 |
| 57 | 05:43 | USDARS_otc | CALL | 61.0% | 76.0% | 100 |
| 58 | 05:50 | USDBDT_otc | CALL | 61.0% | 83.0% | 100 |
| 59 | 05:59 | USDBDT_otc | CALL | 64.0% | 77.0% | 100 |
| 60 | 06:01 | USDARS_otc | CALL | 60.0% | 84.0% | 100 |
| 61 | 06:04 | USDBDT_otc | PUT | 61.0% | 80.0% | 100 |
| 62 | 06:06 | USDBDT_otc | PUT | 60.0% | 77.0% | 100 |
| 63 | 06:14 | USDARS_otc | CALL | 61.0% | 81.0% | 100 |
| 64 | 06:20 | USDARS_otc | CALL | 60.0% | 78.0% | 100 |
| 65 | 06:23 | USDBDT_otc | PUT | 61.0% | 78.0% | 100 |
| 66 | 06:34 | USDDZD_otc | PUT | 63.0% | 83.0% | 100 |
| 67 | 06:38 | USDBDT_otc | PUT | 61.0% | 80.0% | 100 |
| 68 | 06:41 | BRLUSD_otc | PUT | 65.0% | 83.0% | 100 |
| 69 | 06:45 | USDARS_otc | CALL | 61.0% | 82.0% | 100 |
| 70 | 06:50 | BRLUSD_otc | PUT | 62.0% | 85.0% | 100 |
| 71 | 06:52 | USDBDT_otc | CALL | 61.0% | 81.0% | 100 |
| 72 | 07:03 | USDDZD_otc | PUT | 60.0% | 81.0% | 100 |
| 73 | 07:12 | USDARS_otc | CALL | 60.0% | 82.0% | 100 |
| 74 | 07:20 | USDDZD_otc | CALL | 60.0% | 77.0% | 100 |
| 75 | 07:21 | USDARS_otc | PUT | 62.0% | 83.0% | 100 |
| 76 | 07:37 | USDDZD_otc | PUT | 63.0% | 79.0% | 100 |
| 77 | 07:40 | BRLUSD_otc | CALL | 60.0% | 83.0% | 100 |
| 78 | 07:48 | USDDZD_otc | PUT | 65.0% | 83.0% | 100 |
| 79 | 07:53 | USDARS_otc | CALL | 62.0% | 82.0% | 100 |
| 80 | 08:03 | USDDZD_otc | PUT | 61.0% | 83.0% | 100 |
| 81 | 08:07 | BRLUSD_otc | PUT | 63.0% | 87.0% | 100 |
| 82 | 08:09 | USDARS_otc | PUT | 62.0% | 88.0% | 100 |
| 83 | 08:18 | USDARS_otc | CALL | 60.0% | 82.0% | 100 |
| 84 | 08:22 | BRLUSD_otc | PUT | 60.0% | 81.0% | 100 |
| 85 | 08:25 | USDBDT_otc | PUT | 60.0% | 78.0% | 100 |
| 86 | 08:29 | USDBDT_otc | PUT | 60.0% | 82.0% | 100 |
| 87 | 08:38 | BRLUSD_otc | PUT | 61.0% | 81.0% | 100 |
| 88 | 08:41 | USDBDT_otc | CALL | 60.0% | 81.0% | 100 |
| 89 | 08:53 | USDBDT_otc | PUT | 61.0% | 83.0% | 100 |
| 90 | 08:55 | BRLUSD_otc | PUT | 63.0% | 84.0% | 100 |
| 91 | 09:01 | USDDZD_otc | CALL | 62.0% | 83.0% | 100 |
| 92 | 09:05 | USDDZD_otc | PUT | 62.0% | 76.0% | 100 |
| 93 | 09:08 | USDBDT_otc | CALL | 60.0% | 80.0% | 100 |
| 94 | 09:10 | BRLUSD_otc | PUT | 63.0% | 80.0% | 100 |
| 95 | 09:16 | USDARS_otc | CALL | 60.0% | 76.0% | 100 |
| 96 | 09:23 | USDDZD_otc | CALL | 61.0% | 81.0% | 100 |
| 97 | 09:27 | USDBDT_otc | CALL | 64.0% | 84.0% | 100 |
| 98 | 09:37 | USDDZD_otc | CALL | 60.0% | 79.0% | 100 |
| 99 | 09:45 | BRLUSD_otc | PUT | 61.0% | 82.0% | 100 |
| 100 | 09:48 | USDDZD_otc | CALL | 61.0% | 80.0% | 100 |
| 101 | 09:54 | BRLUSD_otc | PUT | 60.0% | 86.0% | 100 |
| 102 | 09:57 | USDBDT_otc | PUT | 60.0% | 87.0% | 100 |
| 103 | 10:11 | BRLUSD_otc | CALL | 61.0% | 87.0% | 100 |
| 104 | 10:13 | USDBDT_otc | PUT | 64.0% | 88.0% | 100 |
| 105 | 10:18 | USDDZD_otc | CALL | 60.0% | 76.0% | 100 |
| 106 | 10:24 | BRLUSD_otc | PUT | 64.0% | 82.0% | 100 |
| 107 | 10:31 | USDARS_otc | CALL | 62.0% | 80.0% | 100 |
| 108 | 10:36 | USDDZD_otc | PUT | 60.0% | 82.0% | 100 |
| 109 | 10:39 | BRLUSD_otc | CALL | 60.0% | 77.0% | 100 |
| 110 | 10:43 | USDARS_otc | CALL | 63.0% | 83.0% | 100 |
| 111 | 10:51 | BRLUSD_otc | PUT | 60.0% | 77.0% | 100 |
| 112 | 11:04 | USDARS_otc | CALL | 60.0% | 80.0% | 100 |
| 113 | 11:07 | BRLUSD_otc | PUT | 65.0% | 82.0% | 100 |
| 114 | 11:09 | USDBDT_otc | CALL | 61.0% | 78.0% | 100 |
| 115 | 11:22 | USDARS_otc | PUT | 63.0% | 79.0% | 100 |
| 116 | 11:26 | USDDZD_otc | PUT | 60.0% | 78.0% | 100 |
| 117 | 11:27 | USDARS_otc | PUT | 60.0% | 85.0% | 100 |
| 118 | 11:37 | BRLUSD_otc | PUT | 60.0% | 83.0% | 100 |
| 119 | 11:42 | USDBDT_otc | PUT | 62.0% | 83.0% | 100 |
| 120 | 11:47 | BRLUSD_otc | PUT | 60.0% | 80.0% | 100 |
| 121 | 12:04 | USDBDT_otc | PUT | 61.0% | 81.0% | 100 |
| 122 | 12:07 | BRLUSD_otc | CALL | 62.0% | 84.0% | 100 |
| 123 | 12:12 | USDDZD_otc | PUT | 61.0% | 83.0% | 100 |
| 124 | 12:22 | USDBDT_otc | PUT | 61.0% | 85.0% | 100 |
| 125 | 12:31 | USDDZD_otc | PUT | 62.0% | 81.0% | 100 |
| 126 | 12:35 | USDBDT_otc | PUT | 60.0% | 82.0% | 100 |
| 127 | 12:39 | USDARS_otc | CALL | 60.0% | 87.0% | 100 |
| 128 | 12:50 | USDBDT_otc | CALL | 60.0% | 78.0% | 100 |
| 129 | 12:51 | USDARS_otc | PUT | 62.0% | 81.0% | 100 |
| 130 | 12:54 | BRLUSD_otc | PUT | 65.0% | 83.0% | 100 |
| 131 | 12:57 | USDARS_otc | PUT | 60.0% | 83.0% | 100 |
| 132 | 13:00 | USDDZD_otc | PUT | 64.0% | 83.0% | 100 |
| 133 | 13:11 | USDDZD_otc | PUT | 61.0% | 84.0% | 100 |
| 134 | 13:17 | USDARS_otc | CALL | 61.0% | 78.0% | 100 |
| 135 | 13:22 | USDBDT_otc | PUT | 60.0% | 76.0% | 100 |
| 136 | 13:26 | BRLUSD_otc | PUT | 60.0% | 79.0% | 100 |
| 137 | 13:35 | BRLUSD_otc | PUT | 61.0% | 81.0% | 100 |
| 138 | 13:36 | BRLUSD_otc | PUT | 60.0% | 81.0% | 100 |
| 139 | 13:42 | USDARS_otc | CALL | 61.0% | 81.0% | 100 |
| 140 | 13:49 | USDBDT_otc | PUT | 60.0% | 83.0% | 100 |
| 141 | 13:55 | BRLUSD_otc | PUT | 60.0% | 80.0% | 100 |
| 142 | 14:01 | USDDZD_otc | PUT | 63.0% | 80.0% | 100 |
| 143 | 14:04 | USDDZD_otc | PUT | 61.0% | 82.0% | 100 |
| 144 | 14:09 | BRLUSD_otc | PUT | 60.0% | 76.0% | 100 |
| 145 | 14:16 | BRLUSD_otc | PUT | 64.0% | 79.0% | 100 |
| 146 | 14:21 | USDARS_otc | PUT | 64.0% | 85.0% | 100 |
| 147 | 14:25 | USDBDT_otc | CALL | 60.0% | 82.0% | 100 |
| 148 | 14:31 | BRLUSD_otc | CALL | 64.0% | 82.0% | 100 |
| 149 | 14:35 | USDBDT_otc | PUT | 69.0% | 83.0% | 100 |
| 150 | 14:47 | USDARS_otc | CALL | 62.0% | 81.0% | 100 |
| 151 | 14:56 | BRLUSD_otc | PUT | 60.0% | 77.0% | 100 |
| 152 | 14:59 | USDARS_otc | CALL | 61.0% | 77.0% | 100 |
| 153 | 15:01 | USDDZD_otc | CALL | 61.0% | 77.0% | 100 |
| 154 | 15:11 | USDBDT_otc | PUT | 61.0% | 86.0% | 100 |
| 155 | 15:14 | BRLUSD_otc | CALL | 60.0% | 81.0% | 100 |
| 156 | 15:15 | USDBDT_otc | CALL | 61.0% | 78.0% | 100 |
| 157 | 15:22 | BRLUSD_otc | CALL | 61.0% | 79.0% | 100 |
| 158 | 15:36 | USDARS_otc | CALL | 62.0% | 82.0% | 100 |
| 159 | 15:39 | BRLUSD_otc | PUT | 66.0% | 80.0% | 100 |
| 160 | 15:43 | USDDZD_otc | PUT | 61.0% | 81.0% | 100 |
| 161 | 15:46 | USDBDT_otc | PUT | 61.0% | 76.0% | 100 |
| 162 | 15:50 | USDARS_otc | PUT | 60.0% | 74.0% | 100 |
| 163 | 15:56 | USDDZD_otc | PUT | 61.0% | 79.0% | 100 |
| 164 | 16:06 | BRLUSD_otc | PUT | 63.0% | 87.0% | 100 |
| 165 | 16:10 | BRLUSD_otc | PUT | 65.0% | 80.0% | 100 |
| 166 | 16:14 | BRLUSD_otc | PUT | 62.0% | 87.0% | 100 |
| 167 | 16:15 | USDBDT_otc | CALL | 61.0% | 83.0% | 100 |
| 168 | 16:18 | BRLUSD_otc | PUT | 60.0% | 83.0% | 100 |
| 169 | 16:23 | USDARS_otc | CALL | 60.0% | 79.0% | 100 |
| 170 | 16:26 | BRLUSD_otc | PUT | 60.0% | 81.0% | 100 |
| 171 | 16:28 | USDARS_otc | CALL | 61.0% | 81.0% | 100 |
| 172 | 16:35 | BRLUSD_otc | PUT | 60.0% | 77.0% | 100 |
| 173 | 16:37 | USDARS_otc | PUT | 65.0% | 86.0% | 100 |
| 174 | 16:43 | BRLUSD_otc | CALL | 60.0% | 80.0% | 100 |
| 175 | 16:48 | USDDZD_otc | PUT | 62.0% | 84.0% | 100 |
| 176 | 16:56 | BRLUSD_otc | PUT | 61.0% | 84.0% | 100 |
| 177 | 16:59 | BRLUSD_otc | PUT | 61.0% | 83.0% | 100 |
| 178 | 17:00 | BRLUSD_otc | PUT | 63.0% | 82.0% | 100 |
| 179 | 17:03 | USDDZD_otc | PUT | 61.0% | 84.0% | 100 |
| 180 | 17:09 | USDBDT_otc | PUT | 62.0% | 85.0% | 100 |
| 181 | 17:24 | USDARS_otc | PUT | 64.0% | 81.0% | 100 |
| 182 | 17:27 | USDDZD_otc | CALL | 60.0% | 76.0% | 100 |
| 183 | 17:30 | USDARS_otc | CALL | 62.0% | 84.0% | 100 |
| 184 | 17:35 | USDBDT_otc | PUT | 63.0% | 81.0% | 100 |
| 185 | 17:37 | BRLUSD_otc | PUT | 60.0% | 82.0% | 100 |
| 186 | 17:41 | USDARS_otc | PUT | 60.0% | 85.0% | 100 |
| 187 | 17:42 | USDBDT_otc | PUT | 61.0% | 84.0% | 100 |
| 188 | 17:53 | USDDZD_otc | PUT | 62.0% | 80.0% | 100 |
| 189 | 17:55 | USDARS_otc | CALL | 66.0% | 86.0% | 100 |
| 190 | 17:57 | USDBDT_otc | PUT | 61.0% | 82.0% | 100 |
| 191 | 18:08 | BRLUSD_otc | PUT | 61.0% | 83.0% | 100 |
| 192 | 18:10 | USDBDT_otc | PUT | 61.0% | 86.0% | 100 |
| 193 | 18:19 | USDDZD_otc | PUT | 60.0% | 84.0% | 100 |
| 194 | 18:23 | USDDZD_otc | PUT | 66.0% | 86.0% | 100 |
| 195 | 18:25 | USDDZD_otc | CALL | 61.0% | 81.0% | 100 |
| 196 | 18:29 | BRLUSD_otc | PUT | 60.0% | 79.0% | 100 |
| 197 | 18:40 | USDARS_otc | PUT | 65.0% | 79.0% | 100 |
| 198 | 18:42 | USDBDT_otc | PUT | 63.0% | 81.0% | 100 |
| 199 | 18:54 | BRLUSD_otc | CALL | 61.0% | 81.0% | 100 |
| 200 | 18:59 | USDDZD_otc | PUT | 61.0% | 85.0% | 100 |

---

## 📊 Per-Asset Summary

| Asset | Total Minutes | Avg L1 % | Avg Combined % | Best Combined % |
|-------|---------------|----------|----------------|------------------|
| BRLUSD_otc | 99 | 61.3% | 81.3% | 88.0% |
| USDARS_otc | 84 | 61.3% | 80.8% | 89.0% |
| USDBDT_otc | 82 | 61.7% | 81.1% | 88.0% |
| USDDZD_otc | 72 | 61.6% | 80.7% | 87.0% |

---

## 📈 Schedule Statistics

- Total signals per 24h cycle: **251**
- Average combined win rate: **81.5%**
- Min combined: 74.0%
- Max combined: 89.0%
- Unique assets in schedule: 4
- Signal frequency: every 3 minutes

