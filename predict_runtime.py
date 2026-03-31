import json
import math
import sys
from datetime import date as dt_date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import joblib
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "bowler-DatsetFinal.csv"
INTERNATIONAL_MODEL_PATH = BASE_DIR / "international-mode.pkl"
LOCAL_MODEL_PATH = BASE_DIR / "local-mode.pkl"

CURRENT_SRI_LANKA_BOWLERS = [
    {"bowler_name": "Wanindu Hasaranga", "bowler_type": "Right Arm Leg Spin"},
    {"bowler_name": "Maheesh Theekshana", "bowler_type": "Off Spin"},
    {"bowler_name": "Dushmantha Chameera", "bowler_type": "Right Arm Pace"},
    {"bowler_name": "Dilshan Madushanka", "bowler_type": "Left Arm Pace"},
    {"bowler_name": "Matheesha Pathirana", "bowler_type": "Right Arm Pace"},
    {"bowler_name": "Dhananjaya de Silva", "bowler_type": "Off Spin"},
    {"bowler_name": "Nuwan Thushara", "bowler_type": "Right Arm Pace"},
    {"bowler_name": "Eshan Malinga", "bowler_type": "Right Arm Pace"},
    {"bowler_name": "Jeffrey Vandersay", "bowler_type": "Right Arm Leg Spin"},
    {"bowler_name": "Dunith Wellalage", "bowler_type": "Left Arm Spin"},
    {"bowler_name": "Asitha Fernando", "bowler_type": "Right Arm Pace"},
    {"bowler_name": "Binura Fernando", "bowler_type": "Left Arm Pace"},
    {"bowler_name": "Dushan Hemantha", "bowler_type": "Right Arm Leg Spin"},
]

SRI_LANKA_LOCATIONS = {
    "Colombo": {"latitude": 6.9271, "longitude": 79.8612, "timezone": "Asia/Colombo"},
    "Kandy": {"latitude": 7.2906, "longitude": 80.6337, "timezone": "Asia/Colombo"},
    "Galle": {"latitude": 6.0535, "longitude": 80.2210, "timezone": "Asia/Colombo"},
    "Jaffna": {"latitude": 9.6615, "longitude": 80.0255, "timezone": "Asia/Colombo"},
    "Dambulla": {"latitude": 7.8567, "longitude": 80.6510, "timezone": "Asia/Colombo"},
    "Hambantota": {"latitude": 6.1241, "longitude": 81.1185, "timezone": "Asia/Colombo"},
    "Kurunegala": {"latitude": 7.4863, "longitude": 80.3647, "timezone": "Asia/Colombo"},
    "Matara": {"latitude": 5.9549, "longitude": 80.5550, "timezone": "Asia/Colombo"},
    "Negombo": {"latitude": 7.2083, "longitude": 79.8358, "timezone": "Asia/Colombo"},
    "Rathnapura": {"latitude": 6.6828, "longitude": 80.3992, "timezone": "Asia/Colombo"},
    "Anuradhapura": {"latitude": 8.3114, "longitude": 80.4037, "timezone": "Asia/Colombo"},
    "Trincomalee": {"latitude": 8.5874, "longitude": 81.2152, "timezone": "Asia/Colombo"},
    "Batticaloa": {"latitude": 7.7102, "longitude": 81.6924, "timezone": "Asia/Colombo"},
    "Badulla": {"latitude": 6.9934, "longitude": 81.0550, "timezone": "Asia/Colombo"},
}

GROUND_LOCATIONS = {
    "R. Premadasa Stadium": {"name": "R. Premadasa Stadium", "latitude": 6.9371, "longitude": 79.8730, "timezone": "Asia/Colombo"},
    "R Premadasa Stadium": {"name": "R. Premadasa Stadium", "latitude": 6.9371, "longitude": 79.8730, "timezone": "Asia/Colombo"},
    "Pallekele International Cricket Stadium": {"name": "Pallekele International Cricket Stadium", "latitude": 7.2803, "longitude": 80.7228, "timezone": "Asia/Colombo"},
    "Galle International Stadium": {"name": "Galle International Stadium", "latitude": 6.0328, "longitude": 80.2168, "timezone": "Asia/Colombo"},
    "Rangiri Dambulla International Stadium": {"name": "Rangiri Dambulla International Stadium", "latitude": 7.8567, "longitude": 80.6510, "timezone": "Asia/Colombo"},
    "Mahinda Rajapaksa Stadium": {"name": "Mahinda Rajapaksa Stadium", "latitude": 6.0999, "longitude": 80.9342, "timezone": "Asia/Colombo"},
    "SSC Colombo": {"name": "SSC Colombo", "latitude": 6.9062, "longitude": 79.8707, "timezone": "Asia/Colombo"},
    "Sydney Cricket Ground": {"name": "Sydney Cricket Ground", "latitude": -33.8917, "longitude": 151.2240, "timezone": "Australia/Sydney"},
    "Melbourne Cricket Ground": {"name": "Melbourne Cricket Ground", "latitude": -37.8199, "longitude": 144.9834, "timezone": "Australia/Melbourne"},
    "The Oval": {"name": "The Oval", "latitude": 51.4839, "longitude": -0.1140, "timezone": "Europe/London"},
    "London (The Oval)": {"name": "The Oval", "latitude": 51.4839, "longitude": -0.1140, "timezone": "Europe/London"},
    "Lord's": {"name": "Lord's", "latitude": 51.5290, "longitude": -0.1722, "timezone": "Europe/London"},
    "Eden Park": {"name": "Eden Park", "latitude": -36.8750, "longitude": 174.7448, "timezone": "Pacific/Auckland"},
    "Wankhede Stadium": {"name": "Wankhede Stadium", "latitude": 18.9389, "longitude": 72.8258, "timezone": "Asia/Kolkata"},
}

BOWLER_TYPE_NAME_OVERRIDES = {
    "Kuldeep Yadav": "LeftArmLegBreak",
    "Tabraiz Shamsi": "LeftArmLegBreak",
    "Jeffrey Vandersay": "RightArmLegBreak",
    "Rashid Khan": "RightArmLegBreak",
}

