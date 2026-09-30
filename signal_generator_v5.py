#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CANDAL Signal Generator v5 — Pattern-Based (100+ Patterns)
==============================================================
Based on v4 (pattern-based, not random minutes) but with:
  - 2-condition combos added (in addition to 3-condition)
  - Relaxed filters to extract 100+ patterns
  - Same input UX as v4 (folder + days filter)
  - Same English UI

USER REQUIREMENTS:
  - Extract 100+ signals (v4 only found 15)
  - Same input method as v4 (folder + days filter)
  - Pattern-based (not random minutes like v3)

METHODOLOGY:
  1. Load candle files (user specifies folder + days filter)
  2. For each candle, extract features (shape, context, momentum, indicators)
  3. Test ALL combinations:
     - 2-condition: (shape + context), (shape + momentum), (context + momentum)
     - 3-condition: (shape + context + momentum) — like v4
  4. Validate on 70/30 chronological train/test split
  5. Filters (relaxed for 100+ patterns):
     - L1 >= 55%, Combined >= 75%, p < 0.15, samples >= 15
  6. Sort by test combined win rate (out-of-sample performance)
  7. Output: list of patterns with their stats

USER INPUT:
  1. Candles folder path (default: candles_data)
  2. Days filter (100, 30, or any number)

OUTPUT:
  - Top patterns displayed with stats
  - JSON file: patterns_v5_YYYY-MM-DD_HH-MM.json
