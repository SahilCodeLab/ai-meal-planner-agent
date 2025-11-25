# agents/meal_planner_agent.py
"""
Meal Planner Agent - improved no-repeat weekly planner
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Set
import random

logger = logging.getLogger("MealPlannerAgent")


class MealPlannerSpecialist:
    """Specialized agent for meal planning with memory"""

    def __init__(self, memory_bank):
        self.memory_bank = memory_bank
        self.recipe_db = self._load_recipes()
        logger.info("MealPlannerSpecialist initialized")

    def _load_recipes(self) -> Dict:
        """Load recipes with enhanced database"""
        try:
            with open("data/recipes.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Recipes database not found, falling back to empty structure")
            # Provide empty pools
            return {"recipes": {"breakfast": [], "lunch": [], "dinner": []}}

    async def generate_personalized_plan(self, user_preferences: Dict, user_id: str) -> Dict:
        """Generate meal plan considering user history and preferences"""
        logger.info(f"Generating personalized plan for user: {user_id}")

        # Get user history for variety
        user_history = self._get_user_meal_history(user_id)

        diet_type = user_preferences.get("diet_type", "vegetarian")
        calorie_target = user_preferences.get("calorie_target", 2000)
        allergies = user_preferences.get("allergies", [])
        cuisine_pref = user_preferences.get("cuisine_preference", "any")

        weekly_plan = {}
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # used sets to avoid repeats across days
        used_breakfasts: Set[str] = set()
        used_lunches: Set[str] = set()
        used_dinners: Set[str] = set()

        # Precompute candidate pools filtered by preferences
        pools = {}
        for meal_type in ["breakfast", "lunch", "dinner"]:
            pool = self.recipe_db["recipes"].get(meal_type, [])
            filtered = [
                r
                for r in pool
                if (r.get("type", "vegetarian") == diet_type or diet_type == "mixed")
                and not any(allergy.lower() in json.dumps(r.get("ingredients", {})).lower() for allergy in allergies)
            ]
            pools[meal_type] = filtered

        for i, day in enumerate(days):
            daily_plan = await self._generate_daily_plan(
                pools,
                used_breakfasts,
                used_lunches,
                used_dinners,
                day_index=i,
                calorie_target=calorie_target,
            )
            weekly_plan[day] = daily_plan

        # AI-powered optimization (keeps structure)
        optimized_plan = await self._optimize_with_ai(weekly_plan, user_preferences)

        logger.info(f"Generated plan with {len(optimized_plan)} days")
        return optimized_plan

    async def _generate_daily_plan(
        self,
        pools: Dict[str, List[Dict]],
        used_breakfasts: Set[str],
        used_lunches: Set[str],
        used_dinners: Set[str],
        day_index: int,
        calorie_target: int,
    ) -> Dict:
        """Generate plan for a single day with variety, updating used_sets"""
        meals = {}
        total_calories = 0

        # helper to pick without repeating if possible
        def pick_recipe(pool: List[Dict], used_set: Set[str]):
            if not pool:
                return None
            # candidates not in used_set
            candidates = [r for r in pool if r["name"] not in used_set]
            if candidates:
                choice = random.choice(candidates)
            else:
                # all used, pick least recently used logic: just pick random but prefer variety via shuffle
                choice = random.choice(pool)
            used_set.add(choice["name"])
            return choice

        breakfast = pick_recipe(pools.get("breakfast", []), used_breakfasts) or self._create_fallback_meal("breakfast", "vegetarian")
        lunch = pick_recipe(pools.get("lunch", []), used_lunches) or self._create_fallback_meal("lunch", "vegetarian")
        dinner = pick_recipe(pools.get("dinner", []), used_dinners) or self._create_fallback_meal("dinner", "vegetarian")

        meals["breakfast"] = breakfast
        meals["lunch"] = lunch
        meals["dinner"] = dinner

        total_calories = breakfast.get("calories", 300) + lunch.get("calories", 400) + dinner.get("calories", 350)

        return {
            "meals": meals,
            "total_calories": total_calories,
            "nutrition_score": self._calculate_nutrition_score(meals),
            "variety_score": self._calculate_variety_score(meals, self._get_user_meal_history_scores())
        }

    def _get_user_meal_history(self, user_id: str) -> List:
        """Get user's meal history from memory"""
        try:
            with open("memory/meal_history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
            return [h for h in history if h.get("user_id") == user_id]
        except Exception:
            return []

    def _get_user_meal_history_scores(self) -> List:
        """Return recent meal name list for variety scoring (helper)"""
        try:
            with open("memory/meal_history.json", "r", encoding="utf-8") as f:
                history = json.load(f)
            recent = []
            for entry in history[-3:]:
                for day_plan in entry.get("meal_plan", {}).values():
                    for m in day_plan.get("meals", {}).values():
                        recent.append(m.get("name"))
            return recent
        except Exception:
            return []

    def _create_fallback_meal(self, meal_type: str, diet_type: str) -> Dict:
        """Create fallback meal when no recipes match"""
        return {
            "name": f"Fallback {meal_type.title()}",
            "ingredients": {"basic_food": 100, "vegetables": 50},
            "calories": 300,
            "protein": 15,
            "carbs": 40,
            "fat": 8,
            "prep_time": 15,
            "type": diet_type,
        }

    def _calculate_nutrition_score(self, meals: Dict) -> float:
        """Calculate nutrition balance score"""
        total_protein = sum(meal.get("protein", 0) for meal in meals.values())
        total_carbs = sum(meal.get("carbs", 0) for meal in meals.values())
        total_fat = sum(meal.get("fat", 0) for meal in meals.values())
        denom = total_protein + total_carbs + total_fat
        protein_ratio = total_protein / denom if denom > 0 else 0.33
        return min(10.0, abs(protein_ratio - 0.3) * 100)

    def _calculate_variety_score(self, meals: Dict, recent_list: List) -> float:
        """Calculate meal variety score"""
        current_meals = [meal["name"] for meal in meals.values()]
        recent_meals = list(recent_list or [])
        new_meals = set(current_meals) - set(recent_meals)
        variety_score = len(new_meals) / len(current_meals) * 10 if current_meals else 5.0
        return min(10.0, variety_score)

    async def _optimize_with_ai(self, weekly_plan: Dict, user_preferences: Dict) -> Dict:
        """AI-powered optimization of meal plan (simple calorie scaling for now)"""
        total_weekly_calories = sum(day.get("total_calories", 0) for day in weekly_plan.values())
        target_weekly_calories = user_preferences.get("calorie_target", 2000) * 7

        if total_weekly_calories > 0:
            adjustment_factor = target_weekly_calories / total_weekly_calories
            for day, day_plan in weekly_plan.items():
                for mname, recipe in day_plan["meals"].items():
                    # scale numeric fields
                    for k in ["calories", "protein", "carbs", "fat"]:
                        if k in recipe:
                            recipe[k] = max(0, int(recipe[k] * adjustment_factor))
                day_plan["total_calories"] = int(day_plan.get("total_calories", 0) * adjustment_factor)

        return weekly_plan
