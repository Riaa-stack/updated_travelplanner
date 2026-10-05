from app.agents.trip_planner_agent import TripPlannerAgent
from app.external.geoapify_api import GeoapifyAPI
from app.external.weather_api import WeatherAPI


class TravelOrchestrator:
    """Coordinates the complete trip plan with one AI generation call.

    AI-heavy planning is intentionally consolidated into TripPlannerAgent so
    a single /api/trips/plan request does not fan out into many LLM calls.
    External services remain separate because they provide live/non-LLM data.
    """

    def __init__(self):
        self.trip_planner_agent = TripPlannerAgent()
        self.weather_api = WeatherAPI()
        self.geoapify = GeoapifyAPI()

    def generate_trip(self, user_input: dict):
        print("\n==============================")
        print("🚀 Starting TripPlannerAgent")
        print("==============================")
        print("➡️ One OpenRouter request for the complete AI plan...")

        ai_result = self.trip_planner_agent.execute(user_input)
        ai_plan = ai_result["data"]

        preference = ai_plan["preference"]
        budget = ai_plan["budget"]
        route = ai_plan["route"]
        crowd = ai_plan["crowd"]
        companion = ai_plan["travel_companion"]

        self._validate_route(route, user_input["days"])
        self._validate_budget(budget, user_input["budget"])

        print("✅ TripPlannerAgent Finished")

        # ------------------------------------------------------------------
        # Live location enrichment. These calls do NOT use Gemini/OpenRouter.
        # ------------------------------------------------------------------
        print("\n==============================")
        print("🚀 Starting Geoapify enrichment")
        print("==============================")

        for day in route["days"]:
            for activity in day.get("activities", []):
                location = f"{activity.get('location', '')}, {user_input['destination']}"

                try:
                    print("Searching Geoapify:", location)
                    coordinates = self.geoapify.geocode(location)
                    activity["coordinates"] = coordinates

                    if coordinates:
                        activity["nearby_hotels"] = self.geoapify.search_hotels(
                            coordinates["latitude"],
                            coordinates["longitude"],
                        )
                        activity["nearby_places"] = self.geoapify.search_places(
                            coordinates["latitude"],
                            coordinates["longitude"],
                        )
                    else:
                        activity["nearby_hotels"] = []
                        activity["nearby_places"] = []

                except Exception as exc:
                    print(f"Geoapify Error for {location}: {exc}")
                    activity["coordinates"] = None
                    activity["nearby_hotels"] = []
                    activity["nearby_places"] = []

        print("✅ Geoapify enrichment finished")

        # ------------------------------------------------------------------
        # Live weather. This also does NOT use Gemini/OpenRouter.
        # ------------------------------------------------------------------
        print("\n==============================")
        print("🚀 Starting OpenWeather API")
        print("==============================")

        weather = self._get_weather(user_input)
        print("✅ OpenWeather API Finished")

        return {
            "preference": preference,
            "budget": budget,
            "route": route,
            "weather": weather,
            "crowd": crowd,
            "travel_companion": companion,
        }

    @staticmethod
    def _validate_route(route: dict, total_days: int):
        days = route.get("days")
        if not isinstance(days, list) or len(days) != int(total_days):
            raise ValueError(
                f"AI itinerary returned {len(days) if isinstance(days, list) else 0} "
                f"days; expected {total_days}."
            )

        for index, day in enumerate(days, start=1):
            if day.get("day") != index:
                raise ValueError(f"AI itinerary day numbering is invalid at day {index}.")
            activities = day.get("activities")
            if not isinstance(activities, list) or len(activities) != 3:
                raise ValueError(f"Day {index} must contain exactly 3 activities.")

    @staticmethod
    def _validate_budget(budget: dict, requested_budget):
        categories = [
            "hotel_budget",
            "food_budget",
            "transport_budget",
            "activity_budget",
            "misc_budget",
        ]
        total = sum(float(budget.get(key, 0)) for key in categories)
        requested = float(requested_budget)

        if abs(total - requested) > 0.01:
            raise ValueError(
                f"AI budget allocation ({total}) does not equal requested budget ({requested})."
            )

        budget["estimated_total"] = requested_budget

    def _get_weather(self, user_input: dict):
        forecast = self.weather_api.get_forecast(user_input["destination"])
        forecast_list = forecast.get("list", [])

        if not forecast_list:
            return {"weather": []}

        weather = {"weather": []}

        for day in range(int(user_input["days"])):
            index = min(day * 8, len(forecast_list) - 1)
            item = forecast_list[index]
            condition = item["weather"][0]["main"]

            weather["weather"].append(
                {
                    "day": day + 1,
                    "condition": condition,
                    "temperature": f'{round(item["main"]["temp"])}°C',
                    "activity_suitable": condition not in ["Rain", "Thunderstorm"],
                    "warning": "Carry an umbrella." if condition == "Rain" else "",
                }
            )

        return weather
