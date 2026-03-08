# ─────────────────────────────────────────────────────────────────────
#  AgriMind AI — risk_logic.py
#  Risk Detection & Early Warning System
#  Covers: Pest · Disease · Weather · Soil · Market risks
# ─────────────────────────────────────────────────────────────────────

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import math


# ─────────────────────────────────────────
#  SEVERITY & CATEGORY CONSTANTS
# ─────────────────────────────────────────

class Severity:
    CRITICAL = "Critical"
    HIGH     = "High"
    MEDIUM   = "Medium"
    LOW      = "Low"

class Category:
    PEST     = "Pest"
    DISEASE  = "Disease"
    WEATHER  = "Weather"
    SOIL     = "Soil"
    NUTRIENT = "Nutrient"
    MARKET   = "Market"

SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH:     1,
    Severity.MEDIUM:   2,
    Severity.LOW:      3,
}

SEVERITY_SCORE = {
    Severity.CRITICAL: 40,
    Severity.HIGH:     25,
    Severity.MEDIUM:   12,
    Severity.LOW:       5,
}


# ─────────────────────────────────────────
#  DATA MODELS
# ─────────────────────────────────────────

@dataclass
class FarmParams:
    """
    Input parameters describing current farm conditions.
    Passed into the risk engine for evaluation.
    """
    crop:          str
    season:        str
    growth_stage:  str
    temperature:   float          # °C
    humidity:      float          # %
    soil_moisture: float          # %
    uv_index:      float          # 0–11
    wind_speed:    float          # km/h
    soil_ph:       float  = 6.5
    nitrogen:      float  = 40.0  # kg/ha
    phosphorus:    float  = 25.0  # kg/ha
    potassium:     float  = 40.0  # kg/ha
    rainfall_7d:   float  = 0.0   # mm last 7 days
    consecutive_humid_days: int = 0  # days humidity > 65%
    field_size:    float  = 5.0   # acres
    location:      str    = "Maharashtra"


@dataclass
class RiskAlert:
    """
    A single risk alert with full diagnostic and action information.
    """
    id:             str
    category:       str
    severity:       str
    icon:           str
    title:          str
    detail:         str
    impact:         str
    action:         str
    urgency:        str
    risk_score:     int           # Contribution to overall risk score
    conditions_met: List[str]     # Which conditions triggered this alert
    prevention:     List[str]
    dos:            List[str]
    donts:          List[str]
    products:       List[str]     # Recommended chemical/biological products
    cost_estimate:  str
    triggered_at:   str           = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class RiskReport:
    """
    Complete risk assessment report for a farm at a point in time.
    """
    crop:            str
    season:          str
    growth_stage:    str
    location:        str
    alerts:          List[RiskAlert]
    risk_score:      int           # 0–100 composite score
    risk_level:      str           # Low / Medium / High / Critical
    risk_breakdown:  Dict[str, int]
    top_priority:    Optional[str]
    summary:         str
    immediate_actions: List[str]
    weekly_checklist:  List[str]
    scanned_at:      str


# ─────────────────────────────────────────
#  RISK RULE DEFINITIONS
# ─────────────────────────────────────────

@dataclass
class RiskRule:
    """
    A single risk rule with trigger condition and alert template.
    """
    id:         str
    category:   str
    severity:   str
    icon:       str
    title:      str
    trigger:    Callable[[FarmParams], bool]
    conditions: Callable[[FarmParams], List[str]]
    detail:     Callable[[FarmParams], str]
    impact:     str
    action:     str
    urgency:    str
    prevention: List[str]
    dos:        List[str]
    donts:      List[str]
    products:   List[str]
    cost_estimate: str


# ─────────────────────────────────────────
#  RISK RULES DATABASE — 25 RULES
# ─────────────────────────────────────────

