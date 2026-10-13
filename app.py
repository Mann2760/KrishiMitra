import os
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = os.getenv("SQLITE_PATH", str(BASE_DIR / "krishimitra.db"))
USE_FIRESTORE = os.getenv("USE_FIRESTORE", "false").lower() == "true"
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

_firestore = None
if USE_FIRESTORE:
    from google.cloud import firestore
    _firestore = firestore.Client(project=PROJECT_ID)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def init_sqlite():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS advisories (
                id TEXT PRIMARY KEY,
                crop TEXT NOT NULL,
                location TEXT NOT NULL,
                growth_stage TEXT NOT NULL,
                symptoms TEXT NOT NULL,
                language TEXT NOT NULL,
                advisory TEXT NOT NULL,
                generation_mode TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                advisory_id TEXT NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def save_advisory(record):
    if USE_FIRESTORE:
        _firestore.collection("advisories").document(record["id"]).set(record)
    else:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO advisories
                (id, crop, location, growth_stage, symptoms, language, advisory, generation_mode, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["id"], record["crop"], record["location"], record["growth_stage"],
                record["symptoms"], record["language"], record["advisory"],
                record["generation_mode"], record["created_at"]
            ))
            conn.commit()


def get_advisory(advisory_id):
    if USE_FIRESTORE:
        doc = _firestore.collection("advisories").document(advisory_id).get()
        return doc.to_dict() if doc.exists else None
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM advisories WHERE id = ?", (advisory_id,)).fetchone()
        return dict(row) if row else None


def list_advisories(limit=20):
    limit = max(1, min(int(limit), 50))
    if USE_FIRESTORE:
        docs = (
            _firestore.collection("advisories")
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .stream()
        )
        return [doc.to_dict() for doc in docs]
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM advisories ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def save_feedback(record):
    if USE_FIRESTORE:
        _firestore.collection("feedback").document(record["id"]).set(record)
    else:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO feedback (id, advisory_id, rating, comment, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                record["id"], record["advisory_id"], record["rating"],
                record["comment"], record["created_at"]
            ))
            conn.commit()


