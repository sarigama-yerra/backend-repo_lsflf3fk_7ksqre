import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import db, create_document, get_documents

app = FastAPI(title="IELTS Coach API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScoreIn(BaseModel):
    user_id: Optional[str] = None
    module: str
    score: float
    note: Optional[str] = None

class WritingIn(BaseModel):
    user_id: Optional[str] = None
    task_type: str
    prompt: Optional[str] = None
    content: str

class ReminderIn(BaseModel):
    user_id: Optional[str] = None
    title: str
    due_date: datetime
    category: Optional[str] = None

@app.get("/")
def read_root():
    return {"message": "IELTS Coach Backend Running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# 1) Scores: save and list
@app.post("/api/scores")
def add_score(payload: ScoreIn):
    try:
        from schemas import Userscore
        doc = Userscore(**payload.model_dump())
        inserted_id = create_document("userscore", doc)
        return {"id": inserted_id, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scores")
def list_scores(user_id: Optional[str] = None, module: Optional[str] = None, limit: int = 50):
    try:
        filter_dict = {}
        if user_id:
            filter_dict["user_id"] = user_id
        if module:
            filter_dict["module"] = module
        docs = get_documents("userscore", filter_dict, limit)
        for d in docs:
            d["_id"] = str(d.get("_id"))
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2) Writing: submit and simple evaluation mock
@app.post("/api/writing/evaluate")
def evaluate_writing(payload: WritingIn):
    try:
        from schemas import Writingsample
        text = payload.content
        # Simple heuristic evaluation as placeholder for real rubric (Task Response, Coherence, Lexical, Grammar)
        length = len(text.split())
        band = 5.0
        if length > 150 and payload.task_type.lower() == "task1":
            band += 1
        if length > 250 and payload.task_type.lower() == "task2":
            band += 1
        if any(w in text.lower() for w in ["however", "moreover", "furthermore", "consequently"]):
            band += 0.5
        band = min(9.0, round(band * 2) / 2)
        feedback = (
            "This is an automated estimate. Focus on task response, paragraphing, and a wider range of cohesive devices."
        )
        doc = Writingsample(
            user_id=payload.user_id,
            task_type=payload.task_type,
            prompt=payload.prompt,
            content=payload.content,
            estimated_band=band,
            feedback=feedback,
        )
        inserted_id = create_document("writingsample", doc)
        return {"id": inserted_id, "estimated_band": band, "feedback": feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3) Idea generation for essays (simple prompt-based suggestions)
class IdeaPrompt(BaseModel):
    topic: str
    count: int = 5

@app.post("/api/ideas")
def generate_ideas(p: IdeaPrompt):
    topic = p.topic.strip()
    ideas = [
        f"Angle {i+1}: Discuss {topic} from the perspective of education, economy, and culture",
        f"Angle {i+1}: Present causes, effects, and solutions related to {topic}",
        f"Angle {i+1}: Compare advantages vs disadvantages of {topic}",
        f"Angle {i+1}: Balance individual responsibility and government role in {topic}",
        f"Angle {i+1}: Provide examples and counterarguments about {topic}",
    ][: p.count]
    return {"topic": topic, "ideas": ideas}

# 4) Knowledge base: basic IELTS info
IELTS_INFO = {
    "bands": "Band scores range from 0 to 9 in 0.5 increments.",
    "modules": "Listening, Reading, Writing (Task 1 & 2), Speaking",
    "writing_task1": "Summarize visual information in at least 150 words in ~20 minutes.",
    "writing_task2": "Write an essay of at least 250 words in ~40 minutes.",
}

@app.get("/api/info")
def info():
    return IELTS_INFO

# 5) Reading passages mock (Cambridge-like structure)
class PassageRequest(BaseModel):
    level: str = "moderate"
    paragraphs: int = 3

@app.post("/api/reading/passages")
def create_passage(req: PassageRequest):
    title = "The Evolution of Urban Transport"
    paras = [
        "In recent decades, cities have witnessed a dramatic shift in mobility patterns...",
        "Technological innovations have catalyzed new modes such as e-scooters and ride-sharing...",
        "Ultimately, building resilient transport systems requires integrated planning...",
    ][: req.paragraphs]
    questions = [
        {"type": "T/F/NG", "q": "Technological change has influenced city transport."},
        {"type": "MCQ", "q": "Which factor is key to resilient systems?", "options": ["Cost", "Integration", "Speed"], "answer": "Integration"},
    ]
    return {"title": title, "paragraphs": paras, "questions": questions}

# 6) Reminders
@app.post("/api/reminders")
def add_reminder(rem: ReminderIn):
    try:
        from schemas import Reminder
        doc = Reminder(**rem.model_dump())
        inserted_id = create_document("reminder", doc)
        return {"id": inserted_id, "status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reminders")
def list_reminders(user_id: Optional[str] = None, limit: int = 100):
    try:
        filter_dict = {"user_id": user_id} if user_id else {}
        docs = get_documents("reminder", filter_dict, limit)
        for d in docs:
            d["_id"] = str(d.get("_id"))
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 7) Weakness analysis from scores
@app.get("/api/weaknesses")
def weaknesses(user_id: Optional[str] = None):
    try:
        scores = get_documents("userscore", {"user_id": user_id} if user_id else {}, 100)
        by_module = {}
        for s in scores:
            m = s.get("module")
            by_module.setdefault(m, []).append(s.get("score", 0))
        weak = []
        suggestions = []
        for m, vals in by_module.items():
            avg = sum(vals) / max(1, len(vals))
            if avg < 6.5:
                weak.append(m)
                if m.lower() == "writing":
                    suggestions.append("Practice paragraphing, coherence markers, and thesis clarity.")
                if m.lower() == "reading":
                    suggestions.append("Do skimming/scanning drills and vocabulary bundling.")
                if m.lower() == "listening":
                    suggestions.append("Shadow podcasts and improve prediction using question stems.")
        return {"weak_modules": weak, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
