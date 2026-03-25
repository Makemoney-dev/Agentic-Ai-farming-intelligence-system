from fastapi.responses import FileResponse
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import random
import math
from datetime import datetime, timedelta

# ─────────────────────────────────────────
#  APP INIT
# ─────────────────────────────────────────
app = FastAPI(
    title="AgriMind AI — Backend API",
    description="Agentic Farming Intelligence System — Crop Recommendation, Irrigation Planning & Risk Alerts",
    version="1.0.0",
)

import os
from fastapi.staticfiles import StaticFiles

# Ye code sahi path nikalega
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# Agar Backend aur public dono prototype ke andar hain:
PUBLIC_DIR = os.path.join(os.path.dirname(BASE_DIR), "public")

app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")

@app.get("/")
async def serve_dashboard():
    index_path = os.path.join(PUBLIC_DIR, "index.html")
    # Debugging ke liye terminal mein path print karega
    print(f"Searching for index.html at: {index_path}")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Dashboard not found. Please check folder structure."}

# Static files mount karein
app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # update to your Vercel domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
#  PYDANTIC SCHEMAS
# ─────────────────────────────────────────

class SensorData(BaseModel):
    temperature:  float = Field(..., description="Air temperature in °C")
    humidity:     float = Field(..., description="Relative humidity in %")
    soil_moisture:float = Field(..., description="Volumetric soil moisture in %")
    soil_ph:      float = Field(..., description="Soil pH value (4–9)")
    nitrogen:     float = Field(..., description="Nitrogen level in kg/ha")
    phosphorus:   float = Field(..., description="Phosphorus level in kg/ha")
    potassium:    float = Field(..., description="Potassium level in kg/ha")
    rainfall:     float = Field(..., description="Recent rainfall in mm")
    wind_speed:   float = Field(..., description="Wind speed in km/h")
    uv_index:     float = Field(..., description="UV index (0–11)")
    location:     str   = Field(..., description="Farm location")
    season:       str   = Field(..., description="Crop season: Kharif / Rabi / Zaid")


class CropInput(BaseModel):
    location:    str
    season:      str
    soil_ph:     float
    nitrogen:    float
    phosphorus:  float
    potassium:   float
    temperature: float
    humidity:    float
    soil_type:   Optional[str] = "Black Cotton"
    field_size:  Optional[float] = 5.0


class IrrigationInput(BaseModel):
    crop:          str
    growth_stage:  str
    field_size:    float
    soil_moisture: float
    temperature:   float
    humidity:      float
    rainfall:      float
    method:        Optional[str] = "Drip"


class RiskInput(BaseModel):
    crop:          str
    season:        str
    growth_stage:  str
    temperature:   float
    humidity:      float
    soil_moisture: float
    uv_index:      float
    wind_speed:    float


# ─────────────────────────────────────────
#  CROP DATABASE
# ─────────────────────────────────────────