HOURLY_WEATHER_VARS = ",".join(
    [
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "pressure_msl",
        "cloud_cover",
        "wind_speed_10m",
        "wind_gusts_10m",
        "precipitation",
    ]
)


def normalize_bowler_type_label(name, bowler_type):
    name = str(name).strip()
    bowler_type = str(bowler_type).strip()

    if bowler_type == "RightArmRightArmLegBreak":
        return "RightArmLegBreak"
    if bowler_type == "LeftArmRightArmLegBreak":
        return BOWLER_TYPE_NAME_OVERRIDES.get(name, bowler_type)
    return bowler_type


def clean_bowler_type(value):
    value = str(value).strip().lower()
    if "fast" in value or "medium" in value or "pace" in value:
        if "left" in value:
            return "Left Arm Pace"
        return "Right Arm Pace"
    if "leftarmlegbreak" in value or "left arm leg" in value or "chinaman" in value or "unorthodox" in value:
        return "Left Arm Wrist Spin"
    if "leg" in value:
        return "Right Arm Leg Spin"
    if "off" in value:
        return "Off Spin"
    if "orthodox" in value or "left arm spin" in value:
        return "Left Arm Spin"
    return "Other"


def clean_pitch_type(value):
    value = str(value).strip().lower()
    if "green" in value:
        return "Green"
    if "dry" in value:
        return "Dry"
    if "slow" in value:
        return "Slow"
    if "flat" in value:
        return "Flat"
    return "Other"


def is_pace_type(bowler_type):
    return clean_bowler_type(bowler_type) in {"Right Arm Pace", "Left Arm Pace"}


def bowler_role_label(bowler_type):
    return "pace" if is_pace_type(bowler_type) else "spin"


def format_percent(value):
    return f"{float(value):.0f}%"


def format_float(value, digits=2):
    return f"{float(value):.{digits}f}"


def derive_match_period(start_time):
    hour = int(str(start_time).split(":")[0])
    return "night" if hour >= 18 else "day"


def load_json_url(url):
    with urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def geocode_place(place, country_code=None):
    if place in GROUND_LOCATIONS:
        return GROUND_LOCATIONS[place]
    params = {"name": place, "count": 1, "language": "en", "format": "json"}
    if country_code:
        params["countryCode"] = country_code
    url = f"https://geocoding-api.open-meteo.com/v1/search?{urlencode(params)}"
    data = load_json_url(url)
    results = data.get("results") or []
    if not results:
        raise ValueError(f"Could not geocode location: {place}")
    result = results[0]
    return {
        "name": result.get("name", place),
        "latitude": result["latitude"],
        "longitude": result["longitude"],
        "timezone": result.get("timezone", "auto"),
    }


def fetch_forecast_weather(latitude, longitude, timezone, match_date, start_time):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": match_date,
        "end_date": match_date,
        "hourly": HOURLY_WEATHER_VARS,
        "timezone": timezone or "auto",
    }
    url = f"https://api.open-meteo.com/v1/forecast?{urlencode(params)}"
    data = load_json_url(url)
    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        raise ValueError("No hourly weather returned from forecast API")

    target_minutes = _time_to_minutes(start_time)
    best_index = 0
    best_diff = math.inf
    for idx, ts in enumerate(times):
        time_part = ts.split("T")[1]
        diff = abs(_time_to_minutes(time_part) - target_minutes)
        if diff < best_diff:
            best_diff = diff
            best_index = idx

    return {
        "weather_time": times[best_index],
        "temperature_2m": float(hourly["temperature_2m"][best_index]),
        "relative_humidity_2m": float(hourly["relative_humidity_2m"][best_index]),
        "dew_point_2m": float(hourly["dew_point_2m"][best_index]),
        "pressure_msl": float(hourly["pressure_msl"][best_index]),
        "cloud_cover": float(hourly["cloud_cover"][best_index]),
        "wind_speed_10m": float(hourly["wind_speed_10m"][best_index]),
        "wind_gusts_10m": float(hourly["wind_gusts_10m"][best_index]),
        "precipitation": float(hourly["precipitation"][best_index]),
    }


def _time_to_minutes(value):
    hh, mm = str(value).split(":")[:2]
    return int(hh) * 60 + int(mm)


def load_model_bundle(path):
    bundle = joblib.load(path)
    if not isinstance(bundle, dict):
        raise ValueError(f"Unexpected model bundle format for {path}")
    return bundle


