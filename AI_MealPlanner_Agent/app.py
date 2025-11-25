from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import uvicorn
import logging
import json
import os

from tools.memory_tools import AdvancedMemoryTools
from tools.gemini_tools import SmartGeminiTools

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("MealPlannerAPI")

# FastAPI App
app = FastAPI(title="AI Meal Planner", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve UI
if os.path.isdir("templates"):
    app.mount("/static", StaticFiles(directory="templates"), name="static")

memory_tools = None
gemini_tools = None


# =====================================
# MODELS
# =====================================
class UserPreferences(BaseModel):
    diet_type: str
    calorie_target: int
    allergies: List[str]
    cuisine_preference: str
    goals: List[str]


class MealPlanRequest(BaseModel):
    user_id: str
    preferences: UserPreferences
    session_id: Optional[str] = None


# =====================================
# STARTUP
# =====================================
@app.on_event("startup")
async def startup_event():
    global memory_tools, gemini_tools
    logger.info("Initializing tools...")

    memory_tools = AdvancedMemoryTools()
    gemini_tools = SmartGeminiTools()

    logger.info("Startup complete")


# =====================================
# HOME ROUTE (Frontend)
# =====================================
@app.get("/")
async def home():
    if os.path.exists("templates/index.html"):
        return FileResponse("templates/index.html")
    return {"message": "UI not found"}


# =====================================
# GENERATE PLAN
# =====================================
@app.post("/api/meal-plan/generate")
async def generate_plan(req: MealPlanRequest, background: BackgroundTasks):

    logger.info(f"Meal plan request from: {req.user_id}")

    try:
        prefs = req.preferences.dict()

        # Generate meal plan (GeminiTools → fallback auto)
        result = gemini_tools.generate_varied_meal_plan(prefs)

        # Create session
        session_id = memory_tools.create_session(req.user_id)

        # Save preferences
        memory_tools.save_user_preferences(req.user_id, prefs)

        # Save meal history
        memory_tools.save_meal_feedback(
            req.user_id,
            result["meal_plan"],
            {"rating": 0, "comments": "auto saved"}
        )

        return {
            "success": True,
            "meal_plan": result["meal_plan"],
            "analysis": result["analysis"],
            "shopping_list": result["shopping_list"],
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(500, str(e))


# =====================================
# HISTORY FETCH API (Frontend)
# =====================================
@app.get("/api/meal-plan/history/{user_id}")
async def get_history(user_id: str):

    try:
        file = "memory/meal_history.json"

        if not os.path.exists(file):
            return []

        data = json.load(open(file, "r", encoding="utf-8"))

        user_data = [h for h in data if h.get("user_id") == user_id]

        return user_data[::-1]

    except Exception as e:
        logger.error(f"History error: {e}")
        return []


# =====================================
# DELETE HISTORY ENTRY (NEW — WORKING)
# =====================================
@app.delete("/api/meal-plan/history/{user_id}/{timestamp}")
async def delete_history_item(user_id: str, timestamp: str):

    try:
        file = "memory/meal_history.json"

        if not os.path.exists(file):
            return {"success": False, "msg": "History file missing"}

        data = json.load(open(file, "r", encoding="utf-8"))

        new_data = [
            item for item in data
            if not (
                item.get("user_id") == user_id and
                item.get("timestamp") == timestamp
            )
        ]

        json.dump(new_data, open(file, "w", encoding="utf-8"), indent=2)

        return {"success": True, "removed": True}

    except Exception as e:
        logger.error(f"Delete error: {e}")
        return {"success": False, "error": str(e)}


# =====================================
# RUN SERVER
# =====================================
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
