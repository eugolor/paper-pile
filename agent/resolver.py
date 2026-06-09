from duckduckgo_search import DDGS

ACTION_LOOKUP_TEMPLATES = {
    "tax": "how to respond to CRA notice Canada official steps",
    "collections": "how to respond to collections letter Canada rights",
    "government": "how to respond to government notice Canada",
    "bill": "how to dispute or pay bill Canada",
    "bank": "how to respond to bank notice Canada",
    "medical": "how to respond to medical bill or notice Canada",
}

def resolve_next_steps(doc: dict) -> dict:
    doc_type = doc.get("doc_type", "unknown")
    action = doc.get("action_needed")
    if not doc.get("requires_action") or not action:
        return {"next_steps": None, "resources": []}

    query = ACTION_LOOKUP_TEMPLATES.get(doc_type, f"how to respond to {doc_type} notice Canada")
    resources = []
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        resources = [{"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body", "")[:200]}
                     for r in results]
    except Exception:
        pass

    return {
        "action_needed": action,
        "next_steps": f"Based on document type '{doc_type}': {action}",
        "resources": resources
    }