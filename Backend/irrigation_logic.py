# ─────────────────────────────────────────────────────────────────────
#  AgriMind AI — irrigation_logic.py
#  Precision Irrigation Planning Engine
#  Based on FAO-56 Penman-Monteith Evapotranspiration Model
# ─────────────────────────────────────────────────────────────────────

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math


# ─────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────

# Soil water holding capacity (mm/m) by soil type
SOIL_WHC: Dict[str, float] = {
    "Black Cotton": 180,
    "Alluvial":     160,
    "Red Laterite": 120,
    "Sandy Loam":   100,
    "Clay":         200,
}

# Field capacity (%) by soil type
FIELD_CAPACITY: Dict[str, float] = {
    "Black Cotton": 48,
    "Alluvial":     40,
    "Red Laterite": 32,
    "Sandy Loam":   28,
    "Clay":         52,
}

# Permanent wilting point (%) by soil type
WILTING_POINT: Dict[str, float] = {
    "Black Cotton": 22,
    "Alluvial":     18,
    "Red Laterite": 14,
    "Sandy Loam":   10,
    "Clay":         24,
}

# Irrigation method efficiency (fraction 0–1)
METHOD_EFFICIENCY: Dict[str, float] = {
    "Drip":       0.92,
    "Sprinkler":  0.78,
    "Flood":      0.55,
    "Furrow":     0.62,
    "Sub-surface":0.95,
}

# Method application rate (mm/hour)
METHOD_RATE: Dict[str, float] = {
    "Drip":       2.0,
    "Sprinkler":  8.0,
    "Flood":      25.0,
    "Furrow":     18.0,
    "Sub-surface":1.5,
}

# Best irrigation time by method and temperature
def best_time(method: str, temp: float) -> str:
    if temp > 34:
        return "5:30 AM"
    if method in ["Drip", "Sub-surface"]:
        return "6:00 AM"
    if method == "Sprinkler":
        return "6:30 AM"
    return "7:00 AM"


# ─────────────────────────────────────────
#  CROP COEFFICIENT DATABASE (FAO-56)
# ─────────────────────────────────────────
#  Kc values: [Initial, Development, Mid, Late]
#  Stages:    [Germination, Vegetative, Flowering/Peak, Maturity]

CROP_KC: Dict[str, List[float]] = {
    "Soybean":          [0.40, 0.80, 1.15, 0.50],
    "Cotton":           [0.35, 0.75, 1.20, 0.60],
    "Maize":            [0.30, 0.70, 1.20, 0.60],
    "Wheat":            [0.40, 0.70, 1.10, 0.40],
    "Turmeric":         [0.50, 0.90, 1.10, 0.70],
    "Groundnut":        [0.40, 0.70, 1.05, 0.60],
    "Watermelon":       [0.40, 0.75, 1.00, 0.75],
    "Chickpea":         [0.40, 0.70, 1.05, 0.30],
    "Sunflower":        [0.35, 0.75, 1.15, 0.55],
    "Moong":            [0.40, 0.70, 1.00, 0.45],
    "Potato":           [0.50, 0.75, 1.15, 0.75],
    "Mustard":          [0.35, 0.65, 1.05, 0.40],
    "Pigeonpea":        [0.40, 0.70, 1.05, 0.55],
    "Pea":              [0.50, 0.70, 1.10, 0.95],
    "Cucumber":         [0.60, 0.75, 1.00, 0.75],
    "Bitter Gourd":     [0.50, 0.70, 1.00, 0.80],
    "Onion":            [0.50, 0.70, 1.05, 0.85],
    "Sugarcane":        [0.40, 0.80, 1.25, 0.75],
    "Rice":             [1.05, 1.10, 1.20, 1.00],
    "Banana":           [0.50, 0.80, 1.10, 1.00],
}

# Stage index map — maps growth stage name → KC array index
STAGE_INDEX: Dict[str, int] = {
    "Germination":      0,
    "Sprouting":        0,
    "Initial":          0,
    "Vegetative":       1,
    "Tillering":        1,
    "Branching":        1,
    "Development":      1,
    "Flowering":        2,
    "Tasselling":       2,
    "Heading":          2,
    "Pod/Fruit Fill":   2,
    "Boll Formation":   2,
    "Siliqua Fill":     2,
    "Rhizome Dev.":     2,
    "Peak":             2,
    "Maturity":         3,
    "Ripening":         3,
    "Harvest":          3,
}