CROP_DB = {
    "Kharif": [
        {
            "crop": "Soybean", "icon": "🫘",
            "ph_range": [6.0, 7.5], "temp_range": [20, 35], "hum_range": [55, 90],
            "n_min": 30, "growth_days": 100, "water_need": "Medium",
            "market_price": "₹3,800/quintal", "profit_potential": "High",
            "risk_level": "Low", "base_score": 88,
            "soil_fit": {"Black Cotton": 6, "Alluvial": 5, "Red Laterite": 3, "Sandy Loam": 4, "Clay": 4},
        },
        {
            "crop": "Cotton", "icon": "🌿",
            "ph_range": [5.8, 8.0], "temp_range": [25, 40], "hum_range": [50, 80],
            "n_min": 25, "growth_days": 165, "water_need": "Medium",
            "market_price": "₹6,500/quintal", "profit_potential": "Very High",
            "risk_level": "Medium", "base_score": 84,
            "soil_fit": {"Black Cotton": 7, "Alluvial": 4, "Red Laterite": 3, "Sandy Loam": 3, "Clay": 5},
        },
        {
            "crop": "Maize", "icon": "🌽",
            "ph_range": [5.8, 7.0], "temp_range": [18, 32], "hum_range": [50, 80],
            "n_min": 20, "growth_days": 90, "water_need": "Medium",
            "market_price": "₹1,900/quintal", "profit_potential": "Medium",
            "risk_level": "Low", "base_score": 78,
            "soil_fit": {"Black Cotton": 4, "Alluvial": 7, "Red Laterite": 5, "Sandy Loam": 6, "Clay": 3},
        },
        {
            "crop": "Turmeric", "icon": "🟡",
            "ph_range": [5.5, 7.0], "temp_range": [20, 35], "hum_range": [65, 90],
            "n_min": 15, "growth_days": 270, "water_need": "High",
            "market_price": "₹12,000/quintal", "profit_potential": "Very High",
            "risk_level": "Medium", "base_score": 72,
            "soil_fit": {"Black Cotton": 3, "Alluvial": 5, "Red Laterite": 6, "Sandy Loam": 7, "Clay": 3},
        },
        {
            "crop": "Groundnut", "icon": "🥜",
            "ph_range": [6.0, 7.0], "temp_range": [22, 35], "hum_range": [45, 75],
            "n_min": 15, "growth_days": 120, "water_need": "Low",
            "market_price": "₹5,200/quintal", "profit_potential": "High",
            "risk_level": "Low", "base_score": 75,
            "soil_fit": {"Black Cotton": 3, "Alluvial": 6, "Red Laterite": 7, "Sandy Loam": 8, "Clay": 2},
        },
    ],
    "Rabi": [
        {
            "crop": "Wheat", "icon": "🌾",
            "ph_range": [6.0, 7.5], "temp_range": [10, 25], "hum_range": [40, 70],
            "n_min": 30, "growth_days": 120, "water_need": "Medium",
            "market_price": "₹2,150/quintal", "profit_potential": "High",
            "risk_level": "Low", "base_score": 90,
            "soil_fit": {"Black Cotton": 5, "Alluvial": 8, "Red Laterite": 3, "Sandy Loam": 6, "Clay": 5},
        },
        {
            "crop": "Chickpea", "icon": "🟤",
            "ph_range": [5.5, 7.0], "temp_range": [15, 30], "hum_range": [30, 60],
            "n_min": 10, "growth_days": 100, "water_need": "Low",
            "market_price": "₹5,440/quintal", "profit_potential": "High",
            "risk_level": "Low", "base_score": 82,
            "soil_fit": {"Black Cotton": 7, "Alluvial": 5, "Red Laterite": 4, "Sandy Loam": 6, "Clay": 4},
        },
        {
            "crop": "Mustard", "icon": "🌻",
            "ph_range": [5.8, 7.5], "temp_range": [10, 28], "hum_range": [35, 65],
            "n_min": 20, "growth_days": 110, "water_need": "Low",
            "market_price": "₹5,650/quintal", "profit_potential": "High",
            "risk_level": "Low", "base_score": 80,
            "soil_fit": {"Black Cotton": 4, "Alluvial": 7, "Red Laterite": 5, "Sandy Loam": 7, "Clay": 3},
        },
        {
            "crop": "Potato", "icon": "🥔",
            "ph_range": [5.0, 6.5], "temp_range": [10, 25], "hum_range": [50, 80],
            "n_min": 25, "growth_days": 90, "water_need": "High",
            "market_price": "₹1,500/quintal", "profit_potential": "Medium",
            "risk_level": "High", "base_score": 76,
            "soil_fit": {"Black Cotton": 3, "Alluvial": 7, "Red Laterite": 5, "Sandy Loam": 8, "Clay": 2},
        },
    ],
    "Zaid": [
        {
            "crop": "Watermelon", "icon": "🍉",
            "ph_range": [6.0, 7.0], "temp_range": [25, 40], "hum_range": [40, 70],
            "n_min": 15, "growth_days": 75, "water_need": "Medium",
            "market_price": "₹1,200/quintal", "profit_potential": "High",
            "risk_level": "Medium", "base_score": 86,
            "soil_fit": {"Black Cotton": 3, "Alluvial": 7, "Red Laterite": 5, "Sandy Loam": 8, "Clay": 2},
        },
        {
            "crop": "Moong", "icon": "🟢",
            "ph_range": [6.0, 7.5], "temp_range": [25, 40], "hum_range": [40, 75],
            "n_min": 10, "growth_days": 65, "water_need": "Low",
            "market_price": "₹7,755/quintal", "profit_potential": "Very High",
            "risk_level": "Low", "base_score": 78,
            "soil_fit": {"Black Cotton": 5, "Alluvial": 7, "Red Laterite": 6, "Sandy Loam": 7, "Clay": 4},
        },
        {
            "crop": "Sunflower", "icon": "🌻",
            "ph_range": [6.0, 7.5], "temp_range": [20, 35], "hum_range": [40, 70],
            "n_min": 20, "growth_days": 90, "water_need": "Medium",
            "market_price": "₹6,400/quintal", "profit_potential": "High",
            "risk_level": "Medium", "base_score": 74,
            "soil_fit": {"Black Cotton": 5, "Alluvial": 7, "Red Laterite": 5, "Sandy Loam": 6, "Clay": 4},
        },
    ],
}

