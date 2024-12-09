# src/app.py
import os
import sqlite3
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .message_board import MessageBoard
from .llm_client import LLMClient
from .agents import PlannerAgent, ResearcherAgent, CriticAgent, WriterAgent, SummarizerAgent
from .orchestrator import Orchestrator

app = FastAPI()

app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "frontend", "static")), name="static")

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "frontend", "templates"))

SESSION_ID = "main_session"

def get_session_messages(session_id: str = SESSION_ID, db_path: str = "database.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT sender, content, tags, timestamp FROM messages WHERE session_id=? ORDER BY timestamp ASC", (session_id,))
    rows = cur.fetchall()
    conn.close()

    results = []
    for r in rows:
        sender, content, tags_str, ts = r
        tags = tags_str.split(",") if tags_str else []
        results.append({
            "sender": sender,
            "content": content.strip(),
            "tags": tags,
            "timestamp": ts
        })
    return results

def run_session():
    board = MessageBoard(session_id=SESSION_ID)
    llm = LLMClient()

    planner = PlannerAgent(name="Planner", message_board=board, llm_client=llm)
    researcher = ResearcherAgent(name="Researcher", message_board=board, llm_client=llm)
    critic = CriticAgent(name="Critic", message_board=board, llm_client=llm)
    writer = WriterAgent(name="Writer", message_board=board, llm_client=llm)
    summarizer = SummarizerAgent(name="Summarizer", message_board=board, llm_client=llm)

    orchestrator = Orchestrator(
        message_board=board,
        planner=planner,
        researcher=researcher,
        critic=critic,
        writer=writer,
        summarizer=summarizer,
        max_cycles=5
    )
    orchestrator.run()

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    MessageBoard(session_id=SESSION_ID)  # ensure table and session
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/messages")
def api_get_messages():
    msgs = get_session_messages()
    return {"messages": msgs}

@app.post("/api/new_goal")
async def api_new_goal(payload: dict):
    goal = payload.get("goal", None)
    if not goal:
        raise HTTPException(status_code=400, detail="goal is required")

    board = MessageBoard(session_id=SESSION_ID)
    board.post_message("User", goal, tags=["user_goal"])
    run_session()
    return {"status": "ok"}
