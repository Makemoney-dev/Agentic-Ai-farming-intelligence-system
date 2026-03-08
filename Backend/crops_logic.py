# ─────────────────────────────────────────────────────────────────────
#  AgriMind AI — crop_logic.py
#  Crop Recommendation Engine
#  Rule-based multi-factor scoring with ICAR-aligned crop database
# ─────────────────────────────────────────────────────────────────────

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


# ─────────────────────────────────────────
#  DATA MODELS
# ─────────────────────────────────────────

@dataclass
class CropProfile:
    """Complete agronomic profile for a single crop."""
    name:             str
    icon:             str
    season:           str
    category:         str          # Cereal / Pulse / Oilseed / Spice / Vegetable / Fibre
    base_score:       int
    ph_min:           float
    ph_max:           float
    temp_min:         float
    temp_max:         float
    hum_min:          float
    hum_max:          float
    n_min:            float        # Nitrogen minimum kg/ha
    n_optimal:        float
    p_min:            float        # Phosphorus minimum kg/ha
    k_min:            float        # Potassium minimum kg/ha
    growth_days:      int
    water_need:       str          # Low / Medium / High
    water_mm:         str          # Total water requirement mm/season
    market_price:     str
    msp_price:        Optional[str]
    profit_potential: str          # Low / Medium / High / Very High
    risk_level:       str          # Low / Medium / High
    soil_fit:         Dict[str, int] = field(default_factory=dict)
    tags:             List[str]    = field(default_factory=list)
    critical_stage:   str         = ""
    export_demand:    bool        = False
    organic_suitable: bool        = True


@dataclass
class CropScore:
    """Scored crop result returned to API."""
    crop:             str
    icon:             str
    category:         str
    season:           str
    suitability:      int
    grade:            str          # A+ / A / B+ / B / C
    reason:           str
    growth_days:      int
    water_need:       str
    water_mm:         str
    market_price:     str
    msp_price:        Optional[str]
    profit_potential: str
    risk_level:       str
    tags:             List[str]
    critical_stage:   str
    score_breakdown:  Dict[str, int]
    agronomic_tips:   List[str]


# ─────────────────────────────────────────
#  FULL CROP DATABASE
# ─────────────────────────────────────────