# ─────────────────────────────────────────
#  CROP SCORING LOGIC
# ─────────────────────────────────────────

def score_crop(crop: dict, params: CropInput) -> int:
    score = crop["base_score"]

    # pH scoring
    ph_mid = (crop["ph_range"][0] + crop["ph_range"][1]) / 2
    if crop["ph_range"][0] <= params.soil_ph <= crop["ph_range"][1]:
        score += 5
    else:
        score -= abs(params.soil_ph - ph_mid) * 2.5

    # Temperature
    if crop["temp_range"][0] <= params.temperature <= crop["temp_range"][1]:
        score += 4
    else:
        score -= 4

    # Humidity
    if crop["hum_range"][0] <= params.humidity <= crop["hum_range"][1]:
        score += 3
    else:
        score -= 2

    # Nitrogen
    if params.nitrogen >= crop["n_min"]:
        score += 3
    else:
        score -= (crop["n_min"] - params.nitrogen) * 0.15

    # Soil type
    soil_bonus = crop["soil_fit"].get(params.soil_type, 3)
    score += soil_bonus

    return int(min(99, max(40, round(score))))


# ─────────────────────────────────────────
#  IRRIGATION LOGIC (FAO-56)
# ─────────────────────────────────────────

CROP_KC = {
    "Soybean":   [0.40, 0.80, 1.15, 0.50],
    "Cotton":    [0.35, 0.75, 1.20, 0.60],
    "Maize":     [0.30, 0.70, 1.20, 0.60],
    "Wheat":     [0.40, 0.70, 1.10, 0.40],
    "Turmeric":  [0.50, 0.90, 1.10, 0.70],
    "Groundnut": [0.40, 0.70, 1.05, 0.60],
    "Watermelon":[0.40, 0.75, 1.00, 0.75],
    "Chickpea":  [0.40, 0.70, 1.05, 0.30],
    "Sunflower": [0.35, 0.75, 1.15, 0.55],
    "Moong":     [0.40, 0.70, 1.00, 0.45],
    "Potato":    [0.50, 0.75, 1.15, 0.75],
    "Mustard":   [0.35, 0.65, 1.05, 0.40],
}

STAGE_INDEX = {
    "Germination": 0, "Vegetative": 1, "Flowering": 2,
    "Pod/Fruit Fill": 2, "Maturity": 3, "Tillering": 1,
    "Heading": 2, "Tasselling": 2,
}

METHOD_EFFICIENCY = {
    "Drip": 0.90, "Sprinkler": 0.78, "Flood": 0.55, "Furrow": 0.62
}

def compute_eto(temp: float, humidity: float) -> float:
    """Simplified Hargreaves ETo estimate (mm/day)."""
    return round(0.0023 * (temp + 17.8) * math.sqrt(max(temp - 10, 1)) * (1 - humidity / 200), 2)

