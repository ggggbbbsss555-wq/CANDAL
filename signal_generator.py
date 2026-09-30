#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CANDAL Signal Generator — Advanced Binary Options Signal Bot
================================================================
Interactive bot that lets the user control:
  1. Candles folder path (where to find candle JSON files)
  2. Days filter (only load files matching N days, e.g. 100, 30)
  3. Start time (signals begin near this hour, not exactly)
  4. Number of signals to generate

Features:
  - Auto-discovers candle files matching pattern: <asset>_1m_<days>d_<hash>.json
  - Filters files by days count (user-specified: 100, 30, or any)
  - Analyzes each asset on every minute-of-day (1440 minutes)
  - Computes L1, Combined, MTG use, MTG success rates
  - Applies deep filters (inspired by competitor bot analysis):
    * Avoid hours with high loss rates (10, 16, 21, 23 UTC)
    * Avoid assets with high loss rates (BRLUSD)
    * Prefer PUT when L1 is tied (4% safer than CALL)
    * MTG success >= 55%
  - Builds schedule with 3-10 minute variable gaps (obfuscation)
  - 10 minute gap after potential MTG (avoid missing next trade)
  - Asset rotation (no same-asset in consecutive signals)
  - Shows Algerian local time (UTC+1) with صباحاً/مساءً labels
  - Saves schedule to JSON file

Usage:
  python signal_generator.py
  
  Then it asks:
    1. Candles folder path (default: candles_data)
    2. Days filter (default: 100, accepts 30 or any number)
    3. Start time HH:MM UTC (e.g. 20:00)
    4. Number of signals (default: 20)

Output:
  - Beautiful colored schedule on screen
  - JSON file: signals_YYYY-MM-DD_HH-MM.json
  - Statistics: avg L1, Combined, MTG use, MTG success
