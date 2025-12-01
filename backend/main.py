python name=backend/main.py
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models.dish import Dish, DishDetailOut, PreferenceIn, RecommendationOut
from services.matcher import match_dishes

import json
import logging

# Basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ilocano-food-match-ai")

app = FastAPI(
    title="Ilocano Food Match AI - Backend",
    description="API to match Ilocano dishes to user preferences",
    version="1.0.0",
)

# Enable CORS for all origins (frontend is separate)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins for student project
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


DATA_PATH = Path(__file__).resolve().parent / "data" / "dishes.json"


@app.on_event("startup")
def load_data():
    """
    Load dishes.json into memory on startup and validate against Pydantic model.
    """
    logger.info("Loading dishes from %s", DATA_PATH)
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        # Validate and coerce into Dish objects
        dishes: List[Dish] = [Dish(**d) for d in raw]
        # Store in app state
        app.state.dishes = dishes
        logger.info("Loaded %d dishes", len(dishes))
    except Exception as ex:
        logger.exception("Failed to load dishes.json: %s", ex)
        # If load fails, ensure app.state.dishes exists as empty list
        app.state.dishes = []


@app.get("/dishes", response_model=List[Dish])
def get_all_dishes():
    """
    Return the list of all dishes (admin/test use).
    """
    return app.state.dishes


@app.get("/dish/{dish_id}", response_model=Dish)
def get_dish(dish_id: int):
    """
    Return full details for one dish by id.
    """
    for d in app.state.dishes:
        if d.id == dish_id:
            return d
    raise HTTPException(status_code=404, detail="Dish not found")


@app.post("/match", response_model=dict)
def match_endpoint(preference: PreferenceIn):
    """
    Receive user preferences and return top 3 recommendations.
    Response format:
    {
      "recommendations": [
        { "name": "...", "image": "...", "reason": "..." },
        ...
      ]
    }
    """
    dishes: List[Dish] = app.state.dishes
    if not dishes:
        raise HTTPException(status_code=500, detail="Dish dataset not loaded")

    recommendations: List[RecommendationOut] = match_dishes(dishes, preference)

    # Format into the required response (name, image, reason)
    resp = {
        "recommendations": [
            {"name": r.name, "image": r.image, "reason": r.reason, "score": r.score}
            for r in recommendations
        ]
    }
    return resp