RISK_RULES: List[RiskRule] = [

    # ══════════════════════════════════════
    #  PEST RISKS
    # ══════════════════════════════════════

    RiskRule(
        id="whitefly", category=Category.PEST,
        severity=Severity.HIGH, icon="🦟",
        title="Whitefly Infestation Risk",
        trigger=lambda p: p.humidity > 60 and p.temperature > 25,
        conditions=lambda p: [
            f"Humidity {p.humidity}% > 60% threshold",
            f"Temperature {p.temperature}°C > 25°C threshold",
        ],
        detail=lambda p: (
            f"Humidity at {p.humidity}% combined with {p.temperature}°C temperature "
            f"creates ideal whitefly breeding conditions. Populations can double "
            f"every 7–10 days. Risk is {'very high' if p.humidity > 75 else 'high'} "
            f"during {p.growth_stage} stage when canopy is dense."
        ),
        impact="Leaf yellowing, honeydew secretion causing sooty mould, viral disease transmission. "
               "Yield loss 20–40% if population exceeds 10 adults/leaf.",
        action="Apply neem oil 5ml/L on leaf undersides. Deploy yellow sticky traps 10–12/acre. "
               "Spray early morning for best contact.",
        urgency="Within 48 hours",
        prevention=[
            "Install yellow sticky traps at crop canopy level immediately",
            "Apply reflective silver mulch to deter whitefly landing on leaves",
            "Avoid excess nitrogen fertilization — succulent growth attracts whitefly",
            "Plant trap crops (sunflower, marigold) around field border",
        ],
        dos=[
            "Spray neem oil early morning or evening for better contact",
            "Alternate between chemical classes to prevent resistance",
            "Monitor using sticky trap catches twice per week",
        ],
        donts=[
            "Do not spray during afternoon heat — reduces efficacy by 60%",
            "Do not apply same insecticide more than twice consecutively",
            "Do not ignore early signs — population explodes within 10 days",
        ],
        products=["Neem oil 5ml/L", "Imidacloprid 0.3ml/L", "Thiamethoxam 0.3g/L", "Spiromesifen 1ml/L"],
        cost_estimate="₹800–1,200/acre (neem oil spray)",
    ),

    RiskRule(
        id="pod_borer", category=Category.PEST,
        severity=Severity.HIGH, icon="🐛",
        title="Pod/Stem Borer Outbreak Risk",
        trigger=lambda p: p.temperature > 27 and p.humidity > 55 and
                          p.growth_stage in ["Flowering", "Pod/Fruit Fill", "Boll Formation"],
        conditions=lambda p: [
            f"Temperature {p.temperature}°C > 27°C (moth flight threshold)",
            f"Humidity {p.humidity}% > 55% (egg hatching favorable)",
            f"Growth stage {p.growth_stage} — most vulnerable to borer damage",
        ],
        detail=lambda p: (
            f"During {p.growth_stage} stage, high temperature {p.temperature}°C "
            f"and humidity {p.humidity}% favour peak pod borer moth activity at night. "
            f"Larvae bore into pods/bolls directly damaging seeds. "
            f"Single larvae can destroy 4–6 pods before pupating."
        ),
        impact="Direct pod/seed feeding causes 30–50% yield loss. Entry holes invite "
               "secondary fungal infections. Bored pods have zero market value.",
        action="Install pheromone traps 5/acre. Apply Chlorantraniliprole 0.4ml/L or "
               "Emamectin Benzoate 0.4g/L in evening. Avoid spraying during flowering.",
        urgency="Within 24 hours",
        prevention=[
            "Set pheromone traps 4 weeks before expected flowering stage",
            "Intercrop with marigold rows to repel pod borer moths naturally",
            "Apply Bacillus thuringiensis (Bt) spray every 7 days during flowering",
            "Deep plough after harvest to destroy pupae in soil",
        ],
        dos=[
            "Spray in evening when larvae are actively feeding on surface",
            "Use light traps to monitor adult moth population weekly",
            "Apply Bt spray 5 days before chemical spray for IPM compliance",
        ],
        donts=[
            "Do not spray systemic insecticides during peak flowering — harms bees",
            "Do not skip pheromone trap monitoring — early detection is critical",
            "Do not apply only one chemical class — resistance develops rapidly",
        ],
        products=["Chlorantraniliprole 0.4ml/L", "Emamectin Benzoate 0.4g/L",
                  "Bt (Bacillus thuringiensis) 2g/L", "Spinosad 0.3ml/L"],
        cost_estimate="₹1,500–2,500/acre (pheromone traps + spray)",
    ),

    RiskRule(
        id="aphid", category=Category.PEST,
        severity=Severity.MEDIUM, icon="🪲",
        title="Aphid Colony Establishment Risk",
        trigger=lambda p: 18 < p.temperature < 35 and p.humidity > 50,
        conditions=lambda p: [
            f"Temperature {p.temperature}°C in aphid optimal range 18–35°C",
            f"Humidity {p.humidity}% > 50% — favorable for colony growth",
        ],
        detail=lambda p: (
            f"Current conditions ({p.temperature}°C, {p.humidity}% RH) are optimal "
            f"for aphid colony establishment on {p.crop}. Winged forms are likely "
            f"migrating from nearby crops. Colonies double every 4–5 days under "
            f"these conditions."
        ),
        impact="Sap sucking causes leaf curl and stunting. Transmits 100+ plant viruses. "
               "Honeydew promotes sooty mould reducing photosynthesis. Yield loss 15–25%.",
        action="Spray Dimethoate 2ml/L or release Chrysoperla carnea biocontrol agents. "
               "Avoid excessive nitrogen fertilization.",
        urgency="Within 72 hours",
        prevention=[
            "Release Chrysoperla carnea (lacewing) 50,000 eggs/hectare as biocontrol",
            "Apply reflective mulch — disorients winged aphid forms trying to land",
            "Companion plant with coriander or dill to attract aphid predators",
            "Monitor shoot tips and leaf undersides twice weekly",
        ],
        dos=[
            "Begin treatment when colony size exceeds 10–15 aphids per shoot tip",
            "Apply systemic insecticide in morning for better translocation",
            "Encourage natural enemies — avoid broad-spectrum insecticides",
        ],
        donts=[
            "Do not apply pyrethroid sprays — kills natural predators, worsens aphid outbreak",
            "Do not over-irrigate — succulent growth attracts aphids",
            "Do not apply in hot afternoon — phytotoxicity risk increases",
        ],
        products=["Dimethoate 2ml/L", "Thiamethoxam 0.3g/L",
                  "Chrysoperla carnea (biocontrol)", "Verticillium lecanii 5g/L"],
        cost_estimate="₹400–800/acre",
    ),

    RiskRule(
        id="thrips", category=Category.PEST,
        severity=Severity.MEDIUM, icon="🔬",
        title="Thrips Infestation Risk",
        trigger=lambda p: p.temperature > 28 and p.humidity < 55 and p.wind_speed > 15,
        conditions=lambda p: [
            f"Temperature {p.temperature}°C > 28°C (thrips development optimal)",
            f"Humidity {p.humidity}% < 55% — dry conditions favor thrips spread",
            f"Wind speed {p.wind_speed}km/h > 15 — wind disperses thrips widely",
        ],
        detail=lambda p: (
            f"Hot dry weather ({p.temperature}°C, {p.humidity}% RH) with wind {p.wind_speed}km/h "
            f"is ideal for thrips buildup on {p.crop}. Thrips rasp leaf surface cells "
            f"causing silvery streaks. Can transmit Tomato Spotted Wilt Virus (TSWV)."
        ),
        impact="Silvery leaf streaks, flower distortion, scarring of fruits/pods. "
               "TSWV transmission causes total crop loss in susceptible varieties.",
        action="Apply Spinosad 0.3ml/L or Fipronil 2ml/L. Increase humidity with "
               "sprinkler irrigation during hottest part of day.",
        urgency="Within 48 hours",
        prevention=[
            "Use blue sticky traps for thrips monitoring — 5 traps/acre minimum",
            "Apply overhead sprinkler irrigation to disrupt thrips movement",
            "Remove and destroy heavily infested flowers and shoots immediately",
            "Avoid planting downwind of heavily infested neighboring fields",
        ],
        dos=[
            "Direct spray into growing points and flowers where thrips hide",
            "Apply Spinosad during cooler hours for maximum contact",
            "Monitor blue trap catches every 3 days during hot dry spells",
        ],
        donts=[
            "Do not use synthetic pyrethroids alone — thrips rapidly develop resistance",
            "Do not neglect flower-stage monitoring — thrips damage is irreversible",
            "Do not over-irrigate after thrips treatment — leaches soil-applied insecticides",
        ],
        products=["Spinosad 0.3ml/L", "Fipronil 2ml/L",
                  "Abamectin 0.5ml/L", "Beauveria bassiana 5g/L"],
        cost_estimate="₹600–1,000/acre",
    ),

    RiskRule(
        id="mites", category=Category.PEST,
        severity=Severity.MEDIUM, icon="🕷️",
        title="Red Spider Mite Risk",
        trigger=lambda p: p.temperature > 32 and p.humidity < 50,
        conditions=lambda p: [
            f"Temperature {p.temperature}°C > 32°C — mite reproduction accelerates",
            f"Humidity {p.humidity}% < 50% — hot dry conditions ideal for mites",
        ],
        detail=lambda p: (
            f"Extremely hot dry conditions ({p.temperature}°C, {p.humidity}% RH) favour "
            f"red spider mite population explosions. Mites complete lifecycle in just "
            f"5–7 days under these conditions. Colonies form on leaf undersides."
        ),
        impact="Bronze/rusty leaf appearance, premature leaf drop, up to 30% yield loss. "
               "Infestations spread rapidly — entire field affected within 2 weeks.",
        action="Spray Abamectin 0.5ml/L or Spiromesifen 1ml/L targeting leaf undersides. "
               "Apply acaricide, not insecticide — insecticides do not kill mites.",
        urgency="Within 72 hours",
        prevention=[
            "Apply overhead sprinkler irrigation in afternoon to increase humidity",
            "Avoid using pyrethroid insecticides that kill natural mite predators",
            "Release Phytoseiulus persimilis (predatory mite) as biological control",
            "Monitor leaf undersides with 10x hand lens every 5 days",
        ],
        dos=[
            "Use dedicated acaricides — regular insecticides are ineffective on mites",
            "Target leaf undersides where colonies are densest",
            "Alternate between different acaricide classes every spray",
        ],
        donts=[
            "Do not apply pyrethroid sprays — eliminates natural predators, worsens mite outbreak",
            "Do not wait for visible bronzing — treat at first signs of infestation",
            "Do not reuse water sprayed on infested plants on other areas",
        ],
        products=["Abamectin 0.5ml/L", "Spiromesifen 1ml/L",
                  "Hexythiazox 1g/L", "Bifenazate 2ml/L"],
        cost_estimate="₹700–1,200/acre",
    ),

    # ══════════════════════════════════════
    #  DISEASE RISKS
    # ══════════════════════════════════════

    RiskRule(
        id="fungal_blight", category=Category.DISEASE,
        severity=Severity.HIGH, icon="🍄",
        title="Fungal Blight Early Warning",
        trigger=lambda p: p.humidity > 68 and p.temperature > 22,
        conditions=lambda p: [
            f"Humidity {p.humidity}% > 68% — spore germination threshold exceeded",
            f"Temperature {p.temperature}°C > 22°C — mycelial growth optimal",
            f"Consecutive humid days: {p.consecutive_humid_days} days" if p.consecutive_humid_days > 2
            else "Extended leaf wetness period detected",
        ],
        detail=lambda p: (
            f"Sustained humidity {p.humidity}% with temperature {p.temperature}°C "
            f"for {max(p.consecutive_humid_days, 1)}+ days creates high-risk conditions "
            f"for fungal blight, early blight, and leaf spot diseases on {p.crop}. "
            f"Spores germinate within 8–12 hours under these conditions."
        ),
        impact="Leaf defoliation (20–40%), reduced photosynthesis, pod/grain infection, "
               "aflatoxin contamination risk in groundnut and maize. Yield loss 25–50%.",
        action="Apply Mancozeb 75% WP at 2g/L every 10 days as preventive spray. "
               "Improve air circulation. Avoid overhead irrigation during humid periods.",
        urgency="Within 48 hours",
        prevention=[
            "Apply copper oxychloride 3g/L as protective fungicide before rain",
            "Improve canopy air circulation through thinning or wider row spacing",
            "Avoid irrigating in evening — overnight leaf wetness promotes spore germination",
            "Remove and burn infected plant debris immediately to stop spore source",
        ],
        dos=[
            "Spray in early morning before dew dries for maximum efficacy",
            "Alternate between contact and systemic fungicides every spray",
            "Maintain spray interval at 7–10 days during continuous humid weather",
        ],
        donts=[
            "Do not spray when rain is expected within 6 hours — fungicide washed off",
            "Do not use only one fungicide class — resistance develops in 3–4 seasons",
            "Do not skip spray even if no visible symptoms — preventive treatment is critical",
        ],
        products=["Mancozeb 75% WP 2g/L", "Copper oxychloride 3g/L",
                  "Propiconazole 1ml/L", "Azoxystrobin 1ml/L"],
        cost_estimate="₹500–900/acre per spray",
    ),

    RiskRule(
        id="downy_mildew", category=Category.DISEASE,
        severity=Severity.MEDIUM, icon="🌿",
        title="Downy Mildew Susceptibility",
        trigger=lambda p: p.humidity > 70 and 16 <= p.temperature <= 28,
        conditions=lambda p: [
            f"Humidity {p.humidity}% > 70% — downy mildew spore germination favorable",
            f"Temperature {p.temperature}°C in optimal range 16–28°C for disease",
        ],
        detail=lambda p: (
            f"Cool humid conditions ({p.temperature}°C, {p.humidity}% RH) favour "
            f"Peronospora and Plasmopara downy mildew species on {p.crop}. "
            f"Sporangia are produced overnight and released in morning air currents."
        ),
        impact="White powdery growth on lower leaf surface, rapid defoliation, "
               "30% yield loss in susceptible varieties. Spreads rapidly under cool wet conditions.",
        action="Apply Metalaxyl + Mancozeb (Ridomil Gold) 2.5g/L. "
               "Remove and burn infected plant debris immediately.",
        urgency="Within 72 hours",
        prevention=[
            "Use Metalaxyl 35 WS seed treatment 6g/kg seed before sowing",
            "Avoid overhead irrigation — reduces leaf wetness duration significantly",
            "Ensure 45cm+ row spacing for adequate air movement",
            "Plant resistant varieties in areas with history of downy mildew",
        ],
        dos=[
            "Apply both lower and upper leaf surfaces during spray",
            "Start preventive sprays at first sign of forecast humid weather",
            "Use systemic fungicide Metalaxyl for curative action if already infected",
        ],
        donts=[
            "Do not apply contact fungicide alone after symptoms appear — use systemic",
            "Do not compost infected plant material — destroys oospores slowly",
            "Do not delay treatment — disease can destroy 30% of crop in 7 days",
        ],
        products=["Metalaxyl+Mancozeb 2.5g/L", "Dimethomorph 1g/L",
                  "Fosetyl-Al 2g/L", "Cymoxanil 0.8g/L"],
        cost_estimate="₹600–1,000/acre",
    ),

    RiskRule(
        id="powdery_mildew", category=Category.DISEASE,
        severity=Severity.MEDIUM, icon="⬜",
        title="Powdery Mildew Risk",
        trigger=lambda p: 22 < p.temperature < 30 and 40 < p.humidity < 70,
        conditions=lambda p: [
            f"Temperature {p.temperature}°C in powdery mildew optimal range 22–30°C",
            f"Moderate humidity {p.humidity}% — unlike most fungi, PM thrives without rain",
        ],
        detail=lambda p: (
            f"Powdery mildew thrives in moderate temperature {p.temperature}°C with "
            f"moderate humidity {p.humidity}% — unlike most fungal diseases, "
            f"it does NOT require free moisture and can develop during dry spells. "
            f"White powdery patches appear first on upper leaf surface of {p.crop}."
        ),
        impact="White powdery coating covers leaf surface, reduces photosynthesis by 30–40%. "
               "Infected pods/grains are shrivelled. Yield loss 15–25%.",
        action="Apply Sulphur 80% WP 3g/L or Trifloxystrobin 0.5ml/L. "
               "Spray wettable sulphur in early morning during cool weather.",
        urgency="Within 72 hours",
        prevention=[
            "Apply wettable sulphur 3g/L as preventive spray every 15 days",
            "Avoid dense planting — maintain proper plant spacing for air movement",
            "Use resistant varieties — check with local KVK for PM-resistant lines",
            "Apply potassium silicate 5g/L to strengthen cell walls",
        ],
        dos=[
            "Apply sulphur early morning — avoid application when temp > 35°C (phytotoxic)",
            "Alternate sulphur with DMI fungicides every 2 sprays",
            "Spray upper AND lower leaf surfaces thoroughly",
        ],
        donts=[
            "Do not apply sulphur when temperatures exceed 35°C — causes leaf burn",
            "Do not use oil-based sprays within 2 weeks of sulphur application",
            "Do not ignore infected plant debris — removes primary inoculum source",
        ],
        products=["Sulphur 80% WP 3g/L", "Trifloxystrobin 0.5ml/L",
                  "Hexaconazole 1ml/L", "Myclobutanil 1g/L"],
        cost_estimate="₹300–600/acre",
    ),

    RiskRule(
        id="root_rot", category=Category.DISEASE,
        severity=Severity.HIGH, icon="🫚",
        title="Root Rot & Collar Rot Risk",
        trigger=lambda p: p.soil_moisture > 75 and p.temperature > 25,
        conditions=lambda p: [
            f"Soil moisture {p.soil_moisture}% > 75% — anaerobic soil conditions developing",
            f"Temperature {p.temperature}°C > 25°C — Phytophthora/Fusarium growth optimal",
        ],
        detail=lambda p: (
            f"Excessive soil moisture {p.soil_moisture}% combined with warm temperature "
            f"{p.temperature}°C creates ideal conditions for Phytophthora, Fusarium, "
            f"and Pythium root rot pathogens on {p.crop}. Anaerobic soil kills beneficial "
            f"microbes while favouring pathogen spread."
        ),
        impact="Brown/black root discolouration, sudden wilting, plant death within 3–7 days. "
               "Disease spreads rapidly — can wipe out 40–60% of stand in affected patches.",
        action="Improve drainage immediately. Drench soil with Metalaxyl 2g/L + "
               "Trichoderma viride 5g/L around root zone. Avoid irrigation for 5–7 days.",
        urgency="Within 24 hours",
        prevention=[
            "Apply Trichoderma viride 2.5 kg/acre as soil treatment before planting",
            "Use raised beds or ridges in heavy soils prone to waterlogging",
            "Treat seeds with Carbendazim 2g/kg + Thiram 2g/kg before sowing",
            "Ensure proper field drainage channels are maintained and cleared",
        ],
        dos=[
            "Drench root zone — do not spray only foliage for root diseases",
            "Remove and destroy all wilted plants to prevent pathogen spread",
            "Apply biocontrol Trichoderma immediately after draining excess water",
        ],
        donts=[
            "Do not irrigate affected area until moisture drops below 50%",
            "Do not transplant healthy seedlings into recently affected soil patches",
            "Do not apply high nitrogen — succulent growth worsens root rot severity",
        ],
        products=["Metalaxyl 2g/L (drench)", "Trichoderma viride 5g/L",
                  "Copper oxychloride drench 3g/L", "Fosetyl-Al 3g/L"],
        cost_estimate="₹800–1,400/acre",
    ),

    # ══════════════════════════════════════
    #  WEATHER RISKS
    # ══════════════════════════════════════

    RiskRule(
        id="heat_stress", category=Category.WEATHER,
        severity=Severity.MEDIUM, icon="☀️",
        title="Heat & UV Stress Alert",
        trigger=lambda p: p.temperature > 33 or p.uv_index > 8,
        conditions=lambda p: [
            c for c in [
                f"Temperature {p.temperature}°C > 33°C threshold" if p.temperature > 33 else None,
                f"UV index {p.uv_index} > 8 — high radiation causing leaf scorch" if p.uv_index > 8 else None,
            ] if c
        ],
        detail=lambda p: (
            f"Temperature {p.temperature}°C {'and UV index ' + str(p.uv_index) if p.uv_index > 8 else ''} "
            f"exceed safe thresholds for {p.crop} at {p.growth_stage} stage. "
            f"Above 35°C, photosynthesis efficiency drops by 40%. Pollen sterility "
            f"occurs above 38°C during flowering — irreversible yield loss."
        ),
        impact="Pollen sterility at flowering (35–40°C), leaf scorch, accelerated maturity, "
               "reduced grain fill. Yield loss 10–30% per week of heat exposure.",
        action="Schedule irrigation 6–8 AM daily. Apply kaolin clay spray 3% to reflect "
               "sunlight. Apply potassium silicate 5g/L for heat tolerance.",
        urgency="Today",
        prevention=[
            "Apply kaolin clay particle film (Surround WP) 50g/L to reflect solar radiation",
            "Schedule all irrigation for early morning 5:30–8:00 AM only",
            "Apply potassium nitrate 13:0:45 foliar spray for heat stress tolerance",
            "Use shade nets 35% density over nursery beds and young transplants",
        ],
        dos=[
            "Irrigate in small frequent doses to maintain leaf turgor pressure",
            "Monitor stomatal closure — check leaves for rolling at midday",
            "Apply anti-transpirant spray to reduce water loss through leaves",
        ],
        donts=[
            "Do not spray chemical pesticides when temperature exceeds 35°C — phytotoxic",
            "Do not apply urea foliar spray during heat stress — causes leaf burn",
            "Do not skip morning irrigation on days forecast above 38°C",
        ],
        products=["Kaolin clay 3% spray", "Potassium silicate 5g/L",
                  "Anti-transpirant (Vapor Gard) 3ml/L", "KNO₃ 13:0:45 at 10g/L"],
        cost_estimate="₹300–600/acre",
    ),

    RiskRule(
        id="drought_stress", category=Category.WEATHER,
        severity=Severity.CRITICAL, icon="🌵",
        title="CRITICAL — Drought Stress Warning",
        trigger=lambda p: p.soil_moisture < 28,
        conditions=lambda p: [
            f"Soil moisture {p.soil_moisture}% is critically low — below wilting threshold",
            f"Plants entering permanent wilting zone — irreversible damage imminent",
        ],
        detail=lambda p: (
            f"Soil moisture at critically low {p.soil_moisture}% — approaching permanent "
            f"wilting point. {p.crop} at {p.growth_stage} stage is highly vulnerable. "
            f"Stomata are closed, photosynthesis halted, and root hair damage begins "
            f"within 24 hours if moisture is not restored."
        ),
        impact="Permanent wilting damage, aborted flowers and pods, shrivelled grains. "
               "Yield loss 40–70%. Root hair death after 48 hours is irreversible.",
        action="EMERGENCY IRRIGATION — Apply 35–45mm immediately. Apply anti-transpirant "
               "spray. Prioritize crown/root zone irrigation. Do NOT wait.",
        urgency="IMMEDIATE — Next 6 hours",
        prevention=[
            "Install soil moisture tensiometers at 15 cm and 30 cm depth for early warning",
            "Mulch entire field with crop residue 6–8 cm thick to conserve moisture",
            "Build rainwater harvesting bunds along field contour for water conservation",
            "Use deficit irrigation scheduling — maintain moisture above 45% always",
        ],
        dos=[
            "Apply emergency irrigation immediately — every hour of delay worsens damage",
            "Apply 5 kg/acre potassium sulfate to reduce osmotic stress in plants",
            "Install drip system if not present — most efficient for drought management",
        ],
        donts=[
            "Do not apply any fertilizer during drought stress — causes burn and osmotic shock",
            "Do not spray pesticides during drought — concentrated solutions cause phytotoxicity",
            "Do not rotary cultivate — destroys shallow feeder roots",
        ],
        products=["Anti-transpirant spray 3ml/L", "Potassium sulfate 5kg/acre",
                  "Zinc sulfate 0.5% spray for stress recovery"],
        cost_estimate="₹200–400/acre (emergency irrigation cost)",
    ),

    RiskRule(
        id="frost_risk", category=Category.WEATHER,
        severity=Severity.CRITICAL, icon="❄️",
        title="CRITICAL — Frost Risk Alert",
        trigger=lambda p: p.temperature < 7,
        conditions=lambda p: [
            f"Temperature {p.temperature}°C < 7°C — frost formation likely overnight",
            "Clear sky with low wind allows rapid radiative cooling of crop canopy",
        ],
        detail=lambda p: (
            f"Temperature at {p.temperature}°C with clear sky indicates radiation "
            f"frost risk tonight. Ice crystal formation in leaf cells begins at "
            f"0°C — causing permanent cellular rupture. {p.crop} at "
            f"{p.growth_stage} stage is {'highly' if p.growth_stage in ['Germination','Flowering'] else 'moderately'} "
            f"susceptible to frost damage."
        ),
        impact="Ice crystal formation causes cell rupture, leaf blackening, stem death. "
               "Complete crop loss possible in severe frost. Young plants most vulnerable.",
        action="Apply overhead sprinkler irrigation before frost — latent heat protects crop. "
               "Cover with agro-net or plastic mulch. Use anti-frost foggers if available.",
        urgency="IMMEDIATE — Before sunset tonight",
        prevention=[
            "Monitor nighttime temperature hourly using IoT sensor with SMS alerts",
            "Apply potassium nitrate foliar spray 1% for cold hardening (2 days before)",
            "Maintain moist soil — wet soil releases heat slowly and protects roots",
            "Install wind machines or fog generators in frost-prone areas",
        ],
        dos=[
            "Apply overhead irrigation 2 hours before expected frost to release latent heat",
            "Cover nursery beds and young plants with plastic or agro-net immediately",
            "Apply smoke generators upwind of field if available",
        ],
        donts=[
            "Do not remove protective covers until temperature rises above 4°C in morning",
            "Do not harvest frost-damaged fruit — allow to recover for 48 hours first",
            "Do not plant frost-sensitive crops in frost pocket areas (low-lying land)",
        ],
        products=["Potassium nitrate 1% foliar spray", "Anti-frost agro-net 30 GSM",
                  "Plastic mulch for row covering", "Smoke candles (organic)"],
        cost_estimate="₹1,000–2,500/acre (agro-net coverage)",
    ),

    RiskRule(
        id="flood_risk", category=Category.WEATHER,
        severity=Severity.HIGH, icon="🌊",
        title="Flood & Waterlogging Risk",
        trigger=lambda p: p.soil_moisture > 85 or p.rainfall_7d > 80,
        conditions=lambda p: [
            c for c in [
                f"Soil moisture {p.soil_moisture}% > 85% — field approaching saturation" if p.soil_moisture > 85 else None,
                f"7-day cumulative rainfall {p.rainfall_7d}mm > 80mm" if p.rainfall_7d > 80 else None,
            ] if c
        ],
        detail=lambda p: (
            f"{'Soil moisture ' + str(p.soil_moisture) + '%' if p.soil_moisture > 85 else 'Cumulative rainfall ' + str(p.rainfall_7d) + 'mm'} "
            f"indicates severe waterlogging risk for {p.crop}. Anaerobic conditions "
            f"develop within 24–48 hours — root respiration is blocked, causing rapid "
            f"decline in plant health and dramatically increasing disease susceptibility."
        ),
        impact="Root rot, nitrogen volatilization, nutrient deficiency. Anaerobic roots "
               "lose function within 48 hours. Yield loss 25–70% depending on duration.",
        action="Open drainage channels immediately. Apply Trichoderma viride to root zone. "
               "Create furrows to drain standing water. Avoid all field operations until drained.",
        urgency="Within 6 hours",
        prevention=[
            "Maintain clean field drainage channels before monsoon season",
            "Install subsurface drainage pipes in heavy clay/black cotton soils",
            "Plant on raised beds 15–20 cm high in flood-prone fields",
            "Apply gypsum 500 kg/acre to improve water percolation in clay soils",
        ],
        dos=[
            "Create breaches in field bunds to release standing water immediately",
            "Apply Trichoderma + Pseudomonas drench after water recedes to protect roots",
            "Spray zinc sulfate 0.5% after drainage for recovery of stunted plants",
        ],
        donts=[
            "Do not apply any fertilizer until field drains and plants recover (5–7 days)",
            "Do not use heavy machinery in waterlogged field — causes soil compaction",
            "Do not harvest prematurely — damaged plants may recover if drained quickly",
        ],
        products=["Trichoderma viride 2.5kg/acre (drench)", "Pseudomonas fluorescens 2.5kg/acre",
                  "Gypsum 500kg/acre", "Zinc sulfate 0.5% spray"],
        cost_estimate="₹500–800/acre (drainage + biocontrol)",
    ),

    RiskRule(
        id="high_wind", category=Category.WEATHER,
        severity=Severity.MEDIUM, icon="🌪️",
        title="High Wind — Crop Lodging Risk",
        trigger=lambda p: p.wind_speed > 45,
        conditions=lambda p: [
            f"Wind speed {p.wind_speed}km/h > 45km/h — lodging risk threshold exceeded",
            f"{p.crop} at {p.growth_stage} stage with top-heavy canopy",
        ],
        detail=lambda p: (
            f"Wind speed {p.wind_speed}km/h significantly exceeds lodging threshold "
            f"for {p.crop} at {p.growth_stage} stage. Stem breakage, uprooting, "
            f"and physical damage to pods/heads cause direct yield and quality losses."
        ),
        impact="Stem breakage, flower drop, difficult harvesting, 15–35% yield loss. "
               "Lodged crops have higher disease incidence due to poor air circulation.",
        action="Stake tall crops immediately. Avoid spraying operations until wind subsides. "
               "Erect windbreaks on windward side if feasible.",
        urgency="Today — before evening",
        prevention=[
            "Use short-statured, lodging-resistant varieties in wind-exposed fields",
            "Apply mepiquat chloride plant growth regulator for compact strong stem",
            "Maintain proper plant spacing — avoid dense planting that increases height",
            "Install windbreak tree rows (eucalyptus, casuarina) on field border",
        ],
        dos=[
            "Stake pepper, tomato, and tall varieties with bamboo poles immediately",
            "Apply phosphorus + potassium spray to strengthen stem tissue",
            "Harvest mature crops before predicted storm to avoid field losses",
        ],
        donts=[
            "Do not spray any chemical during wind speed >15 km/h — drift causes damage",
            "Do not apply high nitrogen during vegetative stage — excessive stem elongation",
            "Do not delay staking — once lodged, yield recovery is minimal",
        ],
        products=["Mepiquat chloride plant growth regulator", "K₂SO₄ 10g/L foliar spray",
                  "Bamboo stakes for support"],
        cost_estimate="₹200–500/acre (staking labour + material)",
    ),

    # ══════════════════════════════════════
    #  SOIL RISKS
    # ══════════════════════════════════════

    RiskRule(
        id="nitrogen_deficiency", category=Category.NUTRIENT,
        severity=Severity.LOW, icon="🌱",
        title="Nitrogen Deficiency Risk",
        trigger=lambda p: p.nitrogen < 30 or (p.soil_moisture > 72 and p.nitrogen < 50),
        conditions=lambda p: [
            c for c in [
                f"Nitrogen {p.nitrogen}kg/ha < 30 kg/ha minimum threshold" if p.nitrogen < 30 else None,
                f"High moisture {p.soil_moisture}% accelerating nitrogen leaching" if p.soil_moisture > 72 else None,
            ] if c
        ],
        detail=lambda p: (
            f"Nitrogen at {p.nitrogen} kg/ha is {'critically low' if p.nitrogen < 20 else 'below optimal'} "
            f"for {p.crop} at {p.growth_stage} stage. "
            f"{'Excess moisture ' + str(p.soil_moisture) + '% is leaching available nitrogen from root zone.' if p.soil_moisture > 72 else 'Deficiency will reduce chlorophyll synthesis and growth rate.'}"
        ),
        impact="Yellowing starting from older leaves (chlorosis), stunted growth, "
               "pale crop canopy, 15–25% yield reduction if not corrected within 2 weeks.",
        action="Apply urea 25 kg/acre as topdressing. Use slow-release nitrogen fertilizer. "
               "Split application: 50% now + 50% in 7 days.",
        urgency="Within 1 week",
        prevention=[
            "Apply nitrogen in 3 split doses — basal, tillering/vegetative, flowering",
            "Use nitrification inhibitors (neem-coated urea) to reduce leaching",
            "Apply FYM 5 ton/acre before planting as organic nitrogen buffer",
            "Soil test every season to calibrate nitrogen application rates precisely",
        ],
        dos=[
            "Apply urea as furrow placement or subsurface — reduces volatilization by 30%",
            "Use fertigation through drip for best nitrogen use efficiency (90%+)",
            "Apply foliar urea 1% as quick fix for severe deficiency symptoms",
        ],
        donts=[
            "Do not apply nitrogen broadcast before heavy rain — leaching losses > 40%",
            "Do not apply urea on waterlogged soil — denitrification losses are severe",
            "Do not delay correction beyond 2 weeks — yield loss becomes permanent",
        ],
        products=["Urea 46% N at 25 kg/acre", "Neem-coated urea (NCU)",
                  "Calcium ammonium nitrate (CAN)", "19:19:19 water-soluble at 5g/L"],
        cost_estimate="₹300–600/acre",
    ),

    RiskRule(
        id="phosphorus_deficiency", category=Category.NUTRIENT,
        severity=Severity.LOW, icon="⚗️",
        title="Phosphorus Availability Risk",
        trigger=lambda p: p.phosphorus < 20 or p.temperature < 14 or p.soil_ph > 7.8 or p.soil_ph < 5.5,
        conditions=lambda p: [
            c for c in [
                f"Phosphorus {p.phosphorus}kg/ha < 20 kg/ha minimum" if p.phosphorus < 20 else None,
                f"Low temperature {p.temperature}°C reduces phosphorus solubility" if p.temperature < 14 else None,
                f"Soil pH {p.soil_ph} outside optimal P availability range 6.0–7.0" if p.soil_ph > 7.8 or p.soil_ph < 5.5 else None,
            ] if c
        ],
        detail=lambda p: (
            f"Phosphorus availability is {'limited by low levels ' + str(p.phosphorus) + 'kg/ha' if p.phosphorus < 20 else ''}"
            f"{'and cold temperature ' + str(p.temperature) + '°C reducing solubility' if p.temperature < 14 else ''}. "
            f"Soil pH {p.soil_ph} {'(too alkaline — P fixed by calcium)' if p.soil_ph > 7.8 else '(too acidic — P fixed by aluminium/iron)' if p.soil_ph < 5.5 else ''} "
            f"further limits uptake by {p.crop} roots."
        ),
        impact="Purple/reddish discolouration on lower leaves, poor root development, "
               "delayed maturity, poor grain quality. Yield loss 10–20%.",
        action="Apply DAP 50 kg/acre as basal dose. Use PSB biofertilizer to solubilize "
               "fixed phosphorus. Correct soil pH to 6.0–7.0 for best availability.",
        urgency="Within 1 week",
        prevention=[
            "Apply phosphate fertilizer as basal dose before sowing — P does not move in soil",
            "Use PSB (Phosphate Solubilizing Bacteria) biofertilizer 5 kg/acre in soil",
            "Maintain soil organic matter > 1% — humic acids solubilize bound phosphorus",
            "Test soil pH and correct with lime (acidic) or sulfur (alkaline) before planting",
        ],
        dos=[
            "Place DAP in furrow near seed — P uptake zone is within 5 cm of root",
            "Apply foliar KH₂PO₄ 0.5% at vegetative stage as quick supplement",
            "Combine with zinc sulfate 0.5% — P and Zn deficiencies often co-occur",
        ],
        donts=[
            "Do not broadcast phosphorus on alkaline soils — fixation loss is very high",
            "Do not apply phosphorus without soil test — over-application locks out zinc",
            "Do not mix phosphorus fertilizer with urea — chemical reaction reduces availability",
        ],
        products=["DAP 18:46:0 at 50 kg/acre", "SSP 16% P₂O₅ at 75 kg/acre",
                  "PSB biofertilizer 5 kg/acre", "KH₂PO₄ 0.5% foliar spray"],
        cost_estimate="₹400–700/acre",
    ),

    RiskRule(
        id="soil_acidity", category=Category.SOIL,
        severity=Severity.MEDIUM, icon="🧪",
        title="Soil Acidity — pH Imbalance",
        trigger=lambda p: p.soil_ph < 5.8,
        conditions=lambda p: [
            f"Soil pH {p.soil_ph} < 5.8 — below optimal range for most crops",
            f"Acid soil reduces N, P, K and Ca availability; increases Al and Mn toxicity",
        ],
        detail=lambda p: (
            f"Soil pH {p.soil_ph} is in the acidic range. Below pH 5.5, aluminium "
            f"and manganese become toxic to {p.crop} roots. Phosphorus, calcium, "
            f"and magnesium availability drops sharply. Beneficial soil microbial "
            f"activity is severely reduced at pH < 5.5."
        ),
        impact="Root damage from Al/Mn toxicity, severe multi-nutrient deficiency, "
               "poor nodulation in legumes, 20–35% yield reduction in sensitive crops.",
        action="Apply agricultural lime 1–2 ton/acre. Incorporate into soil 4–6 weeks "
               "before planting. Retest soil pH 30 days after liming.",
        urgency="Next planting season preparation",
        prevention=[
            "Apply agricultural lime (CaCO₃) or dolomite lime annually in acidic soils",
            "Use ammonium nitrate instead of ammonium sulfate to slow acidification",
            "Apply wood ash 500 kg/acre as low-cost liming material for organic farms",
            "Maintain organic matter > 2% as natural pH buffer in root zone",
        ],
        dos=[
            "Incorporate lime 4–6 weeks before sowing for maximum pH change",
            "Apply lime in split doses — full dose at once may over-correct pH",
            "Combine lime with gypsum for soils needing calcium but not pH change",
        ],
        donts=[
            "Do not apply lime and urea together — nitrogen volatilization losses",
            "Do not over-lime — pH > 8.0 causes micronutrient deficiencies",
            "Do not expect immediate results — lime takes 4–8 weeks to react fully",
        ],
        products=["Agricultural lime CaCO₃ 1–2 t/acre", "Dolomite lime (Ca+Mg)",
                  "Wood ash 500 kg/acre", "Gypsum 500 kg/acre"],
        cost_estimate="₹800–1,500/acre (liming material + application)",
    ),

    RiskRule(
        id="soil_alkalinity", category=Category.SOIL,
        severity=Severity.MEDIUM, icon="🪨",
        title="Soil Alkalinity Risk",
        trigger=lambda p: p.soil_ph > 8.0,
        conditions=lambda p: [
            f"Soil pH {p.soil_ph} > 8.0 — alkaline conditions limit micronutrient uptake",
            f"Fe, Mn, Zn, B, Cu deficiency likely at this pH level",
        ],
        detail=lambda p: (
            f"Soil pH {p.soil_ph} in highly alkaline range. Iron, manganese, zinc, "
            f"and boron availability drops to near zero above pH 8.0. "
            f"{p.crop} will show interveinal chlorosis (iron deficiency) "
            f"and boron deficiency symptoms at this pH."
        ),
        impact="Iron chlorosis (yellow leaves with green veins), zinc deficiency stunting, "
               "poor pollen fertility due to boron deficiency. Yield loss 20–40%.",
        action="Apply elemental sulfur 50–75 kg/acre to lower pH. Apply chelated iron "
               "EDTA 3g/L as foliar spray. Use acidifying fertilizers ammonium sulfate.",
        urgency="Next planting season preparation",
        prevention=[
            "Apply elemental sulfur 50 kg/acre incorporated 6 weeks before planting",
            "Use ammonium sulfate (21% N) instead of urea — has mild acidifying effect",
            "Apply ferrous sulfate 25 kg/acre for quick iron supplementation",
            "Grow green manure crops (dhaincha, sunhemp) to release organic acids",
        ],
        dos=[
            "Apply chelated micronutrient mixtures as foliar spray for quick correction",
            "Use fertigation with acidic fertilizers to create localized pH reduction",
            "Test soil pH every season in irrigated fields using saline/alkaline water",
        ],
        donts=[
            "Do not apply lime or calcium-rich materials to already alkaline soils",
            "Do not use high-pH irrigation water without treatment in alkaline soils",
            "Do not apply DAP in alkaline soil — phosphorus precipitation is severe",
        ],
        products=["Elemental sulfur 50 kg/acre", "Ferrous sulfate 25 kg/acre",
                  "Chelated Fe-EDTA 3g/L foliar", "Zinc sulfate 25 kg/acre"],
        cost_estimate="₹600–1,200/acre",
    ),
]