"""
import os
import sys
import json
import math
import time
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict, Counter

import numpy as np
import pandas as pd

# =============================================================================
# CONFIG (inspired by competitor bot analysis — 998 signals)
# =============================================================================

# Hours to avoid (loss rate > 15%)
AVOID_HOURS_UTC = [10, 16, 21, 23]

# Assets to avoid (loss rate > 14%)
AVOID_ASSETS = ["BRLUSD_otc"]  # 16.8% loss rate

# Best hours (loss rate < 10%) — preferred for selection
BEST_HOURS_UTC = [11, 17, 20, 15, 9, 18]

# Best assets (loss rate < 10.5%) — preferred for selection
BEST_ASSETS = ["USDCOP_otc", "USDDZD_otc", "USDBDT_otc", "USDIDR_otc", "USDARS_otc"]

# Analysis filters
MIN_SAMPLES = 80           # min samples (80 days × 1 sample per day)
TARGET_L1 = 0.58           # L1 >= 58% (no martingale)
TARGET_COMBINED = 0.78     # Combined >= 78% (with martingale)
CHI_P_VAL = 0.10           # statistical significance
MAX_MTG_USE_RATE = 0.45    # MTG use <= 45%
MIN_MTG_SUCCESS = 0.55     # MTG success >= 55%

# Schedule settings
GAP_MIN = 3               # min gap between signals (minutes)
GAP_NORMAL_MAX = 6         # normal gap (3-6 minutes)
GAP_AFTER_MTG = 10        # longer gap after MTG (10 minutes)

# Display colors
class Colors:
    GREEN = '\033[92m'; RED = '\033[91m'; YELLOW = '\033[93m'
    CYAN = '\033[96m'; BOLD = '\033[1m'; RESET = '\033[0m'


# =============================================================================
# FUNCTIONS
# =============================================================================

def chi_square_p(wins, total, p_null=0.5):
    """Compute one-tailed p-value for H0: win_rate > p_null."""
    if total == 0: return 1.0
    expected = p_null * total
    se = math.sqrt(p_null * (1 - p_null) * total)
    if se == 0: return 1.0
    z = (wins - expected) / se
    return 0.5 * (1 - math.erf(z / math.sqrt(2)))


def discover_candle_files(candles_dir: Path, days_filter: int = None):
    """Auto-discover candle files in the given folder.
    
    Pattern: <asset>_1m_<days>d_<hash>.json
    Example: BRLUSD_otc_1m_100d_90c8207b.json
    
    If days_filter is specified, only load files matching that exact days count.
    If multiple files exist for the same asset, pick the one with most days.
    """
    pattern = "*_1m_*d_*.json"
    files = sorted(candles_dir.glob(pattern))
    if not files:
        return {}
    
    by_asset = {}
    for f in files:
        try:
            asset = f.name.split("_1m_")[0]
            days = int(f.name.split("_1m_")[1].split("d_")[0])
        except (IndexError, ValueError):
            continue
        
        # Apply days filter if specified
        if days_filter is not None and days != days_filter:
            continue
        
        # Pick the file with most days for each asset (if multiple)
        if asset not in by_asset or days > by_asset[asset][0]:
            by_asset[asset] = (days, f)
    
    return by_asset


def load_candles(file_path: Path):
    """Load candles from JSON file."""
    with open(file_path, "r") as fp:
        data = json.load(fp)
    candles = data.get("candles", [])
    # Sort by time + filter invalid
    candles = sorted(candles, key=lambda c: c.get("time", 0))
    candles = [c for c in candles
               if c.get("open", 0) > 0 and c.get("high", 0) > 0
               and c.get("low", 0) > 0 and c.get("close", 0) > 0]
    return candles


def analyze_minute_patterns(asset: str, candles: list):
    """For each minute-of-day (1440 minutes), compute:
       - L1 win rate (without martingale)
       - MTG use rate (how often martingale is needed)
       - MTG success rate (how often martingale recovers the loss)
       - Combined win rate (L1 + MTG)
    """
    if len(candles) < 100:
        return []
    
    df = pd.DataFrame(candles)
    df["time_dt"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df["hour"] = df["time_dt"].dt.hour
    df["minute_of_day"] = df["hour"] * 60 + df["time_dt"].dt.minute
    df["dir"] = (df["close"] > df["open"]).astype(int)  # 1=green, 0=red
    df["next_dir_1"] = df["dir"].shift(-1)
    df["next_dir_2"] = df["dir"].shift(-2)
    
    grouped = df.groupby("minute_of_day")
    stats = []
    for minute_mod, group in grouped:
        n = len(group)
        if n < MIN_SAMPLES:
            continue
        g = group.dropna(subset=["next_dir_1", "next_dir_2"])
        n_valid = len(g)
        if n_valid < MIN_SAMPLES:
            continue
        
        # CALL: predict next green candle
        call_l1_wins = int((g["next_dir_1"] == 1).sum())
        call_l1_lost = g[g["next_dir_1"] != 1]
        call_mtg_wins = int((call_l1_lost["next_dir_2"] == 1).sum())
        call_combined = call_l1_wins + call_mtg_wins
        
        # PUT: predict next red candle
        put_l1_wins = int((g["next_dir_1"] == 0).sum())
        put_l1_lost = g[g["next_dir_1"] != 0]
        put_mtg_wins = int((put_l1_lost["next_dir_2"] == 0).sum())
        put_combined = put_l1_wins + put_mtg_wins
        
        # Pick best direction (prefer PUT on tie — 4% safer)
        if call_l1_wins > put_l1_wins:
            direction = "CALL"; l1_wins = call_l1_wins
            mtg_wins = call_mtg_wins; combined_wins = call_combined
        else:
            direction = "PUT"; l1_wins = put_l1_wins
            mtg_wins = put_mtg_wins; combined_wins = put_combined
        
        l1_wr = l1_wins / n_valid
        combined_wr = combined_wins / n_valid
        mtg_use_rate = (n_valid - l1_wins) / n_valid
        mtg_success = mtg_wins / max(1, (n_valid - l1_wins))
        p = chi_square_p(l1_wins, n_valid)
        
        stats.append({
            "asset": asset,
            "minute_of_day": int(minute_mod),
            "time_utc": f"{minute_mod // 60:02d}:{minute_mod % 60:02d}",
            "hour": int(minute_mod // 60),
            "direction": direction,
            "samples": n_valid,
            "l1_win_rate": l1_wr,
            "mtg_use_rate": mtg_use_rate,
            "mtg_success_rate": mtg_success,
            "combined_win_rate": combined_wr,
            "p_value": p,
        })
    return stats


def filter_signals(stats: list):
    """Apply deep filters to asset signals."""
    filtered = []
    for s in stats:
        if s["asset"] in AVOID_ASSETS:
            continue
        if s["hour"] in AVOID_HOURS_UTC:
            continue
        if s["l1_win_rate"] < TARGET_L1:
            continue
        if s["combined_win_rate"] < TARGET_COMBINED:
            continue
        if s["mtg_use_rate"] > MAX_MTG_USE_RATE:
            continue
        if s["mtg_success_rate"] < MIN_MTG_SUCCESS:
            continue
        if s["p_value"] > CHI_P_VAL:
            continue
        filtered.append(s)
    return filtered


def build_schedule(eligible_signals: list, start_minute: int, n_signals: int):
    """Build signal schedule with 3-10 minute variable gaps.
    
    - Start near start_minute (not exactly at it)
    - Normal gap: 3-6 minutes
    - Gap after potential MTG (if L1 < 65%): 10 minutes
    - No same-asset in consecutive signals
    """
    by_time = sorted(eligible_signals, key=lambda x: x["minute_of_day"])
    
    schedule = []
    used_indices = set()
    current_minute = start_minute
    last_asset = None
    last_l1 = 1.0  # last L1 (1.0 = no MTG needed)
    
    attempts = 0
    max_attempts = n_signals * 100
    
    while len(schedule) < n_signals and attempts < max_attempts:
        attempts += 1
        
        # Determine required gap
        if last_l1 < 0.65:
            required_gap = GAP_AFTER_MTG  # 10 min after MTG
        else:
            required_gap = random.randint(GAP_MIN, GAP_NORMAL_MAX)  # 3-6 min
        
        target_minute = (current_minute + required_gap) % 1440
        
        # Find nearest signal to target_minute (within ±5 minutes)
        best_idx = None
        best_diff = 999
        for i, s in enumerate(by_time):
            if i in used_indices:
                continue
            if s["asset"] == last_asset:
                continue
            diff = abs(s["minute_of_day"] - target_minute)
            if diff > 720:
                diff = 1440 - diff
            if diff < best_diff and diff <= 5:
                best_diff = diff
                best_idx = i
        
        if best_idx is None:
            # Find any signal after target_minute (within 60 min)
            for i, s in enumerate(by_time):
                if i in used_indices: continue
                if s["asset"] == last_asset: continue
                forward = (s["minute_of_day"] - target_minute) % 1440
                if forward < 60:
                    best_idx = i
                    break
        
        if best_idx is None:
            current_minute = (current_minute + 1) % 1440
            continue
        
        s = by_time[best_idx]
        schedule.append(s)
        used_indices.add(best_idx)
        current_minute = s["minute_of_day"]
        last_asset = s["asset"]
        last_l1 = s["l1_win_rate"]
    
    return schedule


def utc_to_algeria(utc_minute: int):
    """Convert UTC minute-of-day to Algeria time (UTC+1)."""
    alg_minute = (utc_minute + 60) % 1440
    h, m = divmod(alg_minute, 60)
    if 5 <= h < 12: period = "morning"
    elif 12 <= h < 17: period = "noon"
    elif 17 <= h < 21: period = "evening"
    else: period = "night"
    return f"{h:02d}:{m:02d}", period


def print_banner():
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}  QX ZERO - Signal Generator (Advanced){Colors.RESET}")
    print(f"{Colors.BOLD}  Binary Options Signal Bot - works on your local candle data{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.YELLOW}  Bot features:{Colors.RESET}")
    print(f"     - Auto-discovers all candle files in the specified folder")
    print(f"     - Filters files by days count (100d, 30d, or any)")
    print(f"     - Analyzes each asset on 1440 minutes of the day")
    print(f"     - Computes L1, Combined, MTG use, MTG success")
    print(f"     - Applies deep filters (inspired by competitor bot analysis)")
    print(f"     - Builds schedule with 3-10 min variable gaps (obfuscation)")
    print(f"     - Shows Algerian local time (UTC+1)")
    print()


def input_with_default(prompt: str, default: str = ""):
    """Read user input with default value."""
    s = input(f"{Colors.YELLOW}{prompt}{Colors.RESET} [{default}]: ").strip()
    return s if s else default


def main():
    print_banner()
    
    # ===== 1. Candles folder path =====
    default_dir = "candles_data"
    candles_dir_str = input_with_default(
        "Enter candles folder path (or press Enter for default 'candles_data')",
        default_dir
    )
    candles_dir = Path(candles_dir_str)
    if not candles_dir.is_absolute():
        script_dir = Path(__file__).parent if "__file__" in globals() else Path.cwd()
        candidates = [candles_dir, script_dir / candles_dir, script_dir.parent / candles_dir]
        for c in candidates:
            if c.exists() and c.is_dir():
                candles_dir = c
                break
    
    print(f"\n{Colors.CYAN}Searching in: {candles_dir}{Colors.RESET}")
    
    # ===== 2. Days filter =====
    days_str = input_with_default(
        "Enter days filter (100, 30, or any number - only files matching this exact day count will be loaded)",
        "100"
    )
    try:
        days_filter = int(days_str)
    except ValueError:
        print(f"{Colors.RED}Invalid number. Using default 100.{Colors.RESET}")
        days_filter = 100
    
    by_asset = discover_candle_files(candles_dir, days_filter=days_filter)
    if not by_asset:
        print(f"{Colors.RED}No candle files matching {days_filter}d pattern in: {candles_dir}{Colors.RESET}")
        print(f"  Expected pattern: <asset>_1m_{days_filter}d_<hash>.json")
        return
    
    print(f"{Colors.GREEN}Found {len(by_asset)} assets with {days_filter}d data:{Colors.RESET}")
    for asset, (days, f) in sorted(by_asset.items()):
        print(f"  {asset} ({days} days) -> {f.name}")
    print()
    
    # ===== 3. Start time =====
    start_time_str = input_with_default(
        "Enter start time HH:MM (24h UTC, e.g. 20:00)",
        "00:00"
    )
    try:
        h, m = map(int, start_time_str.split(":"))
        start_minute = h * 60 + m
        if not (0 <= start_minute < 1440):
            raise ValueError
    except (ValueError, IndexError):
        print(f"{Colors.RED}Invalid format. Use HH:MM (e.g. 20:00){Colors.RESET}")
        return
    
    print(f"\n{Colors.CYAN}Requested start: {h:02d}:{m:02d} UTC{Colors.RESET}")
    print(f"   (Algeria UTC+1: {(h+1)%24:02d}:{m:02d})")
    print(f"   Bot will start near this time (within +-5 minutes){Colors.RESET}")
    print()
    
    # ===== 4. Number of signals =====
    n_str = input_with_default(
        "How many signals do you want? (20-40 recommended)",
        "20"
    )
    try:
        n_signals = int(n_str)
        if n_signals < 1 or n_signals > 200:
            print(f"{Colors.RED}Number must be between 1 and 200{Colors.RESET}")
            return
    except ValueError:
        print(f"{Colors.RED}Please enter a valid integer{Colors.RESET}")
        return
    
    print(f"\n{Colors.CYAN}Requested signals: {n_signals}{Colors.RESET}")
    print()
    
    # ===== 5. Analyze each asset =====
    print(f"{Colors.BOLD}Analysis phase:{Colors.RESET}")
    all_eligible = []
    for asset, (days, f) in by_asset.items():
        print(f"  [{asset}] analyzing {days} days...", end=" ", flush=True)
        candles = load_candles(f)
        if len(candles) < MIN_SAMPLES:
            print(f"{Colors.RED}insufficient data ({len(candles)}){Colors.RESET}")
            continue
        stats = analyze_minute_patterns(asset, candles)
        filtered = filter_signals(stats)
        all_eligible.extend(filtered)
        print(f"{Colors.GREEN}{len(filtered)} valid minutes{Colors.RESET}")
    
    print(f"\n{Colors.GREEN}Total valid minutes: {len(all_eligible)}{Colors.RESET}")
    if not all_eligible:
        print(f"{Colors.RED}No valid signals found. Try longer data (100 days).{Colors.RESET}")
        return
    
    # ===== 6. Build schedule =====
    print(f"\n{Colors.BOLD}Schedule building phase:{Colors.RESET}")
    random.seed(int(time.time()))  # true randomness each run
    schedule = build_schedule(all_eligible, start_minute, n_signals)
    
    if not schedule:
        print(f"{Colors.RED}Failed to build schedule. Try a different start time.{Colors.RESET}")
        return
    
    # ===== 7. Display results =====
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*100}{Colors.RESET}")
    print(f"{Colors.BOLD}  QX ZERO - Signal Schedule{Colors.RESET}")
    print(f"{Colors.BOLD}  Starts near {h:02d}:{m:02d} UTC -> {(h+1)%24:02d}:{m:02d} Algeria{Colors.RESET}")
    print(f"{Colors.BOLD}  Number of signals: {len(schedule)}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*100}{Colors.RESET}")
    
    print(f"\n{'#':<3}{'UTC':<7}{'Algeria':<14}{'Asset':<14}{'Direction':<10}{'L1%':<7}{'Comb%':<8}{'MTG Use':<9}{'Gap'}")
    print('-' * 100)
    
    prev_minute = None
    for i, s in enumerate(schedule, 1):
        utc_h, utc_m = divmod(s["minute_of_day"], 60)
        alg_time, period = utc_to_algeria(s["minute_of_day"])
        
        asset_short = s["asset"].replace("_otc", "-OTC")
        arrow = "BUY " if s["direction"] == "CALL" else "SELL"
        
        if prev_minute is not None:
            gap = (s["minute_of_day"] - prev_minute) % 1440
            gap_str = f"{gap} min"
        else:
            gap_str = "(start)"
        
        # Color by strength
        if s["combined_win_rate"] >= 0.87:
            l1_color = Colors.GREEN
        elif s["combined_win_rate"] >= 0.83:
            l1_color = Colors.YELLOW
        else:
            l1_color = Colors.RESET
        
        print(f"{i:<3}{utc_h:02d}:{utc_m:02d}   {alg_time} {period:<8}{asset_short:<14}{arrow:<10}"
              f"{l1_color}{s['l1_win_rate']*100:>4.0f}%   {s['combined_win_rate']*100:>4.0f}%    {s['mtg_use_rate']*100:>4.0f}%      {gap_str}{Colors.RESET}")
        
        prev_minute = s["minute_of_day"]
    
    # ===== 8. Statistics =====
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*100}{Colors.RESET}")
    print(f"{Colors.BOLD}  Statistics{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*100}{Colors.RESET}")
    
    avg_l1 = sum(s["l1_win_rate"] for s in schedule) / len(schedule)
    avg_comb = sum(s["combined_win_rate"] for s in schedule) / len(schedule)
    avg_mtg_use = sum(s["mtg_use_rate"] for s in schedule) / len(schedule)
    avg_mtg_succ = sum(s["mtg_success_rate"] for s in schedule) / len(schedule)
    unique_assets = len(set(s["asset"] for s in schedule))
    
    print(f"  - Total signals: {Colors.BOLD}{len(schedule)}{Colors.RESET}")
    print(f"  - Avg L1 (no MTG): {Colors.BOLD}{avg_l1*100:.1f}%{Colors.RESET}")
    print(f"  - Avg Combined (with MTG): {Colors.GREEN}{avg_comb*100:.1f}%{Colors.RESET}")
    print(f"  - Avg MTG use: {avg_mtg_use*100:.1f}% (rare)")
    print(f"  - Avg MTG success: {avg_mtg_succ*100:.1f}%")
    print(f"  - Unique assets: {unique_assets}")
    
    print(f"\n{Colors.BOLD}  Expected outcome:{Colors.RESET}")
    expected_wins = avg_comb * len(schedule)
    expected_losses = len(schedule) - expected_wins
    print(f"  - Wins: ~{Colors.GREEN}{expected_wins:.0f}{Colors.RESET} of {len(schedule)}")
    print(f"  - Losses: ~{Colors.RED}{expected_losses:.0f}{Colors.RESET} of {len(schedule)}")
    print(f"  - Expected win rate: {Colors.BOLD}{avg_comb*100:.1f}%{Colors.RESET}")
    
    # ===== 9. Save schedule to JSON =====
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = Path(f"signals_{timestamp}.json")
    output_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candles_dir": str(candles_dir),
        "days_filter": days_filter,
        "start_time_utc": f"{h:02d}:{m:02d}",
        "n_signals_requested": n_signals,
        "n_signals_generated": len(schedule),
        "stats": {
            "avg_l1_win_rate": avg_l1,
            "avg_combined_win_rate": avg_comb,
            "avg_mtg_use_rate": avg_mtg_use,
            "avg_mtg_success_rate": avg_mtg_succ,
            "unique_assets": unique_assets,
        },
        "signals": [
            {
                "index": i,
                "utc_time": f"{divmod(s['minute_of_day'], 60)[0]:02d}:{divmod(s['minute_of_day'], 60)[1]:02d}",
                "algeria_time": utc_to_algeria(s["minute_of_day"])[0],
                "asset": s["asset"],
                "direction": s["direction"],
                "l1_win_rate": s["l1_win_rate"],
                "combined_win_rate": s["combined_win_rate"],
                "mtg_use_rate": s["mtg_use_rate"],
                "mtg_success_rate": s["mtg_success_rate"],
                "samples": s["samples"],
            }
            for i, s in enumerate(schedule, 1)
        ],
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\n{Colors.GREEN}Schedule saved to: {output_file}{Colors.RESET}")
    
    # ===== 10. Trading rules =====
    print(f"\n{Colors.YELLOW}{Colors.BOLD}Trading rules:{Colors.RESET}")
    print(f"  - MTG = ONE retry only (no MTG2)")
    print(f"  - If L1 loses -> MTG on the very next candle")
    print(f"  - After MTG, wait 10 minutes before next signal")
    print(f"  - Normal gap is 3-6 minutes (randomized for obfuscation)")
    print(f"  - No same asset in consecutive signals")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Stopped.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
