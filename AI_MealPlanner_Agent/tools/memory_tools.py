# tools/memory_tools.py
"""
AdvancedMemoryTools — robust, safe JSON handling for sessions, prefs, history.
Overwrite the existing tools/memory_tools.py with this file.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any
import os

logger = logging.getLogger("MemoryTools")
logger.addHandler(logging.NullHandler())


class AdvancedMemoryTools:
    def __init__(self):
        self.base_dir = "memory"
        self.sessions_file = os.path.join(self.base_dir, "active_sessions.json")
        self.preferences_file = os.path.join(self.base_dir, "user_preferences.json")
        self.history_file = os.path.join(self.base_dir, "meal_history.json")
        self._ensure_files()

    def _ensure_files(self):
        os.makedirs(self.base_dir, exist_ok=True)

        # sessions: dict
        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

        # preferences: dict
        if not os.path.exists(self.preferences_file):
            with open(self.preferences_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

        # history: list
        if not os.path.exists(self.history_file):
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    # ---------- helpers ----------
    def _safe_load(self, path: str, default: Any):
        try:
            txt = open(path, "r", encoding="utf-8").read().strip()
            if not txt:
                return default
            return json.loads(txt)
        except Exception:
            return default

    def _safe_write(self, path: str, data: Any):
        try:
            with open(path + ".tmp", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(path + ".tmp", path)
            return True
        except Exception as e:
            logger.error(f"Safe write error ({path}): {e}")
            try:
                # best-effort fallback
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e2:
                logger.error(f"Fallback write failed ({path}): {e2}")
                return False

    # ---------- sessions ----------
    def create_session(self, user_id: str) -> str:
        session_id = f"sess_{user_id}_{int(datetime.now().timestamp())}"
        sessions = self._safe_load(self.sessions_file, default={})
        sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "context": {},
        }
        self._safe_write(self.sessions_file, sessions)
        logger.info(f"Created session: {session_id}")
        return session_id

    def update_session(self, session_id: str, updates: Dict):
        sessions = self._safe_load(self.sessions_file, default={})
        if session_id in sessions:
            sessions[session_id].update(updates)
            sessions[session_id]["last_activity"] = datetime.now().isoformat()
            self._safe_write(self.sessions_file, sessions)
            logger.debug(f"Updated session: {session_id}")
        else:
            logger.warning(f"Session not found when updating: {session_id}")

    def get_session(self, session_id: str) -> Dict:
        sessions = self._safe_load(self.sessions_file, default={})
        return sessions.get(session_id, {})

    # ---------- preferences ----------
    def save_user_preferences(self, user_id: str, preferences: Dict):
        prefs = self._safe_load(self.preferences_file, default={})
        prefs[user_id] = {
            **preferences,
            "last_updated": datetime.now().isoformat(),
            "preference_strength": self._calc_strength(preferences),
        }
        ok = self._safe_write(self.preferences_file, prefs)
        if ok:
            logger.info(f"Saved preferences for {user_id}")
        return ok

    def get_user_preferences(self, user_id: str) -> Dict:
        prefs = self._safe_load(self.preferences_file, default={})
        return prefs.get(user_id, {})

    def _calc_strength(self, preferences: Dict) -> Dict:
        strength = {}
        for k, v in preferences.items():
            if isinstance(v, bool):
                strength[k] = "strong" if v else "weak"
            elif isinstance(v, list):
                strength[k] = "strong" if len(v) > 0 else "weak"
            elif isinstance(v, str):
                strength[k] = "medium" if v and v not in ["any", "flexible"] else "weak"
            else:
                strength[k] = "weak"
        return strength

    # ---------- history ----------
    def save_meal_feedback(self, user_id: str, meal_plan: Dict, feedback: Dict):
        history = self._safe_load(self.history_file, default=[])
        entry = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "meal_plan": meal_plan,
            "feedback": feedback or {},
        }
        history.append(entry)

        # keep last 500 entries overall to avoid growth (configurable)
        if len(history) > 500:
            history = history[-500:]

        ok = self._safe_write(self.history_file, history)
        if ok:
            logger.info(f"Saved history entry for {user_id}")
        return ok

    def get_user_history(self, user_id: str, limit: int = 20) -> List[Dict]:
        history = self._safe_load(self.history_file, default=[])
        user_entries = [h for h in history if h.get("user_id") == user_id]
        # latest first
        return list(reversed(user_entries))[:limit]

    # ---------- recommendations (simple) ----------
    def get_meal_recommendations(self, user_id: str, limit: int = 5) -> List[Dict]:
        user_history = self.get_user_history(user_id, limit=100)
        # naive approach: return most recent meal plans
        recs = []
        for h in user_history:
            recs.append({"timestamp": h.get("timestamp"), "sample": list(h.get("meal_plan", {}).keys())})
            if len(recs) >= limit:
                break
        return recs

    # ---------- maintenance ----------
    def cleanup_old_sessions(self, days_old: int = 7):
        sessions = self._safe_load(self.sessions_file, default={})
        cutoff = datetime.now().timestamp() - (days_old * 24 * 3600)
        kept = {}
        for sid, s in sessions.items():
            try:
                last = datetime.fromisoformat(s.get("last_activity")).timestamp()
            except Exception:
                last = 0
            if last >= cutoff:
                kept[sid] = s
            else:
                logger.info(f"Cleaning session {sid}")
        self._safe_write(self.sessions_file, kept)
        return True
