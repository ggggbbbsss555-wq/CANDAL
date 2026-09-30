#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CANDAL Signal Generator — Advanced Binary Options Signal Bot
================================================================
يتحكم المستخدم في:
  1. مسار مجلد الشموع (candles_data)
  2. ساعة البدء (يبدأ من تلك الساعة تقريباً، ليس بالضبط)
  3. عدد الإشارات المطلوبة

الميزات:
  - يجد تلقائياً كل ملفات الشموع في المجلد (نفس أسماء المستودع)
  - يحلل كل عملة: يحسب L1, Combined, MTG use rate, MTG success rate
  - يطبّق فلترة عميقة (مستوحاة من تحليل بوت المنافس):
    * تجنّب الساعات السيئة (10, 16, 21, 23 UTC)
    * تجنّب العملات الضعيفة (BRLUSD)
    * تفضيل PUT عند التعادل
    * MTG success ≥ 55%
  - يبني جدول إشارات بفجوات 3-10 دقائق (تشويش)
  - يحسب التوقيت المحلي (UTC+1 للجزائر)
  - يطبع القائمة بصيغة جميلة

طريقة الاستخدام:
  python signal_generator.py
  
  ثم سيطلب منك:
    1. مسار مجلد الشموع (default: candles_data في نفس المجلد)
    2. ساعة البدء (HH:MM, 24h, UTC)
    3. عدد الإشارات (default: 20)

الإخراج:
  - قائمة الإشارات على الشاشة
  - ملف JSON يحفظ القائمة: signals_YYYY-MM-DD_HH-MM.json
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
# CONFIG (مستوحى من تحليل بوت المنافس — 998 إشارة)
# =============================================================================

# ساعات محددة للتجنب (نسبة خسائر > 15%)
AVOID_HOURS_UTC = [10, 16, 21, 23]

# عملات محددة للتجنب (نسبة خسائر > 14%)
AVOID_ASSETS = ["BRLUSD_otc"]  # 16.8% خسائر

# ساعات مميزة (نسبة خسائر < 10%) — تفضيل عند الاختيار
BEST_HOURS_UTC = [11, 17, 20, 15, 9, 18]

# عملات مميزة (نسبة خسائر < 10.5%) — تفضيل عند الاختيار
BEST_ASSETS = ["USDCOP_otc", "USDDZD_otc", "USDBDT_otc", "USDIDR_otc", "USDARS_otc"]

# فلاتر التحليل
MIN_SAMPLES = 80           # عينات كحد أدنى (80 يوم × 1)
TARGET_L1 = 0.58           # L1 ≥ 58% (بدون مارتنجال)
TARGET_COMBINED = 0.78     # Combined ≥ 78% (مع MTG)
CHI_P_VAL = 0.10           # أهمية إحصائية (متساهلة)
MAX_MTG_USE_RATE = 0.45    # MTG use ≤ 45%
MIN_MTG_SUCCESS = 0.55     # MTG success ≥ 55%

# إعدادات الجدول
GAP_MIN = 3               # أقل فجوة بين الإشارات (دقائق)
GAP_NORMAL_MAX = 6         # فجوة عادية (3-6 دقائق)
GAP_AFTER_MTG = 10        # فجوة كبيرة بعد MTG (10 دقائق)

# عرض الألوان
class Colors:
    GREEN = '\033[92m'; RED = '\033[91m'; YELLOW = '\033[93m'
    CYAN = '\033[96m'; BOLD = '\033[1m'; RESET = '\033[0m'


# =============================================================================
# FUNCTIONS
# =============================================================================

def chi_square_p(wins, total, p_null=0.5):
    """احسب p-value لاختبار فرضية أن نسبة الفوز > p_null."""
    if total == 0: return 1.0
    expected = p_null * total
    se = math.sqrt(p_null * (1 - p_null) * total)
    if se == 0: return 1.0
    z = (wins - expected) / se
    return 0.5 * (1 - math.erf(z / math.sqrt(2)))


def discover_candle_files(candles_dir: Path):
    """يجد تلقائياً كل ملفات الشموع في المجلد.
    
    يبحث عن أنماط مثل: <asset>_1m_<days>d_<hash>.json
    مثال: BRLUSD_otc_1m_100d_90c8207b.json
    
    إذا وُجدت ملفات متعددة لنفس العملة، يختار الأحدث/الأطول.
    """
    pattern = "*_1m_*d_*.json"
    files = sorted(candles_dir.glob(pattern))
    if not files:
        return {}
    
    by_asset = {}
    for f in files:
        try:
            # استخرج اسم العملة وعدد الأيام
            asset = f.name.split("_1m_")[0]
            days = int(f.name.split("_1m_")[1].split("d_")[0])
        except (IndexError, ValueError):
            continue
        if asset not in by_asset or days > by_asset[asset][0]:
            by_asset[asset] = (days, f)
    
    return by_asset