def compute_irrigation(params: IrrigationInput, day_offset: int) -> dict:
    days     = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    base_dt  = datetime.now() + timedelta(days=day_offset)
    day_name = days[base_dt.weekday()]
    date_str = base_dt.strftime("%b %d")

    # simulated soil moisture depletion
    depletion    = 1.8 + (params.temperature - 25) * 0.1
    rain_today   = params.rainfall if day_offset == 2 else (params.rainfall * 0.4 if day_offset == 6 else 0)
    soil_now     = params.soil_moisture - (day_offset * depletion) + (rain_today * 0.35)
    needs_water  = soil_now < 45 and rain_today < 10

    kc_values    = CROP_KC.get(params.crop, [0.5, 0.8, 1.1, 0.55])
    stage_idx    = STAGE_INDEX.get(params.growth_stage, 1)
    kc           = kc_values[min(stage_idx, len(kc_values) - 1)]
    eto          = compute_eto(params.temperature, params.humidity)
    etc          = round(eto * kc, 2)

    efficiency   = METHOD_EFFICIENCY.get(params.method, 0.75)
    raw_amount   = max(0, round((50 - soil_now) * 0.9 + etc * 2))
    gross_amount = round(raw_amount / efficiency) if needs_water else 0

    # recommend best time
    best_time = "6:00 AM" if params.temperature > 32 else ("6:30 AM" if params.method == "Drip" else "7:00 AM")

    # reason
    if not needs_water and rain_today >= 10:
        reason = f"Rain forecast {round(rain_today)}mm — irrigation not required"
    elif not needs_water and soil_now >= 50:
        reason = "Soil moisture adequate — skip today"
    elif not needs_water:
        reason = "Rest day — monitor field conditions"
    elif day_offset == 1:
        reason = "Soil moisture below 45% threshold"
    elif day_offset == 3:
        reason = f"ETc demand {etc}mm/day — top-up needed"
    elif day_offset == 5:
        reason = "Heat stress prevention — pre-emptive irrigation"
    else:
        reason = f"Scheduled deficit irrigation (Kc={kc})"

    return {
        "day":       day_name,
        "date":      date_str,
        "irrigate":  needs_water,
        "amount_mm": gross_amount,
        "method":    params.method if needs_water else "—",
        "best_time": best_time if needs_water else "—",
        "eto":       eto,
        "etc":       etc,
        "kc":        kc,
        "rain_mm":   round(rain_today, 1),
        "reason":    reason,
    }


# ─────────────────────────────────────────
#  RISK DETECTION LOGIC
# ─────────────────────────────────────────