CROPS: List[CropProfile] = [

    # ── KHARIF ──────────────────────────────────────────────────────

    CropProfile(
        name="Soybean", icon="🫘", season="Kharif", category="Oilseed/Pulse",
        base_score=88,
        ph_min=6.0, ph_max=7.5, temp_min=20, temp_max=35, hum_min=55, hum_max=90,
        n_min=30, n_optimal=60, p_min=20, k_min=30,
        growth_days=100, water_need="Medium", water_mm="450–550",
        market_price="₹3,800/quintal", msp_price="₹4,600/quintal",
        profit_potential="High", risk_level="Low",
        soil_fit={"Black Cotton":6,"Alluvial":5,"Red Laterite":3,"Sandy Loam":4,"Clay":4},
        tags=["Nitrogen-fixing","Kharif staple","Export demand","Oil + protein"],
        critical_stage="Flowering & Pod Fill", export_demand=True,
        agronomic_tips=[
            "Inoculate seeds with Bradyrhizobium japonicum 200g/10kg seed before sowing",
            "Maintain row spacing 30–45 cm for maximum canopy and nodulation",
            "Apply 20 kg P₂O₅/ha as basal dose — soybean is high phosphorus feeder",
            "Monitor for pod borer and aphids from 30 DAS using pheromone traps",
            "Harvest when 95% pods turn brown and grain moisture is 13–14%",
        ]
    ),

    CropProfile(
        name="Cotton", icon="🌿", season="Kharif", category="Fibre",
        base_score=84,
        ph_min=5.8, ph_max=8.0, temp_min=25, temp_max=40, hum_min=50, hum_max=80,
        n_min=25, n_optimal=100, p_min=15, k_min=40,
        growth_days=165, water_need="Medium", water_mm="700–1200",
        market_price="₹6,500/quintal", msp_price="₹7,020/quintal",
        profit_potential="Very High", risk_level="Medium",
        soil_fit={"Black Cotton":7,"Alluvial":4,"Red Laterite":3,"Sandy Loam":3,"Clay":5},
        tags=["Cash crop","High MSP","Black soil preferred","Bt varieties available"],
        critical_stage="Boll Formation", export_demand=True,
        agronomic_tips=[
            "Plant Bt Cotton (RCH-2, MRC-7351) for bollworm resistance management",
            "Split nitrogen: 50% basal + 25% square formation + 25% boll development",
            "Maintain excellent drainage — cotton is extremely sensitive to waterlogging",
            "Apply foliar urea spray 2% at boll development stage for quality improvement",
            "Harvest in early morning to prevent fiber quality loss from afternoon heat",
        ]
    ),

    CropProfile(
        name="Maize", icon="🌽", season="Kharif", category="Cereal",
        base_score=78,
        ph_min=5.8, ph_max=7.0, temp_min=18, temp_max=32, hum_min=50, hum_max=80,
        n_min=20, n_optimal=120, p_min=15, k_min=25,
        growth_days=90, water_need="Medium", water_mm="500–800",
        market_price="₹1,900/quintal", msp_price="₹2,090/quintal",
        profit_potential="Medium", risk_level="Low",
        soil_fit={"Black Cotton":4,"Alluvial":7,"Red Laterite":5,"Sandy Loam":6,"Clay":3},
        tags=["Short duration","Feed crop","Drought tolerant","Silage option"],
        critical_stage="Tasselling & Silking",
        agronomic_tips=[
            "Apply 120 kg N/ha in 3 splits — knee-high stage topdressing gives best response",
            "Never skip irrigation at tasselling and silking — critical yield formation stages",
            "Maintain 65,000–75,000 plants/hectare for optimal yield",
            "Weed management within first 30 days prevents 40% yield loss",
            "Harvest at 28–32% grain moisture for silage, 14–16% for grain storage",
        ]
    ),

    CropProfile(
        name="Turmeric", icon="🟡", season="Kharif", category="Spice",
        base_score=72,
        ph_min=5.5, ph_max=7.0, temp_min=20, temp_max=35, hum_min=65, hum_max=90,
        n_min=15, n_optimal=60, p_min=20, k_min=60,
        growth_days=270, water_need="High", water_mm="1500–2000",
        market_price="₹12,000/quintal", msp_price=None,
        profit_potential="Very High", risk_level="Medium",
        soil_fit={"Black Cotton":3,"Alluvial":5,"Red Laterite":6,"Sandy Loam":7,"Clay":3},
        tags=["Spice crop","Premium price","Long duration","Medicinal value"],
        critical_stage="Rhizome Development",
        agronomic_tips=[
            "Use rhizomes 40–60 g size with 2+ viable buds for best germination rate",
            "Apply FYM 25 t/ha + Azospirillum biofertilizer for organic yield boost",
            "Provide shade netting 25–30% during summer to prevent leaf scorch",
            "Harvest 8–9 months after planting when leaves turn yellow and dry",
            "Cure harvested rhizomes by boiling 45–60 minutes before sun-drying",
        ]
    ),

    CropProfile(
        name="Groundnut", icon="🥜", season="Kharif", category="Oilseed",
        base_score=75,
        ph_min=6.0, ph_max=7.0, temp_min=22, temp_max=35, hum_min=45, hum_max=75,
        n_min=15, n_optimal=25, p_min=30, k_min=25,
        growth_days=120, water_need="Low", water_mm="400–600",
        market_price="₹5,200/quintal", msp_price="₹6,377/quintal",
        profit_potential="High", risk_level="Low",
        soil_fit={"Black Cotton":3,"Alluvial":6,"Red Laterite":7,"Sandy Loam":8,"Clay":2},
        tags=["Oil seed","Low water","Sandy soil preferred","High MSP"],
        critical_stage="Pegging & Pod Fill",
        agronomic_tips=[
            "Treat seeds with Trichoderma viride 4g/kg to prevent collar rot disease",
            "Apply gypsum 500 kg/ha at pegging stage for direct calcium supply to pods",
            "Stop irrigation 15 days before harvest for proper shell hardening",
            "Maintain pH 6.0–6.5 for maximum nutrient availability",
            "Harvest when inner shell shows dark brown veins and leaves turn yellow",
        ]
    ),

    CropProfile(
        name="Pigeonpea (Tur)", icon="🟤", season="Kharif", category="Pulse",
        base_score=76,
        ph_min=5.5, ph_max=7.5, temp_min=18, temp_max=38, hum_min=40, hum_max=75,
        n_min=10, n_optimal=25, p_min=20, k_min=20,
        growth_days=170, water_need="Low", water_mm="350–500",
        market_price="₹7,000/quintal", msp_price="₹7,000/quintal",
        profit_potential="High", risk_level="Low",
        soil_fit={"Black Cotton":6,"Alluvial":5,"Red Laterite":6,"Sandy Loam":5,"Clay":4},
        tags=["Pulse","Drought resistant","Nitrogen fixer","Intercrop-friendly"],
        critical_stage="Flowering & Pod Fill",
        agronomic_tips=[
            "Inoculate seeds with Rhizobium sp. biofertilizer for best nodulation",
            "Excellent intercrop with soybean at 1:3 ratio for better land utilization",
            "One supplemental irrigation at pod fill stage significantly boosts yield",
            "Wilt-resistant varieties (ICPL-87, BDN-2) recommended in endemic areas",
            "Harvest in stages as pods mature unevenly to minimize shattering losses",
        ]
    ),

    # ── RABI ────────────────────────────────────────────────────────

    CropProfile(
        name="Wheat", icon="🌾", season="Rabi", category="Cereal",
        base_score=90,
        ph_min=6.0, ph_max=7.5, temp_min=10, temp_max=25, hum_min=40, hum_max=70,
        n_min=30, n_optimal=120, p_min=25, k_min=40,
        growth_days=120, water_need="Medium", water_mm="450–650",
        market_price="₹2,150/quintal", msp_price="₹2,275/quintal",
        profit_potential="High", risk_level="Low",
        soil_fit={"Black Cotton":5,"Alluvial":8,"Red Laterite":3,"Sandy Loam":6,"Clay":5},
        tags=["Rabi staple","High MSP","Cold tolerant","Major food crop"],
        critical_stage="Heading & Grain Fill",
        agronomic_tips=[
            "Sow in last week of October to mid-November for optimal yield",
            "Apply 120 kg N + 60 kg P + 40 kg K per hectare as fertilizer dose",
            "Provide 6 irrigations: CRI, tillering, jointing, flowering, milky, dough stages",
            "Use rust-resistant varieties HD-2967, GW-322 for disease management",
            "Harvest at golden yellow stage with 15–17% grain moisture",
        ]
    ),

    CropProfile(
        name="Chickpea", icon="🟡", season="Rabi", category="Pulse",
        base_score=82,
        ph_min=5.5, ph_max=7.0, temp_min=15, temp_max=30, hum_min=30, hum_max=60,
        n_min=10, n_optimal=20, p_min=25, k_min=20,
        growth_days=100, water_need="Low", water_mm="300–400",
        market_price="₹5,440/quintal", msp_price="₹5,440/quintal",
        profit_potential="High", risk_level="Low",
        soil_fit={"Black Cotton":7,"Alluvial":5,"Red Laterite":4,"Sandy Loam":6,"Clay":4},
        tags=["Pulse","Drought resistant","Nitrogen fixer","Low water"],
        critical_stage="Flowering",
        agronomic_tips=[
            "Inoculate seeds with Mesorhizobium ciceri 200g/10kg seed before sowing",
            "Avoid excess nitrogen — chickpea fixes its own through root nodules",
            "One pre-sowing irrigation + 1–2 supplemental at branching and pod fill",
            "Monitor pod borer from 30 DAS with pheromone traps — most critical pest",
            "Harvest at 70–75% pod maturity to minimize shattering losses",
        ]
    ),

    CropProfile(
        name="Mustard", icon="🌼", season="Rabi", category="Oilseed",
        base_score=80,
        ph_min=5.8, ph_max=7.5, temp_min=10, temp_max=28, hum_min=35, hum_max=65,
        n_min=20, n_optimal=80, p_min=20, k_min=20,
        growth_days=110, water_need="Low", water_mm="350–500",
        market_price="₹5,650/quintal", msp_price="₹5,650/quintal",
        profit_potential="High", risk_level="Low",
        soil_fit={"Black Cotton":4,"Alluvial":7,"Red Laterite":5,"Sandy Loam":7,"Clay":3},
        tags=["Oilseed","Short duration","Cold tolerant","High MSP"],
        critical_stage="Siliqua Formation",
        agronomic_tips=[
            "Sow 5 kg/ha seed rate at 30 cm row spacing for optimum plant population",
            "Apply sulfur 40 kg/ha — mustard is highly sulfur-responsive crop",
            "Critical irrigations at branching, flowering, and siliqua filling stages",
            "Harvest when 75% siliqua turn yellow to avoid shattering",
            "Intercrop with wheat at 1:9 ratio for better returns and pest control",
        ]
    ),

    CropProfile(
        name="Potato", icon="🥔", season="Rabi", category="Vegetable",
        base_score=76,
        ph_min=5.0, ph_max=6.5, temp_min=10, temp_max=25, hum_min=50, hum_max=80,
        n_min=25, n_optimal=120, p_min=30, k_min=80,
        growth_days=90, water_need="High", water_mm="600–800",
        market_price="₹1,500/quintal", msp_price=None,
        profit_potential="Medium", risk_level="High",
        soil_fit={"Black Cotton":3,"Alluvial":7,"Red Laterite":5,"Sandy Loam":8,"Clay":2},
        tags=["Vegetable crop","High input","Cold crop","Storage crop"],
        critical_stage="Tuber Initiation",
        agronomic_tips=[
            "Use certified disease-free seed tubers of 30–50 g with 2–3 buds",
            "Apply earthing-up twice: at 25 and 40 days after planting",
            "Monitor for late blight — spray Metalaxyl+Mancozeb every 7–10 days in humid weather",
            "Haulm killing 15 days before harvest gives better skin set and shelf life",
            "Store at 2–4°C with 90–95% humidity for long-term preservation",
        ]
    ),

    CropProfile(
        name="Pea", icon="🫛", season="Rabi", category="Pulse",
        base_score=74,
        ph_min=6.0, ph_max=7.5, temp_min=8, temp_max=22, hum_min=40, hum_max=70,
        n_min=10, n_optimal=20, p_min=20, k_min=25,
        growth_days=75, water_need="Low", water_mm="300–500",
        market_price="₹3,600/quintal", msp_price=None,
        profit_potential="Medium", risk_level="Low",
        soil_fit={"Black Cotton":4,"Alluvial":7,"Red Laterite":4,"Sandy Loam":7,"Clay":3},
        tags=["Pulse","Short duration","Cold loving","Vegetable + grain"],
        critical_stage="Pod Fill",
        agronomic_tips=[
            "Sow October–November — very sensitive to warm weather above 28°C",
            "Inoculate with Rhizobium leguminosarum for efficient nitrogen fixation",
            "Two irrigations at pre-flowering and pod filling stages are sufficient",
            "Harvest green pods at 60–70% maturity for premium vegetable market",
            "Use powdery mildew resistant varieties in humid regions",
        ]
    ),

    # ── ZAID ────────────────────────────────────────────────────────

    CropProfile(
        name="Watermelon", icon="🍉", season="Zaid", category="Vegetable",
        base_score=86,
        ph_min=6.0, ph_max=7.0, temp_min=25, temp_max=40, hum_min=40, hum_max=70,
        n_min=15, n_optimal=60, p_min=20, k_min=30,
        growth_days=75, water_need="Medium", water_mm="400–600",
        market_price="₹1,200/quintal", msp_price=None,
        profit_potential="High", risk_level="Medium",
        soil_fit={"Black Cotton":3,"Alluvial":7,"Red Laterite":5,"Sandy Loam":8,"Clay":2},
        tags=["Summer crop","Short duration","High demand","Drip-friendly"],
        critical_stage="Fruit Fill",
        agronomic_tips=[
            "Use drip irrigation with fertigation for best fruit quality and water saving",
            "Train vines on trellis — hanging fruit develops better shape and reduces rot",
            "Apply boron spray 0.2% at flowering for improved fruit set",
            "Harvest when tendril opposite to fruit dries and bottom spot turns cream",
            "Intercrop with short-duration vegetables to maximize land utilization",
        ]
    ),

    CropProfile(
        name="Moong (Green Gram)", icon="🟢", season="Zaid", category="Pulse",
        base_score=78,
        ph_min=6.0, ph_max=7.5, temp_min=25, temp_max=40, hum_min=40, hum_max=75,
        n_min=10, n_optimal=20, p_min=20, k_min=20,
        growth_days=65, water_need="Low", water_mm="300–400",
        market_price="₹7,755/quintal", msp_price="₹8,682/quintal",
        profit_potential="Very High", risk_level="Low",
        soil_fit={"Black Cotton":5,"Alluvial":7,"Red Laterite":6,"Sandy Loam":7,"Clay":4},
        tags=["Pulse","Short duration","Drought tolerant","Very high MSP"],
        critical_stage="Flowering & Pod Fill",
        agronomic_tips=[
            "Treat seeds with Rhizobium + PSB biofertilizer for better nodulation",
            "Sow at 20–25 kg/ha with 30×10 cm spacing for optimum plant population",
            "3–4 irrigations sufficient — critical at flowering and pod fill stages",
            "Harvest in 2–3 pickings as pods mature at different times",
            "Dry threshed grain to 10% moisture before storage to prevent fungi",
        ]
    ),

    CropProfile(
        name="Sunflower", icon="🌻", season="Zaid", category="Oilseed",
        base_score=74,
        ph_min=6.0, ph_max=7.5, temp_min=20, temp_max=35, hum_min=40, hum_max=70,
        n_min=20, n_optimal=80, p_min=25, k_min=30,
        growth_days=90, water_need="Medium", water_mm="500–700",
        market_price="₹6,400/quintal", msp_price="₹6,760/quintal",
        profit_potential="High", risk_level="Medium",
        soil_fit={"Black Cotton":5,"Alluvial":7,"Red Laterite":5,"Sandy Loam":6,"Clay":4},
        tags=["Oilseed","Bee pollinated","High oil content","Short duration"],
        critical_stage="Seed Fill",
        agronomic_tips=[
            "Hand pollination or beehive placement increases yield by 15–30%",
            "Apply boron 1.5 kg/ha + sulfur 20 kg/ha for higher oil content",
            "Bird scaring essential at grain fill — birds cause 20–40% loss",
            "Harvest when back of head turns yellow-brown and seeds have hard shell",
            "Process within 2–3 months for fresh oil quality",
        ]
    ),

    CropProfile(
        name="Cucumber", icon="🥒", season="Zaid", category="Vegetable",
        base_score=82,
        ph_min=5.8, ph_max=7.0, temp_min=22, temp_max=38, hum_min=50, hum_max=80,
        n_min=20, n_optimal=60, p_min=20, k_min=30,
        growth_days=55, water_need="Medium", water_mm="350–500",
        market_price="₹1,000/quintal", msp_price=None,
        profit_potential="Medium", risk_level="Low",
        soil_fit={"Black Cotton":3,"Alluvial":7,"Red Laterite":5,"Sandy Loam":8,"Clay":3},
        tags=["Vegetable","Fast growing","Market ready quickly","Trellis crop"],
        critical_stage="Fruit Set",
        agronomic_tips=[
            "Sow 2 seeds per hill 2 cm deep at 60×30 cm spacing",
            "Provide trellis support for climbing varieties for better air circulation",
            "Harvest every 2–3 days after fruiting starts to encourage continuous setting",
            "Use yellow sticky traps for aphid and whitefly management",
            "Mulching reduces evaporation by 30% and suppresses weeds effectively",
        ]
    ),
]


