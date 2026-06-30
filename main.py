from fastapi import FastAPI, Body
from pathlib import Path
from typing import Any
import json
import re


app = FastAPI(
    title="Car Insurance Vehicle API",
    description="API for retrieving vehicle information by license plate",
    version="1.1.0"
)


BASE_DIR = Path(__file__).resolve().parent
VEHICLES_DB_PATH = BASE_DIR / "vehicles.json"


def load_vehicles_db() -> dict:
    """
    Loads the mock vehicle database from a JSON file.
    In a real production system, this could be replaced with
    a real database or an external vehicle registry API.
    """
    with open(VEHICLES_DB_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


VEHICLES_DB = load_vehicles_db()


def is_valid_license_plate(license_plate: str) -> bool:
    """
    Validates that the license plate contains only digits
    and has 7 or 8 characters.
    """
    return bool(re.fullmatch(r"\d{7,8}", license_plate))


def normalize_request_body(payload: Any) -> dict:
    """
    Normalizes the request body into a Python dictionary.

    This supports both:
    1. A real JSON object:
       {"license_plate": "12345678"}

    2. A stringified JSON object, which some no-code tools may send:
       "{\"license_plate\": \"12345678\"}"
    """
    if isinstance(payload, dict):
        return payload

    if isinstance(payload, str):
        try:
            parsed_payload = json.loads(payload)

            if isinstance(parsed_payload, dict):
                return parsed_payload

        except json.JSONDecodeError:
            return {
                "license_plate": payload
            }

    return {}


def empty_vehicle_data(license_plate: str = "") -> dict:
    """
    Returns an empty vehicle data object.

    This keeps the API response structure consistent,
    even when the vehicle is not found or the license plate is invalid.
    """
    return {
        "license_plate": license_plate,
        "manufacturer": "",
        "model": "",
        "year": 0,
        "color": ""
    }


def build_response(
    success: bool,
    data: dict,
    error_code: str = "",
    error_message: str = ""
) -> dict:
    """
    Builds a consistent response structure for all cases.

    Every response always contains:
    - success
    - data
    - error

    This is important for Insait, because the custom tool extracts
    the same paths from every API response.
    """
    return {
        "success": success,
        "data": data,
        "error": {
            "code": error_code,
            "message": error_message
        }
    }


@app.get("/")
def root():
    return {
        "message": "Car Insurance Vehicle API is running",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok"
    }


@app.post("/vehicle-info")
async def get_vehicle_info(
    payload: Any = Body(
        ...,
        example={
            "license_plate": "12345678"
        }
    )
):
    body = normalize_request_body(payload)

    license_plate = str(body.get("license_plate", "")).strip()

    if not is_valid_license_plate(license_plate):
        return build_response(
            success=False,
            data=empty_vehicle_data(license_plate),
            error_code="INVALID_LICENSE_PLATE",
            error_message="License plate must contain only 7-8 digits"
        )

    vehicle = VEHICLES_DB.get(license_plate)

    if vehicle is None:
        return build_response(
            success=False,
            data=empty_vehicle_data(license_plate),
            error_code="VEHICLE_NOT_FOUND",
            error_message="Vehicle was not found"
        )

    return build_response(
        success=True,
        data={
            "license_plate": license_plate,
            "manufacturer": vehicle.get("manufacturer", ""),
            "model": vehicle.get("model", ""),
            "year": vehicle.get("year", 0),
            "color": vehicle.get("color", "")
        }
    )