def load_source_dataframe():
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.strip()
    df = df.dropna(how="all").copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    if "overs" not in df.columns:
        runs_num = pd.to_numeric(df.get("runs"), errors="coerce")
        economy_num = pd.to_numeric(df.get("economy"), errors="coerce")
        df["overs"] = np.where(economy_num.gt(0), runs_num / economy_num, np.nan)

    numeric_cols = [
        "wickets",
        "runs",
        "economy",
        "overs",
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "pressure_msl",
        "cloud_cover",
        "wind_speed_10m",
        "wind_gusts_10m",
        "precipitation",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["match_type", "pitch_type", "ground", "your_team", "opposition_team", "bowler_type", "match_period", "bowler_name"]:
        df[col] = df[col].astype(str).str.strip()

    df["match_type"] = df["match_type"].str.upper()
    df["pitch_type"] = df["pitch_type"].apply(clean_pitch_type)
    df["bowler_type"] = df.apply(lambda row: normalize_bowler_type_label(row["bowler_name"], row["bowler_type"]), axis=1)
    df["bowler_type"] = df["bowler_type"].apply(clean_bowler_type)
    df["did_well"] = (
        ((df["wickets"] >= 1) & (df["economy"] <= 7.0)) |
        ((df["wickets"] == 0) & (df["economy"] <= 3.0))
    ).astype(int)
    return df


SOURCE_DF = load_source_dataframe()
INTERNATIONAL_MODEL = load_model_bundle(INTERNATIONAL_MODEL_PATH)
LOCAL_MODEL = load_model_bundle(LOCAL_MODEL_PATH)


def extract_model_factors(model_bundle, top_n=12):
    pipeline = model_bundle["pipeline"]
    model = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocessor"]

    try:
        feature_names = preprocessor.get_feature_names_out()
    except Exception:
        feature_names = [f"feature_{idx}" for idx in range(len(model.feature_importances_))]

    importance_df = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    def prettify(name):
        text = str(name)
        prefixes = ["num__", "cat__"]
        for prefix in prefixes:
            if text.startswith(prefix):
                text = text[len(prefix):]
        text = text.replace("onehot__", "").replace("imputer__", "")
        return text

    overall = [
        {
            "feature": prettify(row["feature"]),
            "importance": round(float(row["importance"]), 4),
        }
        for _, row in importance_df.head(top_n).iterrows()
    ]

    condition_mask = importance_df["feature"].str.contains(
        "pitch|dew|humidity|cloud|wind|temperature|weather|pace|spin|match_period|start|time_bucket|regime",
        case=False,
        na=False,
    )
    condition_related = [
        {
            "feature": prettify(row["feature"]),
            "importance": round(float(row["importance"]), 4),
        }
        for _, row in importance_df[condition_mask].head(top_n).iterrows()
    ]

    return {
        "overall_top_features": overall,
        "condition_related_features": condition_related,
    }


def build_international_history(frame):
    out = frame.sort_values(["date", "start_time"]).copy()
    bowler_group = out.groupby("bowler_name", group_keys=False)
    opponent_group = out.groupby(["bowler_name", "opposition_team"], group_keys=False)
    ground_group = out.groupby(["bowler_name", "ground"], group_keys=False)
    format_group = out.groupby(["bowler_name", "match_type"], group_keys=False)
    team_group = out.groupby("your_team", group_keys=False)
    team_ground_group = out.groupby(["your_team", "ground"], group_keys=False)

    out["bowler_prior_matches"] = bowler_group.cumcount()
    out["bowler_recent_wickets_3"] = bowler_group["wickets"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    out["bowler_recent_runs_3"] = bowler_group["runs"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    out["bowler_recent_economy_3"] = bowler_group["economy"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    out["bowler_recent_well_rate_5"] = bowler_group["did_well"].transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    out["bowler_career_wickets_before"] = bowler_group["wickets"].transform(lambda s: s.shift(1).expanding().mean())
    out["bowler_career_economy_before"] = bowler_group["economy"].transform(lambda s: s.shift(1).expanding().mean())
    out["bowler_recent_vs_opposition"] = opponent_group["did_well"].transform(lambda s: s.shift(1).expanding().mean())
    out["bowler_recent_vs_ground"] = ground_group["did_well"].transform(lambda s: s.shift(1).expanding().mean())
    out["bowler_recent_well_rate_by_format_5"] = format_group["did_well"].transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    out["bowler_recent_economy_by_format_3"] = format_group["economy"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    out["bowler_recent_wickets_by_format_3"] = format_group["wickets"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    out["bowler_format_experience"] = format_group.cumcount()
    out["team_matches_before"] = team_group.cumcount()
    out["team_ground_matches_before"] = team_ground_group.cumcount()
    out["team_ground_familiarity"] = np.where(out["team_matches_before"] > 0, out["team_ground_matches_before"] / out["team_matches_before"], 0.0)
    out["bowler_ground_experience"] = ground_group.cumcount()
    out["bowler_opposition_experience"] = opponent_group.cumcount()

    fill_values = {
        "bowler_prior_matches": 0,
        "bowler_recent_wickets_3": 0.0,
        "bowler_recent_runs_3": out["runs"].median(),
        "bowler_recent_economy_3": out["economy"].median(),
        "bowler_recent_well_rate_5": out["did_well"].mean(),
        "bowler_career_wickets_before": 0.0,
        "bowler_career_economy_before": out["economy"].median(),
        "bowler_recent_vs_opposition": out["did_well"].mean(),
        "bowler_recent_vs_ground": out["did_well"].mean(),
        "bowler_recent_well_rate_by_format_5": out["did_well"].mean(),
        "bowler_recent_economy_by_format_3": out["economy"].median(),
        "bowler_recent_wickets_by_format_3": 0.0,
        "bowler_format_experience": 0,
        "team_matches_before": 0,
        "team_ground_matches_before": 0,
        "team_ground_familiarity": 0.0,
        "bowler_ground_experience": 0,
        "bowler_opposition_experience": 0,
    }
    for col, value in fill_values.items():
        out[col] = out[col].fillna(value)
    return out.sort_index()


def add_common_base_features(frame, include_local_condition_summary=False):
    out = frame.copy()
    out["swing_factor"] = out["relative_humidity_2m"] * out["wind_speed_10m"]
    out["dew_spread"] = out["temperature_2m"] - out["dew_point_2m"]
    out["gust_ratio"] = out["wind_gusts_10m"] / (out["wind_speed_10m"] + 1)
    out["is_humid"] = (out["relative_humidity_2m"] >= 70).astype(int)
    out["is_cloudy"] = (out["cloud_cover"] >= 60).astype(int)
    out["temperature_band"] = pd.cut(out["temperature_2m"], [-np.inf, 22, 30, np.inf], labels=["Cool", "Warm", "Hot"]).astype("object").fillna("Warm")
    out["humidity_band"] = pd.cut(out["relative_humidity_2m"], [-np.inf, 50, 75, np.inf], labels=["Low", "Medium", "High"]).astype("object").fillna("Medium")
    if "month" in out.columns:
        out["seasonal_condition_band"] = pd.cut(out["month"], [0, 3, 6, 9, 12], labels=["Q1", "Q2", "Q3", "Q4"], include_lowest=True).astype("object").fillna("Q1")

    out["is_right_arm_pace"] = (out["bowler_type"] == "Right Arm Pace").astype(int)
    out["is_left_arm_pace"] = (out["bowler_type"] == "Left Arm Pace").astype(int)
    out["is_pace"] = (out["is_right_arm_pace"] | out["is_left_arm_pace"]).astype(int)
    out["is_right_arm_leg_spin"] = (out["bowler_type"] == "Right Arm Leg Spin").astype(int)
    out["is_left_arm_wrist_spin"] = (out["bowler_type"] == "Left Arm Wrist Spin").astype(int)
    out["is_off_spin"] = (out["bowler_type"] == "Off Spin").astype(int)
    out["is_left_arm_spin"] = (out["bowler_type"] == "Left Arm Spin").astype(int)
    out["is_spin"] = out[["is_right_arm_leg_spin", "is_left_arm_wrist_spin", "is_off_spin", "is_left_arm_spin"]].sum(axis=1).gt(0).astype(int)
    out["cloud_seam_boost"] = out["is_cloudy"] * out["is_pace"]

    out["pace_humidity"] = out["is_pace"] * out["relative_humidity_2m"]
    out["spin_dryness"] = out["is_spin"] * (100 - out["relative_humidity_2m"])
    out["dew_factor"] = ((out["relative_humidity_2m"] >= 75) & (out["dew_point_2m"] >= 20)).astype(int)
    out["dew_spin"] = out["dew_factor"] * out["is_spin"]
    out["dew_pace"] = out["dew_factor"] * out["is_pace"]
    out["dew_severity_band"] = pd.cut(out["relative_humidity_2m"] + out["dew_point_2m"], [-np.inf, 70, 90, np.inf], labels=["Low", "Medium", "High"]).astype("object").fillna("Medium")

    out["pitch_green"] = (out["pitch_type"] == "Green").astype(int)
    out["pitch_dry"] = (out["pitch_type"] == "Dry").astype(int)
    out["pitch_slow"] = (out["pitch_type"] == "Slow").astype(int)
    out["pitch_flat"] = (out["pitch_type"] == "Flat").astype(int)
    out["pace_help_score"] = out["pitch_type"].map({"Green": 3, "Flat": 1, "Dry": 1}).fillna(0)
    out["spin_help_score"] = out["pitch_type"].map({"Dry": 3, "Slow": 3, "Flat": 1}).fillna(0)
    out["green_pace"] = out["pitch_green"] * out["is_pace"]
    out["green_spin"] = out["pitch_green"] * out["is_spin"]
    out["dry_spin"] = out["pitch_dry"] * out["is_spin"]
    out["slow_spin"] = out["pitch_slow"] * out["is_spin"]
    out["flat_pace"] = out["pitch_flat"] * out["is_pace"]
    out["pitch_bowler_fit"] = out["pace_help_score"] * out["is_pace"] + out["spin_help_score"] * out["is_spin"]
    out["dry_right_arm_leg_spin"] = out["pitch_dry"] * out["is_right_arm_leg_spin"]
    out["dry_left_arm_wrist_spin"] = out["pitch_dry"] * out["is_left_arm_wrist_spin"]
    out["slow_right_arm_leg_spin"] = out["pitch_slow"] * out["is_right_arm_leg_spin"]
    out["slow_left_arm_wrist_spin"] = out["pitch_slow"] * out["is_left_arm_wrist_spin"]
    out["green_left_arm_pace"] = out["pitch_green"] * out["is_left_arm_pace"]
    out["green_right_arm_pace"] = out["pitch_green"] * out["is_right_arm_pace"]

    start_dt = pd.to_datetime(out["start_time"], format="%H:%M:%S", errors="coerce")
    start_minutes = start_dt.dt.hour.fillna(12) * 60 + start_dt.dt.minute.fillna(0)
    out["start_hour"] = start_dt.dt.hour.fillna(12).astype(float)
    out["late_start"] = (start_minutes >= (17 * 60 + 30)).astype(int)
    out["night_start"] = (start_minutes > (18 * 60 + 30)).astype(int)
    out["time_bucket"] = pd.cut(start_minutes, [-np.inf, 15 * 60, 18 * 60 + 30, np.inf], labels=["Afternoon", "Evening", "Night"]).astype("object").fillna("Afternoon")
    out["dew_late_start"] = out["dew_factor"] * out["late_start"]
    out["dew_night_start"] = out["dew_factor"] * out["night_start"]
    out["dew_spin_penalty"] = out["dew_factor"] * out["is_spin"] * out["night_start"]
    out["dew_pace_benefit"] = out["dew_factor"] * out["is_pace"] * out["night_start"]
    out["night_humidity"] = out["night_start"] * out["relative_humidity_2m"]
    out["late_start_spin"] = out["late_start"] * out["is_spin"]
    out["late_start_pace"] = out["late_start"] * out["is_pace"]

    if include_local_condition_summary:
        out["match_type_pitch_combo"] = out["match_type"].astype(str) + "_" + out["pitch_type"].astype(str)
        out["match_period_pitch_combo"] = out["match_period"].astype(str) + "_" + out["pitch_type"].astype(str)
        out["pace_on_green_at_night"] = out["is_pace"] * out["pitch_green"] * out["night_start"]
        out["spin_on_dry_day"] = out["is_spin"] * out["pitch_dry"] * (1 - out["night_start"])
        out["cloud_humidity_combo"] = out["is_cloudy"] * out["relative_humidity_2m"]
        out["weather_volatility_proxy"] = out["gust_ratio"] * (1 + out["is_cloudy"]) * (1 + out["relative_humidity_2m"] / 100.0)
        out["seam_friendly_condition_score"] = out["pitch_green"] * 2.0 + out["is_cloudy"] * 1.5 + (out["relative_humidity_2m"] / 100.0) + (out["wind_speed_10m"] / 20.0) + out["night_start"] * 0.5
        out["spin_friendly_condition_score"] = out["pitch_dry"] * 2.0 + out["pitch_slow"] * 2.0 + ((100 - out["relative_humidity_2m"]) / 100.0) + (1 - out["night_start"]) * 0.5 - out["dew_factor"] * 1.0
        out["pace_spin_balance_feature"] = out["seam_friendly_condition_score"] - out["spin_friendly_condition_score"]
        regime_parts = np.select([out["pitch_green"].eq(1), out["pitch_dry"].eq(1), out["pitch_slow"].eq(1), out["pitch_flat"].eq(1)], ["green", "dry", "slow", "flat"], default="other")
        moisture_parts = np.select([out["dew_factor"].eq(1), out["is_humid"].eq(1), out["temperature_band"].eq("Hot")], ["dewy", "humid", "hot"], default="neutral")
        out["pitch_weather_regime"] = pd.Series(regime_parts, index=out.index) + "_" + pd.Series(moisture_parts, index=out.index)
        out["match_type_weather_regime"] = out["match_type"].astype(str) + "_" + out["pitch_weather_regime"].astype(str)

    return out


def add_international_history_features(frame, historical_maps):
    out = frame.copy()
    default_value = historical_maps["global_mean"]

    def map_tuple(map_name, cols):
        lookup = historical_maps[map_name]
        return out.apply(lambda row: lookup.get(tuple(row[col] for col in cols), default_value), axis=1)

    out["bowler_overall_success"] = out["bowler_name"].map(historical_maps["bowler_overall_success"]).fillna(default_value)
    out["bowler_vs_opposition_success"] = map_tuple("bowler_vs_opposition_success", ["bowler_name", "opposition_team"])
    out["bowler_vs_ground_success"] = map_tuple("bowler_vs_ground_success", ["bowler_name", "ground"])
    out["bowler_match_type_success"] = map_tuple("bowler_match_type_success", ["bowler_name", "match_type"])
    out["bowler_type_pitch_success"] = map_tuple("bowler_type_pitch_success", ["bowler_type", "pitch_type"])
    out["bowler_type_opposition_success"] = map_tuple("bowler_type_opposition_success", ["bowler_type", "opposition_team"])
    out["bowler_type_match_success"] = map_tuple("bowler_type_match_success", ["bowler_type", "match_type"])
    out["ground_bowler_type_success"] = map_tuple("ground_bowler_type_success", ["ground", "bowler_type"])
    out["pitch_match_type_success"] = map_tuple("pitch_match_type_success", ["pitch_type", "match_type"])
    out["opposition_recent_form_vs_bowler_type"] = map_tuple("opposition_recent_form_vs_bowler_type", ["opposition_team", "bowler_type"])
    out["opposition_recent_form_vs_spin"] = out["opposition_team"].map(historical_maps["opposition_recent_form_vs_spin"]).fillna(default_value)
    out["opposition_recent_form_vs_pace"] = out["opposition_team"].map(historical_maps["opposition_recent_form_vs_pace"]).fillna(default_value)
    out["venue_pace_bias"] = out["ground"].map(historical_maps["venue_pace_bias"]).fillna(default_value)
    out["venue_spin_bias"] = out["ground"].map(historical_maps["venue_spin_bias"]).fillna(default_value)
    out["team_ground_familiarity"] = out.apply(lambda row: historical_maps["team_ground_familiarity"].get((row["your_team"], row["ground"]), 0.0), axis=1)
    out["bowler_condition_fit"] = out["bowler_type_pitch_success"] * 0.5 + out["ground_bowler_type_success"] * 0.3
    out["bowler_context_form"] = out["bowler_overall_success"] * 0.4 + out["bowler_vs_opposition_success"] * 0.4 + out["bowler_vs_ground_success"] * 0.2
    return out


def add_local_history_features(frame, local_historical_maps):
    out = frame.copy()
    default_value = local_historical_maps["global_mean"]

    def map_tuple(map_name, cols):
        lookup = local_historical_maps[map_name]
        return out.apply(lambda row: lookup.get(tuple(row[col] for col in cols), default_value), axis=1)

    out["bowler_type_strength"] = out["bowler_type"].map(local_historical_maps["bowler_type_perf"]).fillna(default_value)
    out["pitch_success_rate"] = out["pitch_type"].map(local_historical_maps["pitch_perf"]).fillna(default_value)
    out["type_pitch_combo"] = map_tuple("type_pitch_perf", ["bowler_type", "pitch_type"])
    out["type_match_combo"] = map_tuple("type_match_perf", ["bowler_type", "match_type"])
    out["type_period_combo"] = map_tuple("type_period_perf", ["bowler_type", "match_period"])
    out["match_pitch_combo"] = map_tuple("match_pitch_perf", ["match_type", "pitch_type"])
    out["period_pitch_combo"] = map_tuple("period_pitch_perf", ["match_period", "pitch_type"])
    return out


def build_weather_preview(place, start_time, match_date=None, sri_lanka_only=False):
    match_date = match_date or dt_date.today().isoformat()
    if sri_lanka_only and place in SRI_LANKA_LOCATIONS:
        geo = {"name": place, **SRI_LANKA_LOCATIONS[place]}
    else:
        geo = geocode_place(place, country_code="LK" if sri_lanka_only else None)
    weather = fetch_forecast_weather(geo["latitude"], geo["longitude"], geo["timezone"], match_date, start_time)
    return {
        "location": geo["name"],
        "latitude": geo["latitude"],
        "longitude": geo["longitude"],
        "timezone": geo["timezone"],
        "date": match_date,
        "start_time": start_time,
        "match_period": derive_match_period(start_time),
        **weather,
    }


def _latest_bowler_pool(df, your_team=None):
    work = df.copy()
    if your_team is not None:
        work = work[work["your_team"] == your_team].copy()
    work = work.sort_values(["date", "start_time"]).drop_duplicates("bowler_name", keep="last")
    return work[["bowler_name", "bowler_type"]].dropna().copy()


def _current_sri_lanka_pool():
    return pd.DataFrame(
        [
            {
                "bowler_name": player["bowler_name"],
                "bowler_type": clean_bowler_type(player["bowler_type"]),
            }
            for player in CURRENT_SRI_LANKA_BOWLERS
        ]
    )


def _select_balanced_top_n(pred_df, top_n, pitch_type=None):
    ranked = pred_df.sort_values("score", ascending=False).copy()
    top = ranked.head(top_n).copy()
    pace_candidates = ranked[ranked["bowler_type"].apply(is_pace_type)]
    required_pacers = 2 if clean_pitch_type(pitch_type) == "Green" else 1

    if top["bowler_type"].apply(is_pace_type).sum() >= required_pacers:
        return top

    if pace_candidates.empty:
        return top

    needed = min(required_pacers, len(pace_candidates))
    keep_pacers = top[top["bowler_type"].apply(is_pace_type)]
    missing = max(0, needed - len(keep_pacers))
    extra_pacers = pace_candidates.loc[~pace_candidates.index.isin(keep_pacers.index)].head(missing)
    removable = top.loc[~top.index.isin(keep_pacers.index)].sort_values("score", ascending=True).head(len(extra_pacers))
    top = pd.concat([top.drop(removable.index), extra_pacers], ignore_index=False)
    return top.sort_values("score", ascending=False).head(top_n)


def build_international_explanation(row, weather, pitch_type, match_type, selected_names):
    reasons = []
    pitch_type = clean_pitch_type(pitch_type)
    role = bowler_role_label(row["bowler_type"])
    humidity = float(weather["relative_humidity_2m"])
    cloud = float(weather["cloud_cover"])
    wind = float(weather["wind_speed_10m"])
    dew_point = float(weather["dew_point_2m"])
    temp = float(weather["temperature_2m"])
    score = float(row["score"])

    if role == "pace" and (pitch_type == "Green" or (humidity >= 70 and cloud >= 60)):
        reasons.append(
            f"Humidity is {format_percent(humidity)}, cloud cover is {format_percent(cloud)}, and wind is {format_float(wind, 1)} km/h, which is a seam-friendly weather profile for a pace bowler."
        )
    if role == "spin" and pitch_type in {"Dry", "Slow"} and humidity < 75:
        reasons.append(
            f"The {pitch_type.lower()} surface and humidity around {format_percent(humidity)} are more supportive of spin grip than heavy-dew conditions."
        )
    if dew_point >= 20 and str(row.get("match_period", "")).lower() == "night":
        reasons.append(
            f"Dew point is {format_float(dew_point, 1)}°C in a night match, so dew risk is material and bowlers who handle wet-ball conditions better gain value."
        )
    if float(row.get("bowler_recent_well_rate_by_format_5", 0)) > 0.55:
        reasons.append(
            f"Recent {match_type} form is strong, with a recent well-rate of {format_percent(row['bowler_recent_well_rate_by_format_5'] * 100)} in this format."
        )
    if float(row.get("bowler_match_type_success", 0)) > 0.55:
        reasons.append(
            f"Historical {match_type} performance is solid, with match-type success around {format_percent(row['bowler_match_type_success'] * 100)}."
        )
    if float(row.get("bowler_vs_opposition_success", 0)) > 0.55:
        reasons.append(
            f"He has a good record against this opposition, with success around {format_percent(row['bowler_vs_opposition_success'] * 100)} in similar past matchups."
        )
    if float(row.get("bowler_vs_ground_success", 0)) > 0.55:
        reasons.append(
            f"He also has a positive history at this venue, with ground-specific success near {format_percent(row['bowler_vs_ground_success'] * 100)}."
        )
    if role == "pace" and pitch_type == "Green":
        reasons.append("A green pitch triggers the pace-balance rule, so the final combination intentionally keeps at least two seam options.")
    elif role == "pace" and row["bowler_name"] in selected_names:
        reasons.append("The final shortlist keeps at least one pace option to maintain attack balance across conditions.")

    if not reasons:
        reasons.append(
            f"This bowler remained highly ranked because his overall condition-fit and historical context features stayed competitive for a {match_type} on a {pitch_type.lower()} pitch."
        )

    risk = (
        "If live pitch behaviour differs from the expected surface label, this recommendation can shift."
        if pitch_type in {"Green", "Dry", "Slow"}
        else "This recommendation is more weather-driven than venue-specific, so last-minute condition changes may affect it."
    )

    summary = (
        f"{row['bowler_name']} ranks highly because the {pitch_type.lower()} pitch, current weather profile "
        f"({format_float(temp, 1)}°C, {format_percent(humidity)} humidity, {format_percent(cloud)} cloud), and his past cricketing context align well."
    )
    return {"summary": summary, "key_reasons": reasons[:4], "risk_note": risk}


def build_local_explanation(row, weather, pitch_type, match_type, selected_types):
    reasons = []
    pitch_type = clean_pitch_type(pitch_type)
    role = bowler_role_label(row["bowler_type"])
    humidity = float(weather["relative_humidity_2m"])
    cloud = float(weather["cloud_cover"])
    wind = float(weather["wind_speed_10m"])
    temp = float(weather["temperature_2m"])
    dew_point = float(weather["dew_point_2m"])

    if role == "pace" and float(row.get("seam_friendly_condition_score", 0)) >= float(row.get("spin_friendly_condition_score", 0)):
        reasons.append(
            f"The condition summary is pace-leaning: cloud cover is {format_percent(cloud)}, humidity is {format_percent(humidity)}, and wind is {format_float(wind, 1)} km/h."
        )
    if role == "spin" and float(row.get("spin_friendly_condition_score", 0)) > float(row.get("seam_friendly_condition_score", 0)):
        reasons.append(
            f"The condition summary is spin-leaning because the {pitch_type.lower()} surface and lower moisture penalty suit spin better than seam."
        )
    if str(row.get("pitch_weather_regime", "")).strip():
        reasons.append(
            f"The model classified the surface-weather pattern as '{row['pitch_weather_regime']}', which aligns well with this bowling type."
        )
    if float(row.get("type_match_combo", 0)) > 0.55:
        reasons.append(
            f"This bowling type has good historical success in {match_type}, with type-format success around {format_percent(row['type_match_combo'] * 100)}."
        )
    if dew_point >= 20 and str(row.get("match_period", "")).lower() == "night":
        reasons.append(
            f"Dew point is {format_float(dew_point, 1)}°C for a night match, so dew handling matters in the selection logic."
        )
    if role == "pace" and pitch_type == "Green":
        reasons.append("A green pitch triggers the local balance rule, so the shortlist keeps at least two pace options.")
    elif role == "pace" and row["bowler_type"] in selected_types:
        reasons.append("The local shortlist keeps at least one pace option for balance.")

    if not reasons:
        reasons.append(
            f"This bowling type stayed near the top because its pitch-weather fit and match-type suitability remained strong under the current conditions."
        )

    risk = "Local recommendations are more condition-driven than player-specific, so team selection still matters." 
    summary = (
        f"{row['bowler_type']} ranks highly because the {pitch_type.lower()} pitch and current weather "
        f"({format_float(temp, 1)}°C, {format_percent(humidity)} humidity, {format_percent(cloud)} cloud) suit this bowling profile."
    )
    return {"summary": summary, "key_reasons": reasons[:4], "risk_note": risk}


def predict_international(match_type, pitch_type, ground, your_team, opposition_team, start_time, match_date=None, top_n=4):
    match_date = pd.to_datetime(match_date or dt_date.today().isoformat())
    weather = build_weather_preview(ground, start_time, match_date.strftime("%Y-%m-%d"))
    history_df = SOURCE_DF[SOURCE_DF["date"] < match_date].copy()
    history_with_recent = build_international_history(history_df)
    if str(your_team).strip().lower() == "sri lanka":
        pool = _current_sri_lanka_pool()
    else:
        pool = _latest_bowler_pool(history_df, your_team)
    if pool.empty:
        raise ValueError(f"No candidate bowlers found for team '{your_team}'")

    rows = []
    for _, player in pool.iterrows():
        rows.append(
            {
                "match_type": str(match_type).upper(),
                "pitch_type": clean_pitch_type(pitch_type),
                "ground": ground,
                "your_team": your_team,
                "opposition_team": opposition_team,
                "bowler_name": player["bowler_name"],
                "bowler_type": clean_bowler_type(player["bowler_type"]),
                "start_time": start_time,
                "match_period": derive_match_period(start_time),
                "date": match_date,
                "year": int(match_date.year),
                "month": int(match_date.month),
                **{k: weather[k] for k in ["temperature_2m", "relative_humidity_2m", "dew_point_2m", "pressure_msl", "cloud_cover", "wind_speed_10m", "wind_gusts_10m", "precipitation"]},
            }
        )

    pred_df = pd.DataFrame(rows)

    snapshot_cols = [
        "bowler_prior_matches",
        "bowler_recent_wickets_3",
        "bowler_recent_runs_3",
        "bowler_recent_economy_3",
        "bowler_recent_well_rate_5",
        "bowler_career_wickets_before",
        "bowler_career_economy_before",
    ]
    bowler_latest = history_with_recent.sort_values(["date", "start_time"]).drop_duplicates("bowler_name", keep="last")
    pred_df = pred_df.merge(bowler_latest[["bowler_name", *snapshot_cols]], on="bowler_name", how="left")

    by_format = history_with_recent.sort_values(["date", "start_time"]).drop_duplicates(["bowler_name", "match_type"], keep="last")
    pred_df = pred_df.merge(
        by_format[["bowler_name", "match_type", "bowler_recent_well_rate_by_format_5", "bowler_recent_economy_by_format_3", "bowler_recent_wickets_by_format_3", "bowler_format_experience"]],
        on=["bowler_name", "match_type"],
        how="left",
    )
    by_opp = history_with_recent.sort_values(["date", "start_time"]).drop_duplicates(["bowler_name", "opposition_team"], keep="last")
    pred_df = pred_df.merge(by_opp[["bowler_name", "opposition_team", "bowler_recent_vs_opposition", "bowler_opposition_experience"]], on=["bowler_name", "opposition_team"], how="left")
    by_ground = history_with_recent.sort_values(["date", "start_time"]).drop_duplicates(["bowler_name", "ground"], keep="last")
    pred_df = pred_df.merge(by_ground[["bowler_name", "ground", "bowler_recent_vs_ground", "bowler_ground_experience"]], on=["bowler_name", "ground"], how="left")
    by_team_ground = history_with_recent.sort_values(["date", "start_time"]).drop_duplicates(["your_team", "ground"], keep="last")
    pred_df = pred_df.merge(by_team_ground[["your_team", "ground", "team_ground_familiarity"]], on=["your_team", "ground"], how="left")

    pred_df = add_common_base_features(pred_df, include_local_condition_summary=False)
    pred_df = add_international_history_features(pred_df, INTERNATIONAL_MODEL["historical_maps"])

    for col in INTERNATIONAL_MODEL["features"]:
        if col not in pred_df.columns:
            pred_df[col] = 0 if col not in {"match_type", "pitch_type", "ground", "your_team", "opposition_team", "bowler_name", "bowler_type", "start_time", "match_period", "temperature_band", "humidity_band", "time_bucket"} else "Unknown"

    X = pred_df[INTERNATIONAL_MODEL["features"]].copy()
    probs = INTERNATIONAL_MODEL["pipeline"].predict_proba(X)[:, 1]
    pred_df["score"] = probs
    top = _select_balanced_top_n(pred_df, top_n, pitch_type=pitch_type)
    remaining = (
        pred_df.loc[~pred_df["bowler_name"].isin(top["bowler_name"])]
        .sort_values("score", ascending=False)
        .copy()
    )
    selected_names = set(top["bowler_name"].tolist())
    results = []
    for _, row in top.iterrows():
        record = {
            "bowler_name": row["bowler_name"],
            "bowler_type": row["bowler_type"],
            "score": round(float(row["score"]), 4),
        }
        record.update(build_international_explanation(row, weather, pitch_type, match_type, selected_names))
        results.append(record)

    alternatives = []
    for _, row in remaining.iterrows():
        record = {
            "bowler_name": row["bowler_name"],
            "bowler_type": row["bowler_type"],
            "score": round(float(row["score"]), 4),
        }
        alternatives.append(record)

    return {
        "mode": "international",
        "weather": weather,
        "threshold": INTERNATIONAL_MODEL["threshold"],
        "results": results,
        "alternatives": alternatives,
    }


def predict_local(match_type, pitch_type, location, start_time, match_date=None, top_n=4, candidate_bowlers=None):
    match_date = pd.to_datetime(match_date or dt_date.today().isoformat())
    weather = build_weather_preview(location, start_time, match_date.strftime("%Y-%m-%d"), sri_lanka_only=True)

    if candidate_bowlers:
        rows = [{"bowler_name": b.get("bowler_name", "Unknown"), "bowler_type": clean_bowler_type(b["bowler_type"])} for b in candidate_bowlers]
    else:
        candidate_types = sorted(SOURCE_DF["bowler_type"].dropna().astype(str).str.strip().unique().tolist())
        rows = [{"bowler_type": bt} for bt in candidate_types]

    for row in rows:
        row.update(
            {
                "match_type": str(match_type).upper(),
                "pitch_type": clean_pitch_type(pitch_type),
                "start_time": start_time,
                "match_period": derive_match_period(start_time),
                "date": match_date,
                "year": int(match_date.year),
                "month": int(match_date.month),
                **{k: weather[k] for k in ["temperature_2m", "relative_humidity_2m", "dew_point_2m", "pressure_msl", "cloud_cover", "wind_speed_10m", "wind_gusts_10m", "precipitation"]},
            }
        )

    pred_df = pd.DataFrame(rows)
    pred_df = add_common_base_features(pred_df, include_local_condition_summary=True)
    pred_df = add_local_history_features(pred_df, LOCAL_MODEL["local_historical_maps"])

    for col in LOCAL_MODEL["features"]:
        if col not in pred_df.columns:
            pred_df[col] = 0 if col not in {"match_type", "pitch_type", "bowler_type", "start_time", "match_period", "temperature_band", "humidity_band", "seasonal_condition_band", "dew_severity_band", "time_bucket", "match_type_pitch_combo", "match_period_pitch_combo", "pitch_weather_regime", "match_type_weather_regime"} else "Unknown"

    X = pred_df[LOCAL_MODEL["features"]].copy()
    probs = LOCAL_MODEL["pipeline"].predict_proba(X)[:, 1]
    pred_df["score"] = probs
    top = _select_balanced_top_n(pred_df, top_n, pitch_type=pitch_type).copy()
    remaining = pred_df.loc[~pred_df.index.isin(top.index)].sort_values("score", ascending=False).copy()

    selected_types = set(top["bowler_type"].tolist())
    results = []
    for _, row in top.iterrows():
        record = {"bowler_type": row["bowler_type"], "score": round(float(row["score"]), 4)}
        if "bowler_name" in top.columns:
            record["bowler_name"] = row["bowler_name"]
        record.update(build_local_explanation(row, weather, pitch_type, match_type, selected_types))
        results.append(record)

    alternatives = []
    for _, row in remaining.iterrows():
        record = {"bowler_type": row["bowler_type"], "score": round(float(row["score"]), 4)}
        if "bowler_name" in remaining.columns and pd.notna(row.get("bowler_name")):
            record["bowler_name"] = row["bowler_name"]
        alternatives.append(record)

    return {
        "mode": "local",
        "weather": weather,
        "threshold": LOCAL_MODEL["threshold"],
        "results": results,
        "alternatives": alternatives,
    }


def demo_international():
    return predict_international(
        match_type="T20",
        pitch_type="Green",
        ground="R. Premadasa Stadium",
        your_team="Sri Lanka",
        opposition_team="India",
        start_time="19:00:00",
    )


def demo_local():
    return predict_local(
        match_type="T20",
        pitch_type="Flat",
        location="Colombo",
        start_time="19:00:00",
    )


def run_payload(payload):
    mode = str(payload.get("mode", "")).strip().lower()
    include_factors = bool(payload.get("show_feature_importance"))
    if mode == "international":
        required = ["match_type", "pitch_type", "ground", "your_team", "opposition_team"]
        missing = [key for key in required if not payload.get(key)]
        if missing:
            raise ValueError(f"Missing required international fields: {', '.join(missing)}")
        result = predict_international(
            match_type=payload["match_type"],
            pitch_type=payload["pitch_type"],
            ground=payload["ground"],
            your_team=payload["your_team"],
            opposition_team=payload["opposition_team"],
            start_time=payload.get("start_time", "19:00:00"),
            match_date=payload.get("match_date"),
            top_n=int(payload.get("top_n", 4)),
        )
        if include_factors:
            result["model_factors"] = extract_model_factors(INTERNATIONAL_MODEL)
        return result

    if mode == "local":
        if not payload.get("match_type") or not payload.get("pitch_type"):
            raise ValueError("Missing required local fields: match_type, pitch_type")
        location = payload.get("location") or payload.get("city")
        if not location:
            raise ValueError("Missing required local field: location")
        result = predict_local(
            match_type=payload["match_type"],
            pitch_type=payload["pitch_type"],
            location=location,
            start_time=payload.get("start_time", "19:00:00"),
            match_date=payload.get("match_date"),
            top_n=int(payload.get("top_n", 4)),
            candidate_bowlers=payload.get("candidate_bowlers"),
        )
        if include_factors:
            result["model_factors"] = extract_model_factors(LOCAL_MODEL)
        return result

    raise ValueError("Payload mode must be 'international' or 'local'")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            payload = json.loads(sys.argv[1])
            print(json.dumps(run_payload(payload)))
        except Exception as exc:
            print(json.dumps({"error": str(exc)}))
            raise
    else:
        print("===== INTERNATIONAL DEMO =====")
        print(json.dumps(demo_international(), indent=2))
        print("\n===== LOCAL DEMO =====")
        print(json.dumps(demo_local(), indent=2))
