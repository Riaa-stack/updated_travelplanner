from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.trip import Trip
from app.extensions import db
from app.orchestrators.travel_orchestrator import TravelOrchestrator
from app.schemas.trip_schema import TripSchema
from app.services.trip_service import TripService
from app.utils.trip_validation import validate_trip_plan, validate_replan_request

trip_bp = Blueprint(
    "trips",
    __name__,
    url_prefix="/api/trips"
)

trip_schema = TripSchema()


@trip_bp.route("", methods=["POST"])
@jwt_required()
def create_trip():
    """
    Create a new trip
    """

    data = request.get_json(silent=True)

    if not data:
        return {
            "success": False,
            "message": "No input data provided."
        }, 400

    errors = trip_schema.validate(data)

    if errors:
        return {
            "success": False,
            "errors": errors
        }, 400

    user_id = get_jwt_identity()

    return TripService.create_trip(user_id, data)


@trip_bp.route("", methods=["GET"])
@jwt_required()
def get_all_trips():
    """
    Get all trips of logged-in user
    """

    user_id = get_jwt_identity()

    return TripService.get_all_trips(user_id)


@trip_bp.route("/<uuid:trip_id>", methods=["GET"])
@jwt_required()
def get_trip(trip_id):
    """
    Get trip by ID
    """

    user_id = get_jwt_identity()

    return TripService.get_trip_by_id(user_id, trip_id)


@trip_bp.route("/<uuid:trip_id>", methods=["PUT"])
@jwt_required()
def update_trip(trip_id):
    """
    Update trip
    """

    data = request.get_json(silent=True)

    if not data:
        return {
            "success": False,
            "message": "No input data provided."
        }, 400

    errors = trip_schema.validate(data)

    if errors:
        return {
            "success": False,
            "errors": errors
        }, 400

    user_id = get_jwt_identity()

    return TripService.update_trip(user_id, trip_id, data)


@trip_bp.route("/plan", methods=["POST"])
@jwt_required()
def plan_trip():
    """
    Generate a complete AI travel plan.
    """

    try:

        data = request.get_json(silent=True)

        if not data:
            return {
                "success": False,
                "message": "No input data provided."
            }, 400

        validation_errors = validate_trip_plan(data)
        if validation_errors:
            return {
                "success": False,
                "message": "Please correct the invalid trip details.",
                "errors": validation_errors
            }, 400

        orchestrator = TravelOrchestrator()

        result = orchestrator.generate_trip(data)
        user_id = get_jwt_identity()

        trip = Trip(
            user_id=user_id,
            destination=data["destination"],
            budget=data["budget"],
            currency=data.get("currency", "USD"),
            days=data["days"],
            interests=data["interests"],
            travel_style=result["preference"]["travel_style"],
            plan_data=result,
            status="planned"
        )

        db.session.add(trip)
        db.session.commit()

        # The complete generated itinerary is persisted in trips.plan_data.
        # Return the database ID so the frontend can always reference the
        # persisted record rather than a temporary client-side ID.
        result["id"] = str(trip.id)
        result["destination"] = trip.destination
        result["budget"] = trip.budget
        result["currency"] = trip.currency
        result["days"] = trip.days
        result["travel_style"] = trip.travel_style
        result["status"] = trip.status

        return {
            "success": True,
            "message": "Trip generated and saved successfully.",
            "data": result
        }, 200

    except Exception as e:
        import traceback

        traceback.print_exc()

        return {
            "success": False,
            "message": "Unable to generate the trip right now. Please try again."
        }, 500


@trip_bp.route("/<uuid:trip_id>/replan", methods=["POST"])
@jwt_required()
def replan_trip(trip_id):
    """Replan an existing saved trip and persist the updated itinerary."""
    try:
        user_id = get_jwt_identity()
        trip = Trip.query.filter_by(id=trip_id, user_id=user_id).first()

        if not trip:
            return {
                "success": False,
                "message": "Trip not found."
            }, 404

        data = request.get_json(silent=True)
        validation_errors = validate_replan_request(data)
        if validation_errors:
            return {
                "success": False,
                "message": "Please correct the replanning details.",
                "errors": validation_errors
            }, 400

        reason = data["reason"].strip()
        details = data["details"].strip()

        # Keep the original trip requirements and give the AI the current
        # saved plan so replanning modifies the existing trip rather than
        # creating an unrelated itinerary.
        current_plan = trip.plan_data or {}

        # When the user changes the budget, use the new amount as the actual
        # planning budget. The AI must rebuild the allocation around it.
        replanning_budget = trip.budget
        replanning_currency = trip.currency
        replanning_days = trip.days
        if reason == "Budget Changed" and details:
            import re
            budget_match = re.search(r"(?:USD|INR)\s*([0-9]+(?:\.[0-9]+)?)", details, re.IGNORECASE)
            if budget_match:
                replanning_budget = float(budget_match.group(1))
            currency_match = re.match(r"New budget:\s*(USD|INR)", details, re.IGNORECASE)
            if currency_match:
                replanning_currency = currency_match.group(1).upper()
        elif reason == "Trip Duration Changed":
            import re
            days_match = re.fullmatch(r"New duration:\s*(\d+)\s+days?", details, re.IGNORECASE)
            if days_match:
                replanning_days = int(days_match.group(1))

        planner_input = {
            "destination": trip.destination,
            "budget": replanning_budget,
            "currency": replanning_currency,
            "days": replanning_days,
            "interests": trip.interests,
            "group_type": data.get("group_type", "Couple (2)"),
            "travel_style": trip.travel_style or data.get("travel_style", "Cultural & Luxury"),
            "season": data.get("season", "Current season"),
            "accommodation_preference": data.get("accommodation_preference", "Flexible"),
            "transport_preference": data.get("transport_preference", "Flexible"),
            "special_requirements": data.get("special_requirements", ""),
            "replan": True,
            "replan_reason": reason,
            "replan_details": details,
            "current_plan": current_plan,
        }

        orchestrator = TravelOrchestrator()
        result = orchestrator.generate_trip(planner_input)

        # Update the SAME database row. Do not create a second trip.
        trip.destination = planner_input["destination"]
        trip.budget = planner_input["budget"]
        trip.currency = planner_input["currency"]
        trip.days = planner_input["days"]
        trip.interests = planner_input["interests"]
        trip.travel_style = result["preference"].get("travel_style")
        trip.plan_data = result
        trip.status = "planned"

        db.session.commit()

        result["id"] = str(trip.id)
        result["updated_at"] = trip.updated_at.isoformat() if trip.updated_at else None

        return {
            "success": True,
            "message": "Trip replanned and saved successfully.",
            "data": result
        }, 200

    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": "Unable to complete the request right now. Please try again."
        }, 500

@trip_bp.route("/<uuid:trip_id>", methods=["DELETE"])
@jwt_required()
def delete_trip(trip_id):
    """
    Delete trip
    """

    user_id = get_jwt_identity()

    return TripService.delete_trip(user_id, trip_id)