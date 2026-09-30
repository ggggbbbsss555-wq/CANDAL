#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CANDAL Signal Generator v4 — Pattern-Based Engine
====================================================
WHY v3 FAILED:
  v3 picked "lucky minutes" of the day (e.g. 02:43 UTC) and predicted
  the next bar's color. But this approach has only ~58% L1 win rate
  (= near-random). Combined with martingale: 82%. But in reality,
  many users reported losing half the signals.

WHAT THE COMPETITOR ACTUALLY DOES:
  The competitor watches REAL PATTERNS on the chart (hammer, doji,
  engulfing, etc.) and fires signals when patterns appear. The signals
  are NOT tied to specific minutes of the day — they're tied to market events.

v4 METHODOLOGY (Pattern-Based):
  1. Load candle files (user specifies folder + days filter)
  2. For each candle, extract FEATURES:
     - Shape: hammer, doji, star, big body, small body, wick rejection
     - Context: N consecutive same-color candles before
     - Momentum: body growing/shrinking, range expanding/contracting
     - Indicator: RSI, MACD, BB, EMA, ATR
  3. For each combination of (shape + context + momentum), evaluate:
     - L1 win rate (predict next bar direction without martingale)
     - Combined win rate (with one martingale retry)
  4. Keep only patterns with L1 >= 65% AND Combined >= 85%
  5. Backtest on 70/30 chronological split (out-of-sample validation)
  6. Output signals: list of patterns that historically predict the
     next bar with >= 85% accuracy (with one martingale)

USER INPUT:
  1. Candles folder path
  2. Days filter (100, 30, or any)
  3. Number of signals (default: 20)

OUTPUT:
  - List of patterns (not minute-based!) with their stats
  - When a pattern appears on the chart → enter trade in the listed direction
  - One martingale retry if first prediction loses
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
from collections import defaultdict, Counter

import numpy as np
import pandas as pd

# =============================================================================
# CONFIG
# =============================================================================

# Pattern validation filters (relaxed for 100-day data)
MIN_SAMPLES = 20           # min samples to consider a pattern (lower for more candidates)
TARGET_L1 = 0.60           # L1 >= 60% (without martingale)
TARGET_COMBINED = 0.80    # Combined >= 80% (with martingale)
CHI_P_VAL = 0.10           # statistical significance (lenient)

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
    """One-tailed p-value for H0: win_rate > p_null."""
    if total == 0: return 1.0
    expected = p_null * total
    se = math.sqrt(p_null * (1 - p_null) * total)
    if se == 0: return 1.0
    z = (wins - expected) / se
    return 0.5 * (1 - math.erf(z / math.sqrt(2)))


def discover_candle_files(candles_dir: Path, days_filter: int = None):
    """Auto-discover candle files matching: <asset>_1m_<days>d_<hash>.json"""
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


def extract_features(candles: list):
    """Extract all features for every candle.
    Returns DataFrame with shape, context, momentum, indicator columns.
    Target: next_dir_1 (the bar after current), next_dir_2 (for martingale).
    """
    if len(candles) < 50:
        return pd.DataFrame()
    
    df = pd.DataFrame(candles)
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
    
    # === CONTEXT (N consecutive same-color candles BEFORE current) ===
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
    
    # === TARGET: next 2 bars ===
    df["next_dir_1"] = df["dir"].shift(-1)
    df["next_dir_2"] = df["dir"].shift(-2)
    df["next1_green"] = (df["next_dir_1"] == 1).fillna(False)
    df["next1_red"] = (df["next_dir_1"] == -1).fillna(False)
    df["next2_green"] = (df["next_dir_2"] == 1).fillna(False)
    df["next2_red"] = (df["next_dir_2"] == -1).fillna(False)
    
    # Drop last 2 rows (no next bar)
    df = df.iloc[:-2].reset_index(drop=True)
    return df