# ─────────────────────────────────────────
#  RISK SCORING ENGINE
# ─────────────────────────────────────────

def compute_risk_score(alerts: List[RiskAlert]) -> int:
    """
    Compute composite farm risk score 0–100 from list of alerts.
    Weighted by severity — Critical alerts have highest weight.
    """
    raw = sum(SEVERITY_SCORE.get(a.severity, 5) for a in alerts)
    return min(99, raw)


def get_risk_level(score: int) -> str:
    """Map numeric risk score to risk level label."""
    if score >= 70:
        return "Critical"
    elif score >= 50:
        return "High"
    elif score >= 28:
        return "Medium"
    else:
        return "Low"


def build_risk_breakdown(alerts: List[RiskAlert]) -> Dict[str, int]:
    """Count alerts per category."""
    breakdown: Dict[str, int] = {}
    for alert in alerts:
        breakdown[alert.category] = breakdown.get(alert.category, 0) + 1
    return breakdown


def build_immediate_actions(alerts: List[RiskAlert]) -> List[str]:
    """Extract top 5 most urgent actions from High/Critical alerts."""
    urgent = [a for a in alerts if a.severity in [Severity.CRITICAL, Severity.HIGH]]
    actions = []
    for a in urgent[:5]:
        actions.append(f"[{a.severity.upper()}] {a.icon} {a.title}: {a.action.split('.')[0]}")
    return actions


