def find_connections(docs: list[dict]) -> list[dict]:
    connections = []
    for i, doc_a in enumerate(docs):
        for j, doc_b in enumerate(docs):
            if i >= j:
                continue
            reasons = []
            sender_a = (doc_a.get("sender") or "").lower()
            sender_b = (doc_b.get("sender") or "").lower()
            if sender_a and sender_b and sender_a == sender_b:
                reasons.append(f"Both from the same sender: {doc_a.get('sender')}")
            deadline_a = doc_a.get("deadline")
            deadline_b = doc_b.get("deadline")
            if deadline_a and deadline_b and deadline_a == deadline_b:
                reasons.append(f"Same deadline: {deadline_a}")
            text_a = (doc_a.get("full_text") or "").lower()
            text_b = (doc_b.get("full_text") or "").lower()
            keywords = ["account number", "reference number", "file number", "case number", "sin", "tax year"]
            for kw in keywords:
                if kw in text_a and kw in text_b:
                    reasons.append(f"Both reference '{kw}' — may be related")
                    break
            if reasons:
                connections.append({
                    "doc_a_index": i,
                    "doc_b_index": j,
                    "doc_a_summary": doc_a.get("summary", f"Document {i+1}"),
                    "doc_b_summary": doc_b.get("summary", f"Document {j+1}"),
                    "reasons": reasons
                })
    return connections