python name=backend/services/matcher.py
from typing import List
import re
import logging

from models.dish import Dish, PreferenceIn, RecommendationOut

logger = logging.getLogger("matcher")


def normalize_token(s: str) -> str:
    """
    Helper to normalize strings for comparison.
    """
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def parse_restriction_token(restr: str) -> str:
    """
    Convert dietary restriction text into a canonical token to match against dish tags or ingredients.
    Examples:
      "no-pork" -> "pork"
      "no pork" -> "pork"
      "no seafood" -> "seafood"
      "vegetarian" -> "vegetarian" (if user provides direct tags)
    """
    s = restrict_strip = (restr or "").lower()
    s = s.replace("_", " ").replace("-", " ")
    s = s.strip()
    # Remove leading "no " or "no-" if present
    s = re.sub(r"^no\s+", "", s)
    s = s.strip()
    # normalize non-alnum
    s = normalize_token(s)
    return s


def match_dishes(dishes: List[Dish], prefs: PreferenceIn, top_n: int = 3) -> List[RecommendationOut]:
    """
    Core matching algorithm:
      +3 points for taste match
      +3 points for ingredient preference match (if any preferred ingredient present)
      -5 points for each restriction that matches an ingredient/dietary tag
      +2 points for cooking method match
      +1 point if dish fits the occasion

    Returns a list of RecommendationOut sorted by score desc (top_n).
    """

    # Normalize preferences
    pref_taste = normalize_token(prefs.preferred_taste or "")
    pref_ingredients = [normalize_token(i) for i in prefs.ingredients_preference or []]
    pref_cooking = normalize_token(prefs.cooking_method or "")
    pref_occasion = normalize_token(prefs.occasion or "")

    restriction_tokens = [parse_restriction_token(r) for r in (prefs.dietary_restrictions or []) if r]

    logger.debug("Preferences normalized: taste=%s, ingredients=%s, cooking=%s, occasion=%s, restrictions=%s",
                 pref_taste, pref_ingredients, pref_cooking, pref_occasion, restriction_tokens)

    results: List[RecommendationOut] = []

    for dish in dishes:
        score = 0
        reasons = []

        # Normalize dish fields
        dish_taste = normalize_token(dish.taste)
        dish_ingredients = [normalize_token(i) for i in dish.ingredients]
        dish_cooking = normalize_token(dish.cooking_method)
        dish_tags = [normalize_token(t) for t in dish.dietary_tags]
        dish_occasions = [normalize_token(o) for o in (dish.occasions or [])]

        # Taste match
        if pref_taste:
            if pref_taste == dish_taste:
                score += 3
                reasons.append(f"Matches taste: {dish.taste} (+3)")

        # Ingredient preference match (any)
        ingredient_matches = set(pref_ingredients).intersection(set(dish_ingredients))
        if ingredient_matches:
            score += 3
            matches_str = ", ".join(sorted(ingredient_matches))
            reasons.append(f"Contains preferred ingredient(s): {matches_str} (+3)")

        # Dietary restrictions: penalize strongly if dish contains restricted ingredient or tag
        for rt in restriction_tokens:
            if not rt:
                continue
            # If restriction token matches any ingredient or dietary tag -> penalty
            if rt in dish_ingredients or rt in dish_tags:
                score -= 5
                reasons.append(f"Contains restricted item: {rt} (-5)")

        # Cooking method match
        if pref_cooking:
            if pref_cooking == dish_cooking:
                score += 2
                reasons.append(f"Cooking method matches: {dish.cooking_method} (+2)")

        # Occasion fit
        if pref_occasion:
            if pref_occasion in dish_occasions:
                score += 1
                reasons.append(f"Suitable for: {prefs.occasion} (+1)")

        # Fallback small reason if nothing matched positively
        if not reasons:
            reasons.append("No strong positive matches; showing as lower-scoring suggestion")

        # Build reason text (prioritize descriptive explanation)
        reason_text = "; ".join(reasons)

        results.append(RecommendationOut(
            id=dish.id,
            name=dish.name,
            image=dish.image,
            reason=reason_text,
            score=score
        ))

    # Sort by score desc, then by name (stable deterministic)
    results.sort(key=lambda r: (r.score, r.name), reverse=True)

    # Return top_n recommendations
    top_results = results[:top_n]
    logger.info("Top %d recommendations computed", len(top_results))
    return top_results