# ─────────────────────────────────────────
#  SCORING ENGINE
# ─────────────────────────────────────────

def _score_ph(crop: CropProfile, ph: float) -> int:
    """Score soil pH suitability (0–15 points)."""
    if crop.ph_min <= ph <= crop.ph_max:
        mid = (crop.ph_min + crop.ph_max) / 2
        proximity = 1 - abs(ph - mid) / ((crop.ph_max - crop.ph_min) / 2)
        return int(10 + proximity * 5)
    deviation = min(abs(ph - crop.ph_min), abs(ph - crop.ph_max))
    return max(0, int(8 - deviation * 3))


def _score_temperature(crop: CropProfile, temp: float) -> int:
    """Score temperature suitability (0–12 points)."""
    if crop.temp_min <= temp <= crop.temp_max:
        mid = (crop.temp_min + crop.temp_max) / 2
        proximity = 1 - abs(temp - mid) / ((crop.temp_max - crop.temp_min) / 2)
        return int(8 + proximity * 4)
    return max(0, int(6 - abs(temp - (crop.temp_min + crop.temp_max) / 2) * 0.5))


def _score_humidity(crop: CropProfile, hum: float) -> int:
    """Score humidity suitability (0–10 points)."""
    if crop.hum_min <= hum <= crop.hum_max:
        return 10
    deviation = min(abs(hum - crop.hum_min), abs(hum - crop.hum_max))
    return max(0, int(8 - deviation * 0.2))


