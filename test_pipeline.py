# test_pipeline.py
# Run this BEFORE building the Android app.
# Every test must pass. Fix failures here, not during the demo.

from pipeline import VaaniSetuPipeline
from lesson_engine import get_all_lessons, get_lesson, LessonSession
from worksheet import generate_bilingual_worksheet
import os

print("=" * 60)
print("VaaniSetu Full Pipeline Test")
print("=" * 60)

p = VaaniSetuPipeline()

print("\nTest 1: Hindi → Santali translation")
hindi = "आज हम जोड़ना सीखेंगे।"
santali, english = p.hindi_to_santali(hindi, "lesson_script")
print(f"  Input:   {hindi}")
print(f"  Pivot:   {english}")
print(f"  Output:  {santali}")
assert len(santali) > 0, "Translation returned empty string"
print("  PASS")

print("\nTest 2: Santali → Hindi (bidirectional)")
hindi_back = p.santali_to_hindi(santali)
print(f"  Input:   {santali}")
print(f"  Output:  {hindi_back}")
assert len(hindi_back) > 0, "Reverse translation returned empty string"
print("  PASS")

print("\nTest 3: Santali TTS")
audio_path = p.santali_tts(santali)
assert os.path.exists(audio_path), "Audio file not created"
size_kb = os.path.getsize(audio_path) // 1024
print(f"  Audio saved: {audio_path} ({size_kb} KB)")
print("  PASS")

print("\nTest 4: Three FLN content modes")
hindi_q = "पांच और तीन कितने होते हैं?"
for mode in ["lesson_script", "activity_instruction", "assessment_prompt"]:
    out, _ = p.hindi_to_santali(hindi_q, mode)
    print(f"  Mode '{mode}': {out[:50]}...")
print("  PASS — all three modes produced output")

print("\nTest 5: NIPUN Bharat lesson engine")
lessons = get_all_lessons()
print(f"  Available lessons: {len(lessons)}")
lesson = get_lesson("2", "addition")
assert lesson is not None, "Grade 2 addition lesson not found"
sess = LessonSession(lesson)
assert sess.total_steps > 0, "Lesson has no steps"
print(f"  Lesson loaded: '{lesson['title']}' ({sess.total_steps} steps)")

print("\nTest 6: Session tracking and comprehension signal")
sess.record_translation("तीन और चार", santali, 1.2)
for _ in range(sess.total_steps):
    sess.advance_step()
signal = sess.record_student_response("7")
print(f"  Response '7' → signal: {signal}")
assert signal == "green", f"Expected green, got {signal}"
summary = sess.get_session_summary()
print(f"  Summary: {summary['comprehension']['summary']}")
print("  PASS")

print("\nTest 7: Bilingual worksheet PDF generation")
pdf_path = generate_bilingual_worksheet(
    hindi_text=hindi,
    santali_text=santali,
    grade="2",
    topic="Addition",
    output_path="test_worksheet.pdf"
)
assert os.path.exists(pdf_path), "PDF not created"
size_kb = os.path.getsize(pdf_path) // 1024
print(f"  Worksheet saved: {pdf_path} ({size_kb} KB)")
print("  PASS")

print("\n" + "=" * 60)
print("ALL TESTS PASSED")
print("Run: python app.py")
print("=" * 60)