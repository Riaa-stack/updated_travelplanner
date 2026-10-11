from math import isfinite
from marshmallow import Schema, fields, validate, validates, ValidationError, pre_load


class TripSchema(Schema):
    destination = fields.String(required=True, validate=validate.Length(min=2, max=150))
    budget = fields.Float(required=True, allow_nan=False)
    days = fields.Integer(required=True, strict=True)
    interests = fields.List(
        fields.String(validate=validate.Length(min=1, max=250)),
        required=True,
        validate=validate.Length(min=1, max=20),
    )
    currency = fields.String(load_default="USD", validate=validate.OneOf(["USD", "INR"]))
    travel_style = fields.String(allow_none=True)

    @pre_load
    def trim_text(self, data, **kwargs):
        if not isinstance(data, dict):
            raise ValidationError("Request body must be a JSON object.")
        cleaned = dict(data)
        if isinstance(cleaned.get("destination"), str):
            cleaned["destination"] = cleaned["destination"].strip()
        if isinstance(cleaned.get("interests"), list):
            cleaned["interests"] = [item.strip() if isinstance(item, str) else item for item in cleaned["interests"]]
        return cleaned

    @validates("budget")
    def validate_budget(self, value, **kwargs):
        if not isfinite(value) or value <= 0:
            raise ValidationError("Budget must be a finite number greater than 0.")

    @validates("days")
    def validate_days(self, value, **kwargs):
        if value < 1 or value > 30:
            raise ValidationError("Days must be between 1 and 30.")

    @validates("destination")
    def validate_destination(self, value, **kwargs):
        if not value.strip():
            raise ValidationError("Destination cannot be empty.")

    @validates("interests")
    def validate_interests(self, value, **kwargs):
        if any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValidationError("Each interest must be non-empty text.")
