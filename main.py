from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
import json
import re


app = FastAPI(
    title="Car Insurance Vehicle API",
    description="API for retrieving vehicle information by license plate",
    version="1.0.0"
)


BASE_DIR = Path(__file__).resolve().parent
VEHICLES_DB_PATH = BASE_DIR / "vehicles.json"


class VehicleRequest(BaseModel):
    license_plate: str


def load_vehicles_db() -> dict:
    """
    Loads the mock vehicle database from a JSON file.
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

    # Invalid format -> HTTP 200 (return, NOT raise), so Insait can read & branch
    if not is_valid_license_plate(license_plate):
        return {
            "success": False,
            "data": {
                "license_plate": license_plate,
                "manufacturer": "",
                "model": "",
                "year": 0,
                "color": ""
            },
            "error": {
                "code": "INVALID_LICENSE_PLATE",
                "message": "License plate must contain only 7-8 digits"
            }
        }

    vehicle = VEHICLES_DB.get(license_plate)

    # Not found -> HTTP 200 (return, NOT raise)
    if vehicle is None:
        return {
            "success": False,
            "data": {
                "license_plate": license_plate,
                "manufacturer": "",
                "model": "",
                "year": 0,
                "color": ""
            },
            "error": {
                "code": "VEHICLE_NOT_FOUND",
                "message": "Vehicle was not found"
            }
        }

    # Found -> HTTP 200
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