def fallback_advisory(crop, location, stage, symptoms, language):
    # Safe, deterministic fallback so the app still runs without a Gemini key.
    labels = {
        "English": {
            "title": "Preliminary crop observation plan",
            "note": "Demo mode: this is a general checklist, not a diagnosis.",
            "steps": [
                "Inspect 5–10 plants in different parts of the field and note whether the same symptoms repeat.",
                "Check both sides of affected leaves and look for insects, spots, yellowing, wilting, or damage patterns.",
                "Take clear photos in daylight and record when the symptoms first appeared and whether they are spreading.",
                "Avoid mixing or applying pesticides until the cause is confirmed and the product label and local guidance are checked."
            ],
            "expert": "Contact a local agricultural extension officer, KVK, or qualified agronomist if symptoms spread quickly, many plants are affected, or the crop is at risk.",
            "follow": "Recheck the same marked plants in 24–48 hours and record any change."
        },
        "Hindi": {
            "title": "फसल के शुरुआती निरीक्षण की योजना",
            "note": "डेमो मोड: यह सामान्य जाँच-सूची है, पक्का निदान नहीं।",
            "steps": [
                "खेत के अलग-अलग हिस्सों में 5–10 पौधों की जाँच करें और देखें कि लक्षण बार-बार दिख रहे हैं या नहीं।",
                "प्रभावित पत्तियों के दोनों तरफ देखें और कीट, धब्बे, पीलापन, मुरझाना या नुकसान के पैटर्न नोट करें।",
                "दिन के उजाले में साफ तस्वीरें लें और लिखें कि लक्षण कब शुरू हुए और क्या वे फैल रहे हैं।",
                "कारण की पुष्टि होने और उत्पाद के लेबल व स्थानीय सलाह जाँचने से पहले कीटनाशक न मिलाएँ या न छिड़कें।"
            ],
            "expert": "यदि लक्षण तेजी से फैलें, कई पौधे प्रभावित हों या फसल को खतरा हो, तो स्थानीय कृषि अधिकारी, KVK या योग्य कृषि विशेषज्ञ से संपर्क करें।",
            "follow": "24–48 घंटे बाद उन्हीं चिन्हित पौधों को दोबारा जाँचें और बदलाव लिखें।"
        },
        "Marathi": {
            "title": "पिकाच्या प्राथमिक निरीक्षणाची योजना",
            "note": "डेमो मोड: ही सामान्य तपासणी यादी आहे; निश्चित निदान नाही.",
            "steps": [
                "शेतातील वेगवेगळ्या भागांतील ५–१० झाडे तपासा आणि तीच लक्षणे वारंवार दिसतात का ते नोंदवा.",
                "प्रभावित पानांच्या दोन्ही बाजू तपासा; कीड, डाग, पिवळेपणा, कोमेजणे किंवा नुकसानाचा नमुना नोंदवा.",
                "दिवसा स्पष्ट फोटो घ्या आणि लक्षणे कधी सुरू झाली व पसरत आहेत का ते लिहा.",
                "कारण निश्चित होईपर्यंत आणि उत्पादनाचे लेबल व स्थानिक मार्गदर्शन तपासेपर्यंत कीटकनाशके मिसळू किंवा फवारू नका.",
            ],
            "expert": "लक्षणे वेगाने पसरत असतील, अनेक झाडे बाधित असतील किंवा पिकाला धोका असेल तर स्थानिक कृषी अधिकारी, KVK किंवा पात्र कृषी तज्ज्ञांशी संपर्क साधा.",
            "follow": "२४–४८ तासांनी तीच चिन्हांकित झाडे पुन्हा तपासा आणि बदल नोंदवा."
        }
    }
    text = labels.get(language, labels["English"])
    steps = "\n".join(f"{i+1}. {step}" for i, step in enumerate(text["steps"]))
    return (
        f"{text['title']}\n\n{ text['note'] }\n\n"
        f"Your report\n- Crop: {crop}\n- Location: {location}\n- Growth stage: {stage}\n- Observed symptoms: {symptoms}\n\n"
        f"Recommended next steps\n{steps}\n\n"
        f"When to seek expert help\n{text['expert']}\n\n"
        f"Follow-up\n{text['follow']}\n\n"
        "Important: This tool does not confirm a pest or disease and does not replace local expert advice. "
        "Do not use a chemical treatment based only on this response."
    )


