"""Reusable validation for trip-planning and replanning API requests."""
from datetime import date, datetime
from math import isfinite
import re
from zoneinfo import ZoneInfo

MAX_DESTINATION_LENGTH = 150
MAX_INTERESTS_LENGTH = 1000
MAX_SPECIAL_REQUIREMENTS_LENGTH = 2000
MAX_CUSTOM_CHANGE_LENGTH = 2000
MAX_TRIP_DAYS = 30
ALLOWED_CURRENCIES = {"USD", "INR"}
ALLOWED_TRAVELERS = {
    "Solo Explorer", "Couple (2)", "Family with Kids (3-4)",
    "Group of Friends (4+)", "Business & Leisure"
}
ALLOWED_TRAVEL_STYLES = {
    "Cultural & Luxury", "Relaxed & Scenic", "Fast-Paced Adventure",
    "Foodie & Gastronomy", "Budget Backpacker"
}
ALLOWED_SEASONS = {
    "Spring (Cherry Blossom)", "Summer (Warm & Sunny)",
    "Autumn (Foliage & Mild)", "Winter (Snow & Ski)"
}
ALLOWED_REPLAN_REASONS = {
    "Budget Changed", "Weather Conditions Changed",
    "Crowded / Queue Mitigation", "Trip Duration Changed"
}
ALLOWED_WEATHER = {
    "Heavy Rain", "Storm / Thunderstorm", "Snow", "Extreme Heat",
    "Cold Weather", "Strong Winds", "Fog / Poor Visibility"
}


def local_today() -> date:
    """Current app-local date; set to the primary product timezone (India)."""
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


def _clean_text(value, label, errors, *, required=True, maximum=None, minimum=1):
    if value is None:
        if required:
            errors[label] = f"{label.replace('_', ' ').capitalize()} is required."
        return ""
    if not isinstance(value, str):
        errors[label] = f"{label.replace('_', ' ').capitalize()} must be text."
        return ""
    cleaned = value.strip()
    if required and not cleaned:
        errors[label] = f"{label.replace('_', ' ').capitalize()} is required."
    elif cleaned and len(cleaned) < minimum:
        errors[label] = f"{label.replace('_', ' ').capitalize()} must contain at least {minimum} characters."
    elif maximum is not None and len(cleaned) > maximum:
        errors[label] = f"{label.replace('_', ' ').capitalize()} cannot exceed {maximum} characters."
    return cleaned