def _score_nitrogen(crop: CropProfile, nitrogen: float) -> int:
    """Score nitrogen level suitability (0–10 points)."""
    if nitrogen >= crop.n_optimal:
        return 10
    elif nitrogen >= crop.n_min:
        ratio = (nitrogen - crop.n_min) / max(crop.n_optimal - crop.n_min, 1)
        return int(5 + ratio * 5)
    else:
        deficit = crop.n_min - nitrogen
        return max(0, int(5 - deficit * 0.15))


def _score_npk(crop: CropProfile, phosphorus: float, potassium: float) -> int:
    """Score NPK balance (0–8 points)."""
    score = 0
    if phosphorus >= crop.p_min:
        score += 4
    else:
        score += max(0, int(4 * phosphorus / crop.p_min))
    if potassium >= crop.k_min:
        score += 4
    else:
        score += max(0, int(4 * potassium / crop.k_min))
    return score


def _score_soil_type(crop: CropProfile, soil_type: str) -> int:
    """Score soil type compatibility (0–10 points)."""
    fit = crop.soil_fit.get(soil_type, 3)
    return fit + 2   # normalize to 0–10 scale (fit is 0–8)


def _get_grade(score: int) -> str:
    if score >= 90: return "A+"
    elif score >= 80: return "A"
    elif score >= 70: return "B+"
    elif score >= 60: return "B"
    else: return "C"