def build_weekly_checklist(alerts: List[RiskAlert], params: FarmParams) -> List[str]:
    """Generate a practical weekly monitoring checklist."""
    checklist = [
        f"☐ Monitor {params.crop} field every morning for pest and disease symptoms",
        f"☐ Check soil moisture at 15cm and 30cm depth daily",
        f"☐ Verify irrigation system pressure and emitter uniformity",
        f"☐ Review IMD weather forecast for next 7 days at 8 AM daily",
        f"☐ Count sticky trap catches (yellow + blue) every 3 days",
    ]
    for alert in alerts:
        if alert.severity in [Severity.HIGH, Severity.CRITICAL]:
            checklist.append(f"☐ [{alert.severity}] {alert.icon} {alert.title}: {alert.dos[0] if alert.dos else alert.action[:60]}")
    return checklist[:8]


def build_summary(alerts: List[RiskAlert], params: FarmParams, score: int) -> str:
    """Generate a plain-language summary of the risk assessment."""
    level = get_risk_level(score)
    high_alerts = [a for a in alerts if a.severity in [Severity.CRITICAL, Severity.HIGH]]
    if not alerts:
        return (
            f"Farm risk assessment for {params.crop} at {params.location} shows "
            f"LOW RISK under current conditions. Continue routine monitoring."
        )
    top = high_alerts[0] if high_alerts else alerts[0]
    return (
        f"Risk assessment for {params.crop} ({params.growth_stage} stage) at "
        f"{params.location} shows {level.upper()} overall risk (score: {score}/100). "
        f"Primary concern: {top.title} — {top.action.split('.')[0]}. "
        f"Total {len(alerts)} alerts detected: "
        f"{sum(1 for a in alerts if a.severity == Severity.CRITICAL)} Critical, "
        f"{sum(1 for a in alerts if a.severity == Severity.HIGH)} High, "
        f"{sum(1 for a in alerts if a.severity == Severity.MEDIUM)} Medium, "
        f"{sum(1 for a in alerts if a.severity == Severity.LOW)} Low priority."
    )


