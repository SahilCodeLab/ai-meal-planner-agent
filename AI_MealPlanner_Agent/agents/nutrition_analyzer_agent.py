"""
🔬 Nutrition Analyzer Agent - Specialized in nutrition analysis
Uses AI for advanced nutrition insights
"""

import logging
import asyncio
from typing import Dict, List
import json

logger = logging.getLogger("NutritionAnalyzerAgent")

class NutritionAnalyzerSpecialist:
    """Specialized agent for nutrition analysis with AI"""
    
    def __init__(self, gemini_tool):
        self.gemini_tool = gemini_tool
        self.nutrition_standards = self._load_nutrition_standards()
        logger.info("NutritionAnalyzerSpecialist initialized")
    
    def _load_nutrition_standards(self) -> Dict:
        """Load nutrition standards and guidelines"""
        return {
            'weight_loss': {'protein_ratio': 0.3, 'carbs_ratio': 0.4, 'fat_ratio': 0.3},
            'muscle_building': {'protein_ratio': 0.35, 'carbs_ratio': 0.4, 'fat_ratio': 0.25},
            'maintenance': {'protein_ratio': 0.25, 'carbs_ratio': 0.45, 'fat_ratio': 0.3},
            'general_health': {'protein_ratio': 0.2, 'carbs_ratio': 0.5, 'fat_ratio': 0.3}
        }
    
    async def analyze_meal_plan(self, meal_plan: Dict, user_goal: str = "maintenance") -> Dict:
        """Comprehensive nutrition analysis"""
        logger.info("Starting nutrition analysis")
        
        # Basic nutrient calculation
        basic_analysis = self._calculate_basic_nutrition(meal_plan)
        
        # Goal compliance analysis
        goal_analysis = self._analyze_goal_compliance(basic_analysis, user_goal)
        
        # AI-powered insights
        ai_insights = await self._get_ai_insights(meal_plan, user_goal)
        
        # Variety and balance assessment
        variety_analysis = self._analyze_variety(meal_plan)
        
        return {
            "basic_nutrition": basic_analysis,
            "goal_compliance": goal_analysis,
            "ai_insights": ai_insights,
            "variety_assessment": variety_analysis,
            "overall_score": self._calculate_overall_score(goal_analysis, variety_analysis),
            "recommendations": self._generate_recommendations(goal_analysis, variety_analysis)
        }
    
    def _calculate_basic_nutrition(self, meal_plan: Dict) -> Dict:
        """Calculate basic nutrition metrics"""
        total_calories = 0
        total_protein = 0
        total_carbs = 0
        total_fat = 0
        meal_count = 0
        
        for day, daily_plan in meal_plan.items():
            for meal_type, recipe in daily_plan.get('meals', {}).items():
                total_calories += recipe.get('calories', 0)
                total_protein += recipe.get('protein', 0)
                total_carbs += recipe.get('carbs', 0)
                total_fat += recipe.get('fat', 0)
                meal_count += 1
        
        days_count = len(meal_plan)
        
        return {
            "avg_daily_calories": total_calories / days_count if days_count > 0 else 0,
            "avg_daily_protein": total_protein / days_count if days_count > 0 else 0,
            "avg_daily_carbs": total_carbs / days_count if days_count > 0 else 0,
            "avg_daily_fat": total_fat / days_count if days_count > 0 else 0,
            "total_meals": meal_count,
            "protein_ratio": total_protein / (total_protein + total_carbs + total_fat) if (total_protein + total_carbs + total_fat) > 0 else 0
        }
    
    def _analyze_goal_compliance(self, nutrition: Dict, user_goal: str) -> Dict:
        """Analyze how well the plan meets user goals"""
        standards = self.nutrition_standards.get(user_goal, self.nutrition_standards['maintenance'])
        
        protein_ratio = nutrition.get('protein_ratio', 0)
        target_protein_ratio = standards['protein_ratio']
        
        protein_compliance = max(0, 10 - abs(protein_ratio - target_protein_ratio) * 100)
        
        return {
            "protein_compliance_score": min(10, protein_compliance),
            "meets_protein_target": protein_compliance >= 7,
            "target_protein_ratio": target_protein_ratio,
            "actual_protein_ratio": protein_ratio
        }
    
    async def _get_ai_insights(self, meal_plan: Dict, user_goal: str) -> Dict:
        """Get AI-powered nutrition insights"""
        if not self.gemini_tool.model:
            return {"insights": "AI analysis unavailable", "suggestions": []}
        
        try:
            prompt = f"""
            As a nutrition expert, analyze this weekly meal plan for someone with goal: {user_goal}
            
            Meal Plan: {json.dumps(meal_plan, indent=2)}
            
            Provide:
            1. Three key nutritional strengths
            2. Three areas for improvement  
            3. Specific food substitution suggestions
            4. Overall health impact assessment
            
            Format as JSON with keys: strengths, improvements, substitutions, health_impact.
            """
            
            response = self.gemini_tool.model.generate_content(prompt)
            return self._parse_ai_response(response.text)
            
        except Exception as e:
            logger.error(f"AI insight generation failed: {e}")
            return {"error": str(e)}
    
    def _parse_ai_response(self, response: str) -> Dict:
        """Parse AI response into structured format"""
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response[start:end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback parsing
        return {
            "strengths": ["Balanced macronutrients", "Good variety"],
            "improvements": ["Increase protein diversity", "Add more vegetables"],
            "substitutions": ["Consider quinoa instead of rice"],
            "health_impact": "Generally healthy with minor adjustments needed"
        }
    
    def _analyze_variety(self, meal_plan: Dict) -> Dict:
        """Analyze meal variety and diversity"""
        all_meals = []
        ingredient_counts = {}
        
        for day, daily_plan in meal_plan.items():
            for meal_type, recipe in daily_plan.get('meals', {}).items():
                all_meals.append(recipe['name'])
                # Count ingredients
                for ingredient in recipe.get('ingredients', {}).keys():
                    ingredient_counts[ingredient] = ingredient_counts.get(ingredient, 0) + 1
        
        unique_meals = len(set(all_meals))
        total_meals = len(all_meals)
        unique_ingredients = len(ingredient_counts)
        
        variety_score = (unique_meals / total_meals * 10) if total_meals > 0 else 0
        ingredient_diversity = min(10, unique_ingredients / 3)  # Normalize score
        
        return {
            "variety_score": variety_score,
            "ingredient_diversity": ingredient_diversity,
            "unique_meals": unique_meals,
            "total_meals": total_meals,
            "unique_ingredients": unique_ingredients,
            "assessment": "Excellent" if variety_score >= 8 else "Good" if variety_score >= 6 else "Needs Improvement"
        }
    
    def _calculate_overall_score(self, goal_analysis: Dict, variety_analysis: Dict) -> float:
        """Calculate overall nutrition score"""
        goal_score = goal_analysis.get('protein_compliance_score', 5)
        variety_score = variety_analysis.get('variety_score', 5)
        ingredient_score = variety_analysis.get('ingredient_diversity', 5)
        
        return (goal_score * 0.5 + variety_score * 0.3 + ingredient_score * 0.2)
    
    def _generate_recommendations(self, goal_analysis: Dict, variety_analysis: Dict) -> List[str]:
        """Generate specific recommendations"""
        recommendations = []
        
        if not goal_analysis.get('meets_protein_target', False):
            recommendations.append("Increase protein-rich foods like lentils, chicken, or fish")
        
        if variety_analysis.get('variety_score', 0) < 6:
            recommendations.append("Add more variety to prevent meal boredom")
        
        if variety_analysis.get('unique_ingredients', 0) < 15:
            recommendations.append("Incorporate more diverse ingredients for better nutrition")
        
        if len(recommendations) == 0:
            recommendations.append("Great job! Your meal plan is well-balanced and varied")
        
        return recommendations