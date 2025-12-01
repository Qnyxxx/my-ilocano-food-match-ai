python name=backend/models/dish.py
from typing import List, Optional
from pydantic import BaseModel, Field


class Dish(BaseModel):
    """
    Pydantic model representing a dish as stored in dishes.json.
    """
    id: int
    name: str
    description: Optional[str] = ""
    ingredients: List[str] = Field(default_factory=list)
    taste: str  # e.g., "salty", "sweet", "spicy", "sour", "bitter"
    cooking_method: str  # e.g., "grilled", "fried", "boiled", "fermented"
    dietary_tags: List[str] = Field(default_factory=list)  # e.g., ["pork", "seafood", "vegetarian"]
    image: Optional[str] = None  # image file name or URL
    occasions: List[str] = Field(default_factory=list)  # e.g., ["everyday", "celebration", "merienda"]


class PreferenceIn(BaseModel):
    """
    Input model for /match endpoint.
    """
    preferred_taste: Optional[str] = None
    ingredients_preference: List[str] = Field(default_factory=list)
    dietary_restrictions: List[str] = Field(default_factory=list)  # e.g., ["no-pork", "no seafood"]
    cooking_method: Optional[str] = None
    occasion: Optional[str] = None


class RecommendationOut(BaseModel):
    """
    Model for recommendation result.
    """
    id: int
    name: str
    image: Optional[str] = None
    reason: str
    score: int
