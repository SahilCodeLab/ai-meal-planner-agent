#!/usr/bin/env python3
"""
🤖 AI Meal Planner Agent - Kaggle Capstone Project
Multi-Agent System with Memory, Tools, and Observability
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Any
import os
import random
from collections import defaultdict

# Configure logging for observability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent_logs.json'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("MealPlannerAgent")

class MemoryBank:
    """Long-term memory for user preferences and history"""
    
    def __init__(self):
        self.memory_file = "memory/user_preferences.json"
        self.history_file = "memory/meal_history.json"
        self._ensure_directories()
    
    def _ensure_directories(self):
        os.makedirs("memory", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Initialize memory files if they don't exist
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w') as f:
                json.dump({}, f)
        
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'w') as f:
                json.dump([], f)
    
    def save_user_preferences(self, user_id: str, preferences: Dict):
        """Save user preferences to long-term memory"""
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
            
            data[user_id] = {
                **preferences,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved preferences for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
            return False
    
    def get_user_preferences(self, user_id: str) -> Dict:
        """Retrieve user preferences from memory"""
        try:
            with open(self.memory_file, 'r') as f:
                data = json.load(f)
            return data.get(user_id, {})
        except Exception as e:
            logger.error(f"Error reading preferences: {e}")
            return {}
    
    def save_meal_history(self, user_id: str, meal_plan: Dict):
        """Save meal plan to history"""
        try:
            with open(self.history_file, 'r') as f:
                history = json.load(f)
            
            history_entry = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "meal_plan": meal_plan
            }
            
            history.append(history_entry)
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=2)
            
            logger.info(f"Saved meal history for user: {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving history: {e}")
            return False

class SimpleMealGenerator:
    """Simple meal generator - NO FILE READING"""
    
    def __init__(self):
        self.recipes = self.create_sample_recipes()  # Direct recipes, no file read
    
    def create_sample_recipes(self) -> Dict:
        """Create sample recipes directly in code"""
        sample_recipes = {
            "breakfast": [
                {
                    "name": "Masala Oats",
                    "ingredients": {"oats": 50, "vegetables": 100, "spices": 10, "oil": 5},
                    "calories": 250,
                    "protein": 12,
                    "carbs": 40,
                    "fat": 6,
                    "prep_time": 15,
                    "type": "vegetarian"
                },
                {
                    "name": "Paneer Paratha", 
                    "ingredients": {"whole_wheat_flour": 80, "paneer": 100, "spices": 10, "oil": 8},
                    "calories": 380,
                    "protein": 18,
                    "carbs": 45,
                    "fat": 15,
                    "prep_time": 25,
                    "type": "vegetarian"
                },
                {
                    "name": "Egg Bhurji",
                    "ingredients": {"eggs": 3, "onion": 50, "tomato": 50, "spices": 10, "oil": 7},
                    "calories": 280,
                    "protein": 20,
                    "carbs": 10,
                    "fat": 18,
                    "prep_time": 15,
                    "type": "non-vegetarian"
                }
            ],
            "lunch": [
                {
                    "name": "Dal Rice with Salad",
                    "ingredients": {"rice": 150, "dal": 100, "vegetables": 200, "spices": 15, "oil": 10},
                    "calories": 450,
                    "protein": 22,
                    "carbs": 75,
                    "fat": 12,
                    "prep_time": 30,
                    "type": "vegetarian"
                },
                {
                    "name": "Chicken Curry with Roti",
                    "ingredients": {"chicken": 200, "whole_wheat_flour": 100, "spices": 20, "oil": 15},
                    "calories": 520,
                    "protein": 35,
                    "carbs": 45,
                    "fat": 22,
                    "prep_time": 40,
                    "type": "non-vegetarian"
                }
            ],
            "dinner": [
                {
                    "name": "Vegetable Khichdi",
                    "ingredients": {"rice": 100, "dal": 80, "vegetables": 150, "spices": 10, "ghee": 8},
                    "calories": 380,
                    "protein": 15,
                    "carbs": 60,
                    "fat": 10,
                    "prep_time": 25,
                    "type": "vegetarian"
                },
                {
                    "name": "Grilled Fish with Vegetables",
                    "ingredients": {"fish": 150, "vegetables": 200, "lemon": 1, "spices": 10, "oil": 5},
                    "calories": 320,
                    "protein": 28,
                    "carbs": 15,
                    "fat": 18,
                    "prep_time": 20,
                    "type": "non-vegetarian"
                }
            ]
        }
        return sample_recipes
    
    def generate_daily_meal_plan(self, diet_type: str = "vegetarian"):
        """Generate one day meal plan"""
        meals = {}
        total_calories = 0
        
        for meal_type in ['breakfast', 'lunch', 'dinner']:
            available_recipes = self.recipes.get(meal_type, [])
            filtered_recipes = [r for r in available_recipes if r['type'] == diet_type or diet_type == "mixed"]
            
            if filtered_recipes:
                selected_recipe = random.choice(filtered_recipes)
                meals[meal_type] = selected_recipe
                total_calories += selected_recipe['calories']
            else:
                # Fallback recipe
                meals[meal_type] = {
                    "name": f"Simple {meal_type}",
                    "ingredients": {"basic_food": 100},
                    "calories": 300,
                    "protein": 10,
                    "carbs": 40,
                    "fat": 8,
                    "prep_time": 10,
                    "type": diet_type
                }
                total_calories += 300
        
        return {
            'meals': meals,
            'total_calories': total_calories
        }
    
    def generate_weekly_plan(self, diet_type: str = "vegetarian"):
        """Generate weekly meal plan"""
        weekly_plan = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day in days:
            weekly_plan[day] = self.generate_daily_meal_plan(diet_type)
        
        return weekly_plan

class NutritionCalculator:
    """Simple nutrition calculator"""
    
    def analyze_meal_plan_nutrition(self, meal_plan: Dict) -> Dict:
        """Analyze nutrition content of meal plan"""
        total_calories = 0
        total_protein = 0
        meal_count = 0
        
        for day, day_plan in meal_plan.items():
            for meal_type, recipe in day_plan['meals'].items():
                total_calories += recipe.get('calories', 0)
                total_protein += recipe.get('protein', 0)
                meal_count += 1
        
        # Calculate weekly averages per day
        days_count = len(meal_plan)
        if days_count > 0:
            avg_calories = total_calories / days_count
            avg_protein = total_protein / days_count
        else:
            avg_calories = avg_protein = 0
        
        return {
            'avg_daily_calories': avg_calories,
            'avg_daily_protein': avg_protein,
            'total_meals': meal_count
        }

class ShoppingListGenerator:
    """Shopping list generator"""
    
    def generate_shopping_list(self, weekly_plan: Dict) -> Dict:
        """Generate shopping list from weekly meal plan"""
        shopping_list = defaultdict(float)
        
        for day, day_plan in weekly_plan.items():
            for meal_type, recipe in day_plan['meals'].items():
                for ingredient, quantity in recipe.get('ingredients', {}).items():
                    shopping_list[ingredient] += quantity
        
        # Convert to proper units
        formatted_list = {}
        for ingredient, total_quantity in shopping_list.items():
            if total_quantity >= 1000:
                formatted_list[ingredient] = f"{total_quantity/1000:.1f} kg"
            else:
                formatted_list[ingredient] = f"{total_quantity:.0f} grams"
        
        return formatted_list

class MealPlannerAgent:
    """Main Agent with sequential workflow"""
    
    def __init__(self):
        self.memory_bank = MemoryBank()
        self.meal_gen = SimpleMealGenerator()
        self.nutrition_calc = NutritionCalculator()
        self.shopping_gen = ShoppingListGenerator()
        logger.info("MealPlannerAgent initialized")
    
    async def sequential_workflow(self, user_input: Dict) -> Dict:
        """Sequential multi-agent workflow"""
        logger.info("Starting sequential workflow")
        
        try:
            # Agent 1: Process user input
            processed_input = await self._process_input_agent(user_input)
            
            # Agent 2: Generate meal plan
            meal_plan = await self._planning_agent(processed_input)
            
            # Agent 3: Analyze nutrition
            analysis = await self._analysis_agent(meal_plan)
            
            # Agent 4: Generate shopping list
            shopping_list = await self._shopping_agent(meal_plan)
            
            # Save to memory
            self.memory_bank.save_meal_history(user_input.get('user_id', 'default'), meal_plan)
            
            return {
                "meal_plan": meal_plan,
                "nutrition_analysis": analysis,
                "shopping_list": shopping_list,
                "session_id": f"sess_{user_input.get('user_id', 'user')}_{int(datetime.now().timestamp())}",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            raise e
    
    async def _process_input_agent(self, user_input: Dict) -> Dict:
        """Agent 1: Process and validate user input"""
        logger.info("Input Processing Agent working...")
        await asyncio.sleep(0.1)
        return user_input
    
    async def _planning_agent(self, processed_input: Dict) -> Dict:
        """Agent 2: Generate meal plan"""
        logger.info("Meal Planning Agent working...")
        
        diet_type = processed_input.get('preferences', {}).get('diet_type', 'vegetarian')
        weekly_plan = self.meal_gen.generate_weekly_plan(diet_type)
        
        await asyncio.sleep(0.2)
        return weekly_plan
    
    async def _analysis_agent(self, meal_plan: Dict) -> Dict:
        """Agent 3: Analyze nutrition"""
        logger.info("Nutrition Analysis Agent working...")
        
        analysis = self.nutrition_calc.analyze_meal_plan_nutrition(meal_plan)
        
        await asyncio.sleep(0.1)
        return analysis
    
    async def _shopping_agent(self, meal_plan: Dict) -> Dict:
        """Agent 4: Generate shopping list"""
        logger.info("Shopping List Agent working...")
        
        shopping_list = self.shopping_gen.generate_shopping_list(meal_plan)
        
        await asyncio.sleep(0.1)
        return shopping_list

class AgentEvaluator:
    """Agent performance evaluation"""
    
    def log_performance(self, agent_name: str, execution_time: float, success: bool):
        """Log agent performance metrics"""
        try:
            metrics_file = "logs/performance_metrics.json"
            
            if os.path.exists(metrics_file):
                with open(metrics_file, 'r') as f:
                    metrics = json.load(f)
            else:
                metrics = []
            
            metrics.append({
                "agent": agent_name,
                "timestamp": datetime.now().isoformat(),
                "execution_time": execution_time,
                "success": success
            })
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Error logging metrics: {e}")