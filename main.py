from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
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


async def parse_request_body(request: Request) -> dict:
    """
    Parses the request body.

    Some no-code platforms may send the JSON body as a real JSON object,
    while others may send it as a stringified JSON object.
    This function supports both formats.
    """
    try:
        body = await request.json()
    except Exception:
        return {}

    if isinstance(body, dict):
        return body

    if isinstance(body, str):
        try:
            parsed_body = json.loads(body)
            if isinstance(parsed_body, dict):
                return parsed_body
        except json.JSONDecodeError:
            return {}

    return {}


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
async def get_vehicle_info(request: Request):
    body = await parse_request_body(request)

    license_plate = str(body.get("license_plate", "")).strip()

    if not is_valid_license_plate(license_plate):
        return {
            "success": False,
            "error": {
                "code": "INVALID_LICENSE_PLATE",
                "message": "License plate must contain only 7-8 digits"
            }
        }

    vehicle = VEHICLES_DB.get(license_plate)

    if vehicle is None:
        return {
            "success": False,
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
        }
    }