# pipeline.py
# Core AI pipeline with all novelty features

import torch
import numpy as np
import soundfile as sf
import whisper
import time
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from parler_tts import ParlerTTSForConditionalGeneration
from IndicTransToolkit.processor import IndicProcessor

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Running on: {DEVICE}")

class VaaniSetuPipeline:

    def __init__(self):
        print("Loading VaaniSetu pipeline...")

        # ── Hindi ASR ──────────────────────────────────────────────────────
        print("  Loading Whisper (Hindi ASR)...")
        self.whisper = whisper.load_model(
            "small", download_root="./models/whisper")
        print("  Whisper loaded.")

        # ── NMT: Indic→En (for Hindi→English pivot step) ──────────────────
        print("  Loading IndicTrans2 Indic→En...")
        self.tok_indic_en = AutoTokenizer.from_pretrained(
            "./models/indic_en", trust_remote_code=True)
        self.mdl_indic_en = AutoModelForSeq2SeqLM.from_pretrained(
            "./models/indic_en",
            trust_remote_code=True,
            torch_dtype=torch.float32
        ).to(DEVICE)
        self.mdl_indic_en.eval()
        print("  Indic→En loaded.")

        # ── NMT: En→Indic (for English→Santali pivot step) ────────────────
        print("  Loading IndicTrans2 En→Indic (includes Santali)...")
        self.tok_en_indic = AutoTokenizer.from_pretrained(
            "./models/en_indic", trust_remote_code=True)
        self.mdl_en_indic = AutoModelForSeq2SeqLM.from_pretrained(
            "./models/en_indic",
            trust_remote_code=True,
            torch_dtype=torch.float32
        ).to(DEVICE)
        self.mdl_en_indic.eval()
        print("  En→Indic loaded.")

        # ── TTS: Santali speech synthesis ─────────────────────────────────
        # Indic Parler-TTS needs TWO tokenizers: one for the prompt (text to
        # speak) and one for the description (voice style). This differs
        # from the standard Parler-TTS single-tokenizer usage.
        print("  Loading Indic Parler-TTS (Santali)...")
        self.tts_mdl = ParlerTTSForConditionalGeneration.from_pretrained(
            "./models/indic_tts").to(DEVICE)
        self.tts_mdl.eval()
        self.tts_prompt_tokenizer = AutoTokenizer.from_pretrained(
            "./models/indic_tts")
        self.tts_desc_tokenizer = AutoTokenizer.from_pretrained(
            self.tts_mdl.config.text_encoder._name_or_path)
        print("  TTS loaded.")

        # ── IndicProcessor ─────────────────────────────────────────────────
        self.ip = IndicProcessor(inference=True)
        print("\nAll models loaded. VaaniSetu is ready.\n")

    # ── PRIVATE: raw NMT translation ──────────────────────────────────────

    def _translate(self, text, src_lang, tgt_lang, tokenizer, model):
        batch = self.ip.preprocess_batch(
            [text], src_lang=src_lang, tgt_lang=tgt_lang)
        inputs = tokenizer(
            batch, truncation=True, padding="longest",
            return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            generated = model.generate(
                **inputs, num_beams=4,
                num_return_sequences=1, max_new_tokens=256)
        decoded = tokenizer.batch_decode(
            generated, skip_special_tokens=True,
            clean_up_tokenization_spaces=True)
        result = self.ip.postprocess_batch(decoded, lang=tgt_lang)
        return result[0]

    # ── PUBLIC: Hindi ASR ─────────────────────────────────────────────────

    def transcribe_hindi(self, audio_path):
        """Hindi audio → Hindi text. Uses Whisper (excellent Hindi quality)."""
        result = self.whisper.transcribe(audio_path, language="hi")
        return result["text"].strip()

    # ── PUBLIC: Hindi → Santali (via English pivot) ───────────────────────

    def hindi_to_santali(self, hindi_text, content_mode="lesson_script"):
        """
        Hindi text → Santali text
        Uses English as pivot for better quality on low-resource Santali.
        content_mode: "lesson_script" | "activity_instruction" | "assessment_prompt"
        """
        mode_context = {
            "lesson_script":        "शिक्षण: ",
            "activity_instruction": "गतिविधि निर्देश: ",
            "assessment_prompt":    "प्रश्न: "
        }
        prefix = mode_context.get(content_mode, "")
        enriched = prefix + hindi_text

        english = self._translate(
            enriched, "hin_Deva", "eng_Latn",
            self.tok_indic_en, self.mdl_indic_en)

        santali = self._translate(
            english, "eng_Latn", "sat_Olck",
            self.tok_en_indic, self.mdl_en_indic)

        return santali, english

    # ── PUBLIC: Santali → Hindi (reverse, via English pivot) ─────────────

    def santali_to_hindi(self, santali_text):
        """Santali text → Hindi text (bidirectional return path)"""
        english = self._translate(
            santali_text, "sat_Olck", "eng_Latn",
            self.tok_indic_en, self.mdl_indic_en)

        hindi = self._translate(
            english, "eng_Latn", "hin_Deva",
            self.tok_en_indic, self.mdl_en_indic)

        return hindi

    # ── PUBLIC: Santali TTS ───────────────────────────────────────────────

    def santali_tts(self, santali_text, output_path="output_santali.wav"):
        """Santali text → WAV audio file"""
        description = "A female speaker delivers clear, natural Santali speech."

        desc_inputs = self.tts_desc_tokenizer(
            description, return_tensors="pt").input_ids.to(DEVICE)
        prompt_inputs = self.tts_prompt_tokenizer(
            santali_text, return_tensors="pt").input_ids.to(DEVICE)

        with torch.no_grad():
            audio = self.tts_mdl.generate(
                input_ids=desc_inputs, prompt_input_ids=prompt_inputs)

        audio_np = audio.cpu().numpy().squeeze()
        if audio_np.ndim > 1:
            audio_np = audio_np[0]
        sf.write(output_path, audio_np, samplerate=self.tts_mdl.config.sampling_rate)
        return output_path

    # ── PUBLIC: Full forward pipeline ────────────────────────────────────

    def full_forward_pipeline(self, audio_path, content_mode="lesson_script"):
        """
        Complete teacher→student pipeline:
        Hindi audio → Hindi text → Santali text → Santali audio
        Returns dict with all outputs and timing.
        """
        t_start = time.time()

        t0 = time.time()
        hindi_text = self.transcribe_hindi(audio_path)
        t_asr = round(time.time() - t0, 2)

        t0 = time.time()
        santali_text, english_pivot = self.hindi_to_santali(
            hindi_text, content_mode)
        t_nmt = round(time.time() - t0, 2)

        t0 = time.time()
        audio_path_out = self.santali_tts(santali_text)
        t_tts = round(time.time() - t0, 2)

        total = round(time.time() - t_start, 2)

        return {
            "hindi_text":     hindi_text,
            "english_pivot":  english_pivot,
            "santali_text":   santali_text,
            "audio_path":     audio_path_out,
            "latency": {
                "asr_seconds": t_asr,
                "nmt_seconds": t_nmt,
                "tts_seconds": t_tts,
                "total_seconds": total
            }
        }