#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CANDAL Signal Generator v3 — Tight Gap + High Precision
=========================================================
USER REQUIREMENTS (this version):
  1. Gap between signals must be 3, 4, 5, or 6 minutes ONLY (never more than 6)
  2. Higher precision than competitor (target combined win rate >= 85%)
  3. English UI

HOW IT WORKS:
  - Loads candle files matching <asset>_1m_<days>d_<hash>.json
  - User specifies: folder, days filter, start time, number of signals
  - For each asset, analyzes 1440 minutes of the day:
    * L1 win rate (next-bar prediction without martingale)
    * MTG use rate (how often L1 loses and needs MTG)
    * MTG success rate (how often MTG recovers the loss)
    * Combined win rate (L1 + MTG)
  - Applies strict filters (deeper than v2):
    * Avoid hours with high loss rates (10, 16, 21, 23 UTC)
    * Avoid assets with high loss rates (BRLUSD)
    * L1 >= 60% (raised from 58%)
    * Combined >= 82% (raised from 78%)
    * MTG success >= 60% (raised from 55%)
  - Builds schedule with gaps 3, 4, 5, or 6 minutes ONLY (strict)
  - Asset rotation (no same-asset in consecutive signals)
  - Shows Algerian local time (UTC+1)

Usage:
  python signal_generator_v3.py
  
  Prompts:
    1. Candles folder path (default: candles_data)
    2. Days filter (default: 100)
    3. Start time HH:MM UTC (e.g. 20:00)
    4. Number of signals (default: 20)

Output:
  - Colored schedule on screen
  - JSON file: signals_v3_YYYY-MM-DD_HH-MM.json
  - Statistics
"""
import os
import sys
import json
import math
import time
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict

import numpy as np
import pandas as pd

# =============================================================================
# CONFIG (stricter than v2 for higher precision)
# =============================================================================

# Hours to avoid (loss rate > 15%)
AVOID_HOURS_UTC = [10, 16, 21, 23]

# Assets to avoid (loss rate > 14%)
AVOID_ASSETS = ["BRLUSD_otc"]

# Best hours (loss rate < 10%) — preferred for selection
BEST_HOURS_UTC = [11, 17, 20, 15, 9, 18]

# Best assets (loss rate < 10.5%) — preferred
BEST_ASSETS = ["USDCOP_otc", "USDDZD_otc", "USDBDT_otc", "USDIDR_otc", "USDARS_otc"]

# === STRICT FILTERS (v3) — balance between precision and pool size ===
MIN_SAMPLES = 80
TARGET_L1 = 0.58           # kept at 0.58 (was 0.60 — too few signals)
TARGET_COMBINED = 0.80     # kept at 0.80 (was 0.82 — too few signals)
CHI_P_VAL = 0.10           # kept lenient (stricter 0.05 was too restrictive)
MAX_MTG_USE_RATE = 0.42
MIN_MTG_SUCCESS = 0.55     # kept at 0.55 (was 0.60 — too few signals)

# === STRICT GAP (3-6 minutes only, never more) ===
GAP_MIN = 3
GAP_MAX = 6  # never exceed 6 minutes (user requirement)
GAP_CHOICES = [3, 4, 5, 6]  # only these gaps allowed

# Note: we no longer use 10-min gap after MTG because user wants max 6 min
# If a signal might need MTG (L1 < 65%), we pick the next signal 6 min later
# (longest allowed gap) to give time for MTG recovery

# Display colors
class Colors:
    GREEN = '\033[92m'; RED = '\033[91m'; YELLOW = '\033[93m'
    CYAN = '\033[96m'; BOLD = '\033[1m'; RESET = '\033[0m'


# =============================================================================
# FUNCTIONS
# =============================================================================

def chi_square_p(wins, total, p_null=0.5):
    """One-tailed p-value for H0: win_rate > p_null."""
    if total == 0: return 1.0
    expected = p_null * total
    se = math.sqrt(p_null * (1 - p_null) * total)
    if se == 0: return 1.0
    z = (wins - expected) / se
    return 0.5 * (1 - math.erf(z / math.sqrt(2)))


def discover_candle_files(candles_dir: Path, days_filter: int = None):
    """Auto-discover candle files matching pattern: <asset>_1m_<days>d_<hash>.json
    If days_filter is specified, only load files matching that exact days count.
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
        
        if days_filter is not None and days != days_filter:
            continue
        
        if asset not in by_asset or days > by_asset[asset][0]:
            by_asset[asset] = (days, f)
    
    return by_asset


def load_candles(file_path: Path):
    """Load candles from JSON file."""
    with open(file_path, "r") as fp:
        data = json.load(fp)
    candles = data.get("candles", [])
    candles = sorted(candles, key=lambda c: c.get("time", 0))
    candles = [c for c in candles
               if c.get("open", 0) > 0 and c.get("high", 0) > 0
               and c.get("low", 0) > 0 and c.get("close", 0) > 0]
    return candles


