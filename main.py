from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
import re


app = FastAPI(
    title="Car Insurance Vehicle API",
    description="API for retrieving vehicle information by license plate",
    version="1.3.0"
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
    return bool(re.fullmatch(r"\d{7,8}", license_plate))


def build_response(
    success: bool,
    license_plate: str,
    vehicle_manufacturer: str = "",
    vehicle_model: str = "",
    vehicle_year: int = 0,
    vehicle_color: str = "",
    api_status_code: str = "",
    api_status_message: str = ""
) -> dict:
    """
    Flat response for Insait.

    Important:
    Do not return a top-level field named 'error',
    because some no-code tools may treat it as a tool failure.
    """
    return {
        "success": success,
        "license_plate": license_plate,
        "vehicle_manufacturer": vehicle_manufacturer,
        "vehicle_model": vehicle_model,
        "vehicle_year": vehicle_year,
        "vehicle_color": vehicle_color,
        "api_status_code": api_status_code,
        "api_status_message": api_status_message
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
def get_vehicle_info(request: VehicleRequest):
    license_plate = request.license_plate.strip()

    if not is_valid_license_plate(license_plate):
        return build_response(
            success=False,
            license_plate=license_plate,
            api_status_code="INVALID_LICENSE_PLATE",
            api_status_message="License plate must contain only 7-8 digits"
        )

    vehicle = VEHICLES_DB.get(license_plate)

    if vehicle is None:
        return build_response(
            success=False,
            license_plate=license_plate,
            api_status_code="VEHICLE_NOT_FOUND",
            api_status_message="Vehicle was not found"
        )

    return build_response(
        success=True,
        license_plate=license_plate,
        vehicle_manufacturer=vehicle.get("manufacturer", ""),
        vehicle_model=vehicle.get("model", ""),
        vehicle_year=vehicle.get("year", 0),
        vehicle_color=vehicle.get("color", ""),
        api_status_code="",
        api_status_message=""
    )