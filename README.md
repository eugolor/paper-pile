# 📬 Paper Pile Agent

> An AI agent that reads, verifies, and prioritizes your mail pile, built for immigrant families and non-technical users.

**Live demo → [huggingface.co/spaces/eugolor/paper-pile](https://huggingface.co/spaces/eugolor/paper-pile)**



## What It Does That a Chat Can't

Paper Pile Agent is a **multi-step agentic pipeline**, not a wrapper around a single prompt. Here's what it does that you cannot replicate by dragging a photo into ChatGPT:

| Capability | Single chat | Paper Pile Agent |
|---|---|---|
| Read and summarize a document | ✅ | ✅ |
| Verify if the sender is legitimate | ❌ | ✅ |
| Cross-reference multiple documents and find connections | ❌ | ✅ |
| Look up the real Canadian government resource for your specific situation | ❌ | ✅ |
| Remember what you uploaded last time and flag follow-ups | ❌ | ✅ |
| Export deadlines to a calendar file | ❌ | ✅ |
| Run entirely offline — no data sent to third parties | ❌ | ✅ |

---

## Architecture

```
User uploads photo(s)
        ↓
  Agent orchestrator
  ┌─────┬──────────┬────────────┬──────────────┬────────┐
  ↓     ↓          ↓            ↓              ↓        ↓
Vision  Scam     Cross-doc   Next-step      Memory
+ OCR  verifier   linker      resolver       store
  └─────┴──────────┴────────────┴──────────────┴────────┘
        ↓
  Synthesis + reasoning
        ↓
  Priority checklist
  + verified senders
  + linked documents
  + real next steps
  + .ics calendar export
```

**Model:** `Qwen2.5-VL-7B-Instruct` — vision + language, 7B parameters, served via Modal  
**Frontend:** Gradio on HuggingFace Spaces  
**Inference:** Modal (A10G GPU, ~$1.10/hr, ~$250 credits from hackathon)  
**Privacy:** Fully offline verification — no third-party AI APIs, no data sent to OpenAI/Anthropic

---

## The Five Agent Tools

### 1. Vision + OCR (`agent/vision.py`)
Sends each document image to a Modal-hosted Qwen2.5-VL-7B endpoint. Returns structured JSON: doc type, sender, plain-language summary, urgency, deadline, required action, and full extracted text.

### 2. Scam Verifier (`agent/verifier.py`)
Checks the sender against a curated database of known Canadian organizations — federal and provincial government agencies, major banks, insurance companies, telecoms, and utilities. Scans document text for known scam phrases. Runs entirely locally, no web calls.

### 3. Cross-Document Linker (`agent/linker.py`)
Compares all documents in the pile pairwise. Flags connections: same sender, same deadline, shared reference numbers, overlapping case/account identifiers. Surfaces relationships a human would miss when reading one letter at a time.

### 4. Next-Step Resolver (`agent/resolver.py`)
Maps each document type to curated, real Canadian government and consumer protection resources. CRA notices get CRA portal links. Collections letters get Ontario consumer rights links. Insurance documents get CDCP and OLHI links. All hardcoded — no hallucinated URLs.

### 5. Memory Store (`agent/memory.py`)
Persists the last 20 sessions as a local JSON file. On each new upload, compares senders against past sessions and flags anything that looks like a second notice or follow-up. Requires at least 2 past sessions before alerting to avoid false positives.

---

## Output

For each mail pile, the agent produces:

- **Follow-up alerts** — flagging documents from senders you've heard from before
- **Urgent items** — prioritized, with deadline and exact action required
- **Full document list** — plain-language summary + sender verification status for every doc
- **Connected documents** — cross-references across the pile
- **Calendar export** — `.ics` file with all deadlines, importable to any calendar app

---

## Tech Stack

```
Gradio          → frontend UI, hosted on HuggingFace Spaces
Modal           → GPU inference endpoint (Qwen2.5-VL-7B)
Transformers    → model loading and inference
qwen-vl-utils   → vision input processing
Python          → agent pipeline orchestration
```

---

## Setup

### 1. Clone and install
```bash
git clone https://github.com/YOUR_USERNAME/paper-pile-agent
cd paper-pile-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Deploy the Modal endpoint
```bash
pip install modal
modal setup
modal deploy modal_app.py
```
Copy the endpoint URL Modal prints.

### 3. Set the environment variable
```bash
export MODAL_ENDPOINT="https://YOUR_USERNAME--paperpile-analyze-endpoint.modal.run"
```

Or add it as a secret in your HuggingFace Space settings.

### 4. Run locally
```bash
gradio app.py
```

---

## Project Structure

```
paper-pile-agent/
├── app.py                  # Gradio frontend
├── modal_app.py            # Modal GPU inference endpoint
├── agent/
│   ├── vision.py           # OCR + document classification (calls Modal)
│   ├── verifier.py         # Offline sender verification
│   ├── linker.py           # Cross-document connection finder
│   ├── resolver.py         # Next-step resource lookup
│   └── memory.py           # Session memory and follow-up detection
└── requirements.txt
```


## Built By

**Ejiro Ugolor** — CS Honours graduate, York University (Lassonde School of Engineering)  
ML / AI Engineering · [huggingface.co/eugolor](https://huggingface.co/eugolor)




---
title: Paper Pile
emoji: 🏃
colorFrom: red
colorTo: green
sdk: gradio
sdk_version: 6.17.3
python_version: '3.13'
app_file: app.py
pinned: false
license: mit
short_description: Agent that reads, verifies, and prioritizes your mail pile
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