def load_candles(file_path: Path):
    """يحمل الشموع من ملف JSON."""
    with open(file_path, "r") as fp:
        data = json.load(fp)
    candles = data.get("candles", [])
    # ترتيب زمني + فلترة
    candles = sorted(candles, key=lambda c: c.get("time", 0))
    candles = [c for c in candles
               if c.get("open", 0) > 0 and c.get("high", 0) > 0
               and c.get("low", 0) > 0 and c.get("close", 0) > 0]
    return candles


def analyze_minute_patterns(asset: str, candles: list):
    """لكل دقيقة من اليوم (1440 دقيقة)، يحسب:
       - L1 win rate (بدون مارتنجال)
       - MTG use rate (كم مرة يحتاج MTG)
       - MTG success rate (نسبة نجاح MTG)
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
        
        # CALL: توقع شمعة خضراء تالية
        call_l1_wins = int((g["next_dir_1"] == 1).sum())
        call_l1_lost = g[g["next_dir_1"] != 1]
        call_mtg_wins = int((call_l1_lost["next_dir_2"] == 1).sum())
        call_combined = call_l1_wins + call_mtg_wins
        
        # PUT: توقع شمعة حمراء تالية
        put_l1_wins = int((g["next_dir_1"] == 0).sum())
        put_l1_lost = g[g["next_dir_1"] != 0]
        put_mtg_wins = int((put_l1_lost["next_dir_2"] == 0).sum())
        put_combined = put_l1_wins + put_mtg_wins
        
        # اختر الأفضل (تفضيل PUT عند التعادل)
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
    """يطبّق الفلاتر العميقة على إشارات العملة."""
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
    """يبني جدول الإشارات بفجوات 3-10 دقائق.
    
    - يبدأ من start_minute (تقريباً، ليس بالضبط)
    - فجوة عادية: 3-6 دقائق
    - فجوة بعد MTG (إذا L1 < 65%): 10 دقائق
    - لا يكرر نفس العملة في إشارتين متتاليتين
    """
    # رتّب حسب الوقت
    by_time = sorted(eligible_signals, key=lambda x: x["minute_of_day"])
    
    schedule = []
    used = set()  # (asset, minute) لمنع التكرار
    used_indices = set()
    current_minute = start_minute
    last_asset = None
    last_l1 = 1.0  # آخر L1 (1.0 = لا يحتاج MTG)
    
    attempts = 0
    max_attempts = n_signals * 100
    
    while len(schedule) < n_signals and attempts < max_attempts:
        attempts += 1
        
        # حدّد الفجوة المطلوبة
        if last_l1 < 0.65:
            required_gap = GAP_AFTER_MTG  # 10 دقائق بعد MTG
        else:
            required_gap = random.randint(GAP_MIN, GAP_NORMAL_MAX)  # 3-6 دقائق
        
        target_minute = (current_minute + required_gap) % 1440
        
        # ابحث عن أقرب إشارة لـ target_minute (±5 دقائق)
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
            # ابحث عن أي إشارة بعد target_minute (±30 دقيقة)
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
    """يحوّل دقيقة UTC إلى توقيت الجزائر (UTC+1)."""
    alg_minute = (utc_minute + 60) % 1440
    h, m = divmod(alg_minute, 60)
    if 5 <= h < 12: period = "صباحاً"
    elif 12 <= h < 17: period = "ظهراً"
    elif 17 <= h < 21: period = "مساءً"
    else: period = "ليلاً"
    return f"{h:02d}:{m:02d}", period


def print_banner():
    print(f"{Colors.CYAN}{Colors.BOLD}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}  💎 QX ZERO — Signal Generator (Advanced){Colors.RESET}")
    print(f"{Colors.BOLD}  بوت إشارات Binary Options — يعمل على بياناتك المحلية{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.YELLOW}  ✦ ميزات البوت:{Colors.RESET}")
    print(f"     • يجد تلقائياً كل ملفات الشموع في المجلد المحدد")
    print(f"     • يحلل كل عملة على 1440 دقيقة من اليوم")
    print(f"     • يحسب L1, Combined, MTG use, MTG success")
    print(f"     • يطبّق فلترة عميقة (مستوحاة من تحليل بوت المنافس)")
    print(f"     • يبني جدول إشارات بفجوات 3-10 دقائق (تشويش)")
    print(f"     • يحسب التوقيت المحلي (UTC+1 للجزائر)")
    print()


def input_with_default(prompt: str, default: str = ""):
    """يقرأ إدخال المستخدم مع قيمة افتراضية."""
    s = input(f"{Colors.YELLOW}{prompt}{Colors.RESET} [{default}]: ").strip()
    return s if s else default


def main():
    print_banner()
    
    # ===== 1. مسار مجلد الشموع =====
    default_dir = "candles_data"
    candles_dir_str = input_with_default(
        "📂 أدخل مسار مجلد الشموع (أو اضغط Enter للمجلد الافتراضي 'candles_data')",
        default_dir
    )
    # إذا المسار نسبي، حوّله لمطلق بالنسبة لمجلد السكريبت
    candles_dir = Path(candles_dir_str)
    if not candles_dir.is_absolute():
        # ابحث أيضاً في مجلد السكريبت
        script_dir = Path(__file__).parent if "__file__" in globals() else Path.cwd()
        candidates = [candles_dir, script_dir / candles_dir, script_dir.parent / candles_dir]
        for c in candidates:
            if c.exists() and c.is_dir():
                candles_dir = c
                break
    
    print(f"\n{Colors.CYAN}🔍 البحث في: {candles_dir}{Colors.RESET}")
    by_asset = discover_candle_files(candles_dir)
    if not by_asset:
        print(f"{Colors.RED}✗ لم يتم العثور على ملفات شموع في: {candles_dir}{Colors.RESET}")
        print(f"  أنماط متوقعة: <asset>_1m_<days>d_<hash>.json")
        return
    
    print(f"{Colors.GREEN}✓ وجدت {len(by_asset)} عملة:{Colors.RESET}")
    for asset, (days, f) in sorted(by_asset.items()):
        print(f"  {asset} ({days} يوم) → {f.name}")
    print()
    
    # ===== 2. ساعة البدء =====
    start_time_str = input_with_default(
        "⏰ أدخل ساعة البدء (HH:MM بصيغة 24 ساعة UTC، مثل 20:00)",
        "00:00"
    )
    try:
        h, m = map(int, start_time_str.split(":"))
        start_minute = h * 60 + m
        if not (0 <= start_minute < 1440):
            raise ValueError
    except (ValueError, IndexError):
        print(f"{Colors.RED}✗ صيغة غير صحيحة. استخدم HH:MM (مثل 20:00){Colors.RESET}")
        return
    
    print(f"\n{Colors.CYAN}⏰ ساعة البدء المطلوبة: {h:02d}:{m:02d} UTC{Colors.RESET}")
    print(f"   (الجزائر UTC+1: {(h+1)%24:02d}:{m:02d})")
    print(f"   البوت سيبدأ البحث من هذه الساعة تقريباً (±5 دقائق){Colors.RESET}")
    print()
    
    # ===== 3. عدد الإشارات =====
    n_str = input_with_default(
        "🎯 كم عدد الإشارات التي تريدها؟ (20-40 موصى بها)",
        "20"
    )
    try:
        n_signals = int(n_str)
        if n_signals < 1 or n_signals > 200:
            print(f"{Colors.RED}✗ العدد يجب أن يكون بين 1 و 200{Colors.RESET}")
            return
    except ValueError:
        print(f"{Colors.RED}✗ أدخل رقماً صحيحاً{Colors.RESET}")
        return
    
    print(f"\n{Colors.CYAN}🎯 عدد الإشارات المطلوب: {n_signals}{Colors.RESET}")
    print()
    
    # ===== 4. تحليل كل عملة =====
    print(f"{Colors.BOLD}🔍 مرحلة التحليل:{Colors.RESET}")
    all_eligible = []
    for asset, (days, f) in by_asset.items():
        print(f"  [{asset}] تحليل {days} يوم...", end=" ", flush=True)
        candles = load_candles(f)
        if len(candles) < MIN_SAMPLES:
            print(f"{Colors.RED}بيانات غير كافية ({len(candles)}){Colors.RESET}")
            continue
        stats = analyze_minute_patterns(asset, candles)
        filtered = filter_signals(stats)
        all_eligible.extend(filtered)
        print(f"{Colors.GREEN}{len(filtered)} دقيقة صالحة{Colors.RESET}")
    
    print(f"\n{Colors.GREEN}✓ إجمالي الدقائق الصالحة: {len(all_eligible)}{Colors.RESET}")
    if not all_eligible:
        print(f"{Colors.RED}✗ لا توجد إشارات صالحة. جرّب بيانات أطول (100 يوم).{Colors.RESET}")
        return
    
    # ===== 5. بناء الجدول =====
    print(f"\n{Colors.BOLD}📋 مرحلة بناء الجدول:{Colors.RESET}")
    random.seed(int(time.time()))  # عشوائية حقيقية كل تشغيل
    schedule = build_schedule(all_eligible, start_minute, n_signals)
    
    if not schedule:
        print(f"{Colors.RED}✗ لم يتم بناء جدول. جرّب ساعة بدء مختلفة.{Colors.RESET}")
        return
    
    # ===== 6. عرض النتائج =====
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*100}{Colors.RESET}")
    print(f"{Colors.BOLD}  💎 QX ZERO — قائمة الإشارات{Colors.RESET}")
    print(f"{Colors.BOLD}  ⏰ تبدأ من {h:02d}:{m:02d} UTC (تقريباً) → {(h+1)%24:02d}:{m:02d} بتوقيت الجزائر{Colors.RESET}")
    print(f"{Colors.BOLD}  🎯 عدد الإشارات: {len(schedule)}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*100}{Colors.RESET}")
    
    print(f"\n{'#':<3}{'UTC':<7}{'الجزائر':<14}{'العملة':<14}{'الاتجاه':<10}{'L1%':<7}{'Comb%':<8}{'MTG Use':<9}{'الفجوة'}")
    print('-' * 100)
    
    prev_minute = None
    for i, s in enumerate(schedule, 1):
        utc_h, utc_m = divmod(s["minute_of_day"], 60)
        alg_time, period = utc_to_algeria(s["minute_of_day"])
        
        asset_short = s["asset"].replace("_otc", "-OTC")
        arrow = "🟢 CALL" if s["direction"] == "CALL" else "🔴 PUT"
        
        if prev_minute is not None:
            gap = (s["minute_of_day"] - prev_minute) % 1440
            gap_str = f"{gap} دقيقة"
        else:
            gap_str = "(البداية)"
        
        # لون حسب القوة
        if s["combined_win_rate"] >= 0.87:
            l1_color = Colors.GREEN
        elif s["combined_win_rate"] >= 0.83:
            l1_color = Colors.YELLOW
        else:
            l1_color = Colors.RESET
        
        print(f"{i:<3}{utc_h:02d}:{utc_m:02d}   {alg_time} {period:<7}{asset_short:<14}{arrow:<10}"
              f"{l1_color}{s['l1_win_rate']*100:>4.0f}%   {s['combined_win_rate']*100:>4.0f}%    {s['mtg_use_rate']*100:>4.0f}%      {gap_str}{Colors.RESET}")
        
        prev_minute = s["minute_of_day"]
    
    # ===== 7. الإحصائيات =====
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*100}{Colors.RESET}")
    print(f"{Colors.BOLD}  📊 الإحصائيات{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*100}{Colors.RESET}")
    
    avg_l1 = sum(s["l1_win_rate"] for s in schedule) / len(schedule)
    avg_comb = sum(s["combined_win_rate"] for s in schedule) / len(schedule)
    avg_mtg_use = sum(s["mtg_use_rate"] for s in schedule) / len(schedule)
    avg_mtg_succ = sum(s["mtg_success_rate"] for s in schedule) / len(schedule)
    unique_assets = len(set(s["asset"] for s in schedule))
    
    print(f"  • إجمالي الإشارات: {Colors.BOLD}{len(schedule)}{Colors.RESET}")
    print(f"  • متوسط L1 (بدون MTG): {Colors.BOLD}{avg_l1*100:.1f}%{Colors.RESET}")
    print(f"  • متوسط Combined (مع MTG): {Colors.GREEN}{avg_comb*100:.1f}%{Colors.RESET}")
    print(f"  • متوسط MTG use: {avg_mtg_use*100:.1f}% (نادر)")
    print(f"  • متوسط MTG success: {avg_mtg_succ*100:.1f}%")
    print(f"  • عملات مختلفة: {unique_assets}")
    
    print(f"\n{Colors.BOLD}  🎯 التوقع:{Colors.RESET}")
    expected_wins = avg_comb * len(schedule)
    expected_losses = len(schedule) - expected_wins
    print(f"  • رابحة: ~{Colors.GREEN}{expected_wins:.0f}{Colors.RESET} من {len(schedule)}")
    print(f"  • خاسرة: ~{Colors.RED}{expected_losses:.0f}{Colors.RESET} من {len(schedule)}")
    print(f"  • نسبة النجاح المتوقعة: {Colors.BOLD}{avg_comb*100:.1f}%{Colors.RESET}")
    
    # ===== 8. حفظ القائمة =====
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = Path(f"signals_{timestamp}.json")
    output_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candles_dir": str(candles_dir),
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
    print(f"\n{Colors.GREEN}✓ تم حفظ القائمة في: {output_file}{Colors.RESET}")
    
    # ===== 9. قواعد التشغيل =====
    print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️ قواعد التشغيل:{Colors.RESET}")
    print(f"  • MTG = مرة واحدة فقط (لا MTG2)")
    print(f"  • إذا فشل L1 → MTG في الشمعة التالية مباشرة")
    print(f"  • بعد MTG، انتظر 10 دقائق قبل الصفقة التالية")
    print(f"  • الفجوة العادية 3-6 دقائق (متغيرة للتشويش)")
    print(f"  • لا تكرر نفس العملة في إشارتين متتاليتين")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}تم الإيقاف.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}خطأ: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