# ─────────────────────────────────────────
#  MAIN RISK SCANNING FUNCTION
# ─────────────────────────────────────────

def scan_risks(params: FarmParams, min_severity: Optional[str] = None) -> RiskReport:
    """
    Evaluate all risk rules against current farm parameters.
    Returns a complete RiskReport with all triggered alerts.

    Parameters
    ----------
    params       : FarmParams — current farm conditions
    min_severity : Optional filter — return only alerts at or above this severity
                   Options: "Critical" | "High" | "Medium" | "Low" (default: all)

    Returns
    -------
    RiskReport with full alert list, scores, and recommendations.
    """
    alerts: List[RiskAlert] = []

    for rule in RISK_RULES:
        try:
            if rule.trigger(params):
                conditions = rule.conditions(params)
                detail     = rule.detail(params)
                alert = RiskAlert(
                    id             = rule.id,
                    category       = rule.category,
                    severity       = rule.severity,
                    icon           = rule.icon,
                    title          = rule.title,
                    detail         = detail,
                    impact         = rule.impact,
                    action         = rule.action,
                    urgency        = rule.urgency,
                    risk_score     = SEVERITY_SCORE[rule.severity],
                    conditions_met = conditions,
                    prevention     = rule.prevention,
                    dos            = rule.dos,
                    donts          = rule.donts,
                    products       = rule.products,
                    cost_estimate  = rule.cost_estimate,
                )
                alerts.append(alert)
        except Exception:
            continue

    # Sort: Critical → High → Medium → Low
    alerts.sort(key=lambda a: SEVERITY_ORDER.get(a.severity, 4))

    # Apply severity filter
    if min_severity and min_severity in SEVERITY_ORDER:
        threshold = SEVERITY_ORDER[min_severity]
        alerts = [a for a in alerts if SEVERITY_ORDER.get(a.severity, 4) <= threshold]

    # Compute scores and summary
    score     = compute_risk_score(alerts)
    level     = get_risk_level(score)
    breakdown = build_risk_breakdown(alerts)
    top       = alerts[0].title if alerts else None
    summary   = build_summary(alerts, params, score)

    return RiskReport(
        crop             = params.crop,
        season           = params.season,
        growth_stage     = params.growth_stage,
        location         = params.location,
        alerts           = alerts,
        risk_score       = score,
        risk_level       = level,
        risk_breakdown   = breakdown,
        top_priority     = top,
        summary          = summary,
        immediate_actions= build_immediate_actions(alerts),
        weekly_checklist = build_weekly_checklist(alerts, params),
        scanned_at       = datetime.now().isoformat(),
    )


