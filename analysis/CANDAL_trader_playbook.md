# 🎯 CANDAL Trader Playbook — Top 25 Binary Exploits

**Generated:** from 1078 total exploits
**Filtered to:** martingale win rate >=85% with statistical significance (p<0.05)
**Top picks:** 25 highest-confidence exploits

---

## How to Use This Playbook

Each exploit is a **rule** for entering a binary option trade.

**The rule is:**
1. Wait until ALL the listed conditions are TRUE at the close of the current 1-minute candle.
2. Enter the trade in the listed DIRECTION (CALL if BULL, PUT if BEAR).
3. Trade duration: **1 minute** (the very next candle).
4. If the first trade LOSES, enter the same direction on the very next bar (Martingale, **only once**).
5. If the second trade also loses, **stop** — do not continue martingale.

**Note on time-window exploits:** the entry only fires at the specific UTC hour listed.
**Note on London KZ exploits:** the entry only fires between 07:00-09:59 UTC.

---

## Top 25 Exploits — Sorted by Martingale Win Rate

### #1 🔴 USDMXN_otc — PUT (SELL) (97.3% Martingale)

<div class='exploit-card'>

**Type:** `Triple+LondonKZ`

**Conditions:** RSI(14) > 70 (overbought) + Three consecutive green candles before this bar + ATR below its 50-bar average (low volatility)

**Performance:**
- Signals in 30 days: **37**
- Level 1 win rate (no martingale): **73.0%**
- Martingale win rate (with 1 retry): **97.3%**
- Statistical p-value: **0.0009** (✓ significant)

</div>

### #2 🟢 USDIDR_otc — CALL (BUY) (94.6% Martingale)

<div class='exploit-card'>

**Type:** `Triple+LondonKZ`

**Conditions:** Close below Bollinger Lower Band + Three consecutive red candles before this bar + ATR below its 50-bar average (low volatility)

**Performance:**
- Signals in 30 days: **37**
- Level 1 win rate (no martingale): **81.1%**
- Martingale win rate (with 1 retry): **94.6%**
- Statistical p-value: **0.0030** (✓ significant)

</div>

### #3 🔴 BRLUSD_otc — PUT (SELL) (93.8% Martingale)

<div class='exploit-card'>

**Type:** `TimeWindow`

**Conditions:** At 18:00 UTC, when: Shooting star

**Performance:**
- Signals in 30 days: **48**
- Level 1 win rate (no martingale): **58.3%**
- Martingale win rate (with 1 retry): **93.8%**
- Statistical p-value: **0.0013** (✓ significant)

</div>

### #4 🔴 USDMXN_otc — PUT (SELL) (93.3% Martingale)

<div class='exploit-card'>

**Type:** `Triple+LondonKZ`

**Conditions:** RSI(14) > 70 (overbought) + Two consecutive green candles before this bar + ATR below its 50-bar average (low volatility)

**Performance:**
- Signals in 30 days: **60**
- Level 1 win rate (no martingale): **65.0%**
- Martingale win rate (with 1 retry): **93.3%**
- Statistical p-value: **0.0005** (✓ significant)

</div>

### #5 🟢 USDZAR_otc — CALL (BUY) (93.3% Martingale)

<div class='exploit-card'>

**Type:** `TripleCombo`

**Conditions:** RSI(14) < 30 (oversold) + Hammer candle (long lower wick, small body) + Two consecutive red candles before this bar

**Performance:**
- Signals in 30 days: **30**
- Level 1 win rate (no martingale): **63.3%**
- Martingale win rate (with 1 retry): **93.3%**
- Statistical p-value: **0.0102** (~ marginal)

</div>

### #6 🔴 USDPKR_otc — PUT (SELL) (92.2% Martingale)

<div class='exploit-card'>

**Type:** `TimeWindow`

**Conditions:** At 13:00 UTC, when: Close above Bollinger Upper Band

**Performance:**
- Signals in 30 days: **64**
- Level 1 win rate (no martingale): **67.2%**
- Martingale win rate (with 1 retry): **92.2%**
- Statistical p-value: **0.0007** (✓ significant)

</div>

### #7 🔴 USDZAR_otc — PUT (SELL) (92.0% Martingale)

<div class='exploit-card'>

**Type:** `TimeWindow`

**Conditions:** At 04:00 UTC, when: Close above Bollinger Upper Band

**Performance:**
- Signals in 30 days: **75**
- Level 1 win rate (no martingale): **60.0%**
- Martingale win rate (with 1 retry): **92.0%**
- Statistical p-value: **0.0003** (✓ significant)

</div>

### #8 🟢 BRLUSD_otc — CALL (BUY) (91.9% Martingale)

<div class='exploit-card'>

**Type:** `Triple+LondonKZ`

**Conditions:** Hammer candle (long lower wick, small body) + Current candle is green + ATR below its 50-bar average (low volatility)

**Performance:**
- Signals in 30 days: **37**
- Level 1 win rate (no martingale): **73.0%**
- Martingale win rate (with 1 retry): **91.9%**
- Statistical p-value: **0.0088** (✓ significant)