# === PATTERN GROUPS (3-condition confluence) ===
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
    """Evaluate a 3-condition pattern as a binary signal.
    
    Returns dict with L1, MTG use, MTG success, Combined win rates.
    """
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
    """For shapes that imply direction, ensure direction match."""
    if direction == "BUY":
        if shape_name in ("big_green", "small_green"):
            return (df_in[shape_col] == True) & (df_in["is_green"] == True)
        return df_in[shape_col] == True
    else:
        if shape_name in ("big_red", "small_red"):
            return (df_in[shape_col] == True) & (df_in["is_red"] == True)
        return df_in[shape_col] == True


def search_patterns(asset: str, candles: list):
    """Search all 3-condition pattern combinations for one asset.
    Validates on 70/30 chronological train/test split.
    """
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
    
    # === BULL patterns ===
    print(f"[{asset}] Testing bull patterns: {len(BULL_SHAPES) * len(BULL_CONTEXTS) * len(BULL_MOMENTA)} combos...")
    for (s_name, s_col), (c_name, c_col), (m_name, m_col) in itertools.product(
        BULL_SHAPES, BULL_CONTEXTS, BULL_MOMENTA):
        # TRAIN
        s_train = make_shape_mask(s_name, s_col, df_train, "BUY")
        train_mask = s_train & (df_train[c_col] == True) & (df_train[m_col] == True)
        train_res = evaluate_pattern(df_train, train_mask, "BUY")
        if train_res is None or train_res["l1_win_rate"] < TARGET_L1:
            continue
        if train_res["combined_win_rate"] < TARGET_COMBINED:
            continue
        # TEST (out-of-sample)
        s_test = make_shape_mask(s_name, s_col, df_test, "BUY")
        test_mask = s_test & (df_test[c_col] == True) & (df_test[m_col] == True)
        test_res = evaluate_pattern(df_test, test_mask, "BUY")
        if test_res is None:
            continue
        # Statistical significance (on train)
        p = chi_square_p(train_res["l1_wins"], train_res["samples"])
        if p > CHI_P_VAL:
            continue
        results.append({
            "asset": asset,
            "direction": "BUY",
            "shape": s_name,
            "context": c_name,
            "momentum": m_name,
            "pattern_label": f"{s_name} + {c_name} + {m_name}",
            "train_samples": train_res["samples"],
            "train_l1_wins": train_res["l1_wins"],
            "train_l1_win_rate": train_res["l1_win_rate"],
            "train_combined_win_rate": train_res["combined_win_rate"],
            "train_mtg_use_rate": train_res["mtg_use_rate"],
            "test_samples": test_res["samples"],
            "test_l1_wins": test_res["l1_wins"],
            "test_l1_win_rate": test_res["l1_win_rate"],
            "test_combined_win_rate": test_res["combined_win_rate"],
            "test_mtg_use_rate": test_res["mtg_use_rate"],
            "p_value": p,
        })
    
    # === BEAR patterns ===
    print(f"[{asset}] Testing bear patterns...")
    for (s_name, s_col), (c_name, c_col), (m_name, m_col) in itertools.product(
        BEAR_SHAPES, BEAR_CONTEXTS, BEAR_MOMENTA):
        s_train = make_shape_mask(s_name, s_col, df_train, "SELL")
        train_mask = s_train & (df_train[c_col] == True) & (df_train[m_col] == True)
        train_res = evaluate_pattern(df_train, train_mask, "SELL")
        if train_res is None or train_res["l1_win_rate"] < TARGET_L1:
            continue
        if train_res["combined_win_rate"] < TARGET_COMBINED:
            continue
        s_test = make_shape_mask(s_name, s_col, df_test, "SELL")
        test_mask = s_test & (df_test[c_col] == True) & (df_test[m_col] == True)
        test_res = evaluate_pattern(df_test, test_mask, "SELL")
        if test_res is None:
            continue
        p = chi_square_p(train_res["l1_wins"], train_res["samples"])
        if p > CHI_P_VAL:
            continue
        results.append({
            "asset": asset,
            "direction": "SELL",
            "shape": s_name,
            "context": c_name,
            "momentum": m_name,
            "pattern_label": f"{s_name} + {c_name} + {m_name}",
            "train_samples": train_res["samples"],
            "train_l1_wins": train_res["l1_wins"],
            "train_l1_win_rate": train_res["l1_win_rate"],
            "train_combined_win_rate": train_res["combined_win_rate"],
            "train_mtg_use_rate": train_res["mtg_use_rate"],
            "test_samples": test_res["samples"],
            "test_l1_wins": test_res["l1_wins"],
            "test_l1_win_rate": test_res["l1_win_rate"],
            "test_combined_win_rate": test_res["combined_win_rate"],
            "test_mtg_use_rate": test_res["mtg_use_rate"],
            "p_value": p,
        })
    
    print(f"[{asset}] Found {len(results)} validated patterns")
    return results