def _build_reason(crop: CropProfile, params: dict, score: int) -> str:
    """Generate a human-readable reason for the score."""
    positives, negatives = [], []

    if params["ph_min"] <= params.get("soil_ph", 6.5) <= params["ph_max"]:
        positives.append(f"soil pH {params.get('soil_ph',6.5)} is ideal")
    else:
        negatives.append(f"soil pH {params.get('soil_ph',6.5)} is outside optimal range")

    if crop.temp_min <= params.get("temperature", 28) <= crop.temp_max:
        positives.append(f"temperature {params.get('temperature',28)}°C suits well")
    else:
        negatives.append(f"temperature {params.get('temperature',28)}°C not ideal")

    if params.get("nitrogen", 38) >= crop.n_min:
        positives.append("nitrogen levels sufficient")
    else:
        negatives.append("nitrogen below recommended minimum")

    fit = crop.soil_fit.get(params.get("soil_type","Alluvial"), 3)
    if fit >= 6:
        positives.append(f"{params.get('soil_type','Alluvial')} soil highly compatible")
    elif fit <= 3:
        negatives.append(f"{params.get('soil_type','Alluvial')} soil not ideal")

    parts = []
    if positives:
        parts.append("; ".join(positives[:2]).capitalize())
    if negatives:
        parts.append("however " + negatives[0])
    return ". ".join(parts) + "." if parts else "Suitable under current conditions."


