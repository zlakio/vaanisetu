# VaaniSetu — AI Teaching Assistant for Tribal Classrooms

**Smart India Hackathon 2026 | Problem Statement SIH26042 | Smart Education**
**Government of Jharkhand | NIPUN Bharat Aligned**

VaaniSetu is a bidirectional Hindi↔Santali speech translation and teaching assistant, built to help teachers in tribal classrooms deliver mother-tongue-based foundational learning under the NIPUN Bharat / PALASH MTB-MLE programme.

---

## The Problem

Teachers in tribal regions often don't speak the local mother tongue (e.g. Santali) of their students, creating a language barrier that undermines Foundational Literacy and Numeracy (FLN) outcomes for young children. VaaniSetu bridges that gap in real time, in the classroom, without requiring the teacher to learn the language.

## What Makes This Different

1. **Bidirectional** — the teacher speaks Hindi, the student can respond in Santali, and the teacher hears it back in Hindi.
2. **Three FLN content modes** — lesson scripts, activity instructions, and assessment prompts are each translated with different curricular context, not generic sentence-by-sentence translation.
3. **Pre-loaded NIPUN Bharat lesson templates** — structured, grade-appropriate teaching sequences for Grades 1–3, not a blank translation box.
4. **Comprehension signal** — after an assessment prompt, the app shows a green/yellow/red signal per student response.
5. **Session summary** — a teacher-facing report after each lesson: sentences translated, comprehension score, time spent.
6. **Bilingual worksheet + flashcard generator** — auto-generated PDF worksheets aligned to NIPUN Bharat learning outcomes.

## Architecture

```
Android app (Kotlin, teacher UI)
        │  audio + text over local WiFi
        ▼
Python backend (Flask REST API)
   ├─ Whisper (Hindi ASR)
   ├─ IndicTrans2 (Hindi ⇄ Santali, via English pivot)
   └─ Indic Parler-TTS (Santali speech synthesis)
```

This prototype runs the Python AI pipeline on a laptop, with the Android app and laptop on the same WiFi network for the demo. Full on-device inference (ONNX INT8 on a 2GB RAM tablet, per the problem statement's offline requirement) is planned as a Phase 2 optimization — this build demonstrates the complete feature set end-to-end.

## Tech Stack

| Layer | Technology |
|---|---|
| ASR | OpenAI Whisper (small) |
| Translation | AI4Bharat IndicTrans2 (distilled, 200M) |
| TTS | AI4Bharat Indic Parler-TTS |
| Backend | Python, Flask |
| PDF generation | ReportLab |
| Mobile app | Kotlin, Android (Views + OkHttp) |

---

## Setup

### Prerequisites

- Python 3.10 or 3.11
- Android Studio
- ~4 GB free disk space for models
- A C++ build toolchain (Windows: Visual Studio Build Tools with the "Desktop development with C++" workload — required to compile `IndicTransToolkit`)

### Backend

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac / Linux

pip install --upgrade pip

# Core ML
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install transformers==4.46.1 accelerate sentencepiece sacremoses protobuf

# IndicTrans2 toolkit
pip install git+https://github.com/VarunGumma/IndicTransToolkit.git

# Whisper
pip install openai-whisper

# TTS + audio
pip install soundfile librosa numpy scipy
pip install git+https://github.com/huggingface/parler-tts.git

# API server + PDF + utilities
pip install flask flask-cors reportlab pillow pydub hf_xet
```

Download the models (one-time, ~3.5 GB):

```bash
python download_models.py
```

Some AI4Bharat models are gated on Hugging Face — log in first and accept access on each model page before downloading:

```bash
pip install huggingface_hub
huggingface-cli login
```

Run the test suite before touching the Android app:

```bash
python test_pipeline.py
```

Start the server:

```bash
python app.py
```

Find your laptop's local IP (`ipconfig` on Windows / `ifconfig` on Mac/Linux) and confirm the server is reachable at `http://<your-ip>:5000/health` from a browser on the same WiFi network.

### Android app

1. Open the `VaaniSetu` project in Android Studio.
2. Update the `SERVER` constant in `MainActivity.kt` with your laptop's local IP.
3. Build and run on a device connected to the same WiFi network as the backend.

---

## Project Structure

```
sih_proto/
├── app.py              # Flask REST API server
├── pipeline.py          # ASR + NMT + TTS pipeline
├── lesson_engine.py     # NIPUN Bharat lesson templates + session tracking
├── worksheet.py          # Bilingual PDF worksheet generator
├── test_pipeline.py     # End-to-end test suite
├── download_models.py   # One-time model download script
└── models/               # Downloaded model weights (not committed — see .gitignore)

VaaniSetu/                # Android Studio project (Kotlin)
```

---