# Root depth (m) by crop and growth stage
ROOTING_DEPTH: Dict[str, List[float]] = {
    "Soybean":   [0.20, 0.50, 0.80, 0.80],
    "Cotton":    [0.20, 0.60, 1.20, 1.20],
    "Maize":     [0.20, 0.60, 1.00, 1.00],
    "Wheat":     [0.20, 0.50, 1.00, 1.00],
    "Groundnut": [0.20, 0.40, 0.60, 0.60],
    "Potato":    [0.20, 0.40, 0.60, 0.60],
    "Rice":      [0.15, 0.30, 0.50, 0.50],
    "Sunflower": [0.30, 0.60, 1.20, 1.20],
    "default":   [0.20, 0.50, 0.80, 0.80],
}

# Allowable depletion fraction (p) — fraction of TAW before stress
DEPLETION_FRACTION: Dict[str, float] = {
    "Soybean":   0.50,
    "Cotton":    0.65,
    "Maize":     0.55,
    "Wheat":     0.55,
    "Turmeric":  0.30,
    "Groundnut": 0.50,
    "Potato":    0.35,
    "Rice":      0.20,
    "default":   0.50,
}


# ─────────────────────────────────────────
#  DATA MODELS
# ─────────────────────────────────────────

@dataclass
class DaySchedule:
    """Irrigation schedule for a single day."""
    day:             str
    date:            str
    day_number:      int
    irrigate:        bool
    amount_mm:       float        # Gross water application
    net_amount_mm:   float        # Net water reaching root zone
    method:          str
    best_time:       str
    duration_hours:  float        # Time required for irrigation
    eto:             float        # Reference evapotranspiration mm/day
    etc:             float        # Crop evapotranspiration mm/day
    kc:              float        # Crop coefficient
    soil_moisture:   float        # Estimated soil moisture %
    taw:             float        # Total available water mm
    raw:             float        # Readily available water mm
    depletion:       float        # Current soil water depletion mm
    rain_mm:         float        # Rainfall that day
    reason:          str
    stress_risk:     str          # None / Low / Medium / High
    notes:           str          = ""


@dataclass
class IrrigationSummary:
    """Week-level irrigation summary."""
    crop:                    str
    growth_stage:            str
    method:                  str
    field_size_acres:        float
    total_irrigation_days:   int
    skip_days:               int
    total_water_mm:          float
    total_net_water_mm:      float
    total_liters:            int
    flood_equivalent_mm:     float
    water_savings_percent:   float
    avg_eto_mm_day:          float
    avg_etc_mm_day:          float
    avg_kc:                  float
    peak_demand_day:         str
    next_irrigation_day:     str
    critical_alert:          Optional[str]
    schedule:                List[DaySchedule]
    tips:                    List[str]
    generated_at:            str


# ─────────────────────────────────────────
#  EVAPOTRANSPIRATION ENGINE (FAO-56)
# ─────────────────────────────────────────

def compute_eto_hargreaves(
    temp_max:  float,
    temp_min:  float,
    temp_mean: float,
    ra:        float = 15.0,   # Extraterrestrial radiation MJ/m²/day (default Pune June)
) -> float:
    """
    Hargreaves-Samani ETo estimation (mm/day).
    FAO-56 Eq. 52 — suitable when only temperature data is available.

    Parameters
    ----------
    temp_max  : Maximum daily temperature °C
    temp_min  : Minimum daily temperature °C
    temp_mean : Mean daily temperature °C
    ra        : Extraterrestrial radiation MJ/m²/day

    Returns
    -------
    ETo in mm/day
    """
    td = max(temp_max - temp_min, 1.0)
    eto = 0.0023 * (temp_mean + 17.8) * math.sqrt(td) * ra * 0.408
    return round(max(1.0, min(12.0, eto)), 2)