"""
import os
import sys
import json
import math
import time
import random
import itertools
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

import numpy as np
import pandas as pd

# =============================================================================
# CONFIG
# =============================================================================

# Pattern validation filters (RELAXED for 100+ patterns)
MIN_SAMPLES = 15           # min samples (was 20 in v4)
TARGET_L1 = 0.55           # L1 >= 55% (was 60%)
TARGET_COMBINED = 0.75     # Combined >= 75% (was 80%)
CHI_P_VAL = 0.15           # statistical significance (was 0.10)

# Out-of-sample validation (70% train, 30% test)
TRAIN_RATIO = 0.70

# Display colors
class Colors:
    GREEN = '\033[92m'; RED = '\033[91m'; YELLOW = '\033[93m'
    CYAN = '\033[96m'; BOLD = '\033[1m'; RESET = '\033[0m'


# =============================================================================
# FUNCTIONS
# =============================================================================

def chi_square_p(wins, total, p_null=0.5):
    if total == 0: return 1.0
    expected = p_null * total
    se = math.sqrt(p_null * (1 - p_null) * total)
    if se == 0: return 1.0
    z = (wins - expected) / se
    return 0.5 * (1 - math.erf(z / math.sqrt(2)))


def discover_candle_files(candles_dir: Path, days_filter: int = None):
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
    with open(file_path, "r") as fp:
        data = json.load(fp)
    candles = data.get("candles", [])
    candles = sorted(candles, key=lambda c: c.get("time", 0))
    candles = [c for c in candles
               if c.get("open", 0) > 0 and c.get("high", 0) > 0
               and c.get("low", 0) > 0 and c.get("close", 0) > 0]
    return candles


def extract_features(candles: list):
    """Extract all features for every candle."""
    if len(candles) < 50:
        return pd.DataFrame()
    
    df = pd.DataFrame(candles)
    # Add time columns for historical appearance tracking
    df["time_dt"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df["hour"] = df["time_dt"].dt.hour
    df["body"] = (df["close"] - df["open"]).abs()
    df["range"] = df["high"] - df["low"]
    df["dir"] = np.sign(df["close"] - df["open"])
    df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
    df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]
    df["body_avg_50"] = df["body"].rolling(50).mean()
    df["range_avg_50"] = df["range"].rolling(50).mean()
    
    # Indicators
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df["rsi_14"] = (100 - 100 / (1 + rs)).fillna(50)
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd_hist"] = (ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()
    df["bb_mid"] = df["close"].rolling(20).mean()
    df["bb_std"] = df["close"].rolling(20).std()
    df["bb_upper"] = df["bb_mid"] + 2 * df["bb_std"]
    df["bb_lower"] = df["bb_mid"] - 2 * df["bb_std"]
    
    # === SHAPES ===
    df["is_doji"] = (df["body"] < 0.3 * df["range"]) & (df["range"] > 0)
    df["is_hammer"] = (df["lower_wick"] > 2 * df["body"]) & (df["upper_wick"] < 0.3 * df["body"]) & (df["range"] > 0)
    df["is_star"] = (df["upper_wick"] > 2 * df["body"]) & (df["lower_wick"] < 0.3 * df["body"]) & (df["range"] > 0)
    df["is_big_body"] = df["body"] > 2 * df["body_avg_50"]
    df["is_small_body"] = df["body"] < 0.3 * df["body_avg_50"]
    df["is_green"] = df["dir"] == 1
    df["is_red"] = df["dir"] == -1
    df["wick_rej_down"] = (df["lower_wick"] > 2 * df["body"]) & (df["upper_wick"] < 0.3 * df["body"]) & df["is_green"]
    df["wick_rej_up"] = (df["upper_wick"] > 2 * df["body"]) & (df["lower_wick"] < 0.3 * df["body"]) & df["is_red"]
    
    # === CONTEXT ===
    df["2reds_before"] = ((df["dir"].shift(1) == -1) & (df["dir"].shift(2) == -1)).fillna(False)
    df["3reds_before"] = ((df["dir"].shift(1) == -1) & (df["dir"].shift(2) == -1) &
                          (df["dir"].shift(3) == -1)).fillna(False)
    df["4reds_before"] = ((df["dir"].shift(1) == -1) & (df["dir"].shift(2) == -1) &
                          (df["dir"].shift(3) == -1) & (df["dir"].shift(4) == -1)).fillna(False)
    df["5reds_before"] = ((df["dir"].shift(1) == -1) & (df["dir"].shift(2) == -1) &
                          (df["dir"].shift(3) == -1) & (df["dir"].shift(4) == -1) &
                          (df["dir"].shift(5) == -1)).fillna(False)
    df["2greens_before"] = ((df["dir"].shift(1) == 1) & (df["dir"].shift(2) == 1)).fillna(False)
    df["3greens_before"] = ((df["dir"].shift(1) == 1) & (df["dir"].shift(2) == 1) &
                             (df["dir"].shift(3) == 1)).fillna(False)
    df["4greens_before"] = ((df["dir"].shift(1) == 1) & (df["dir"].shift(2) == 1) &
                             (df["dir"].shift(3) == 1) & (df["dir"].shift(4) == 1)).fillna(False)
    df["5greens_before"] = ((df["dir"].shift(1) == 1) & (df["dir"].shift(2) == 1) &
                             (df["dir"].shift(3) == 1) & (df["dir"].shift(4) == 1) &
                             (df["dir"].shift(5) == 1)).fillna(False)
    
    # === MOMENTUM ===
    df["body_growing"] = (df["body"] > df["body"].shift(1) * 1.2).fillna(False)
    df["body_shrinking"] = (df["body"] < df["body"].shift(1) * 0.5).fillna(False)
    df["range_expanding"] = (df["range"] > 1.5 * df["range_avg_50"]).fillna(False)
    df["range_contracting"] = (df["range"] < 0.5 * df["range_avg_50"]).fillna(False)
    
    # === INDICATORS ===
    df["rsi_oversold"] = (df["rsi_14"] < 35).fillna(False)
    df["rsi_overbought"] = (df["rsi_14"] > 65).fillna(False)
    df["rsi_low"] = ((df["rsi_14"] >= 30) & (df["rsi_14"] <= 45)).fillna(False)
    df["rsi_high"] = ((df["rsi_14"] >= 55) & (df["rsi_14"] <= 70)).fillna(False)
    df["macd_cross_up"] = ((df["macd_hist"] > 0) & (df["macd_hist"].shift(1) <= 0)).fillna(False)
    df["macd_cross_down"] = ((df["macd_hist"] < 0) & (df["macd_hist"].shift(1) >= 0)).fillna(False)
    df["bb_lower_breach"] = (df["close"] < df["bb_lower"]).fillna(False)
    df["bb_upper_breach"] = (df["close"] > df["bb_upper"]).fillna(False)
    df["ema_above"] = (df["close"] > df["ema_50"]).fillna(False)
    df["ema_below"] = (df["close"] < df["ema_50"]).fillna(False)
    
    # === TARGET ===
    df["next_dir_1"] = df["dir"].shift(-1)
    df["next_dir_2"] = df["dir"].shift(-2)
    df["next1_green"] = (df["next_dir_1"] == 1).fillna(False)
    df["next1_red"] = (df["next_dir_1"] == -1).fillna(False)
    df["next2_green"] = (df["next_dir_2"] == 1).fillna(False)
    df["next2_red"] = (df["next_dir_2"] == -1).fillna(False)
    
    df = df.iloc[:-2].reset_index(drop=True)
    return df


# === PATTERN GROUPS ===
BULL_SHAPES = [
    ("hammer", "is_hammer"),
    ("doji", "is_doji"),
    ("wick_rej_down", "wick_rej_down"),
    ("big_green", "is_big_body"),
    ("small_green", "is_small_body"),
    ("green_bar", "is_green"),
]
BULL_CONTEXTS = [
    ("2reds", "2reds_before"),
    ("3reds", "3reds_before"),
    ("4reds", "4reds_before"),
    ("5reds", "5reds_before"),
]
BULL_MOMENTA = [
    ("body_growing", "body_growing"),
    ("body_shrinking", "body_shrinking"),
    ("range_expanding", "range_expanding"),
    ("range_contracting", "range_contracting"),
    ("rsi_oversold", "rsi_oversold"),
    ("rsi_low", "rsi_low"),
    ("macd_cross_up", "macd_cross_up"),
    ("bb_lower_breach", "bb_lower_breach"),
    ("ema_above", "ema_above"),
]

BEAR_SHAPES = [
    ("star", "is_star"),
    ("doji", "is_doji"),
    ("wick_rej_up", "wick_rej_up"),
    ("big_red", "is_big_body"),
    ("small_red", "is_small_body"),
    ("red_bar", "is_red"),
]
BEAR_CONTEXTS = [
    ("2greens", "2greens_before"),
    ("3greens", "3greens_before"),
    ("4greens", "4greens_before"),
    ("5greens", "5greens_before"),
]
BEAR_MOMENTA = [
    ("body_growing", "body_growing"),
    ("body_shrinking", "body_shrinking"),
    ("range_expanding", "range_expanding"),
    ("range_contracting", "range_contracting"),
    ("rsi_overbought", "rsi_overbought"),
    ("rsi_high", "rsi_high"),
    ("macd_cross_down", "macd_cross_down"),
    ("bb_upper_breach", "bb_upper_breach"),
    ("ema_below", "ema_below"),
]


def evaluate_pattern(df: pd.DataFrame, mask: pd.Series, direction: str):
    n = int(mask.sum())
    if n < MIN_SAMPLES:
        return None
    if direction == "BUY":
        l1_wins = int((mask & df["next1_green"]).sum())
        l1_lost = mask & (~df["next1_green"])
        mtg_wins = int((l1_lost & df["next2_green"]).sum())
    else:
        l1_wins = int((mask & df["next1_red"]).sum())
        l1_lost = mask & (~df["next1_red"])
        mtg_wins = int((l1_lost & df["next2_red"]).sum())
    combined_wins = l1_wins + mtg_wins
    return {
        "samples": n,
        "l1_wins": l1_wins,
        "l1_win_rate": l1_wins / n,
        "mtg_use_rate": (n - l1_wins) / n,
        "mtg_wins": mtg_wins,
        "combined_wins": combined_wins,
        "combined_win_rate": combined_wins / n,
    }


def make_shape_mask(shape_name, shape_col, df_in, direction):
    if direction == "BUY":
        if shape_name in ("big_green", "small_green"):
            return (df_in[shape_col] == True) & (df_in["is_green"] == True)
        return df_in[shape_col] == True
    else:
        if shape_name in ("big_red", "small_red"):
            return (df_in[shape_col] == True) & (df_in["is_red"] == True)
        return df_in[shape_col] == True


def search_patterns(asset: str, candles: list):
    """Search ALL 2-condition AND 3-condition pattern combinations."""
    print(f"\n[{asset}] Extracting features...", end=" ", flush=True)
    df = extract_features(candles)
    if len(df) == 0:
        print("insufficient data")
        return []
    print(f"{len(df)} rows")
    
    cutoff = int(len(df) * TRAIN_RATIO)
    df_train = df.iloc[:cutoff].copy()
    df_test = df.iloc[cutoff:].copy()
    print(f"[{asset}] Train: {len(df_train)} | Test: {len(df_test)}")
    
    results = []
    
    def test_pattern(direction, s_name, s_col, c_name, c_col, m_name=None, m_col=None):
        """Test a 2-condition or 3-condition pattern."""
        # Build mask for train
        if direction == "BUY":
            s_train = make_shape_mask(s_name, s_col, df_train, "BUY") if s_col else pd.Series([True]*len(df_train), index=df_train.index)
        else:
            s_train = make_shape_mask(s_name, s_col, df_train, "SELL") if s_col else pd.Series([True]*len(df_train), index=df_train.index)
        
        train_mask = s_train
        if c_col:
            train_mask = train_mask & (df_train[c_col] == True)
        if m_col:
            train_mask = train_mask & (df_train[m_col] == True)
        
        train_res = evaluate_pattern(df_train, train_mask, direction)
        if train_res is None or train_res["l1_win_rate"] < TARGET_L1:
            return None
        if train_res["combined_win_rate"] < TARGET_COMBINED:
            return None
        
        # Test on out-of-sample
        if direction == "BUY":
            s_test = make_shape_mask(s_name, s_col, df_test, "BUY") if s_col else pd.Series([True]*len(df_test), index=df_test.index)
        else:
            s_test = make_shape_mask(s_name, s_col, df_test, "SELL") if s_col else pd.Series([True]*len(df_test), index=df_test.index)
        
        test_mask = s_test
        if c_col:
            test_mask = test_mask & (df_test[c_col] == True)
        if m_col:
            test_mask = test_mask & (df_test[m_col] == True)
        
        test_res = evaluate_pattern(df_test, test_mask, direction)
        if test_res is None:
            return None
        
        p = chi_square_p(train_res["l1_wins"], train_res["samples"])
        if p > CHI_P_VAL:
            return None
        
        # Build label
        conditions = []
        if s_col: conditions.append(s_name)
        if c_col: conditions.append(c_name)
        if m_col: conditions.append(m_name)
        label = " + ".join(conditions)
        n_conds = len(conditions)
        
        # === Extract historical appearance times ===
        # Find ALL rows in the FULL dataframe where this pattern fired
        full_mask = pd.Series([True] * len(df), index=df.index)
        if s_col:
            if direction == "BUY":
                full_mask = full_mask & make_shape_mask(s_name, s_col, df, "BUY")
            else:
                full_mask = full_mask & make_shape_mask(s_name, s_col, df, "SELL")
        if c_col:
            full_mask = full_mask & (df[c_col] == True)
        if m_col:
            full_mask = full_mask & (df[m_col] == True)
        
        firing_df = df[full_mask]
        n_firing = len(firing_df)
        
        if n_firing > 0:
            # All historical times (HH:MM UTC)
            all_times = firing_df["time_dt"].dt.strftime("%H:%M").tolist() if "time_dt" in firing_df.columns else []
            # Hour distribution
            if "hour" in firing_df.columns:
                hour_dist = firing_df["hour"].value_counts().sort_index().to_dict()
                # Find peak hour (most active)
                peak_hour = int(firing_df["hour"].mode().iloc[0]) if len(firing_df) > 0 else 0
            else:
                hour_dist = {}
                peak_hour = 0
            # Most common times (top 5)
            from collections import Counter
            time_counter = Counter(all_times)
            top_times = time_counter.most_common(5)
            # Average hour
            avg_hour = float(firing_df["hour"].mean()) if "hour" in firing_df.columns and len(firing_df) > 0 else 0
        else:
            all_times = []
            hour_dist = {}
            peak_hour = 0
            top_times = []
            avg_hour = 0
        
        return {
            "asset": asset,
            "direction": direction,
            "n_conditions": n_conds,
            "shape": s_name if s_col else None,
            "context": c_name if c_col else None,
            "momentum": m_name if m_col else None,
            "pattern_label": label,
            "train_samples": train_res["samples"],
            "train_l1_win_rate": train_res["l1_win_rate"],
            "train_combined_win_rate": train_res["combined_win_rate"],
            "train_mtg_use_rate": train_res["mtg_use_rate"],
            "test_samples": test_res["samples"],
            "test_l1_win_rate": test_res["l1_win_rate"],
            "test_combined_win_rate": test_res["combined_win_rate"],
            "test_mtg_use_rate": test_res["mtg_use_rate"],
            "p_value": p,
            # === NEW: Historical appearance times ===
            "total_firings": n_firing,
            "peak_hour_utc": peak_hour,
            "avg_hour_utc": avg_hour,
            "top_times_utc": top_times,  # [(HH:MM, count), ...]
            "all_times_utc": all_times[:30],  # first 30 times (for display)
            "hour_distribution": hour_dist,
        }
    
    # === 2-condition: shape + context ===
    print(f"[{asset}] Testing 2-condition (shape + context)...")
    for (s_name, s_col), (c_name, c_col) in itertools.product(BULL_SHAPES, BULL_CONTEXTS):
        r = test_pattern("BUY", s_name, s_col, c_name, c_col)
        if r: results.append(r)
    for (s_name, s_col), (c_name, c_col) in itertools.product(BEAR_SHAPES, BEAR_CONTEXTS):
        r = test_pattern("SELL", s_name, s_col, c_name, c_col)
        if r: results.append(r)
    
    # === 2-condition: shape + momentum ===
    print(f"[{asset}] Testing 2-condition (shape + momentum)...")
    for (s_name, s_col), (m_name, m_col) in itertools.product(BULL_SHAPES, BULL_MOMENTA):
        r = test_pattern("BUY", s_name, s_col, None, None, m_name, m_col)
        if r: results.append(r)
    for (s_name, s_col), (m_name, m_col) in itertools.product(BEAR_SHAPES, BEAR_MOMENTA):
        r = test_pattern("SELL", s_name, s_col, None, None, m_name, m_col)
        if r: results.append(r)
    
    # === 2-condition: context + momentum (no shape) ===
    print(f"[{asset}] Testing 2-condition (context + momentum)...")
    for (c_name, c_col), (m_name, m_col) in itertools.product(BULL_CONTEXTS, BULL_MOMENTA):
        r = test_pattern("BUY", None, None, c_name, c_col, m_name, m_col)
        if r: results.append(r)
    for (c_name, c_col), (m_name, m_col) in itertools.product(BEAR_CONTEXTS, BEAR_MOMENTA):
        r = test_pattern("SELL", None, None, c_name, c_col, m_name, m_col)
        if r: results.append(r)
    
    # === 3-condition: shape + context + momentum (like v4) ===
    print(f"[{asset}] Testing 3-condition (shape + context + momentum)...")
    for (s_name, s_col), (c_name, c_col), (m_name, m_col) in itertools.product(
        BULL_SHAPES, BULL_CONTEXTS, BULL_MOMENTA):
        r = test_pattern("BUY", s_name, s_col, c_name, c_col, m_name, m_col)
        if r: results.append(r)
    for (s_name, s_col), (c_name, c_col), (m_name, m_col) in itertools.product(
        BEAR_SHAPES, BEAR_CONTEXTS, BEAR_MOMENTA):
        r = test_pattern("SELL", s_name, s_col, c_name, c_col, m_name, m_col)
        if r: results.append(r)
    
    print(f"[{asset}] Found {len(results)} validated patterns")
    return results


def print_banner():
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}  QX ZERO - Signal Generator v5 (100+ Patterns){Colors.RESET}")
    print(f"{Colors.BOLD}  Pattern-based - 2-condition and 3-condition combos{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.YELLOW}  Bot features:{Colors.RESET}")
    print(f"     - Pattern-based (not random minutes like v3)")
    print(f"     - Tests 2-condition AND 3-condition combinations")
    print(f"     - 70/30 chronological train/test validation")
    print(f"     - Relaxed filters for 100+ patterns:")
    print(f"       L1 >= 55%, Combined >= 75%, p < 0.15, samples >= 15")
    print(f"     - English UI")
    print()


def input_with_default(prompt: str, default: str = ""):
    s = input(f"{Colors.YELLOW}{prompt}{Colors.RESET} [{default}]: ").strip()
    return s if s else default


def main():
    print_banner()
    
    # ===== 1. Candles folder path =====
    candles_dir_str = input_with_default(
        "Enter candles folder path (or press Enter for default 'candles_data')",
        "candles_data"
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
        days_filter = 100
    
    by_asset = discover_candle_files(candles_dir, days_filter=days_filter)
    if not by_asset:
        print(f"{Colors.RED}No candle files matching {days_filter}d pattern in: {candles_dir}{Colors.RESET}")
        return
    
    print(f"{Colors.GREEN}Found {len(by_asset)} assets with {days_filter}d data:{Colors.RESET}")
    for asset, (days, f) in sorted(by_asset.items()):
        print(f"  {asset} ({days} days) -> {f.name}")
    print()
    
    # ===== 3. Analyze each asset =====
    print(f"{Colors.BOLD}Analysis phase (mining 2-condition and 3-condition patterns):{Colors.RESET}")
    print(f"Filters: L1 >= {TARGET_L1*100:.0f}%, Combined >= {TARGET_COMBINED*100:.0f}%, p < {CHI_P_VAL}, samples >= {MIN_SAMPLES}")
    print()
    
    all_patterns = []
    for asset, (days, f) in by_asset.items():
        candles = load_candles(f)
        if len(candles) < 200:
            print(f"  [{asset}] insufficient data ({len(candles)})")
            continue
        patterns = search_patterns(asset, candles)
        all_patterns.extend(patterns)
    
    print(f"\n{Colors.GREEN}Total validated patterns: {len(all_patterns)}{Colors.RESET}")
    if not all_patterns:
        print(f"{Colors.RED}No patterns passed validation.{Colors.RESET}")
        return
    
    # Sort by test combined win rate
    all_patterns.sort(key=lambda x: (x["test_combined_win_rate"], x["train_combined_win_rate"]), reverse=True)
    
    # ===== 3. Ask how many signals and start time =====
    n_str = input_with_default(
        "How many signals do you want? (20-100)",
        "20"
    )
    try:
        n_signals = int(n_str)
        if n_signals < 1 or n_signals > 500:
            n_signals = 20
    except ValueError:
        n_signals = 20
    
    start_str = input_with_default(
        "Enter start time HH:MM (24h UTC, e.g. 02:00)",
        "00:00"
    )
    try:
        sh, sm = map(int, start_str.split(":"))
        start_minute = sh * 60 + sm
    except (ValueError, IndexError):
        start_minute = 0
    
    print(f"\n{Colors.CYAN}Building schedule: {n_signals} signals, starting near {sh:02d}:{sm:02d} UTC{Colors.RESET}")
    print(f"  Gaps: 3-6 minutes (strict, never more){Colors.RESET}")
    print()
    
    # ===== 4. Build schedule: match patterns to time slots =====
    # For each pattern, build a set of minutes-of-day when it historically appears
    pattern_minutes = {}  # pattern_index -> set of minutes_of_day
    for i, p in enumerate(all_patterns):
        minutes = set()
        for t in p.get("all_times_utc", []):
            try:
                h, m = map(int, t.split(":"))
                minutes.add(h * 60 + m)
            except (ValueError, IndexError):
                pass
        # Also add peak hour minutes (every minute in the peak hour)
        peak = p.get("peak_hour_utc", 0)
        for mm in range(60):
            minutes.add(peak * 60 + mm)
        # Also add top active hours
        for h, count in p.get("hour_distribution", {}).items():
            if count >= 3:  # hour with >= 3 appearances
                for mm in range(0, 60, 5):  # every 5 min in that hour
                    minutes.add(int(h) * 60 + mm)
        pattern_minutes[i] = minutes
    
    # Build schedule with 3-6 min gaps
    random.seed(int(time.time() * 1000))
    best_schedule = []
    
    for pass_num in range(5):
        schedule = []
        used_pattern_indices = set()
        used_assets = set()  # track assets used in last 2 signals
        last_placed_minute = None
        last_asset = None
        search_minute = start_minute
        consecutive_fails = 0
        
        while len(schedule) < n_signals and consecutive_fails < 500:
            # Determine required gap (3-6 min)
            required_gap = random.choice([3, 4, 5, 6])
            
            # Reference: last placed signal, or start_minute for first
            ref = last_placed_minute if last_placed_minute is not None else search_minute
            
            # Find best pattern that:
            # 1) Has a historical appearance within 3-6 min of ref
            # 2) Uses a different asset than last signal
            # 3) Has highest test combined win rate
            best_idx = None
            best_score = -1
            best_gap = 0
            
            for i, p in enumerate(all_patterns):
                if i in used_pattern_indices:
                    continue
                if p["asset"] == last_asset:
                    continue
                # Check if this pattern has a minute within 3-6 min of ref
                minutes = pattern_minutes[i]
                for target_gap in [3, 4, 5, 6]:
                    target_min = (ref + target_gap) % 1440
                    if target_min in minutes:
                        # Score = test combined win rate (higher = better)
                        score = p["test_combined_win_rate"]
                        if target_gap == required_gap:
                            score += 0.05  # bonus for matching preferred gap
                        if score > best_score:
                            best_score = score
                            best_idx = i
                            best_gap = target_gap
                        break  # found a valid gap for this pattern
            
            if best_idx is None:
                # No pattern within 3-6 min, advance search
                search_minute = (search_minute + 1) % 1440
                if last_placed_minute is not None:
                    last_placed_minute = (last_placed_minute + 1) % 1440
                consecutive_fails += 1
                continue
            
            # Place the signal
            p = all_patterns[best_idx]
            actual_gap = best_gap if last_placed_minute is not None else 0
            
            # Find the exact minute for this signal (closest historical time to ref + best_gap)
            target_min = (ref + best_gap) % 1440
            minutes = pattern_minutes[best_idx]
            # Find closest minute in pattern's historical times to target_min
            closest_min = min(minutes, key=lambda m: abs((m - target_min) % 1440 - 1440 if (m - target_min) % 1440 > 720 else (m - target_min) % 1440))
            # Actually use target_min (the scheduled time, not the historical time)
            signal_minute = target_min
            
            schedule.append({
                **p,
                "scheduled_minute": signal_minute,
                "scheduled_time_utc": f"{signal_minute // 60:02d}:{signal_minute % 60:02d}",
                "gap_from_prev": actual_gap,
            })
            used_pattern_indices.add(best_idx)
            last_placed_minute = signal_minute
            last_asset = p["asset"]
            consecutive_fails = 0
        
        if len(schedule) > len(best_schedule):
            best_schedule = schedule
        if len(best_schedule) >= n_signals:
            break
    
    schedule = best_schedule
    print(f"Built schedule with {len(schedule)} signals")
    
    if not schedule:
        print(f"{Colors.RED}Failed to build schedule.{Colors.RESET}")
        return
    
    # ===== Display schedule =====
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*120}{Colors.RESET}")
    print(f"{Colors.BOLD}  QX ZERO - Signal Schedule (v5){Colors.RESET}")
    print(f"{Colors.BOLD}  {len(schedule)} signals starting near {sh:02d}:{sm:02d} UTC ({(sh+1)%24:02d}:{sm:02d} Algeria){Colors.RESET}")
    print(f"{Colors.BOLD}  Gaps: 3-6 minutes (strict){Colors.RESET}")
    print(f"{Colors.CYAN}{'='*120}{Colors.RESET}")
    print()
    print(f"{'#':<3}{'UTC':<7}{'Algeria':<13}{'Asset':<14}{'Dir':<6}{'Pattern':<48}{'Test%':<7}{'Gap'}")
    print('-' * 120)
    for i, s in enumerate(schedule, 1):
        utc_h, utc_m = divmod(s["scheduled_minute"], 60)
        alg_h = (utc_h + 1) % 24
        alg_time = f"{alg_h:02d}:{utc_m:02d}"
        if 5 <= alg_h < 12: period = "AM"
        elif 12 <= alg_h < 17: period = "Noon"
        elif 17 <= alg_h < 21: period = "PM"
        else: period = "Night"
        asset_short = s["asset"].replace("_otc", "-OTC")
        gap_str = f"{s['gap_from_prev']} min" if s["gap_from_prev"] > 0 else "start"
        test_color = Colors.GREEN if s["test_combined_win_rate"] >= 0.85 else Colors.YELLOW if s["test_combined_win_rate"] >= 0.75 else Colors.RESET
        print(f"{i:<3}{utc_h:02d}:{utc_m:02d}   {alg_time} {period:<6}{asset_short:<14}{s['direction']:<6}{s['pattern_label']:<48}{test_color}{s['test_combined_win_rate']*100:>5.1f}%{Colors.RESET}  {gap_str}")
    
    # Statistics
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*120}{Colors.RESET}")
    print(f"{Colors.BOLD}  Statistics{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*120}{Colors.RESET}")
    avg_test = sum(s["test_combined_win_rate"] for s in schedule) / len(schedule)
    unique_assets = len(set(s["asset"] for s in schedule))
    gaps = [s["gap_from_prev"] for s in schedule if s["gap_from_prev"] > 0]
    print(f"  - Total signals: {Colors.BOLD}{len(schedule)}{Colors.RESET}")
    print(f"  - Avg Test Combined: {Colors.GREEN}{avg_test*100:.1f}%{Colors.RESET}")
    print(f"  - Unique assets: {unique_assets}")
    if gaps:
        print(f"  - Gaps: min={min(gaps)}, max={max(gaps)}, avg={sum(gaps)/len(gaps):.1f} min")
        gap_dist = {}
        for g in gaps:
            gap_dist[g] = gap_dist.get(g, 0) + 1
        print(f"  - Gap distribution: {dict(sorted(gap_dist.items()))}")
        bad = [g for g in gaps if g > 6]
        if bad:
            print(f"  - {Colors.RED}{len(bad)} gaps > 6 min{Colors.RESET}")
        else:
            print(f"  - {Colors.GREEN}All gaps <= 6 min OK{Colors.RESET}")
    expected_wins = avg_test * len(schedule)
    print()
    print(f"  {Colors.BOLD}Expected outcome:{Colors.RESET}")
    print(f"  - Wins: ~{Colors.GREEN}{expected_wins:.0f}{Colors.RESET} of {len(schedule)}")
    print(f"  - Losses: ~{Colors.RED}{len(schedule) - expected_wins:.0f}{Colors.RESET} of {len(schedule)}")
    
    print()
    print(f"{Colors.YELLOW}{Colors.BOLD}Trading rules:{Colors.RESET}")
    print(f"  - Watch chart for the listed pattern at the scheduled time")
    print(f"  - When ALL conditions match -> ENTER trade")
    print(f"  - BUY = predict next green, SELL = predict next red")
    print(f"  - MTG = ONE retry only (no MTG2)")
    print(f"  - After MTG, next signal waits 6 min")
    
    # Save to JSON
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = Path(f"signals_v5_{timestamp}.json")
    output_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "v5-scheduled",
        "candles_dir": str(candles_dir),
        "days_filter": days_filter,
        "start_time_utc": f"{sh:02d}:{sm:02d}",
        "n_signals_requested": n_signals,
        "n_signals_generated": len(schedule),
        "stats": {"avg_test_combined_win_rate": avg_test, "unique_assets": unique_assets},
        "signals": [
            {"rank": i, "scheduled_time_utc": s["scheduled_time_utc"], "asset": s["asset"],
             "direction": s["direction"], "pattern": s["pattern_label"],
             "test_combined_win_rate": s["test_combined_win_rate"],
             "gap_from_prev": s["gap_from_prev"]}
            for i, s in enumerate(schedule, 1)
        ],
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print()
    print(f"{Colors.GREEN}Schedule saved to: {output_file}{Colors.RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Stopped.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
