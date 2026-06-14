import json
import os
from datetime import datetime

MEMORY_FILE = "session_memory.json"

def load_memory() -> list:
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_session(docs: list[dict]) -> None:
    memory = load_memory()
    memory.append({
        "timestamp": datetime.now().isoformat(),
        "docs": [{"sender": d.get("sender"), "doc_type": d.get("doc_type"),
                  "summary": d.get("summary"), "deadline": d.get("deadline")} for d in docs]
    })
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory[-20:], f, indent=2)

def find_recurring(docs: list[dict]) -> list[str]:
    memory = load_memory()
    if len(memory) < 2:  # need at least 2 past sessions before alerting
        return []
    past_sessions = memory[:-1]  # exclude current session
    past_senders = set()
    for session in past_sessions:
        for d in session.get("docs", []):
            if d.get("sender"):
                past_senders.add(d["sender"].lower())
    alerts = []
    for doc in docs:
        sender = (doc.get("sender") or "").lower()
        if sender and sender in past_senders:
            alerts.append(f"⚠️ You've received mail from '{doc.get('sender')}' before — this may be a follow-up.")
    return alerts