def compute_eto_simplified(temperature: float, humidity: float) -> float:
    """
    Simplified ETo estimate when only single temperature and humidity are available.
    Approximates Penman-Monteith using empirical correction.

    Returns ETo in mm/day.
    """
    # Adjust for humidity — high humidity reduces evaporation demand
    humidity_factor = 1.0 - (humidity - 50) * 0.005
    humidity_factor = max(0.60, min(1.20, humidity_factor))

    # Base ETo from Hargreaves-like formula
    td  = max(temperature * 0.25, 2.0)   # estimated diurnal range
    eto = 0.0023 * (temperature + 17.8) * math.sqrt(td) * 15.0 * 0.408
    eto = eto * humidity_factor

    return round(max(1.0, min(12.0, eto)), 2)


def get_kc(crop: str, stage: str) -> float:
    """Return FAO-56 crop coefficient Kc for crop and growth stage."""
    kc_list   = CROP_KC.get(crop, [0.5, 0.8, 1.1, 0.55])
    stage_idx = STAGE_INDEX.get(stage, 1)
    return kc_list[min(stage_idx, len(kc_list) - 1)]


def get_root_depth(crop: str, stage: str) -> float:
    """Return effective root depth (m) for crop and growth stage."""
    depths    = ROOTING_DEPTH.get(crop, ROOTING_DEPTH["default"])
    stage_idx = STAGE_INDEX.get(stage, 1)
    return depths[min(stage_idx, len(depths) - 1)]


# ─────────────────────────────────────────
#  SOIL WATER BALANCE
# ─────────────────────────────────────────

def compute_taw(crop: str, stage: str, soil_type: str) -> Tuple[float, float]:
    """
    Compute Total Available Water (TAW) and Readily Available Water (RAW).

    TAW = (FC - WP) × Zr × 1000  (mm)
    RAW = p × TAW                  (mm)

    Returns (TAW, RAW) in mm.
    """
    fc    = FIELD_CAPACITY.get(soil_type, 40) / 100
    wp    = WILTING_POINT.get(soil_type, 18) / 100
    zr    = get_root_depth(crop, stage)
    p     = DEPLETION_FRACTION.get(crop, 0.50)

    taw   = round((fc - wp) * zr * 1000, 1)
    raw   = round(p * taw, 1)
    return taw, raw


def estimate_soil_moisture(
    initial_moisture: float,
    day_offset:       int,
    etc_per_day:      float,
    rain_today:       float,
    irrigation_today: float,
    field_capacity:   float,
    wilting_point:    float,
) -> float:
    """
    Estimate soil moisture on a given day using simplified water balance.

    Returns estimated soil moisture %.
    """
    daily_depletion  = etc_per_day * 1.2    # includes non-ET losses
    moisture         = initial_moisture
    moisture        -= daily_depletion * day_offset
    moisture        += rain_today * 0.35     # runoff factor
    moisture        += irrigation_today * 0.85
    return round(max(wilting_point, min(field_capacity * 1.05, moisture)), 1)


# ─────────────────────────────────────────
#  IRRIGATION SCHEDULING ENGINE
# ─────────────────────────────────────────

def compute_rain_forecast(base_rain: float, day_offset: int) -> float:
    """
    Distribute forecast rainfall across the week.
    Assumes peak rainfall mid-week (day 2–3) and possible secondary event (day 6).
    """
    if day_offset == 2 and base_rain > 5:
        return base_rain
    if day_offset == 3 and base_rain > 15:
        return round(base_rain * 0.40, 1)
    if day_offset == 6 and base_rain > 20:
        return round(base_rain * 0.25, 1)
    return 0.0


def compute_stress_risk(
    soil_moisture: float,
    raw:           float,
    taw:           float,
    wilting_point: float,
) -> str:
    """Classify water stress risk level."""
    depletion_pct = max(0, (FIELD_CAPACITY.get("Alluvial", 40) - soil_moisture))
    if soil_moisture <= wilting_point + 5:
        return "High"
    if depletion_pct > raw:
        return "Medium"
    if depletion_pct > raw * 0.6:
        return "Low"
    return "None"


