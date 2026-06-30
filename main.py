from fastapi import FastAPI, Request
from pydantic import BaseModel
from pathlib import Path
import json
import re


app = FastAPI(
    title="Car Insurance Vehicle API",
    description="API for retrieving vehicle information by license plate",
    version="1.2.0"
)


BASE_DIR = Path(__file__).resolve().parent
VEHICLES_DB_PATH = BASE_DIR / "vehicles.json"


class VehicleRequest(BaseModel):
    license_plate: str


def load_vehicles_db() -> dict:
    """
    Loads the mock vehicle database from a JSON file.
    In production, this could be replaced with a real database
    or an external vehicle registry API.
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


def build_response(
    success: bool,
    license_plate: str,
    manufacturer: str = "",
    model: str = "",
    year: int = 0,
    color: str = "",
    error_code: str = "",
    error_message: str = ""
) -> dict:
    """
    Builds a response that is easy for Insait to extract.

    The response includes:
    1. Flat top-level fields for simple Insait extraction.
    2. Nested data/error objects for a clean API structure.
    """

    data = {
        "license_plate": license_plate,
        "manufacturer": manufacturer,
        "model": model,
        "year": year,
        "color": color
    }

    error = {
        "code": error_code,
        "message": error_message
    }

    return {
        "success": success,

        # Flat fields for Insait extraction
        "vehicle_license_plate": license_plate,
        "vehicle_manufacturer": manufacturer,
        "vehicle_model": model,
        "vehicle_year": year,
        "vehicle_color": color,
        "api_error_code": error_code,
        "api_error_message": error_message,

        # Nested fields for clean API structure
        "data": data,
        "error": error
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

@app.post("/debug-request")
async def debug_request(request: Request):
    raw_body = await request.body()

    try:
        json_body = await request.json()
    except Exception:
        json_body = None

    return {
        "success": True,
        "content_type": request.headers.get("content-type"),
        "raw_body": raw_body.decode("utf-8"),
        "json_body": json_body
    }


@app.post("/vehicle-info")
def get_vehicle_info(request: VehicleRequest):
    license_plate = request.license_plate.strip()

    if not is_valid_license_plate(license_plate):
        return build_response(
            success=False,
            license_plate=license_plate,
            error_code="INVALID_LICENSE_PLATE",
            error_message="License plate must contain only 7-8 digits"
        )

    vehicle = VEHICLES_DB.get(license_plate)

    if vehicle is None:
        return build_response(
            success=False,
            license_plate=license_plate,
            error_code="VEHICLE_NOT_FOUND",
            error_message="Vehicle was not found"
        )

    return build_response(
        success=True,
        license_plate=license_plate,
        manufacturer=vehicle.get("manufacturer", ""),
        model=vehicle.get("model", ""),
        year=vehicle.get("year", 0),
        color=vehicle.get("color", "")
    )