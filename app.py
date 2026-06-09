import gradio as gr
import spaces
import json
from agent.vision import extract_and_classify
from agent.verifier import verify_sender
from agent.linker import find_connections
from agent.resolver import resolve_next_steps
from agent.memory import save_session, find_recurring

@spaces.GPU
def analyze_pile(images):
    if not images:
        return "Please upload at least one document photo.", ""

    docs = []
    for img_path in images:
        doc = extract_and_classify(img_path)
        docs.append(doc)

    recurring_alerts = find_recurring(docs)
    verifications = [verify_sender(d.get("sender", ""), d.get("full_text", "")) for d in docs]
    connections = find_connections(docs)
    resolutions = [resolve_next_steps(d) for d in docs]

    save_session(docs)

    output = build_output(docs, verifications, connections, resolutions, recurring_alerts)
    raw = json.dumps({"docs": docs, "verifications": verifications,
                      "connections": connections, "resolutions": resolutions}, indent=2)
    return output, raw

def build_output(docs, verifications, connections, resolutions, recurring_alerts):
    lines = ["# 📬 Paper Pile Report\n"]

    if recurring_alerts:
        lines.append("## ⚠️ Follow-up Alerts")
        for alert in recurring_alerts:
            lines.append(f"- {alert}")
        lines.append("")

    urgent = [i for i, d in enumerate(docs) if d.get("is_urgent")]
    if urgent:
        lines.append("## 🔴 Urgent Items")
        for i in urgent:
            d = docs[i]
            lines.append(f"**Document {i+1} — {d.get('sender', 'Unknown')}**")
            lines.append(f"> {d.get('summary', '')}")
            if d.get("deadline"):
                lines.append(f"⏰ Deadline: `{d['deadline']}`")
            if d.get("action_needed"):
                lines.append(f"✅ Action: {d['action_needed']}")
            v = verifications[i]
            if v.get("is_suspicious"):
                lines.append(f"🚨 **Suspicious:** {'; '.join(v['scam_flags']) or 'Sender unverified'}")
            r = resolutions[i]
            if r.get("resources"):
                lines.append("🔗 Resources:")
                for res in r["resources"][:2]:
                    lines.append(f"  - [{res['title']}]({res['url']})")
            lines.append("")

    lines.append("## 📋 All Documents")
    for i, d in enumerate(docs):
        v = verifications[i]
        status = "🚨 Suspicious" if v.get("is_suspicious") else "✅ Looks legitimate"
        lines.append(f"### Document {i+1}: {d.get('sender', 'Unknown')} ({d.get('doc_type', 'unknown')})")
        lines.append(f"{d.get('summary', '')}")
        lines.append(f"Sender status: {status}")
        if d.get("deadline"):
            lines.append(f"⏰ Deadline: {d['deadline']}")
        if d.get("action_needed"):
            lines.append(f"Action: {d['action_needed']}")
        lines.append("")

    if connections:
        lines.append("## 🔗 Connected Documents")
        for c in connections:
            lines.append(f"- **Doc {c['doc_a_index']+1}** and **Doc {c['doc_b_index']+1}** are related:")
            for r in c["reasons"]:
                lines.append(f"  - {r}")
        lines.append("")

    return "\n".join(lines)

with gr.Blocks(title="Paper Pile Agent") as demo:
    gr.Markdown("# 📬 Paper Pile Agent\nUpload photos of your mail pile. I'll read, verify, connect, and prioritize everything.")
    with gr.Row():
        with gr.Column():
            images = gr.File(label="Upload document photos", file_count="multiple",
                             file_types=["image"])
            submit = gr.Button("Analyze my pile", variant="primary")
        with gr.Column():
            report = gr.Markdown(label="Report")
            raw_json = gr.Code(label="Raw agent output (JSON)", language="json", visible=False)

    show_raw = gr.Checkbox(label="Show raw agent output")
    show_raw.change(lambda x: gr.update(visible=x), inputs=show_raw, outputs=raw_json)
    submit.click(analyze_pile, inputs=images, outputs=[report, raw_json])

demo.launch()