</div>

### #9 🔴 USDZAR_otc — PUT (SELL) (91.9% Martingale)

<div class='exploit-card'>

**Type:** `TimeWindow`

**Conditions:** At 13:00 UTC, when: Liquidity sweep

**Performance:**
- Signals in 30 days: **37**
- Level 1 win rate (no martingale): **54.1%**
- Martingale win rate (with 1 retry): **91.9%**
- Statistical p-value: **0.0088** (✓ significant)

</div>

### #10 🟢 USDEGP_otc — CALL (BUY) (91.3% Martingale)

<div class='exploit-card'>

**Type:** `TimeWindow`

**Conditions:** At 14:00 UTC, when: Close below Bollinger Lower Band

**Performance:**
- Signals in 30 days: **69**
- Level 1 win rate (no martingale): **63.8%**
- Martingale win rate (with 1 retry): **91.3%**
- Statistical p-value: **0.0009** (✓ significant)

</div>

### #11 🟢 USDZAR_otc — CALL (BUY) (91.2% Martingale)

<div class='exploit-card'>

**Type:** `TimeWindow`

**Conditions:** At 20:00 UTC, when: Hammer candle

**Performance:**
- Signals in 30 days: **57**
- Level 1 win rate (no martingale): **61.4%**
- Martingale win rate (with 1 retry): **91.2%**
- Statistical p-value: **0.0023** (✓ significant)

</div>

### #12 🟢 USDIDR_otc — CALL (BUY) (91.2% Martingale)

<div class='exploit-card'>

**Type:** `Triple+LondonKZ`

**Conditions:** Three consecutive red candles before this bar + Two consecutive dojis before this bar + ATR below its 50-bar average (low volatility)

**Performance:**
- Signals in 30 days: **34**
- Level 1 win rate (no martingale): **61.8%**
- Martingale win rate (with 1 retry): **91.2%**
- Statistical p-value: **0.0147** (~ marginal)

</div>

### #13 🔴 USDINR_otc — PUT (SELL) (91.2% Martingale)

<div class='exploit-card'>

**Type:** `Triple+LondonKZ`

**Conditions:** RSI(14) between 60-75 + Close above Bollinger Upper Band + Doji (body < 30% of range)

**Performance:**
- Signals in 30 days: **34**
- Level 1 win rate (no martingale): **61.8%**
- Martingale win rate (with 1 retry): **91.2%**
- Statistical p-value: **0.0147** (~ marginal)

</div>

### #14 🟢 USDIDR_otc — CALL (BUY) (90.9% Martingale)

<div class='exploit-card'>

**Type:** `TripleCombo`

**Conditions:** Current candle is green + Liquidity sweep (wick below recent low, close back inside) + Two consecutive dojis before this bar

**Performance:**
- Signals in 30 days: **33**
- Level 1 win rate (no martingale): **69.7%**
- Martingale win rate (with 1 retry): **90.9%**
- Statistical p-value: **0.0174** (~ marginal)

</div>

### #15 🔴 USDINR_otc — PUT (SELL) (90.9% Martingale)

<div class='exploit-card'>

**Type:** `Triple+LondonKZ`

**Conditions:** Close above Bollinger Upper Band + Two consecutive green candles before this bar + Doji (body < 30% of range)

**Performance:**
- Signals in 30 days: **33**
- Level 1 win rate (no martingale): **57.6%**
- Martingale win rate (with 1 retry): **90.9%**
- Statistical p-value: **0.0174** (~ marginal)

</div>

### #16 🟢 USDIDR_otc — CALL (BUY) (90.7% Martingale)

<div class='exploit-card'>

**Type:** `Triple+LondonKZ`

**Conditions:** Close below Bollinger Lower Band + Lower wick longer than upper wick + ATR below its 50-bar average (low volatility)

**Performance:**
- Signals in 30 days: **54**
- Level 1 win rate (no martingale): **70.4%**
- Martingale win rate (with 1 retry): **90.7%**
- Statistical p-value: **0.0038** (✓ significant)

</div>

### #17 🟢 USDBDT_otc — CALL (BUY) (90.6% Martingale)

<div class='exploit-card'>

**Type:** `Triple+LondonKZ`

**Conditions:** Close above EMA(50) + Two consecutive red candles before this bar + Two consecutive dojis before this bar

**Performance:**
- Signals in 30 days: **32**
- Level 1 win rate (no martingale): **56.2%**
- Martingale win rate (with 1 retry): **90.6%**
- Statistical p-value: **0.0206** (~ marginal)

</div>

### #18 🔴 USDPHP_otc — PUT (SELL) (90.6% Martingale)

<div class='exploit-card'>

**Type:** `TripleCombo`

**Conditions:** Shooting star (long upper wick, small body) + Fair Value Gap (bearish 3-candle imbalance) + ATR below its 50-bar average (low volatility)

**Performance:**
- Signals in 30 days: **32**
- Level 1 win rate (no martingale): **62.5%**
- Martingale win rate (with 1 retry): **90.6%**
- Statistical p-value: **0.0206** (~ marginal)

