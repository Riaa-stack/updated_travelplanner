from app.agents.base_agent import BaseAgent


class TripPlannerAgent(BaseAgent):
    """Single-call planner that replaces multiple Gemini calls for /api/trips/plan."""

    def __init__(self):
        super().__init__(
            prompt_file="agents/trip_planner.md",
            required_fields=[
                "preference",
                "budget",
                "route",
                "crowd",
                "travel_companion",
            ],
        )
