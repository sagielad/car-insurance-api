from fastapi import FastAPI, Body
from pathlib import Path
from typing import Any
import json
import re

app = FastAPI(
    title="Car Insurance Vehicle API",
    description="API for retrieving vehicle information by license plate",
    version="1.1.0",
)

BASE_DIR = Path(__file__).resolve().parent
VEHICLES_DB_PATH = BASE_DIR / "vehicles.json"


def load_vehicles_db() -> dict:
    """Loads the mock vehicle database from a JSON file."""
    with open(VEHICLES_DB_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


VEHICLES_DB = load_vehicles_db()


def is_valid_license_plate(license_plate: str) -> bool:
    """Valid = 7 or 8 digits only."""
    return bool(re.fullmatch(r"\d{7,8}", license_plate))


def normalize_request_body(payload: Any) -> dict:
    """Accepts both a real JSON object and a stringified JSON body."""
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {"license_plate": payload}
    return {}


# --- Helpers that GUARANTEE one identical schema for every response -------- #
def empty_vehicle(license_plate: str = "") -> dict:
    return {
        "license_plate": license_plate,
        "manufacturer": "",
        "model": "",
        "year": 0,
        "color": "",
    }


def build_response(success: bool, data: dict, code: str = "", message: str = "") -> dict:
    """Every response has the SAME keys: success, data, error.
    This is what makes Insait's extraction paths resolve every time."""
    return {
        "success": success,
        "data": data,
        "error": {"code": code, "message": message},
    }


@app.get("/")
def root():
    return {"message": "Car Insurance Vehicle API is running", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/vehicle-info")
async def get_vehicle_info(payload: Any = Body(..., example={"license_plate": "12345678"})):
    body = normalize_request_body(payload)
    license_plate = str(body.get("license_plate", "")).strip()

    # 1) Invalid format -> data (empty) + error. HTTP 200 so Insait parses it.
    if not is_valid_license_plate(license_plate):
        return build_response(
            success=False,
            data=empty_vehicle(license_plate),
            code="INVALID_LICENSE_PLATE",
            message="License plate must contain only 7-8 digits",
        )

    # 2) Valid format but not in DB -> data (empty) + error.
    vehicle = VEHICLES_DB.get(license_plate)
    if vehicle is None:
        return build_response(
            success=False,
            data=empty_vehicle(license_plate),
            code="VEHICLE_NOT_FOUND",
            message="Vehicle was not found",
        )

    # 3) Found -> data populated, error empty. .get() avoids a 500 if a
    #    record is missing a field.
    return build_response(
        success=True,
        data={
            "license_plate": license_plate,
            "manufacturer": vehicle.get("manufacturer", ""),
            "model": vehicle.get("model", ""),
            "year": vehicle.get("year", 0),
            "color": vehicle.get("color", ""),
        },
    )