import modal

app = modal.App("paperpile")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "transformers>=4.49.0",
        "torch",
        "accelerate",
        "qwen-vl-utils",
        "Pillow",
        "fastapi[standard]",
    )
)

@app.cls(
    image=image,
    gpu="A10G",
    scaledown_window=300,  # keep warm for 5 mins between calls
)
class VisionModel:
    @modal.enter()
    def load(self):
        from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
        import torch
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            "Qwen/Qwen2.5-VL-7B-Instruct",
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        self.processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct")

    @modal.method()
    def analyze(self, image_bytes: bytes) -> dict:
        import torch, re, json
        from qwen_vl_utils import process_vision_info
        from PIL import Image
        import io

        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": (
                        "You are a document analysis assistant. Look at this document carefully.\n\n"
                        "Return a JSON object with these exact keys:\n"
                        "- doc_type: one of [bill, notice, tax, collections, government, bank, insurance, medical, unknown]\n"
                        "- sender: name of the organization that sent this\n"
                        "- summary: what this document is in 1-2 plain sentences a non-English-speaker could understand\n"
                        "- is_urgent: true or false\n"
                        "- deadline: the deadline date if any, or null\n"
                        "- requires_action: true or false\n"
                        "- action_needed: what the recipient needs to do, or null\n"
                        "- full_text: the full extracted text from the document\n\n"
                        "Return only the JSON, no preamble."
                    )}
                ]
            }
        ]

        text = self.processor.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = self.processor(
            text=[text], images=image_inputs, videos=video_inputs,
            padding=True, return_tensors="pt"
        ).to(self.model.device)

        with torch.no_grad():
            output_ids = self.model.generate(**inputs, max_new_tokens=1024)
        trimmed = output_ids[:, inputs.input_ids.shape[1]:]
        raw = self.processor.batch_decode(trimmed, skip_special_tokens=True)[0]
        clean = re.sub(r"```json|```", "", raw).strip()
        try:
            return json.loads(clean)
        except Exception:
            return {
                "doc_type": "unknown", "sender": "unknown", "summary": raw,
                "is_urgent": False, "deadline": None,
                "requires_action": False, "action_needed": None, "full_text": raw
            }


# Expose as a web endpoint so the Gradio Space can call it
@app.function(image=image)
@modal.fastapi_endpoint(method="POST")
async def analyze_endpoint(request: dict) -> dict:
    import base64
    image_bytes = base64.b64decode(request["image_b64"])
    model = VisionModel()
    return model.analyze.remote(image_bytes)