def schedule_day(
    day_offset:       int,
    crop:             str,
    growth_stage:     str,
    method:           str,
    soil_type:        str,
    initial_moisture: float,
    temperature:      float,
    humidity:         float,
    base_rain:        float,
) -> DaySchedule:
    """
    Compute full irrigation schedule for a single day.

    Parameters
    ----------
    day_offset        : 0 = today, 1 = tomorrow, ..., 6 = day 7
    crop              : Crop name
    growth_stage      : Growth stage name
    method            : Irrigation method
    soil_type         : Soil type
    initial_moisture  : Current soil moisture %
    temperature       : Air temperature °C
    humidity          : Relative humidity %
    base_rain         : Weekly rainfall forecast mm
    """
    days_list = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    base_dt   = datetime.now() + timedelta(days=day_offset)
    day_name  = days_list[base_dt.weekday()]
    date_str  = base_dt.strftime("%b %d")

    # Evapotranspiration
    temp_max  = temperature + 4.5
    temp_min  = temperature - 5.0
    eto       = compute_eto_hargreaves(temp_max, temp_min, temperature)
    kc        = get_kc(crop, growth_stage)
    etc       = round(eto * kc, 2)

    # Soil water balance
    fc        = FIELD_CAPACITY.get(soil_type, 40)
    wp        = WILTING_POINT.get(soil_type, 18)
    taw, raw  = compute_taw(crop, growth_stage, soil_type)
    rain_today= compute_rain_forecast(base_rain, day_offset)

    # Estimate current soil moisture
    sm        = estimate_soil_moisture(
        initial_moisture, day_offset, etc,
        rain_today, 0, fc, wp
    )

    # Depletion from field capacity
    depletion = max(0.0, round((fc - sm) / 100 * taw, 1))

    # Decision: irrigate if depletion exceeds RAW and rain is insufficient
    needs_water = (depletion > raw * 0.8) and (rain_today < 8.0)

    # Compute gross application amount
    if needs_water:
        net_amount  = round(depletion + etc * 1.5, 1)
        efficiency  = METHOD_EFFICIENCY.get(method, 0.75)
        gross_amount= round(net_amount / efficiency, 1)
        duration    = round(gross_amount / METHOD_RATE.get(method, 5.0), 2)
    else:
        net_amount   = 0.0
        gross_amount = 0.0
        duration     = 0.0

    # Stress risk
    stress = compute_stress_risk(sm, raw, taw, wp)

    # Reason generation
    if not needs_water and rain_today >= 8:
        reason = f"Rain forecast {rain_today:.0f}mm covers crop water need — skip"
    elif not needs_water and sm >= fc * 0.85:
        reason = f"Soil moisture {sm}% is adequate — no irrigation needed"
    elif not needs_water:
        reason = "Depletion within safe threshold — monitor closely"
    elif stress == "High":
        reason = f"⚠️ Severe water stress — soil at {sm}% near wilting point"
    elif day_offset == 1:
        reason = f"Soil moisture {sm}% below threshold — scheduled top-up"
    elif day_offset == 3:
        reason = f"ETc demand {etc}mm/day requires supplemental irrigation"
    elif day_offset == 5:
        reason = f"Preventive irrigation before weekend heat stress"
    else:
        reason = f"Deficit irrigation to replenish {depletion:.0f}mm soil depletion"

    # Special stage notes
    notes = ""
    critical_stages = ["Flowering", "Pod/Fruit Fill", "Tasselling", "Heading", "Boll Formation"]
    if growth_stage in critical_stages and needs_water:
        notes = f"⚡ Critical stage — {growth_stage} is yield-determining. Do not skip."
    elif growth_stage == "Maturity" and needs_water:
        notes = "💡 Reduce irrigation frequency at maturity for quality grain fill."

    return DaySchedule(
        day            = day_name,
        date           = date_str,
        day_number     = day_offset + 1,
        irrigate       = needs_water,
        amount_mm      = gross_amount,
        net_amount_mm  = net_amount,
        method         = method if needs_water else "—",
        best_time      = best_time(method, temperature) if needs_water else "—",
        duration_hours = duration,
        eto            = eto,
        etc            = etc,
        kc             = kc,
        soil_moisture  = sm,
        taw            = taw,
        raw            = raw,
        depletion      = depletion,
        rain_mm        = rain_today,
        reason         = reason,
        stress_risk    = stress,
        notes          = notes,
    )