# ─────────────────────────────────────────
#  HELPER UTILITIES
# ─────────────────────────────────────────

def get_alerts_by_category(report: RiskReport, category: str) -> List[RiskAlert]:
    """Filter alerts by category from a completed risk report."""
    return [a for a in report.alerts if a.category == category]


def get_alerts_by_severity(report: RiskReport, severity: str) -> List[RiskAlert]:
    """Filter alerts by severity from a completed risk report."""
    return [a for a in report.alerts if a.severity == severity]


def get_all_products(report: RiskReport) -> List[str]:
    """Extract unique product recommendations from all alerts."""
    products = []
    seen     = set()
    for alert in report.alerts:
        for p in alert.products:
            if p not in seen:
                products.append(p)
                seen.add(p)
    return products


def estimate_treatment_cost(report: RiskReport) -> str:
    """Rough estimate of total treatment cost from all alert cost estimates."""
    return f"Estimated total treatment cost: ₹{len(report.alerts) * 600}–{len(report.alerts) * 1200}/acre"


def format_report_terminal(report: RiskReport) -> str:
    """Format risk report as ASCII output for terminal display."""
    out  = f"\n{'═'*70}\n"
    out += f"  AgriMind AI — Risk Report\n"
    out += f"  Crop: {report.crop} | Stage: {report.growth_stage} | Location: {report.location}\n"
    out += f"  Risk Score: {report.risk_score}/100 — {report.risk_level.upper()}\n"
    out += f"{'═'*70}\n\n"

    if not report.alerts:
        out += "  ✅ No risk alerts detected under current conditions.\n"
        return out

    for i, a in enumerate(report.alerts, 1):
        out += f"  {'─'*66}\n"
        out += f"  {i}. {a.icon} [{a.severity.upper()}] {a.title}\n"
        out += f"     Category  : {a.category}\n"
        out += f"     Urgency   : {a.urgency}\n"
        out += f"     Detail    : {a.detail[:90]}...\n"
        out += f"     Action    : {a.action[:90]}\n"
        out += f"     Cost      : {a.cost_estimate}\n"

    out += f"\n  {'═'*70}\n"
    out += f"  SUMMARY: {report.summary}\n"
    out += f"\n  IMMEDIATE ACTIONS:\n"
    for action in report.immediate_actions:
        out += f"  → {action}\n"
    out += f"{'═'*70}\n"
    return out


# ─────────────────────────────────────────
#  QUICK TEST (run directly)
# ─────────────────────────────────────────

if __name__ == "__main__":
    params = FarmParams(
        crop                   = "Soybean",
        season                 = "Kharif",
        growth_stage           = "Flowering",
        temperature            = 29.0,
        humidity               = 72.0,
        soil_moisture          = 38.0,
        uv_index               = 8.5,
        wind_speed             = 18.0,
        soil_ph                = 6.4,
        nitrogen               = 28.0,
        phosphorus             = 18.0,
        potassium              = 40.0,
        rainfall_7d            = 45.0,
        consecutive_humid_days = 4,
        field_size             = 5.2,
        location               = "Pune, Maharashtra",
    )

    report = scan_risks(params)
    print(format_report_terminal(report))

    print(f"  Risk Breakdown : {report.risk_breakdown}")
    print(f"  Top Priority   : {report.top_priority}")
    print(f"  Products Needed: {get_all_products(report)[:5]}")
    print(f"  {estimate_treatment_cost(report)}")
    print(f"\n  Weekly Checklist:")
    for item in report.weekly_checklist:
        print(f"    {item}")