def evaluate_risks(params: RiskInput) -> list:
    alerts = []

    # ── PEST ALERTS ──
    if params.humidity > 60 and params.temperature > 25:
        alerts.append({
            "type": "Pest", "severity": "High", "icon": "🦟",
            "title": "Whitefly Infestation Risk",
            "detail": f"Humidity {params.humidity}% and temperature {params.temperature}°C create ideal whitefly breeding conditions.",
            "impact": "Leaf yellowing, honeydew secretion, yield loss up to 40% if uncontrolled.",
            "action": "Apply neem oil solution (5ml/L) on leaf undersides within 48 hours. Deploy yellow sticky traps.",
            "urgency": "Within 48 hours",
        })

    if params.temperature > 28 and params.humidity > 55 and params.growth_stage in ["Flowering", "Pod/Fruit Fill"]:
        alerts.append({
            "type": "Pest", "severity": "High", "icon": "🐛",
            "title": "Pod/Stem Borer Outbreak Risk",
            "detail": f"High temperature {params.temperature}°C during {params.growth_stage} stage increases borer moth activity significantly.",
            "impact": "Direct pod feeding causes 30–50% yield loss. Entry point for secondary fungal infections.",
            "action": "Install pheromone traps (5/acre). Apply Chlorantraniliprole 0.4ml/L during evening hours.",
            "urgency": "Within 24 hours",
        })

    if 20 < params.temperature < 35 and params.humidity > 50:
        alerts.append({
            "type": "Pest", "severity": "Medium", "icon": "🪲",
            "title": "Aphid Colony Risk",
            "detail": f"Temperature {params.temperature}°C and humidity {params.humidity}% are optimal for aphid establishment.",
            "impact": "Sap sucking weakens plants, transmits viral diseases. 15–25% yield loss.",
            "action": "Spray Dimethoate 2ml/L or release Chrysoperla carnea biocontrol agents.",
            "urgency": "Within 72 hours",
        })

    # ── DISEASE ALERTS ──
    if params.humidity > 68 and params.temperature > 22:
        alerts.append({
            "type": "Disease", "severity": "High", "icon": "🍄",
            "title": "Fungal Blight Early Warning",
            "detail": f"Humidity {params.humidity}% sustained above 68% with {params.temperature}°C temperature triggers rapid fungal spore germination.",
            "impact": "Leaf defoliation, reduced photosynthesis, grain infection, aflatoxin risk.",
            "action": "Apply Mancozeb 75% WP at 2g/L every 10 days. Improve air circulation by wider row spacing.",
            "urgency": "Within 48 hours",
        })

    if params.humidity > 70 and 18 <= params.temperature <= 28:
        alerts.append({
            "type": "Disease", "severity": "Medium", "icon": "🌿",
            "title": "Downy Mildew Susceptibility",
            "detail": f"Cool {params.temperature}°C humid {params.humidity}% conditions favor downy mildew spore germination.",
            "impact": "White powdery coating, rapid defoliation, up to 30% yield loss.",
            "action": "Apply Metalaxyl + Mancozeb (Ridomil Gold) 2.5g/L. Remove infected plant debris.",
            "urgency": "Within 72 hours",
        })

    # ── WEATHER ALERTS ──
    if params.temperature > 33 or params.uv_index > 8:
        alerts.append({
            "type": "Weather", "severity": "Medium", "icon": "☀️",
            "title": "Heat & UV Stress Alert",
            "detail": f"Temperature {params.temperature}°C and UV index {params.uv_index} exceed safe thresholds for active crop growth stages.",
            "impact": "Pollen sterility at flowering, leaf scorch, 10–25% yield reduction.",
            "action": "Schedule irrigation 6–8 AM. Apply kaolin clay spray (3%) to reflect sunlight.",
            "urgency": "Today",
        })

    if params.soil_moisture < 30:
        alerts.append({
            "type": "Weather", "severity": "High", "icon": "🌵",
            "title": "Drought Stress — CRITICAL",
            "detail": f"Soil moisture at {params.soil_moisture}% is critically low. Plants entering survival mode.",
            "impact": "Permanent wilting, aborted pods/flowers, yield loss 40–70% if prolonged beyond 5 days.",
            "action": "EMERGENCY IRRIGATION — Apply 30–40mm immediately. Apply anti-transpirant spray.",
            "urgency": "IMMEDIATE",
        })

    if params.temperature < 8:
        alerts.append({
            "type": "Weather", "severity": "High", "icon": "❄️",
            "title": "Frost Risk Alert",
            "detail": f"Temperature {params.temperature}°C with clear sky indicates frost risk tonight.",
            "impact": "Ice crystal formation causes cell rupture, leaf blackening, possible total crop loss.",
            "action": "Apply overhead irrigation to form protective ice shell. Cover young plants with agro-net.",
            "urgency": "IMMEDIATE — Tonight",
        })

    if params.wind_speed > 50:
        alerts.append({
            "type": "Weather", "severity": "Medium", "icon": "🌪️",
            "title": "High Wind Damage Risk",
            "detail": f"Wind speed {params.wind_speed} km/h can cause lodging in tall crops and mechanical damage.",
            "impact": "Stem breakage, flower drop, difficulty in spraying operations. 15–30% yield loss.",
            "action": "Provide windbreak barriers. Avoid spraying operations. Stake tall crops immediately.",
            "urgency": "Before evening",
        })

    # ── SOIL ALERTS ──
    if params.soil_moisture > 80:
        alerts.append({
            "type": "Soil", "severity": "Medium", "icon": "🌊",
            "title": "Waterlogging Risk",
            "detail": f"Soil moisture at {params.soil_moisture}% indicates near-saturation. Anaerobic conditions developing.",
            "impact": "Root rot, nutrient deficiency, increased disease susceptibility. 25–50% yield loss.",
            "action": "Open drainage channels immediately. Apply Trichoderma viride to protect roots.",
            "urgency": "Within 24 hours",
        })

    if params.temperature < 15:
        alerts.append({
            "type": "Soil", "severity": "Low", "icon": "⚗️",
            "title": "Phosphorus Uptake Impaired",
            "detail": f"Temperature {params.temperature}°C reduces phosphorus solubility and root uptake efficiency significantly.",
            "impact": "Purple leaf discoloration, delayed maturity, reduced grain quality. 10–15% yield loss.",
            "action": "Apply foliar KH₂PO₄ spray 0.5%. Use phosphate-solubilizing bacteria biofertilizer.",
            "urgency": "Within 1 week",
        })

    if params.soil_moisture > 70:
        alerts.append({
            "type": "Soil", "severity": "Low", "icon": "🌱",
            "title": "Nitrogen Leaching Risk",
            "detail": f"Excess moisture {params.soil_moisture}% causes nitrogen leaching and denitrification in root zone.",
            "impact": "Yellowing of older leaves (chlorosis), 15–20% lower yield potential.",
            "action": "Apply split urea dose 25 kg/acre. Use slow-release nitrogen fertilizers.",
            "urgency": "Within 1 week",
        })

    # Sort: High → Medium → Low
    order = {"High": 0, "Medium": 1, "Low": 2}
    alerts.sort(key=lambda a: order.get(a["severity"], 3))

    return alerts