def score_crops(
    season:      str,
    soil_ph:     float,
    temperature: float,
    humidity:    float,
    nitrogen:    float,
    phosphorus:  float,
    potassium:   float,
    soil_type:   str  = "Alluvial",
    top_n:       int  = 4,
) -> List[CropScore]:
    """
    Main scoring function. Evaluates all crops for the given season
    and returns top_n ranked by composite suitability score.

    Parameters
    ----------
    season      : "Kharif" | "Rabi" | "Zaid"
    soil_ph     : Soil pH value (4.0 – 9.0)
    temperature : Air temperature °C
    humidity    : Relative humidity %
    nitrogen    : Soil nitrogen kg/ha
    phosphorus  : Soil phosphorus kg/ha
    potassium   : Soil potassium kg/ha
    soil_type   : One of Black Cotton / Alluvial / Red Laterite / Sandy Loam / Clay
    top_n       : Number of results to return

    Returns
    -------
    List of CropScore objects sorted by suitability descending.
    """
    season_crops = [c for c in CROPS if c.season == season]
    if not season_crops:
        season_crops = [c for c in CROPS if c.season == "Kharif"]

    params = {
        "soil_ph":    soil_ph,
        "temperature":temperature,
        "humidity":   humidity,
        "nitrogen":   nitrogen,
        "phosphorus": phosphorus,
        "potassium":  potassium,
        "soil_type":  soil_type,
        "ph_min":     0,
        "ph_max":     14,
    }

    results = []
    for crop in season_crops:
        params["ph_min"] = crop.ph_min
        params["ph_max"] = crop.ph_max

        ph_score    = _score_ph(crop, soil_ph)
        temp_score  = _score_temperature(crop, temperature)
        hum_score   = _score_humidity(crop, humidity)
        n_score     = _score_nitrogen(crop, nitrogen)
        npk_score   = _score_npk(crop, phosphorus, potassium)
        soil_score  = _score_soil_type(crop, soil_type)

        # Weighted composite score
        raw = (
            crop.base_score * 0.30 +
            ph_score        * 0.20 +
            temp_score      * 0.18 +
            hum_score       * 0.12 +
            n_score         * 0.10 +
            npk_score       * 0.05 +
            soil_score      * 0.05
        )

        final = int(min(99, max(40, round(raw))))

        results.append(CropScore(
            crop             = crop.name,
            icon             = crop.icon,
            category         = crop.category,
            season           = crop.season,
            suitability      = final,
            grade            = _get_grade(final),
            reason           = _build_reason(crop, params, final),
            growth_days      = crop.growth_days,
            water_need       = crop.water_need,
            water_mm         = crop.water_mm,
            market_price     = crop.market_price,
            msp_price        = crop.msp_price,
            profit_potential = crop.profit_potential,
            risk_level       = crop.risk_level,
            tags             = crop.tags,
            critical_stage   = crop.critical_stage,
            score_breakdown  = {
                "base":        crop.base_score,
                "ph":          ph_score,
                "temperature": temp_score,
                "humidity":    hum_score,
                "nitrogen":    n_score,
                "npk":         npk_score,
                "soil_type":   soil_score,
            },
            agronomic_tips   = crop.agronomic_tips,
        ))

    results.sort(key=lambda x: x.suitability, reverse=True)
    return results[:top_n]


