# app.py
# Full REST API — all endpoints for the Android app

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, time, tempfile
from pipeline import VaaniSetuPipeline
from lesson_engine import get_all_lessons, get_lesson, LessonSession
from worksheet import generate_bilingual_worksheet

app = Flask(__name__)
CORS(app)

# ── Load pipeline once at startup ────────────────────────────────────────────
print("Starting VaaniSetu server...")
pipeline = VaaniSetuPipeline()

# ── Active lesson sessions (keyed by session_id) ─────────────────────────────
sessions = {}

# ── Health check ─────────────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "message": "VaaniSetu server running",
        "device": "GPU" if __import__('torch').cuda.is_available() else "CPU"
    })

# ── Lesson catalog ────────────────────────────────────────────────────────────

@app.route("/lessons", methods=["GET"])
def list_lessons():
    """Returns all available NIPUN Bharat lessons"""
    return jsonify({"lessons": get_all_lessons()})

# ── Start a lesson session ────────────────────────────────────────────────────

@app.route("/session/start", methods=["POST"])
def start_session():
    """
    POST: {"grade": "2", "topic": "addition"}
    Returns session_id and first step
    """
    data = request.json
    grade = data.get("grade", "2")
    topic = data.get("topic", "addition")

    lesson = get_lesson(grade, topic)
    if not lesson:
        return jsonify({"error": f"Lesson not found: grade{grade}/{topic}"}), 404

    session_id = f"session_{int(time.time())}"
    sessions[session_id] = LessonSession(lesson)

    session = sessions[session_id]
    return jsonify({
        "session_id": session_id,
        "lesson_title": lesson["title"],
        "competency": lesson["competency"],
        "total_steps": session.total_steps,
        "current_step": session.current_step,
        "step_data": session.current_step_data()
    })

# ── Translate audio (main endpoint) ──────────────────────────────────────────

@app.route("/translate/audio", methods=["POST"])
def translate_audio():
    """
    POST multipart: audio file + mode + session_id (optional)
    Returns: hindi_text, santali_text, audio_url, latency
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    mode       = request.form.get("mode", "lesson_script")
    session_id = request.form.get("session_id", None)

    audio_file = request.files["audio"]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    result = pipeline.full_forward_pipeline(tmp_path, mode)
    os.unlink(tmp_path)

    if session_id and session_id in sessions:
        sess = sessions[session_id]
        sess.record_translation(
            result["hindi_text"],
            result["santali_text"],
            result["latency"]["total_seconds"]
        )

    return jsonify({
        "hindi_text":    result["hindi_text"],
        "santali_text":  result["santali_text"],
        "english_pivot": result["english_pivot"],
        "audio_url":     "/audio/output",
        "latency":       result["latency"]
    })

# ── Serve generated audio ─────────────────────────────────────────────────────

@app.route("/audio/output", methods=["GET"])
def get_audio():
    return send_file("output_santali.wav", mimetype="audio/wav")

# ── Advance lesson step ───────────────────────────────────────────────────────

@app.route("/session/next", methods=["POST"])
def next_step():
    """
    POST: {"session_id": "..."}
    Returns next step data
    """
    session_id = request.json.get("session_id")
    if not session_id or session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    sess = sessions[session_id]
    sess.advance_step()
    step = sess.current_step_data()

    if step is None:
        return jsonify({
            "session_id": session_id,
            "completed": True,
            "message": "Lesson complete — request /session/summary"
        })

    return jsonify({
        "session_id": session_id,
        "completed": False,
        "current_step": sess.current_step,
        "total_steps": sess.total_steps,
        "step_data": step
    })

# ── Record student response (comprehension check) ────────────────────────────

@app.route("/session/response", methods=["POST"])
def record_response():
    """
    POST: {"session_id": "...", "response": "student typed/selected answer"}
    Returns comprehension signal: "green" | "yellow" | "red"
    """
    data       = request.json
    session_id = data.get("session_id")
    response   = data.get("response", "")

    if not session_id or session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    sess   = sessions[session_id]
    signal = sess.record_student_response(response)

    signal_messages = {
        "green":  "Correct! Student understood.",
        "yellow": "Partial — student may need another try.",
        "red":    "Incorrect — repeat the concept."
    }

    return jsonify({
        "signal":  signal,
        "message": signal_messages[signal],
        "response_recorded": response
    })

# ── Session summary (teacher report) ─────────────────────────────────────────

@app.route("/session/summary", methods=["POST"])
def session_summary():
    """
    POST: {"session_id": "..."}
    Returns full session summary for teacher
    """
    session_id = request.json.get("session_id")
    if not session_id or session_id not in sessions:
        return jsonify({"error": "Session not found"}), 404

    summary = sessions[session_id].get_session_summary()
    return jsonify(summary)

# ── Reverse translation (bidirectional) ──────────────────────────────────────

@app.route("/translate/reverse", methods=["POST"])
def translate_reverse():
    """
    POST: {"santali_text": "..."}
    Returns Hindi translation of student's Santali response
    """
    data         = request.json
    santali_text = data.get("santali_text", "")
    if not santali_text:
        return jsonify({"error": "No Santali text provided"}), 400

    hindi_text = pipeline.santali_to_hindi(santali_text)
    return jsonify({
        "santali_text": santali_text,
        "hindi_text":   hindi_text
    })

# ── Worksheet generation ──────────────────────────────────────────────────────

@app.route("/worksheet", methods=["POST"])
def create_worksheet():
    """
    POST: {"hindi_text": "...", "santali_text": "...",
           "grade": "2", "topic": "...", "session_id": "..."}
    Returns bilingual PDF worksheet
    """
    data         = request.json
    hindi_text   = data.get("hindi_text", "")
    santali_text = data.get("santali_text", "")
    grade        = data.get("grade", "2")
    topic        = data.get("topic", "Lesson Content")
    session_id   = data.get("session_id", None)

    lesson_steps = None
    if session_id and session_id in sessions:
        sess = sessions[session_id]
        lesson_steps = []
        for t in sess.translations:
            step_data = sess.lesson["steps"][t["step"]] if t["step"] < len(sess.lesson["steps"]) else {}
            lesson_steps.append({
                "type":               step_data.get("type", "lesson_script"),
                "hindi":              t["hindi"],
                "santali_translated": t["santali"],
                "note":               step_data.get("note", "")
            })

    pdf_path = generate_bilingual_worksheet(
        hindi_text=hindi_text,
        santali_text=santali_text,
        grade=grade,
        topic=topic,
        lesson_steps=lesson_steps,
        output_path="vaanisetu_worksheet.pdf"
    )

    return send_file(pdf_path, mimetype="application/pdf",
                     download_name="VaaniSetu_Worksheet.pdf")

if __name__ == "__main__":
    print("\nVaaniSetu server ready.")
    print("Find your IP: run 'ifconfig' (Mac/Linux) or 'ipconfig' (Windows)")
    print("Update SERVER_URL in MainActivity.kt with your IP")
    print("Starting on port 5000...\n")
    app.run(host="0.0.0.0", port=5000, debug=False)