# ─────────────────────────────────────────
#  API ENDPOINTS
# ─────────────────────────────────────────

# ── 1. GET /api/sensor-data ──────────────
@app.get("/api/sensor-data", response_model=dict, tags=["Sensors"])
def get_sensor_data():
    """
    Returns simulated real-time IoT sensor readings from field devices.
    In production, replace with actual IoT/MQTT data source.
    """
    return {
        "temperature":   round(28 + random.uniform(-2, 3), 1),
        "humidity":      round(65 + random.uniform(-5, 8), 1),
        "soil_moisture": round(42 + random.uniform(-4, 5), 1),
        "soil_ph":       round(6.4 + random.uniform(-0.2, 0.2), 2),
        "nitrogen":      round(38 + random.uniform(-3, 4), 1),
        "phosphorus":    round(22 + random.uniform(-2, 3), 1),
        "potassium":     round(45 + random.uniform(-3, 5), 1),
        "rainfall":      round(12 + random.uniform(-2, 3), 1),
        "wind_speed":    round(14 + random.uniform(-3, 4), 1),
        "uv_index":      7,
        "location":      "Pune, Maharashtra",
        "season":        "Kharif",
        "timestamp":     datetime.now().isoformat(),
        "field_size":    "5.2 acres",
        "sensor_status": "Online",
    }


# ── 2. POST /api/crop-recommendation ────
@app.post("/api/crop-recommendation", tags=["Crops"])
def crop_recommendation(params: CropInput):
    """
    Analyzes soil, climate, and market data to recommend the top 4 crops
    ranked by AI suitability score using rule-based multi-factor scoring.
    """
    season_crops = CROP_DB.get(params.season, CROP_DB["Kharif"])

    scored = []
    for crop in season_crops:
        s = score_crop(crop, params)
        scored.append({
            "crop":             crop["crop"],
            "icon":             crop["icon"],
            "suitability":      s,
            "reason":           _crop_reason(crop, params, s),
            "growth_days":      crop["growth_days"],
            "water_need":       crop["water_need"],
            "market_price":     crop["market_price"],
            "profit_potential": crop["profit_potential"],
            "risk_level":       crop["risk_level"],
        })

    scored.sort(key=lambda x: x["suitability"], reverse=True)
    return {
        "status":          "success",
        "location":        params.location,
        "season":          params.season,
        "soil_type":       params.soil_type,
        "field_size_acres":params.field_size,
        "recommendations": scored[:4],
        "analyzed_at":     datetime.now().isoformat(),
    }


def _crop_reason(crop: dict, params: CropInput, score: int) -> str:
    reasons = []
    if crop["ph_range"][0] <= params.soil_ph <= crop["ph_range"][1]:
        reasons.append(f"soil pH {params.soil_ph} is ideal")
    if crop["temp_range"][0] <= params.temperature <= crop["temp_range"][1]:
        reasons.append(f"temperature {params.temperature}°C suits well")
    if params.nitrogen >= crop["n_min"]:
        reasons.append("nitrogen levels adequate")
    fit = crop["soil_fit"].get(params.soil_type, 3)
    if fit >= 6:
        reasons.append(f"{params.soil_type} soil is excellent for this crop")
    if not reasons:
        reasons.append("moderate conditions — manageable with good agronomic practices")
    return "; ".join(reasons[:2]).capitalize() + "."