# ─────────────────────────────────────────
#  TIPS DATABASE
# ─────────────────────────────────────────

METHOD_TIPS: Dict[str, List[str]] = {
    "Drip": [
        "Operate drip at 6–8 AM to minimize evaporation — saves 15–20% additional water",
        "Clean drip emitters monthly using 1% HCl flush to prevent clogging",
        "Use tensiometer at 30 cm depth for precise soil moisture-based triggering",
        "Fertigate through drip lines: N-P-K in 3:1:2 ratio during vegetative stage",
        "Check lateral pressure uniformity (CV < 10%) for even water distribution",
        "Install sand+screen filter before the drip system to prevent emitter blockage",
    ],
    "Sprinkler": [
        "Operate sprinklers in early morning or evening — avoid midday to cut 25% evaporation",
        "Use catch cans in 4 corners to verify distribution uniformity (>80% DU)",
        "Check operating pressure 2.5–3.5 kg/cm² for optimal throw and coverage",
        "Wind speed >15 km/h reduces uniformity by 20–30% — reschedule if windy",
        "Rotate sprinkler heads regularly and check for clogged nozzles weekly",
        "Apply wetting agent to help water penetrate hydrophobic dry soils",
    ],
    "Flood": [
        "Level field to ±2 cm precision with laser leveler — ensures uniform distribution",
        "Construct bunds 15–20 cm high to retain water and reduce tail-end runoff",
        "Apply flood in early morning to allow time for percolation before afternoon heat",
        "Light tillage after flood irrigation breaks soil crust for better aeration",
        "Tail-water recovery pit at field end can recycle 20–25% of applied water",
        "Avoid over-irrigation — waterlogging for >48 hours reduces yield by 25–40%",
    ],
    "Furrow": [
        "Make furrows 60–75 cm apart and 20–25 cm deep for row crops",
        "Use gated pipes or siphon tubes for controlled, measured water delivery",
        "Alternate furrow irrigation saves 30–40% water with minimal yield impact",
        "Limit furrow length to 100–120 m to avoid uneven distribution",
        "Surge irrigation (intermittent flow) improves advance rate and efficiency",
        "Seal furrow ends after irrigation to prevent tail-water losses",
    ],
    "Sub-surface": [
        "Bury lateral lines 20–40 cm deep depending on root zone depth of crop",
        "Flush laterals every 2 weeks to prevent root intrusion into emitters",
        "Use anti-siphon valves to prevent soil suction back into the system",
        "Sub-surface drip achieves 95%+ efficiency — highest of all methods",
        "Combine with soil moisture sensors for fully automated scheduling",
        "Ideal for orchards and perennial crops — minimal disturbance after installation",
    ],
}

GENERAL_TIPS: List[str] = [
    "Irrigate in the morning — plants absorb water most efficiently between 6–9 AM",
    "Always check weather forecast before irrigating — skip if rain >10mm is forecast",
    "Mulching with 5–7 cm crop residue reduces evaporation by 30–40%",
    "Monitor plant wilting (morning turgidity) as real-time stress indicator",
    "Soil moisture sensors (tensiometers) at 15 cm and 30 cm improve scheduling accuracy by 40%",
    "Avoid irrigation during strong winds (>20 km/h) to prevent drift and uneven distribution",
]


# ─────────────────────────────────────────
#  MAIN PLANNING FUNCTION
# ─────────────────────────────────────────