def validate_trip_plan(data):
    errors = {}
    if not isinstance(data, dict):
        return {"request": "Request body must be a JSON object."}

    destination = _clean_text(data.get("destination"), "destination", errors, maximum=MAX_DESTINATION_LENGTH, minimum=2)

    raw_budget = data.get("budget")
    if isinstance(raw_budget, bool) or raw_budget is None or isinstance(raw_budget, (dict, list)):
        errors["budget"] = "Budget must be a number greater than zero."
    else:
        try:
            budget = float(raw_budget)
            if not isfinite(budget) or budget <= 0:
                errors["budget"] = "Budget must be a finite number greater than zero."
        except (TypeError, ValueError):
            errors["budget"] = "Budget must be a number greater than zero."

    raw_days = data.get("days")
    if isinstance(raw_days, bool):
        errors["days"] = "Travel days must be a whole number between 1 and 30."
    else:
        try:
            # Reject decimals and strings such as "3.5" rather than truncating them.
            if isinstance(raw_days, float) and not raw_days.is_integer():
                raise ValueError
            if isinstance(raw_days, str) and not re.fullmatch(r"\d+", raw_days.strip()):
                raise ValueError
            days = int(raw_days)
            if days < 1 or days > MAX_TRIP_DAYS:
                errors["days"] = f"Travel days must be between 1 and {MAX_TRIP_DAYS}."
        except (TypeError, ValueError):
            errors["days"] = f"Travel days must be a whole number between 1 and {MAX_TRIP_DAYS}."

    currency = data.get("currency", "USD")
    if not isinstance(currency, str) or currency not in ALLOWED_CURRENCIES:
        errors["currency"] = "Currency must be USD or INR."

    travelers = data.get("group_type")
    if not isinstance(travelers, str) or travelers not in ALLOWED_TRAVELERS:
        errors["group_type"] = "Select a valid traveler category."

    travel_style = data.get("travel_style")
    if not isinstance(travel_style, str) or travel_style not in ALLOWED_TRAVEL_STYLES:
        errors["travel_style"] = "Select a valid travel style."

    season = data.get("season")
    if not isinstance(season, str) or season not in ALLOWED_SEASONS:
        errors["season"] = "Select a valid season or climate."

    interests = data.get("interests")
    if isinstance(interests, str):
        if not interests.strip():
            errors["interests"] = "Enter at least one interest."
        elif len(interests.strip()) > MAX_INTERESTS_LENGTH:
            errors["interests"] = f"Interests cannot exceed {MAX_INTERESTS_LENGTH} characters."
    elif isinstance(interests, list):
        if not interests or any(not isinstance(item, str) or not item.strip() for item in interests):
            errors["interests"] = "Interests must contain at least one non-empty text value."
        elif len(", ".join(interests)) > MAX_INTERESTS_LENGTH:
            errors["interests"] = f"Interests cannot exceed {MAX_INTERESTS_LENGTH} characters."
    else:
        errors["interests"] = "Interests must be text or a list of text values."

    special = data.get("special_requirements", "")
    if special is not None and (not isinstance(special, str) or len(special) > MAX_SPECIAL_REQUIREMENTS_LENGTH):
        errors["special_requirements"] = f"Special requirements must be text no longer than {MAX_SPECIAL_REQUIREMENTS_LENGTH} characters."

    start_value, end_value = data.get("start_date"), data.get("end_date")
    start_date = _parse_date(start_value, "start_date", errors)
    end_date = _parse_date(end_value, "end_date", errors)
    today = local_today()
    if start_date and start_date < today:
        errors["start_date"] = "Start date cannot be in the past."
    if end_date and end_date < today:
        errors["end_date"] = "End date cannot be in the past."
    if start_date and end_date and end_date < start_date:
        errors["end_date"] = "End date must be the same as or later than the start date."

    # Optional preferences are validated only if provided.
    allowed_accommodation = {
        "Boutique Luxury Hotel", "5-Star Grand Resort", "Cozy Airbnb Apartment",
        "Traditional Ryokan / Heritage Stay", "Budget Hostel / Capsule"
    }
    allowed_transport = {"Public Transit & Trains", "Bullet Train & Private Taxi", "Rental Car", "Walking & Eco Rides"}
    accommodation = data.get("accommodation_preference")
    transport = data.get("transport_preference")
    if accommodation not in (None, "") and (not isinstance(accommodation, str) or accommodation not in allowed_accommodation):
        errors["accommodation_preference"] = "Select a supported accommodation preference."
    if transport not in (None, "") and (not isinstance(transport, str) or transport not in allowed_transport):
        errors["transport_preference"] = "Select a supported transport preference."

    return errors


def _parse_date(value, field, errors):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        errors[field] = f"{field.replace('_', ' ').capitalize()} is required and must use YYYY-MM-DD format."
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors[field] = f"Enter a valid {field.replace('_', ' ')}."
        return None


def validate_replan_request(data):
    errors = {}
    if not isinstance(data, dict):
        return {"request": "Request body must be a JSON object."}
    reason = data.get("reason")
    if reason not in ALLOWED_REPLAN_REASONS:
        errors["reason"] = "Select a valid reason for replanning."
        return errors
    details = data.get("details", "")
    if not isinstance(details, str):
        errors["details"] = "Replanning details must be text."
        return errors
    details = details.strip()
    if reason == "Budget Changed":
        match = re.fullmatch(r"New budget:\s*(USD|INR)\s+([0-9]+(?:\.[0-9]+)?)", details, re.IGNORECASE)
        if not match or not isfinite(float(match.group(2))) or float(match.group(2)) <= 0:
            errors["details"] = "Provide a valid positive budget and supported currency."
    elif reason == "Weather Conditions Changed":
        if details not in ALLOWED_WEATHER and not (details and len(details) <= 300):
            errors["details"] = "Select a valid weather condition or provide a short description."
        elif not details:
            errors["details"] = "Weather condition is required."
    elif reason == "Crowded / Queue Mitigation":
        if not details:
            errors["details"] = "Enter the crowded place or location."
        elif len(details) > 300:
            errors["details"] = "Location cannot exceed 300 characters."
    elif reason == "Trip Duration Changed":
        match = re.fullmatch(r"New duration:\s*(\d+)\s+days?", details, re.IGNORECASE)
        if not match or not (1 <= int(match.group(1)) <= MAX_TRIP_DAYS):
            errors["details"] = f"Provide a whole-number trip duration between 1 and {MAX_TRIP_DAYS} days."
    return errors
