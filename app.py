import gradio as gr
import json
import tempfile
import os
from agent.vision import extract_and_classify
from agent.verifier import verify_sender
from agent.linker import find_connections
from agent.resolver import resolve_next_steps
from agent.memory import save_session, find_recurring
from agent.calendar import generate_ics

CSS = """
.gradio-container { max-width: 860px !important; margin: 0 auto !important; }
.report-box { background: var(--background-fill-secondary); border-radius: 12px; padding: 24px; }
.urgent { border-left: 4px solid #ef4444; padding-left: 12px; margin-bottom: 12px; }
.badge { display: inline-block; background: #1e293b; color: #94a3b8;
         font-size: 11px; padding: 2px 8px; border-radius: 999px; margin: 2px; }
footer { display: none !important; }
#title { text-align: center; margin-bottom: 4px; }
#subtitle { text-align: center; color: var(--body-text-color-subdued); margin-bottom: 24px; }
"""

def analyze_pile(images):
    if not images:
        return "Upload at least one document photo to get started.", "", None

    docs = []
    for img_path in images:
        doc = extract_and_classify(img_path)
        docs.append(doc)

    recurring_alerts = find_recurring(docs)
    verifications = [verify_sender(d.get("sender", ""), d.get("full_text", "")) for d in docs]
    connections = find_connections(docs)
    resolutions = [resolve_next_steps(d) for d in docs]
    save_session(docs)

    report = build_report(docs, verifications, connections, resolutions, recurring_alerts)
    raw = json.dumps({
        "docs": docs,
        "verifications": verifications,
        "connections": connections,
        "resolutions": resolutions
    }, indent=2)

    # Generate .ics if any deadlines exist
    ics_content = generate_ics(docs)
    ics_path = None
    if ics_content:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".ics", mode="w")
        tmp.write(ics_content)
        tmp.close()
        ics_path = tmp.name

    return report, raw, ics_path

def build_report(docs, verifications, connections, resolutions, recurring_alerts):
    lines = []

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
            v = verifications[i]
            r = resolutions[i]
            lines.append(f"**{d.get('sender', 'Unknown')}** — `{d.get('doc_type', '?')}`")
            lines.append(f"> {d.get('summary', '')}")
            if d.get("deadline"):
                lines.append(f"⏰ **Deadline:** {d['deadline']}")
            if d.get("action_needed"):
                lines.append(f"✅ **Action:** {d['action_needed']}")
            if v.get("is_suspicious"):
                lines.append(f"🚨 **Suspicious:** {'; '.join(v['scam_flags']) or 'Sender unverified'}")
            if r.get("resources"):
                lines.append("🔗 **Resources:**")
                for res in r["resources"][:2]:
                    lines.append(f"  - [{res['title']}]({res['url']})")
            lines.append("")

    lines.append("## 📋 All Documents")
    for i, d in enumerate(docs):
        v = verifications[i]
        status = "🚨 Suspicious" if v.get("is_suspicious") else "✅ Looks legitimate"
        lines.append(f"### Document {i+1}: {d.get('sender', 'Unknown')}")
        lines.append(f"{d.get('summary', '')}")
        lines.append(f"**Sender:** {status}")
        if d.get("deadline"):
            lines.append(f"**Deadline:** {d['deadline']}")
        if d.get("action_needed"):
            lines.append(f"**Action:** {d['action_needed']}")
        lines.append("")

    if connections:
        lines.append("## 🔗 Connected Documents")
        for c in connections:
            lines.append(f"- **Doc {c['doc_a_index']+1}** and **Doc {c['doc_b_index']+1}** are linked:")
            for r in c["reasons"]:
                lines.append(f"  - {r}")
        lines.append("")

    return "\n".join(lines)

with gr.Blocks(css=CSS, title="Paper Pile Agent") as demo:
    gr.Markdown("# 📬 Paper Pile", elem_id="title")
    gr.Markdown(
        "Upload photos of your mail. I'll read every document, verify the sender, "
        "flag what's urgent, find connections, and tell you exactly what to do next.",
        elem_id="subtitle"
    )

    with gr.Row():
        with gr.Column(scale=1):
            images = gr.File(
                label="Drop your mail photos here",
                file_count="multiple",
                file_types=["image"]
            )
            submit = gr.Button("📬 Analyze my pile", variant="primary", size="lg")
            gr.Markdown(
                "`✅ Sender verified` &nbsp; `⏰ Deadlines extracted` &nbsp; "
                "`🔗 Documents linked` &nbsp; `📅 Calendar export`",
            )

        with gr.Column(scale=2):
            report = gr.Markdown(elem_classes=["report-box"])
            calendar_file = gr.File(label="📅 Download calendar (.ics)", visible=False)
            with gr.Accordion("Raw agent output (JSON)", open=False):
                raw_json = gr.Code(language="json")

    def run(images):
        report_md, raw, ics_path = analyze_pile(images)
        cal_update = gr.update(value=ics_path, visible=ics_path is not None)
        return report_md, raw, cal_update

    submit.click(run, inputs=images, outputs=[report, raw_json, calendar_file])

demo.launch()