def generate_irrigation_plan(
    crop:             str,
    growth_stage:     str,
    method:           str,
    field_size_acres: float,
    soil_moisture:    float,
    temperature:      float,
    humidity:         float,
    rainfall_forecast:float,
    soil_type:        str = "Alluvial",
    days:             int = 7,
) -> IrrigationSummary:
    """
    Generate a complete multi-day precision irrigation plan.

    Parameters
    ----------
    crop              : Crop name (must match CROP_KC keys)
    growth_stage      : Current growth stage name
    method            : Irrigation method
    field_size_acres  : Field area in acres
    soil_moisture     : Current soil moisture %
    temperature       : Current air temperature °C
    humidity          : Current relative humidity %
    rainfall_forecast : Expected weekly rainfall mm
    soil_type         : Soil type name
    days              : Number of days to plan (default 7)

    Returns
    -------
    IrrigationSummary with full schedule and analytics.
    """
    schedule: List[DaySchedule] = []

    for i in range(days):
        day = schedule_day(
            day_offset       = i,
            crop             = crop,
            growth_stage     = growth_stage,
            method           = method,
            soil_type        = soil_type,
            initial_moisture = soil_moisture,
            temperature      = temperature,
            humidity         = humidity,
            base_rain        = rainfall_forecast,
        )
        schedule.append(day)

    # ── Analytics ──────────────────────────────────────────────────
    irr_days         = [d for d in schedule if d.irrigate]
    skip_days        = days - len(irr_days)
    total_gross_mm   = round(sum(d.amount_mm for d in schedule), 1)
    total_net_mm     = round(sum(d.net_amount_mm for d in schedule), 1)

    # Convert mm to liters (1 mm × 1 acre = 4046.86 L)
    total_liters     = int(total_gross_mm * field_size_acres * 4046.86 / 1000)

    # Flood equivalent (flood efficiency ~55%)
    flood_equiv      = round(total_net_mm / 0.55, 1)
    savings_pct      = round((1 - total_gross_mm / max(flood_equiv, 1)) * 100, 1)
    savings_pct      = max(0, min(75, savings_pct))

    avg_eto          = round(sum(d.eto for d in schedule) / days, 2)
    avg_etc          = round(sum(d.etc for d in schedule) / days, 2)
    avg_kc           = round(sum(d.kc  for d in schedule) / days, 2)

    # Peak demand day
    peak_day         = max(schedule, key=lambda d: d.etc)
    next_irr         = next((d for d in schedule if d.irrigate), None)

    # Critical alert check
    critical_alert   = None
    stress_days      = [d for d in schedule if d.stress_risk == "High"]
    if stress_days:
        critical_alert = f"⚠️ High water stress expected on {stress_days[0].day} — immediate irrigation required."
    elif soil_moisture < 30:
        critical_alert = "🚨 Current soil moisture critically low — emergency irrigation needed today."

    # Tips
    tips  = METHOD_TIPS.get(method, [])[:4]
    tips += GENERAL_TIPS[:2]

    return IrrigationSummary(
        crop                   = crop,
        growth_stage           = growth_stage,
        method                 = method,
        field_size_acres       = field_size_acres,
        total_irrigation_days  = len(irr_days),
        skip_days              = skip_days,
        total_water_mm         = total_gross_mm,
        total_net_water_mm     = total_net_mm,
        total_liters           = total_liters,
        flood_equivalent_mm    = flood_equiv,
        water_savings_percent  = savings_pct,
        avg_eto_mm_day         = avg_eto,
        avg_etc_mm_day         = avg_etc,
        avg_kc                 = avg_kc,
        peak_demand_day        = peak_day.day,
        next_irrigation_day    = next_irr.day if next_irr else "None this week",
        critical_alert         = critical_alert,
        schedule               = schedule,
        tips                   = tips,
        generated_at           = datetime.now().isoformat(),
    )


# ─────────────────────────────────────────
#  HELPER UTILITIES
# ─────────────────────────────────────────

def get_supported_crops() -> List[str]:
    """Return list of all crops with KC data."""
    return list(CROP_KC.keys())


def get_supported_methods() -> List[str]:
    """Return list of all irrigation methods."""
    return list(METHOD_EFFICIENCY.keys())


def get_method_efficiency(method: str) -> float:
    """Return efficiency fraction for a given irrigation method."""
    return METHOD_EFFICIENCY.get(method, 0.75)


def estimate_season_water(crop: str, soil_type: str = "Alluvial") -> Dict[str, float]:
    """
    Estimate total seasonal water requirement (mm) across all growth stages.

    Returns dict with per-stage and total water estimates.
    """
    kc_values   = CROP_KC.get(crop, [0.5, 0.8, 1.1, 0.55])
    stage_names = ["Germination", "Vegetative", "Flowering", "Maturity"]
    avg_eto     = 5.5  # average ETo for Indian growing season mm/day
    stage_days  = [15, 35, 30, 20]  # typical duration per stage

    result = {}
    total  = 0.0
    for i, (name, kc, dur) in enumerate(zip(stage_names, kc_values, stage_days)):
        etc  = round(kc * avg_eto * dur, 1)
        result[name] = etc
        total += etc

    result["total_mm"] = round(total, 1)
    return result