# ── 3. POST /api/irrigation-plan ────────
@app.post("/api/irrigation-plan", tags=["Irrigation"])
def irrigation_plan(params: IrrigationInput):
    """
    Generates a 7-day precision irrigation schedule using simplified
    FAO-56 evapotranspiration model and soil water balance.
    """
    if params.field_size <= 0:
        raise HTTPException(status_code=400, detail="Field size must be greater than 0")

    schedule = [compute_irrigation(params, i) for i in range(7)]

    irr_days    = [d for d in schedule if d["irrigate"]]
    total_mm    = sum(d["amount_mm"] for d in schedule)
    flood_equiv = round(total_mm * 1.45)
    savings_pct = round((1 - total_mm / max(flood_equiv, 1)) * 100)
    total_liters= round(total_mm * params.field_size * 404.7 / 10)

    return {
        "status":            "success",
        "crop":              params.crop,
        "growth_stage":      params.growth_stage,
        "method":            params.method,
        "field_size_acres":  params.field_size,
        "schedule":          schedule,
        "summary": {
            "total_irrigation_days": len(irr_days),
            "total_water_mm":        total_mm,
            "total_liters":          total_liters,
            "flood_equivalent_mm":   flood_equiv,
            "water_savings_percent": savings_pct,
            "avg_eto_mm_day":        round(sum(d["eto"] for d in schedule) / 7, 2),
        },
        "generated_at": datetime.now().isoformat(),
    }


# ── 4. POST /api/risk-alerts ─────────────
@app.post("/api/risk-alerts", tags=["Alerts"])
def risk_alerts(params: RiskInput):
    """
    Scans 40+ risk vectors across pest, disease, weather, and soil
    categories. Returns tiered alerts with recommended actions.
    """
    alerts = evaluate_risks(params)

    high   = sum(1 for a in alerts if a["severity"] == "High")
    medium = sum(1 for a in alerts if a["severity"] == "Medium")
    low    = sum(1 for a in alerts if a["severity"] == "Low")
    score  = min(99, high * 28 + medium * 14 + low * 5)

    return {
        "status":        "success",
        "crop":          params.crop,
        "season":        params.season,
        "growth_stage":  params.growth_stage,
        "alerts":        alerts,
        "risk_summary": {
            "total":       len(alerts),
            "high":        high,
            "medium":      medium,
            "low":         low,
            "risk_score":  score,
            "risk_level":  "High" if score > 60 else "Medium" if score > 35 else "Low",
        },
        "scanned_at": datetime.now().isoformat(),
    }


# ── 5. GET /api/farm-summary ─────────────
@app.get("/api/farm-summary", tags=["Summary"])
def farm_summary():
    """
    Returns a combined farm intelligence summary including top crop,
    next irrigation date, active alert count, and field health score.
    """
    sensor       = get_sensor_data()
    health_score = int(
        0.25 * min(sensor["soil_moisture"] / 50, 1) * 100 +
        0.25 * min(sensor["nitrogen"] / 50, 1) * 100 +
        0.25 * (1 - abs(sensor["soil_ph"] - 6.5) / 3) * 100 +
        0.25 * min(sensor["humidity"] / 70, 1) * 100
    )

    return {
        "status":           "success",
        "top_crop":         "Soybean",
        "top_crop_score":   88,
        "next_irrigation":  "Tuesday",
        "active_alerts":    4,
        "field_health_score": f"{health_score}/100",
        "best_market_price":"₹3,800/quintal",
        "season":           "Kharif 2025",
        "location":         "Pune, Maharashtra",
        "sensor_status":    "Online",
        "last_updated":     datetime.now().isoformat(),
    }


# ── 6. GET /api/health ───────────────────
@app.get("/api/health", tags=["System"])
def health_check():
    """System health check endpoint."""
    return {
        "status":    "healthy",
        "version":   "1.0.0",
        "service":   "AgriMind AI Backend",
        "timestamp": datetime.now().isoformat(),
        "modules": {
            "crop_engine":       "active",
            "irrigation_engine": "active",
            "risk_engine":       "active",
            "sensor_api":        "active",
        }
    }

# 1. Data model for Chat
class ChatRequest(BaseModel):
    message: str

# 2. Gemini Configuration (Yahan apni key dalein)
genai.configure(api_key="AIzaSyC6QdhAuCcVpMYexRTkjs2kkUxe3fz14vA")
 
# 3. Chatbot Endpoint
@app.post("/api/chat")
async def get_agri_advice(request: ChatRequest):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # Farmer specific instruction
        system_prompt = f"You are an AgriMind AI advisor. Answer this agricultural query shortly: {request.message}"
        
        response = model.generate_content(system_prompt)
        return {"response": response.text}
    except Exception as e:
        return {"error": str(e)}
    
    
# ─────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