def generate_advisory(crop, location, stage, symptoms, language):
    if not GEMINI_API_KEY:
        return fallback_advisory(crop, location, stage, symptoms, language), "demo_fallback"

    try:
        from google import genai
        from google.genai import types
        from google.genai import errors as genai_errors

        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"""
You are KrishiMitra, a cautious agricultural information assistant for smallholder farmers.
Respond in {language}. Use clear, complete, practical advice tailored to the farmer's report.
Farmer report:
Crop: {crop}
Location (farmer-provided; do not infer weather or local conditions): {location}
Growth stage: {stage}
Observed symptoms: {symptoms}

Write a complete response with these headings:
1. What this may indicate
Give 2-3 possible explanations, clearly state that these are possibilities and not a diagnosis.
2. Safe checks to do now
Give 3-5 low-risk observation or cultural-practice steps.
3. Helpful additional information
Ask for the most useful details or photos to narrow the possibilities.
4. When to contact an expert
Explain when to contact a local agricultural extension officer, KVK, or agronomist.
5. Follow-up for the next 24-48 hours
Give a short monitoring plan.

Safety rules:
- Do not prescribe pesticides, chemical dosages, mixtures, or treatments.
- Do not invent weather, market prices, disease prevalence, or official recommendations.
- If information is insufficient, say so and ask for more details.
- Do not claim this is a confirmed diagnosis or guarantee crop outcomes.
- Finish every section and the response completely. Keep the answer concise (about 250-400 words).
- Include a reminder to follow local agricultural guidance.
"""

        last_error = None
        # Retry transient service overload / rate-limit errors. Do not retry auth/model errors.
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.25,
                        max_output_tokens=1800,
                    ),
                )
                candidates = response.candidates or []
                app.logger.info(
                    "Gemini finish reasons: %s",
                    [str(candidate.finish_reason) for candidate in candidates],
                )
                text = (response.text or "").strip()
                app.logger.info("Gemini response character count: %s", len(text))
                if not text:
                    raise RuntimeError("Gemini returned an empty response")
                return text, GEMINI_MODEL
            except Exception as exc:
                last_error = exc
                status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
                message = str(exc).lower()
                transient = status in (429, 500, 502, 503, 504) or any(
                    marker in message for marker in (
                        "429", "500", "502", "503", "504", "resource_exhausted",
                        "unavailable", "too many requests", "high demand"
                    )
                )
                if not transient or attempt == 2:
                    raise
                delay = 2 ** (attempt + 1)
                app.logger.warning(
                    "Temporary Gemini error on attempt %s/3; retrying in %s seconds: %s",
                    attempt + 1, delay, exc,
                )
                time.sleep(delay)

        raise last_error or RuntimeError("Gemini request failed")
    except Exception:
        app.logger.exception("Gemini generation failed after retries; using safe fallback")
        return fallback_advisory(crop, location, stage, symptoms, language), "demo_fallback_after_error"


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "storage": "firestore" if USE_FIRESTORE else "sqlite",
        "gemini_enabled": bool(GEMINI_API_KEY)
    })


@app.post("/api/advisory")
def create_advisory():
    data = request.get_json(silent=True) or {}
    fields = ["crop", "location", "growth_stage", "symptoms", "language"]
    values = {field: str(data.get(field, "")).strip() for field in fields}

    missing = [field for field, value in values.items() if not value]
    if missing:
        return jsonify({"error": "Missing required fields", "fields": missing}), 400

    if len(values["symptoms"]) > 1500:
        return jsonify({"error": "Symptoms must be 1500 characters or fewer"}), 400
    if values["language"] not in {"English", "Hindi", "Marathi"}:
        return jsonify({"error": "Language must be English, Hindi, or Marathi"}), 400

    advisory, mode = generate_advisory(
        values["crop"], values["location"], values["growth_stage"],
        values["symptoms"], values["language"]
    )
    record = {
        "id": str(uuid.uuid4()),
        **values,
        "advisory": advisory,
        "generation_mode": mode,
        "created_at": utc_now(),
    }
    save_advisory(record)
    return jsonify(record), 201


@app.get("/api/advisories")
def advisories():
    try:
        limit = int(request.args.get("limit", "20"))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400
    return jsonify({"items": list_advisories(limit)})


@app.get("/api/advisories/<advisory_id>")
def advisory_detail(advisory_id):
    record = get_advisory(advisory_id)
    if not record:
        return jsonify({"error": "Advisory not found"}), 404
    return jsonify(record)


@app.post("/api/feedback")
def feedback():
    data = request.get_json(silent=True) or {}
    advisory_id = str(data.get("advisory_id", "")).strip()
    comment = str(data.get("comment", "")).strip()[:500]
    try:
        rating = int(data.get("rating", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "rating must be an integer from 1 to 5"}), 400

    if not advisory_id or rating not in range(1, 6):
        return jsonify({"error": "advisory_id and rating (1-5) are required"}), 400
    if not get_advisory(advisory_id):
        return jsonify({"error": "Advisory not found"}), 404

    record = {
        "id": str(uuid.uuid4()),
        "advisory_id": advisory_id,
        "rating": rating,
        "comment": comment,
        "created_at": utc_now(),
    }
    save_feedback(record)
    return jsonify({"message": "Feedback saved", "id": record["id"]}), 201


init_sqlite() if not USE_FIRESTORE else None

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "8080")), debug=True)
