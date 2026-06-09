import requests
import base64
import os
from PIL import Image
import io

# Set this after you deploy: modal deploy modal_app.py
MODAL_ENDPOINT = os.environ.get("MODAL_ENDPOINT", "")

def extract_and_classify(image_path: str) -> dict:
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Resize large images before sending to save bandwidth
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((1024, 1024))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    image_b64 = base64.b64encode(buf.getvalue()).decode()

    if not MODAL_ENDPOINT:
        return _fallback(image_path)

    try:
        response = requests.post(
            MODAL_ENDPOINT,
            json={"image_b64": image_b64},
            timeout=120
        )
        return response.json()
    except Exception as e:
        return _fallback(image_path, error=str(e))

def _fallback(image_path: str, error: str = "") -> dict:
    return {
        "doc_type": "unknown",
        "sender": "Unknown",
        "summary": f"Could not process document. {error}".strip(),
        "is_urgent": False,
        "deadline": None,
        "requires_action": False,
        "action_needed": None,
        "full_text": ""
    }