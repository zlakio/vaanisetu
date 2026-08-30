# download_models.py
# Run ONCE. Takes 20-40 minutes depending on internet speed.
# Models are saved locally — no internet needed after this.

import os
os.makedirs("models", exist_ok=True)

print("=" * 50)
print("Step 1/4: Hindi ASR (Whisper Small)")
print("=" * 50)
import whisper
_ = whisper.load_model("small", download_root="./models/whisper")
print("Done.\n")

print("=" * 50)
print("Step 2/4: Hindi → Santali NMT (IndicTrans2 En-Indic)")
print("Note: Hindi→Santali goes through English pivot for best quality")
print("=" * 50)
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Hindi → English (step 1 of pivot)
model_hi_en = "ai4bharat/indictrans2-indic-en-dist-200M"
tok = AutoTokenizer.from_pretrained(model_hi_en, trust_remote_code=True)
mdl = AutoModelForSeq2SeqLM.from_pretrained(model_hi_en, trust_remote_code=True)
tok.save_pretrained("./models/indic_en")
mdl.save_pretrained("./models/indic_en")
print("Indic→En downloaded.\n")

# English → Santali (step 2 of pivot)
model_en_sat = "ai4bharat/indictrans2-en-indic-dist-200M"
tok2 = AutoTokenizer.from_pretrained(model_en_sat, trust_remote_code=True)
mdl2 = AutoModelForSeq2SeqLM.from_pretrained(model_en_sat, trust_remote_code=True)
tok2.save_pretrained("./models/en_indic")
mdl2.save_pretrained("./models/en_indic")
print("En→Indic (includes Santali) downloaded.\n")

print("=" * 50)
print("Step 3/4: Santali TTS (Indic Parler-TTS)")
print("=" * 50)
from transformers import AutoTokenizer
from parler_tts import ParlerTTSForConditionalGeneration
tts_name = "ai4bharat/indic-parler-tts"
proc = AutoTokenizer.from_pretrained(tts_name)
tts = ParlerTTSForConditionalGeneration.from_pretrained(tts_name)
proc.save_pretrained("./models/indic_tts")
tts.save_pretrained("./models/indic_tts")
print("TTS downloaded.\n")

print("=" * 50)
print("Step 4/4: Verifying all models...")
print("=" * 50)
import os
for path in ["models/whisper", "models/indic_en", "models/en_indic", "models/indic_tts"]:
    exists = os.path.exists(path)
    print(f"  {'OK' if exists else 'MISSING'}: {path}")

print("\nAll models ready. Run: python test_pipeline.py")