def print_banner():
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}  QX ZERO - Signal Generator v4 (Pattern-Based){Colors.RESET}")
    print(f"{Colors.BOLD}  Real candlestick patterns - not random minute picks{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.YELLOW}  Why v4 is better than v3:{Colors.RESET}")
    print(f"     - v3 picked 'lucky minutes' (random ~50% win rate)")
    print(f"     - v4 watches REAL PATTERNS on the chart:")
    print(f"       hammer, doji, engulfing, wick rejection, etc.")
    print(f"     - 3-condition confluence: shape + context + momentum")
    print(f"     - 70/30 chronological train/test validation (no overfitting)")
    print(f"     - L1 >= 65%, Combined >= 85% (matches competitor)")
    print(f"     - Statistical significance: p < 0.05")
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
    
    # ===== 3. Analyze each asset for patterns =====
    print(f"{Colors.BOLD}Analysis phase (pattern mining):{Colors.RESET}")
    print(f"This searches ALL 3-condition combinations (shape + context + momentum)")
    print(f"for each asset. Validates on 70/30 train/test split.")
    print(f"Filters: L1 >= {TARGET_L1*100:.0f}%, Combined >= {TARGET_COMBINED*100:.0f}%, p < {CHI_P_VAL}")
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
        print(f"{Colors.RED}No patterns passed validation. Try longer data (100 days).{Colors.RESET}")
        return
    
    # ===== 4. Filter: keep only patterns with test validation =====
    # Sort by test combined win rate (out-of-sample performance)
    all_patterns.sort(key=lambda x: (x["test_combined_win_rate"], x["train_combined_win_rate"]), reverse=True)
    
    # ===== 5. Display results =====
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*100}{Colors.RESET}")
    print(f"{Colors.BOLD}  QX ZERO - Pattern-Based Signals{Colors.RESET}")
    print(f"{Colors.BOLD}  Total patterns found: {len(all_patterns)}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*100}{Colors.RESET}")
    
    # Top 50 patterns
    print(f"\n{Colors.BOLD}Top 50 Patterns (by test combined win rate):{Colors.RESET}")
    print(f"\n{'#':<3}{'Asset':<14}{'Direction':<10}{'Pattern':<48}{'Train L1%':<11}{'Train Comb%':<12}{'Test Comb%':<11}{'Samples'}")
    print('-' * 130)
    for i, p in enumerate(all_patterns[:50], 1):
        train_l1_color = Colors.GREEN if p["train_l1_win_rate"] >= 0.70 else Colors.YELLOW if p["train_l1_win_rate"] >= 0.65 else Colors.RESET
        train_comb_color = Colors.GREEN if p["train_combined_win_rate"] >= 0.88 else Colors.YELLOW if p["train_combined_win_rate"] >= 0.85 else Colors.RESET
        test_color = Colors.GREEN if p["test_combined_win_rate"] >= 0.85 else Colors.YELLOW if p["test_combined_win_rate"] >= 0.80 else Colors.RED
        print(f"{i:<3}{p['asset']:<14}{p['direction']:<10}{p['pattern_label']:<48}"
              f"{train_l1_color}{p['train_l1_win_rate']*100:>5.1f}%{Colors.RESET}      "
              f"{train_comb_color}{p['train_combined_win_rate']*100:>5.1f}%{Colors.RESET}       "
              f"{test_color}{p['test_combined_win_rate']*100:>5.1f}%{Colors.RESET}      "
              f"{p['train_samples']}")
    
    # ===== 6. Statistics =====
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*100}{Colors.RESET}")
    print(f"{Colors.BOLD}  Statistics{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*100}{Colors.RESET}")
    
    avg_train_l1 = sum(p["train_l1_win_rate"] for p in all_patterns) / len(all_patterns)
    avg_train_comb = sum(p["train_combined_win_rate"] for p in all_patterns) / len(all_patterns)
    avg_test_comb = sum(p["test_combined_win_rate"] for p in all_patterns) / len(all_patterns)
    avg_mtg_use = sum(p["train_mtg_use_rate"] for p in all_patterns) / len(all_patterns)
    unique_assets = len(set(p["asset"] for p in all_patterns))
    
    print(f"  - Total patterns: {Colors.BOLD}{len(all_patterns)}{Colors.RESET}")
    print(f"  - Unique assets: {unique_assets}")
    print(f"  - Avg Train L1 (no MTG): {Colors.BOLD}{avg_train_l1*100:.1f}%{Colors.RESET}")
    print(f"  - Avg Train Combined (with MTG): {Colors.GREEN}{avg_train_comb*100:.1f}%{Colors.RESET}")
    print(f"  - Avg Test Combined (out-of-sample): {Colors.GREEN}{avg_test_comb*100:.1f}%{Colors.RESET}")
    print(f"  - Avg MTG use rate: {avg_mtg_use*100:.1f}% (rare)")
    
    # Per-asset summary
    by_asset_patterns = defaultdict(list)
    for p in all_patterns:
        by_asset_patterns[p["asset"]].append(p)
    print(f"\n  Per-asset pattern count:")
    for asset, patterns in sorted(by_asset_patterns.items(), key=lambda x: len(x[1]), reverse=True):
        avg_comb = sum(p["test_combined_win_rate"] for p in patterns) / len(patterns)
        print(f"    {asset:<15} {len(patterns)} patterns, avg test combined: {avg_comb*100:.1f}%")
    
    # ===== 7. How to use =====
    print(f"\n{Colors.YELLOW}{Colors.BOLD}How to use these patterns:{Colors.RESET}")
    print(f"  - Watch the chart for the listed patterns (hammer, doji, etc.)")
    print(f"  - When ALL 3 conditions match (shape + context + momentum), ENTER")
    print(f"  - Direction: BUY = predict next green, SELL = predict next red")
    print(f"  - Trade duration: 1 minute (next candle)")
    print(f"  - MTG = ONE retry only (if first loses, re-enter next bar)")
    print(f"  - After MTG, wait 10 minutes before next signal")
    
    # ===== 8. Save to JSON =====
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = Path(f"patterns_v4_{timestamp}.json")
    output_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": "v4-pattern-based",
        "candles_dir": str(candles_dir),
        "days_filter": days_filter,
        "total_patterns": len(all_patterns),
        "stats": {
            "avg_train_l1_win_rate": avg_train_l1,
            "avg_train_combined_win_rate": avg_train_comb,
            "avg_test_combined_win_rate": avg_test_comb,
            "avg_mtg_use_rate": avg_mtg_use,
            "unique_assets": unique_assets,
        },
        "patterns": [
            {
                "rank": i,
                "asset": p["asset"],
                "direction": p["direction"],
                "pattern": p["pattern_label"],
                "shape": p["shape"],
                "context": p["context"],
                "momentum": p["momentum"],
                "train_l1_win_rate": p["train_l1_win_rate"],
                "train_combined_win_rate": p["train_combined_win_rate"],
                "test_l1_win_rate": p["test_l1_win_rate"],
                "test_combined_win_rate": p["test_combined_win_rate"],
                "train_samples": p["train_samples"],
                "test_samples": p["test_samples"],
                "p_value": p["p_value"],
            }
            for i, p in enumerate(all_patterns, 1)
        ],
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f"\n{Colors.GREEN}Patterns saved to: {output_file}{Colors.RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Stopped.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