# ─────────────────────────────────────────
#  HELPER UTILITIES
# ─────────────────────────────────────────

def get_all_seasons() -> List[str]:
    """Return list of all available seasons."""
    return list(set(c.season for c in CROPS))


def get_crops_by_season(season: str) -> List[str]:
    """Return crop names for a given season."""
    return [c.name for c in CROPS if c.season == season]


def get_crop_profile(name: str) -> Optional[CropProfile]:
    """Return full agronomic profile for a named crop."""
    for c in CROPS:
        if c.name.lower() == name.lower():
            return c
    return None


def get_water_efficient_crops(season: str, top_n: int = 3) -> List[str]:
    """Return crops with Low water requirement for a season."""
    low_water = [c.name for c in CROPS if c.season == season and c.water_need == "Low"]
    return low_water[:top_n]


def get_high_value_crops(season: str, top_n: int = 3) -> List[str]:
    """Return highest market value crops for a season."""
    season_crops = [c for c in CROPS if c.season == season and c.profit_potential in ["High", "Very High"]]
    return [c.name for c in season_crops[:top_n]]


def summarize_recommendation(scores: List[CropScore]) -> dict:
    """
    Build a human-readable summary dict from a list of CropScore results.
    Intended for the AI agent to narrate to the farmer.
    """
    if not scores:
        return {"summary": "No suitable crops found for current conditions."}

    top = scores[0]
    return {
        "top_crop":         top.crop,
        "top_score":        top.suitability,
        "top_grade":        top.grade,
        "top_reason":       top.reason,
        "top_market_price": top.market_price,
        "top_msp":          top.msp_price,
        "top_growth_days":  top.growth_days,
        "top_water_need":   top.water_need,
        "top_critical_stage": top.critical_stage,
        "runner_up":        scores[1].crop if len(scores) > 1 else None,
        "runner_up_score":  scores[1].suitability if len(scores) > 1 else None,
        "all_crops":        [s.crop for s in scores],
        "generated_at":     datetime.now().isoformat(),
    }


# ─────────────────────────────────────────
#  QUICK TEST (run directly)
# ─────────────────────────────────────────

if __name__ == "__main__":
    results = score_crops(
        season      = "Kharif",
        soil_ph     = 6.4,
        temperature = 28,
        humidity    = 65,
        nitrogen    = 38,
        phosphorus  = 22,
        potassium   = 45,
        soil_type   = "Black Cotton",
        top_n       = 4,
    )

    print("\n🌾 AgriMind AI — Crop Recommendation Engine")
    print("=" * 55)
    for i, r in enumerate(results, 1):
        print(f"\n#{i} {r.icon} {r.crop}")
        print(f"   Score     : {r.suitability}% ({r.grade})")
        print(f"   Reason    : {r.reason}")
        print(f"   Price     : {r.market_price}")
        print(f"   MSP       : {r.msp_price or 'N/A'}")
        print(f"   Growth    : {r.growth_days} days | Water: {r.water_need}")
        print(f"   Profit    : {r.profit_potential} | Risk: {r.risk_level}")
        print(f"   Breakdown : {r.score_breakdown}")
    print()

    summary = summarize_recommendation(results)
    print("📋 Summary:", summary)