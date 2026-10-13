# KrishiMitra 🌱

**A cautious, multilingual crop-observation and follow-up assistant.**

KrishiMitra helps farmers record what they observe, receive an
easy-to-understand next-step plan, and revisit earlier plans. It is an
educational hackathon MVP, not a verified crop-disease diagnosis
service.

## Features

-   Crop, location, growth-stage, symptom, and language input
-   Gemini-generated guidance when `GEMINI_API_KEY` is configured
-   Safe deterministic fallback so the demo works without an API key
-   English, Hindi, and Marathi output options
-   Saved advisory history and user feedback
-   SQLite for local development; Firestore for cloud deployment
-   Flask REST API and responsive browser UI

## Architecture

Browser → Flask app on Cloud Run → Gemini API (server-side key) →
Firestore. Locally, the app uses SQLite unless `USE_FIRESTORE=true`.

## Run locally on Windows

1.  Install Python 3.11+ and Git.

2.  Open PowerShell in this folder.

3.  Create and activate a virtual environment:

    ``` powershell
    py -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

    If PowerShell blocks activation for this terminal, use:

    ``` powershell
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\.venv\Scripts\Activate.ps1
    ```

4.  Install packages and create local configuration:

    ``` powershell
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Copy-Item .env.example .env
    ```

5.  Optional: add your Gemini API key to `.env` as `GEMINI_API_KEY=...`.
    Keep the key private. If the key is blank, the app uses a clearly
    labelled demo fallback.

6.  Start the app:

    ``` powershell
    python app.py
    ```

7.  Open http://127.0.0.1:8080

## API endpoints

  Method   Endpoint                     Purpose
  -------- ---------------------------- -----------------------------------------
  GET      `/api/health`                Health and configuration status
  POST     `/api/advisory`              Generate and save a crop plan
  GET      `/api/advisories?limit=10`   List recent plans
  GET      `/api/advisories/<id>`       Retrieve one plan
  POST     `/api/feedback`              Save a 1--5 rating and optional comment

Example request:

``` json
{
  "crop": "Cotton",
  "location": "Demo district",
  "growth_stage": "Vegetative growth",
  "symptoms": "Some leaves have yellow patches. It started three days ago.",
  "language": "English"
}
```

## Run tests

``` powershell
python -m unittest discover -s tests -v
```

## Deploy

See `IMPLEMENTATION_GUIDE.md` in the companion guide for Google Cloud
setup, Firestore, Secret Manager, Cloud Run deployment, troubleshooting,
the 12-hour plan, demo script, and pitch deck.

## Safety and data notes

-   The assistant does not verify disease identity and must not be used
    as the sole basis for pesticide decisions.
-   The MVP does not connect to live weather, commodity prices, or
    official crop datasets.
-   Do not enter personal contact details or confidential farm
    information.
-   The demo history is not user-isolated. Do not use this build with
    real users until authentication, authorization, retention, and
    privacy controls are implemented.
-   Gemini requests may be processed by Google's API under the terms for
    your account/project. Review the relevant terms before entering
    sensitive data.

## Suggested team split

1.  Backend and API: Flask, validation, storage, tests.
2.  UI and experience: responsive form, result panel, history, feedback.
3.  AI and agriculture validation: prompt quality, multilingual review,
    safety checks.
4.  Cloud and pitch: deployment, demo data, screenshots, slides, backup
    recording.

## License

Add the license required by your team or event before public release.
