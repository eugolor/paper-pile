from duckduckgo_search import DDGS

KNOWN_SCAM_PATTERNS = [
    "you have won", "urgent wire transfer", "irs agent will arrest",
    "cra arrest warrant", "bitcoin payment required", "gift card payment"
]

def verify_sender(sender: str, doc_text: str) -> dict:
    flags = []
    text_lower = doc_text.lower()
    for pattern in KNOWN_SCAM_PATTERNS:
        if pattern in text_lower:
            flags.append(f"Scam phrase detected: '{pattern}'")

    legitimacy = "unknown"
    search_summary = ""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"{sender} official website Canada", max_results=3))
        if results:
            search_summary = results[0].get("body", "")
            top_urls = [r.get("href", "") for r in results]
            gov_domains = [u for u in top_urls if any(d in u for d in [".gc.ca", ".gov", ".ca", ".com"])]
            if gov_domains:
                legitimacy = "likely_legitimate"
            else:
                legitimacy = "unverified"
    except Exception as e:
        search_summary = f"Search failed: {e}"
        legitimacy = "unverified"

    return {
        "sender": sender,
        "legitimacy": legitimacy,
        "scam_flags": flags,
        "search_summary": search_summary,
        "is_suspicious": len(flags) > 0 or legitimacy == "unverified"
    }