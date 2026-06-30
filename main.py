from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
import re


app = FastAPI(
    title="Car Insurance Vehicle API",
    description="API for retrieving vehicle information by license plate",
    version="1.1.0",
)


BASE_DIR = Path(__file__).resolve().parent
VEHICLES_DB_PATH = BASE_DIR / "vehicles.json"


class VehicleRequest(BaseModel):
    license_plate: str


def load_vehicles_db() -> dict:
    with open(VEHICLES_DB_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


VEHICLES_DB = load_vehicles_db()


def is_valid_license_plate(license_plate: str) -> bool:
    """Valid = 7 or 8 digits only."""
    return bool(re.fullmatch(r"\d{7,8}", license_plate))


# --- Helpers: every response has the SAME flat shape -> Insait can always
#     extract success / data.* / error.code / error.message --------------- #
def empty_vehicle(license_plate: str = "") -> dict:
    return {
        "license_plate": license_plate,
        "manufacturer": "",
        "model": "",
        "year": 0,
        "color": "",
    }


def build_response(success: bool, data: dict, code: str = "", message: str = "") -> dict:
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
def get_vehicle_info(request: VehicleRequest):
    license_plate = request.license_plate.strip()

    # Invalid format -> HTTP 200, flat body (NOT HTTPException, NOT nested).
    if not is_valid_license_plate(license_plate):
        return build_response(
            False,
            empty_vehicle(license_plate),
            "INVALID_LICENSE_PLATE",
            "License plate must contain only 7-8 digits",
        )

    # Valid format but not found -> HTTP 200, flat body.
    vehicle = VEHICLES_DB.get(license_plate)
    if vehicle is None:
        return build_response(
            False,
            empty_vehicle(license_plate),
            "VEHICLE_NOT_FOUND",
            "Vehicle was not found",
        )

    # Found -> HTTP 200, data populated, error empty.
    return build_response(
        True,
        {
            "license_plate": license_plate,
            "manufacturer": vehicle.get("manufacturer", ""),
            "model": vehicle.get("model", ""),
            "year": vehicle.get("year", 0),
            "color": vehicle.get("color", ""),
        },
    )