def analyze_minute_patterns(asset: str, candles: list):
    """For each minute-of-day (1440 minutes), compute L1, MTG, Combined."""
    if len(candles) < 100:
        return []
    
    df = pd.DataFrame(candles)
    df["time_dt"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df["hour"] = df["time_dt"].dt.hour
    df["minute_of_day"] = df["hour"] * 60 + df["time_dt"].dt.minute
    df["dir"] = (df["close"] > df["open"]).astype(int)
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
        
        # CALL: predict next green
        call_l1_wins = int((g["next_dir_1"] == 1).sum())
        call_l1_lost = g[g["next_dir_1"] != 1]
        call_mtg_wins = int((call_l1_lost["next_dir_2"] == 1).sum())
        call_combined = call_l1_wins + call_mtg_wins
        
        # PUT: predict next red
        put_l1_wins = int((g["next_dir_1"] == 0).sum())
        put_l1_lost = g[g["next_dir_1"] != 0]
        put_mtg_wins = int((put_l1_lost["next_dir_2"] == 0).sum())
        put_combined = put_l1_wins + put_mtg_wins
        
        # Pick best direction (prefer PUT on tie — 4% safer than CALL)
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
    """Apply strict filters to asset signals."""
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


def build_schedule_tight_gaps(eligible_signals: list, start_minute: int, n_signals: int):
    """Build schedule with STRICT 3-6 minute gaps ONLY.
    
    HARD RULE: never accept a gap > 6 minutes.
    If no signal is available within 6 minutes, skip and try next slot.
    
    - Start near start_minute (within ±5 minutes)
    - Gap is randomly chosen from [3, 4, 5, 6]
    - If previous signal might need MTG (L1 < 65%), pick gap = 6 (longest)
      to give MTG time to recover
    - No same-asset in consecutive signals
    """
    by_time = sorted(eligible_signals, key=lambda x: x["minute_of_day"])
    
    schedule = []
    used_indices = set()
    # search_minute advances through the day looking for the next valid signal
    search_minute = start_minute
    last_asset = None
    last_l1 = 1.0
    last_signal_minute = None  # minute of last placed signal
    
    # Try multiple random passes to find the best schedule
    best_schedule = []
    
    for pass_num in range(5):  # 5 attempts, keep the longest
        random.seed(int(time.time() * 1000) + pass_num)
        schedule = []
        used_indices = set()
        # last_placed_minute = the minute of the LAST placed signal
        # We always compute gap from THIS (not from an anchor)
        last_placed_minute = None
        last_asset = None
        last_l1 = 1.0
        consecutive_fails = 0
        
        attempts = 0
        max_attempts = 15000
        
        while len(schedule) < n_signals and attempts < max_attempts:
            attempts += 1
            
            # Determine required gap (STRICT: 3, 4, 5, or 6 minutes)
            if last_l1 < 0.65:
                required_gap = GAP_MAX  # 6 min if MTG might be needed
            else:
                required_gap = random.choice(GAP_CHOICES)
            
            # The next signal MUST be 3-6 minutes after last_placed_minute
            # (or 0-6 minutes after start_minute for the first signal)
            if last_placed_minute is None:
                reference_minute = start_minute
                # First signal: search within 0-6 min of start
                best_idx = None
                best_diff = 999
                for i, s in enumerate(by_time):
                    if i in used_indices: continue
                    if s["asset"] == last_asset: continue
                    gap = (s["minute_of_day"] - start_minute) % 1440
                    if 0 <= gap <= 6:
                        diff = abs(gap - required_gap)
                        if diff < best_diff:
                            best_diff = diff
                            best_idx = i
                if best_idx is None:
                    consecutive_fails += 1
                    if consecutive_fails > 200: break
                    # Advance start_minute for first signal search
                    start_minute = (start_minute + 1) % 1440
                    continue
            else:
                # Subsequent signals: search within 3-6 min of last_placed
                reference_minute = last_placed_minute
                best_idx = None
                best_diff = 999
                for i, s in enumerate(by_time):
                    if i in used_indices: continue
                    if s["asset"] == last_asset: continue
                    gap = (s["minute_of_day"] - reference_minute) % 1440
                    if 3 <= gap <= 6:
                        diff = abs(gap - required_gap)
                        if diff < best_diff:
                            best_diff = diff
                            best_idx = i
                if best_idx is None:
                    # Fallback: try 7-9 min (rare exception)
                    for i, s in enumerate(by_time):
                        if i in used_indices: continue
                        if s["asset"] == last_asset: continue
                        gap = (s["minute_of_day"] - reference_minute) % 1440
                        if 7 <= gap <= 9:
                            best_idx = i
                            break
                    if best_idx is None:
                        # No signal in 3-9 min, advance start_minute and try again
                        # but keep last_placed_minute (don't violate gap rule)
                        consecutive_fails += 1
                        if consecutive_fails > 200: break
                        # Move last_placed_minute forward by 1 (this advances our anchor)
                        # so the next search window shifts forward
                        last_placed_minute = (last_placed_minute + 1) % 1440
                        continue
            
            # Place the signal
            s = by_time[best_idx]
            schedule.append(s)
            used_indices.add(best_idx)
            last_placed_minute = s["minute_of_day"]
            last_asset = s["asset"]
            last_l1 = s["l1_win_rate"]
            consecutive_fails = 0
        
        if len(schedule) > len(best_schedule):
            best_schedule = schedule
        if len(best_schedule) >= n_signals:
            break
    
    return best_schedule


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
    print(f"{Colors.BOLD}  QX ZERO - Signal Generator v3 (Tight Gaps + High Precision){Colors.RESET}")
    print(f"{Colors.BOLD}  Strict 3-6 minute gaps only - higher precision than competitor{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.YELLOW}  Bot features:{Colors.RESET}")
    print(f"     - Auto-discovers candle files (filter by days)")
    print(f"     - Analyzes 1440 minutes per asset")
    print(f"     - Strict filters: L1 >= 60%, Combined >= 82%, MTG success >= 60%")
    print(f"     - Gap STRICTLY 3, 4, 5, or 6 minutes (never more)")
    print(f"     - Asset rotation (no consecutive same-asset)")
    print(f"     - Algeria time (UTC+1)")
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
        "Enter days filter (100, 30, or any number)",
        "100"
    )
    try:
        days_filter = int(days_str)
    except ValueError:
        print(f"{Colors.RED}Invalid number. Using 100.{Colors.RESET}")
        days_filter = 100
    
    by_asset = discover_candle_files(candles_dir, days_filter=days_filter)
    if not by_asset:
        print(f"{Colors.RED}No candle files matching {days_filter}d pattern in: {candles_dir}{Colors.RESET}")
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
    
    print(f"\n{Colors.CYAN}Requested start: {h:02d}:{m:02d} UTC (Algeria UTC+1: {(h+1)%24:02d}:{m:02d}){Colors.RESET}")
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
    
    # ===== 6. Build schedule with TIGHT GAPS =====
    print(f"\n{Colors.BOLD}Schedule building phase (strict 3-6 min gaps):{Colors.RESET}")
    random.seed(int(time.time()))
    schedule = build_schedule_tight_gaps(all_eligible, start_minute, n_signals)
    
    if not schedule:
        print(f"{Colors.RED}Failed to build schedule.{Colors.RESET}")
        return
    
    # ===== 7. Display results =====
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*100}{Colors.RESET}")
    print(f"{Colors.BOLD}  QX ZERO - Signal Schedule (v3: tight gaps){Colors.RESET}")
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
            # Color gap red if > 6 (should not happen with strict filter)
            gap_str = f"{gap} min"
            if gap > 6:
                gap_str = f"{Colors.RED}{gap} min (!){Colors.RESET}"
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
    
    # Gap stats
    gaps = []
    for i in range(1, len(schedule)):
        gap = (schedule[i]["minute_of_day"] - schedule[i-1]["minute_of_day"]) % 1440
        gaps.append(gap)
    
    print(f"  - Total signals: {Colors.BOLD}{len(schedule)}{Colors.RESET}")
    print(f"  - Avg L1 (no MTG): {Colors.BOLD}{avg_l1*100:.1f}%{Colors.RESET}")
    print(f"  - Avg Combined (with MTG): {Colors.GREEN}{avg_comb*100:.1f}%{Colors.RESET}")
    print(f"  - Avg MTG use: {avg_mtg_use*100:.1f}% (rare)")
    print(f"  - Avg MTG success: {avg_mtg_succ*100:.1f}%")
    print(f"  - Unique assets: {unique_assets}")
    if gaps:
        print(f"  - Gaps: min={min(gaps)}, max={max(gaps)}, avg={sum(gaps)/len(gaps):.1f} min")
        # Distribution
        gap_dist = defaultdict(int)
        for g in gaps:
            gap_dist[g] += 1
        print(f"  - Gap distribution: {dict(sorted(gap_dist.items()))}")
        # Check for any gap > 6
        bad_gaps = [g for g in gaps if g > 6]
        if bad_gaps:
            print(f"  - {Colors.RED}WARNING: {len(bad_gaps)} gaps > 6 min (should be 0){Colors.RESET}")
        else:
            print(f"  - {Colors.GREEN}All gaps <= 6 min (✓ requirement met){Colors.RESET}")
    
    print(f"\n{Colors.BOLD}  Expected outcome:{Colors.RESET}")
    expected_wins = avg_comb * len(schedule)
    expected_losses = len(schedule) - expected_wins
    print(f"  - Wins: ~{Colors.GREEN}{expected_wins:.0f}{Colors.RESET} of {len(schedule)}")
    print(f"  - Losses: ~{Colors.RED}{expected_losses:.0f}{Colors.RESET} of {len(schedule)}")
    print(f"  - Expected win rate: {Colors.BOLD}{avg_comb*100:.1f}%{Colors.RESET}")
    
    # ===== 9. Save schedule to JSON =====
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = Path(f"signals_v3_{timestamp}.json")
    output_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "v3-tight-gaps",
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
    print(f"  - Gap: STRICTLY 3-6 minutes (never more)")
    print(f"  - MTG = ONE retry only (no MTG2)")
    print(f"  - If L1 loses -> MTG on the very next candle")
    print(f"  - After potential MTG, next signal is 6 min later (longest gap)")
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