</div>

### #19 🟢 BRLUSD_otc — CALL (BUY) (90.4% Martingale)

<div class='exploit-card'>

**Type:** `TimeWindow`

**Conditions:** At 17:00 UTC, when: Close below Bollinger Lower Band

**Performance:**
- Signals in 30 days: **94**
- Level 1 win rate (no martingale): **67.0%**
- Martingale win rate (with 1 retry): **90.4%**
- Statistical p-value: **0.0003** (✓ significant)

</div>

### #20 🔴 USDDZD_otc — PUT (SELL) (90.4% Martingale)

<div class='exploit-card'>

**Type:** `TimeWindow`

**Conditions:** At 13:00 UTC, when: Liquidity sweep

**Performance:**
- Signals in 30 days: **52**
- Level 1 win rate (no martingale): **63.5%**
- Martingale win rate (with 1 retry): **90.4%**
- Statistical p-value: **0.0052** (✓ significant)

</div>

### #21 🔴 USDZAR_otc — PUT (SELL) (90.3% Martingale)

<div class='exploit-card'>

**Type:** `Triple+LondonKZ`

**Conditions:** Fair Value Gap (bearish 3-candle imbalance) + MACD histogram crossed from positive to negative + ATR below its 50-bar average (low volatility)

**Performance:**
- Signals in 30 days: **31**
- Level 1 win rate (no martingale): **54.8%**
- Martingale win rate (with 1 retry): **90.3%**
- Statistical p-value: **0.0244** (~ marginal)

</div>

### #22 🟢 USDPHP_otc — CALL (BUY) (90.2% Martingale)

<div class='exploit-card'>

**Type:** `TripleCombo`

**Conditions:** Big green body (>2× average body) + Liquidity sweep (wick below recent low, close back inside) + Three consecutive red candles before this bar

**Performance:**
- Signals in 30 days: **41**
- Level 1 win rate (no martingale): **56.1%**
- Martingale win rate (with 1 retry): **90.2%**
- Statistical p-value: **0.0121** (~ marginal)

</div>

### #23 🟢 USDDZD_otc — CALL (BUY) (90.0% Martingale)

<div class='exploit-card'>

**Type:** `TimeWindow`

**Conditions:** At 08:00 UTC, when: Liquidity sweep

**Performance:**
- Signals in 30 days: **50**
- Level 1 win rate (no martingale): **54.0%**
- Martingale win rate (with 1 retry): **90.0%**
- Statistical p-value: **0.0072** (✓ significant)

</div>

### #24 🔴 USDZAR_otc — PUT (SELL) (90.0% Martingale)

<div class='exploit-card'>

**Type:** `Triple+LondonKZ`

**Conditions:** RSI(14) > 70 (overbought) + Close above Bollinger Upper Band + ATR below its 50-bar average (low volatility)

**Performance:**
- Signals in 30 days: **40**
- Level 1 win rate (no martingale): **57.5%**
- Martingale win rate (with 1 retry): **90.0%**
- Statistical p-value: **0.0142** (~ marginal)

</div>

### #25 🟢 USDPHP_otc — CALL (BUY) (90.0% Martingale)

<div class='exploit-card'>

**Type:** `TripleCombo`

**Conditions:** Fair Value Gap (bullish 3-candle imbalance) + Two consecutive dojis before this bar + ATR below its 50-bar average (low volatility)

**Performance:**
- Signals in 30 days: **30**
- Level 1 win rate (no martingale): **63.3%**
- Martingale win rate (with 1 retry): **90.0%**
- Statistical p-value: **0.0289** (~ marginal)

</div>

---

## 📊 Recommended Daily Routine

1. **Pick 2-3 exploits** from the top 10 above for your trading session.
2. **Match the asset + time window**: only enter when the conditions match.
3. **Stick to the rule**: if Level 1 loses, martingale ONCE then stop.
4. **Risk per trade**: 1-2% of account. After martingale, the next trade
   should be at 1% (do NOT compound martingale sizes).
5. **Avoid the same exploit repeatedly**: even 90% win rate means 1 in 10
   losses. Wait at least 5-10 minutes between trades on the same asset.

## 🎯 Best Hours to Trade (UTC)

Most top exploits cluster around these UTC hours:
- **04:00 UTC** — early Asian volatility (USDINR bb_lower, USDZAR bb_upper)
- **08:00 UTC** — London open (USDDZD sweep)
- **12:00-14:00 UTC** — New York open (USDPKR bb_upper, USDCOP bb_upper, USDEGP bb_lower)
- **18:00 UTC** — Asia crossover (BRLUSD star)
- **20:00 UTC** — late NY (USDZAR hammer)

## ⚠️ Risk Warning

These exploits are based on **30 days** of historical data. Markets
change. Past performance does NOT guarantee future results. Always:
- Start with **demo account** for at least 1 week
- Track every trade in a journal
- Stop trading after 3 consecutive losses
- Re-validate exploits every 2 weeks with new data

