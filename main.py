from fastapi import FastAPI, Body
from pathlib import Path
from typing import Any
import json
import re


app = FastAPI(
    title="Car Insurance Vehicle API",
    description="API for retrieving vehicle information by license plate",
    version="1.0.0"
)


BASE_DIR = Path(__file__).resolve().parent
VEHICLES_DB_PATH = BASE_DIR / "vehicles.json"


def load_vehicles_db() -> dict:
    """
    Loads the mock vehicle database from a JSON file.
    In production, this could be replaced with a real database
    or an external vehicle registry provider.
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

    The API supports multiple formats because some no-code tools
    may send the body as a real JSON object, while others may send
    it as a stringified JSON object.
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


def build_empty_vehicle_data(license_plate: str) -> dict:
    """
    Returns an empty vehicle data structure.

    This keeps the API response schema consistent,
    so external tools like Insait can always extract
    the same fields from the response.
    """
    return {
        "license_plate": license_plate,
        "manufacturer": "",
        "model": "",
        "year": 0,
        "color": ""
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

    empty_vehicle_data = build_empty_vehicle_data(license_plate)

    if not is_valid_license_plate(license_plate):
        return {
            "success": False,
            "data": empty_vehicle_data,
            "error": {
                "code": "INVALID_LICENSE_PLATE",
                "message": "License plate must contain only 7-8 digits"
            }
        }

    vehicle = VEHICLES_DB.get(license_plate)

    if vehicle is None:
        return {
            "success": False,
            "data": empty_vehicle_data,
            "error": {
                "code": "VEHICLE_NOT_FOUND",
                "message": "Vehicle was not found"
            }
        }

    return {
        "success": True,
        "data": {
            "license_plate": license_plate,
            "manufacturer": vehicle["manufacturer"],
            "model": vehicle["model"],
            "year": vehicle["year"],
            "color": vehicle["color"]
        },
        "error": {
            "code": "",
            "message": ""
        }
    }