def irrigation_checklist(method: str, crop: str, stage: str) -> List[str]:
    """Return a pre-irrigation checklist for farmer."""
    base = [
        f"✅ Confirm soil moisture is below threshold before opening {method} system",
        f"✅ Check weather forecast — skip if rain >10mm expected within 24 hours",
        f"✅ Inspect {method} lines/sprinklers/channels for leaks or blockage",
        f"✅ Verify water source availability and pressure is adequate",
        f"✅ Set timer/alarm to avoid over-irrigation",
    ]
    if stage in ["Flowering", "Pod/Fruit Fill", "Tasselling"]:
        base.insert(0, f"⚡ CRITICAL STAGE — {crop} at {stage}: Do NOT skip irrigation today")
    if method == "Drip":
        base.append("✅ Run 5-minute flush before main irrigation to clear sediment")
    return base


def format_schedule_table(summary: IrrigationSummary) -> str:
    """
    Format irrigation schedule as ASCII table for terminal output.
    """
    header = f"\n{'─'*85}\n"
    header += f"  AgriMind AI — {summary.crop} Irrigation Plan ({summary.method})\n"
    header += f"  Stage: {summary.growth_stage} | Field: {summary.field_size_acres} acres | Soil: Alluvial\n"
    header += f"{'─'*85}\n"
    header += f"  {'DAY':<6}{'DATE':<10}{'STATUS':<12}{'AMOUNT':>8}{'METHOD':<14}{'TIME':<10}{'ETo':<8}{'ETc':<8}REASON\n"
    header += f"{'─'*85}\n"

    rows = ""
    for d in summary.schedule:
        status = "💧 IRRIGATE" if d.irrigate else "⬜ SKIP"
        amount = f"{d.amount_mm}mm" if d.irrigate else "—"
        rows += (
            f"  {d.day:<6}{d.date:<10}{status:<12}{amount:>8}  "
            f"{d.method:<12}{d.best_time:<10}{d.eto:<8}{d.etc:<8}{d.reason[:35]}\n"
        )

    footer = f"{'─'*85}\n"
    footer += f"  Total: {summary.total_irrigation_days}/7 days | "
    footer += f"{summary.total_water_mm}mm | "
    footer += f"{summary.total_liters:,} litres | "
    footer += f"~{summary.water_savings_percent}% saved vs flood\n"
    footer += f"{'─'*85}\n"

    return header + rows + footer


# ─────────────────────────────────────────
#  QUICK TEST (run directly)
# ─────────────────────────────────────────

if __name__ == "__main__":
    plan = generate_irrigation_plan(
        crop              = "Soybean",
        growth_stage      = "Flowering",
        method            = "Drip",
        field_size_acres  = 5.2,
        soil_moisture     = 42.0,
        temperature       = 28.0,
        humidity          = 65.0,
        rainfall_forecast = 12.0,
        soil_type         = "Black Cotton",
        days              = 7,
    )

    print(format_schedule_table(plan))

    print(f"  Avg ETo     : {plan.avg_eto_mm_day} mm/day")
    print(f"  Avg ETc     : {plan.avg_etc_mm_day} mm/day")
    print(f"  Avg Kc      : {plan.avg_kc}")
    print(f"  Peak Demand : {plan.peak_demand_day}")
    print(f"  Next Irr    : {plan.next_irrigation_day}")
    if plan.critical_alert:
        print(f"\n  {plan.critical_alert}")

    print(f"\n  💡 Tips:")
    for tip in plan.tips[:3]:
        print(f"     • {tip}")

    print(f"\n  📋 Season Water Estimate for Soybean:")
    sw = estimate_season_water("Soybean")
    for stage, mm in sw.items():
        print(f"     {stage:<20}: {mm} mm")

    print(f"\n  ✅ Pre-Irrigation Checklist:")
    for item in irrigation_checklist("Drip", "Soybean", "Flowering"):
        print(f"     {item}")