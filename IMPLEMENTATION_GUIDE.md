# KrishiMitra --- Complete 12-hour Hackathon Implementation Guide

**Audience:** beginner team of 3--4\
**Primary stack:** Python + Flask + Gemini API + Cloud Firestore +
Google Cloud Run\
**MVP rule:** ship one complete flow before adding features.

## 1. Project brief

### One-line pitch

KrishiMitra turns a farmer's crop observations into a clear,
multilingual next-step plan, while making uncertainty visible and
directing high-risk cases to local agricultural experts.

### Problem statement

Smallholder farmers may notice yellowing, spots, wilting, insects, or
unusual crop growth but may not know what information to collect, which
observations matter, or when to seek qualified help. Advice that is too
technical, not available in a familiar language, or presented as a
confident diagnosis can lead to poor decisions. KrishiMitra provides an
accessible first step: structure the observation, offer cautious general
guidance, suggest what to check next, and recommend local expert help
when needed.

**MVP boundary:** this is not a crop-disease diagnostic device. It does
not provide pesticide dosage or chemical-mixing instructions, and it
does not claim live weather, mandi prices, or verified local disease
data. Any such integration is future work unless a trusted source is
connected and cited.

### Target users

-   Primary: farmer or family member describing an observed crop issue.
-   Secondary: agricultural student, extension worker, or hackathon
    evaluator reviewing the saved plan.
-   Not in MVP: agronomist dashboard, authenticated multi-farmer
    accounts, photo diagnosis, live weather, live prices, offline sync.

### Success criteria for the demo

1.  A visitor can submit a crop concern in under 60 seconds.
2.  The server returns a plan in English, Hindi, or Marathi.
3.  The plan is saved and appears in recent history.
4.  A visitor can reopen a saved plan and submit a rating.
5.  The app works without a Gemini key using a clearly labelled
    fallback.
6.  No API key is exposed in browser code or GitHub.

## 2. User stories and acceptance checks

  -----------------------------------------------------------------------
  ID                      User story              Acceptance check
  ----------------------- ----------------------- -----------------------
  US1                     As a farmer, I can      Required fields
                          select crop, location,  validate; language is
                          growth stage, and       restricted to the
                          language.               supported options.

  US2                     As a farmer, I can      Server rejects empty
                          describe symptoms in my descriptions and
                          own words.              descriptions over 1,500
                                                  characters.

  US3                     As a farmer, I receive  Response contains
                          understandable next     observations, cautious
                          steps.                  possibilities,
                                                  follow-up, and
                                                  expert-referral
                                                  guidance.

  US4                     As a user, I can reopen Recent-history item
                          a previous plan.        loads the saved record
                                                  by ID.

  US5                     As a user, I can rate   Rating from 1 to 5 and
                          the plan.               optional feedback are
                                                  saved.

  US6                     As a judge, I can test  Missing/failed Gemini
                          the app even if AI      configuration uses the
                          configuration fails.    safe demo fallback.

  US7                     As a team, we can run   Setup and deployment
                          the app locally and     commands are documented
                          deploy it.              and health endpoint
                                                  returns `status: ok`.
  -----------------------------------------------------------------------

## 3. Recommended architecture

``` text
Mobile / desktop browser
       |
       | HTTPS, same-origin REST calls
       v
Flask web app (HTML/CSS/JavaScript + API)
       |                         |
       | server-side prompt      | save/read
       v                         v
Gemini API                 Cloud Firestore
       |
       v
Cautious, language-specific advisory

Local mode: Flask + SQLite + optional Gemini API key
Cloud mode: Cloud Run + Firestore + Secret Manager secret for Gemini key
```

### Why this stack?

-   **Python/Flask:** one beginner-friendly backend serves both the web
    page and API.
-   **Plain HTML/CSS/JavaScript:** no Node.js build chain or separate
    frontend deployment.
-   **Gemini API:** adds natural-language guidance; the key stays on the
    server.
-   **Firestore:** managed, document-oriented storage for advisory
    history and feedback.
-   **Cloud Run:** deploys the same container that runs locally.
-   **SQLite:** lets the team build and test before configuring cloud
    credentials.

### What the Google Cloud components do

-   Cloud Run hosts the application.
-   Firestore stores advisory and feedback documents.
-   Secret Manager stores the Gemini API key.
-   Cloud Build builds the container from source during
    `gcloud run deploy --source .` (the Google Cloud CLI may prompt to
    enable required APIs).

## 4. Data model / database schema

### `advisories` collection (Firestore) or table (SQLite)

  ---------------------------------------------------------------------------
  Field               Type              Required          Meaning
  ------------------- ----------------- ----------------- -------------------
  `id`                string / document yes               UUID generated by
                      ID                                  the app

  `crop`              string            yes               Selected crop

  `location`          string            yes               Farmer-entered
                                                          village/district;
                                                          not geocoded

  `growth_stage`      string            yes               Selected stage

  `symptoms`          string            yes               User description,
                                                          max 1,500
                                                          characters

  `language`          string            yes               English, Hindi, or
                                                          Marathi

  `advisory`          string            yes               Generated or
                                                          fallback guidance

  `generation_mode`   string            yes               Model name or
                                                          fallback label

  `created_at`        ISO-8601 string   yes               UTC creation
                                                          timestamp
  ---------------------------------------------------------------------------

### `feedback` collection (Firestore) or table (SQLite)

  Field           Type                   Required   Meaning
  --------------- ---------------------- ---------- ------------------------------
  `id`            string / document ID   yes        UUID
  `advisory_id`   string                 yes        Related advisory
  `rating`        integer                yes        1 through 5
  `comment`       string                 no         Optional, max 500 characters
  `created_at`    ISO-8601 string        yes        UTC timestamp

**Important limitation:** this hackathon starter does not have
authentication or per-user access controls. Its history is shared. Do
not expose it to real users or store sensitive farm records until
authentication, authorization, data retention, and privacy are
implemented.

## 5. REST API contract

All requests/responses use JSON unless the route serves the web page.

### `GET /api/health`

Example response:

``` json
{
  "status": "ok",
  "storage": "sqlite",
  "gemini_enabled": false
}
```

### `POST /api/advisory`

Request:

``` json
{
  "crop": "Cotton",
  "location": "Demo district",
  "growth_stage": "Vegetative growth",
  "symptoms": "Some leaves have yellow patches. It started three days ago.",
  "language": "English"
}
```

Success: HTTP `201`, returning the saved advisory record including `id`,
`advisory`, `generation_mode`, and `created_at`.

Errors: HTTP `400` for missing fields, invalid language, or excessive
symptom text. The server falls back if Gemini errors; the UI shows the
selected generation mode.

### `GET /api/advisories?limit=10`

Returns `{"items": [...]}` sorted newest first. Limit is clamped to
1--50.

### `GET /api/advisories/<id>`

Returns one advisory record or HTTP `404`.

### `POST /api/feedback`

Request:

``` json
{
  "advisory_id": "paste-an-existing-id",
  "rating": 5,
  "comment": "The steps were clear."
}
```

Success: HTTP `201`. Invalid rating, missing ID, or unknown advisory
returns a 4xx error.

## 6. Folder structure

``` text
krishimitra/
├── app.py                 # Flask UI routes, API, Gemini call, persistence
├── requirements.txt       # Python dependencies
├── Dockerfile             # Cloud Run container
├── .env.example           # Safe template; no secrets
├── .gitignore
├── .dockerignore
├── README.md              # Project overview and quick start
├── IMPLEMENTATION_GUIDE.md# This detailed guide
├── templates/
│   └── index.html         # Responsive user interface
├── static/
│   ├── style.css          # Styling
│   └── app.js             # Browser API calls, history, feedback
└── tests/
    └── test_app.py        # API smoke tests
```

The downloadable project ZIP contains the starter source files; save
this guide beside `README.md` as `IMPLEMENTATION_GUIDE.md`.

## 7. Windows setup --- local first

### Prerequisites

Install Python 3.11 or newer and Git. During Python installation, enable
**Add Python to PATH**. Use PowerShell.

### Commands

``` powershell
# 1. Go to the extracted project folder
cd krishimitra

# 2. Create and activate a virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# If PowerShell blocks activation, this applies only to this terminal:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 4. Create local environment file
Copy-Item .env.example .env

# 5. Start the app
python app.py
```

Open `http://127.0.0.1:8080`.

The app uses SQLite by default and runs with a fallback advisory even if
no Gemini API key is configured. To enable Gemini locally, create a key
in Google AI Studio and put it in `.env`:

``` text
GEMINI_API_KEY=your_private_key_here
GEMINI_MODEL=gemini-2.5-flash
USE_FIRESTORE=false
```

Restart the server after editing `.env`. Do not commit `.env` or put the
key in JavaScript, HTML, screenshots, or slides.

### First smoke test

Open `http://127.0.0.1:8080/api/health`. Expected: JSON with
`"status":"ok"`. Submit a test for Cotton or Tomato with a harmless
observation, then check history and feedback.

## 8. Starter code notes

The project source is included in the ZIP. Key implementation decisions:

-   The Flask app serves both `index.html` and REST endpoints, so
    frontend and backend share one origin.
-   The browser renders advisory text via `textContent`, not
    `innerHTML`, to reduce injection risk.
-   The Gemini key is read only by Python from an environment variable.
-   A deterministic fallback keeps the demo usable if the key is
    missing, quota is exhausted, or a request fails.
-   The prompt explicitly prohibits pesticide dosage, chemical mixtures,
    invented live data, and claims of verified diagnosis.
-   The app saves records in SQLite locally and uses Firestore when
    `USE_FIRESTORE=true`.
-   `generation_mode` tells the team whether the response came from
    Gemini or fallback.

For a first build, avoid adding photo uploads, maps, weather, price
feeds, login, chat history, or dashboards before the end-to-end flow is
stable.

## 9. Google Cloud / Firestore deployment

Use the project owner's Google Cloud account. Cloud resources may
require billing to be enabled. Review the current pricing and event
rules before creating resources. Never use a personal key or
service-account JSON in the repository.

### A. Create/select a project and enable CLI access

1.  Create/select a project in Google Cloud Console.
2.  Install Google Cloud CLI for Windows.
3.  Open a new PowerShell terminal and run:

``` powershell
gcloud init
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com firestore.googleapis.com secretmanager.googleapis.com
```

Replace `YOUR_PROJECT_ID` with the actual project ID, not the display
name.

### B. Create Firestore

In Google Cloud Console, open **Firestore** → create database → choose
**Native mode** → choose a region close to your intended users and
consistent with the Cloud Run region. For a hackathon, choose the region
carefully; moving a Firestore database later is not straightforward.

### C. Give Cloud Run permission to write to Firestore

Use the default Compute service account only if the project allows it; a
dedicated runtime service account is preferable. A dedicated example:

``` powershell
gcloud iam service-accounts create krishimitra-runner --display-name="KrishiMitra Cloud Run"
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID --member="serviceAccount:krishimitra-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/datastore.user"
```

Use least privilege and your team's approved project. Do not download a
service-account key. Cloud Run uses its attached service identity.

### D. Create a Gemini API key secret

1.  Create a Gemini API key in Google AI Studio.
2.  Store it in Secret Manager, not in Git or the frontend.

PowerShell (prompts for the key so it is not embedded in the command
text):

``` powershell
$secretValue = Read-Host "Paste Gemini API key"
$secretValue | gcloud secrets create krishimitra-gemini-key --data-file=-
```

If the secret already exists, add a version instead:

``` powershell
$secretValue | gcloud secrets versions add krishimitra-gemini-key --data-file=-
```

Grant the runtime service account access to the secret:

``` powershell
gcloud secrets add-iam-policy-binding krishimitra-gemini-key --member="serviceAccount:krishimitra-runner@YOUR_PROJECT_ID.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

Clear the shell variable after use:

``` powershell
Remove-Variable secretValue
```

### E. Deploy the app

From the project root (where `Dockerfile` and `app.py` exist):

``` powershell
gcloud run deploy krishimitra `
  --source . `
  --region asia-south1 `
  --allow-unauthenticated `
  --service-account krishimitra-runner `
  --set-env-vars USE_FIRESTORE=true,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GEMINI_MODEL=gemini-2.5-flash `
  --set-secrets GEMINI_API_KEY=krishimitra-gemini-key:latest `
  --memory 512Mi `
  --timeout 120
```

If your team chooses another region, use it consistently for the service
and database. `asia-south1` is an example region, not a requirement. The
first source deployment may take several minutes and may prompt you to
enable APIs. Once deployed, the CLI prints a service URL.

**Before demoing:** open the Cloud Run URL; test create advisory,
history, feedback, and `/api/health`. Confirm `storage` says `firestore`
and `gemini_enabled` says `true`. If the Gemini call fails, the app
still uses fallback; inspect Cloud Run logs to find the reason.

### F. Cloud Run costs and security

-   Check the project's billing and quotas before the event; no cloud
    service is guaranteed to be free for every usage pattern.
-   Keep Gemini API key in Secret Manager.
-   Do not commit `.env`, database files, or service-account keys.
-   Public access is enabled in the example for judging convenience.
    This is a shared demo without login; do not store real or sensitive
    farmer records.
-   Before public production use, add Firebase Authentication or another
    identity system, server-side authorization, abuse/rate controls,
    input limits, logging without sensitive text, and a
    privacy/retention policy.
-   Firestore records created by this MVP are not user-isolated.

## 10. Optional Firebase Hosting note

For the simplest MVP, keep the UI and API together on Cloud Run.
Firebase Hosting is not necessary. Adding Hosting introduces another
deployment target and routing configuration, which is a poor trade-off
in a 12-hour beginner hackathon.

If judges explicitly require Firebase Hosting, the safer next step is to
host a separate static frontend on Firebase Hosting and configure a
rewrite/proxy to the Cloud Run API. Do this only after the Cloud Run URL
works end-to-end; do not split the app during the final hours.

## 11. Testing checklist

### Automated tests

With the virtual environment active:

``` powershell
python -m unittest discover -s tests -v
```

Expected: health endpoint, validation, create/read, feedback, and
invalid-language tests pass. If tests fail because an old local database
contains unexpected state, delete only the local `krishimitra.db` while
the app is stopped and rerun.

### Manual end-to-end checklist

-   [ ] Home page loads on desktop and mobile width.
-   [ ] `/api/health` returns HTTP 200.
-   [ ] Empty form is blocked in browser.
-   [ ] Missing API fields return HTTP 400.
-   [ ] Valid report returns HTTP 201 and shows a result.
-   [ ] A second report appears at the top of history.
-   [ ] Clicking a history item reopens the exact saved advisory.
-   [ ] Feedback rating 1--5 is accepted; invalid rating is rejected.
-   [ ] English, Hindi, and Marathi output options are selectable.
-   [ ] Missing/invalid Gemini key still gives the fallback.
-   [ ] No key is visible in browser dev tools, GitHub, or frontend
    files.
-   [ ] Cloud deployment health response reports Firestore mode.
-   [ ] At least one team member tests the deployed URL on a phone
    hotspot or a second device.

### Sample demo inputs

Use clearly labelled test data, not a claim about a real farm: - Crop:
Cotton - Location: Demo district - Stage: Vegetative growth - Symptoms:
"A few leaves have yellow patches. I noticed it three days ago. I have
not checked the underside of the leaves yet." - Language: Marathi or
English

For the pitch, state that this is a simulated example and not a verified
diagnosis.

## 12. 12-hour execution plan

  -----------------------------------------------------------------------
  Time                    Deliverable             Owner suggestion
  ----------------------- ----------------------- -----------------------
  H0--H0:45               Lock MVP, user flow,    All
                          and sample scenario     

  H0:45--H2               Flask app boots; page + Backend + UI
                          health endpoint work    

  H2--H4                  Form submits; fallback  Backend
                          advisory returns;       
                          SQLite saves            

  H3--H5                  Polished responsive UI, UI
                          result panel, history   

  H4--H6                  Gemini integration,     AI/agriculture
                          language choice, prompt 
                          safety                  

  H6--H7                  Feedback API,           Backend + QA
                          validation, automated   
                          tests                   

  H7--H8:30               Firestore + Cloud Run   Cloud owner
                          deployment              

  H8:30--H9:30            Fix only critical       All
                          issues; full deployed   
                          golden path             

  H9:30--H10:30           Slides, demo rehearsal, Pitch owner
                          screenshots             

  H10:30--H11             Freeze features;        All
                          prepare backup demo     
                          recording               

  H11--H12                Submit early, rehearse, All
                          keep deployed URL       
                          stable                  
  -----------------------------------------------------------------------

**Golden path to protect:** open app → enter crop report → receive plan
→ save → reopen from history → submit feedback. If there is a deployment
problem, use local fallback plus a recorded cloud demo; do not add new
features.

## 13. Team split for 3--4 people

-   **Person 1 --- backend:** Flask routes, validation,
    SQLite/Firestore, API tests.
-   **Person 2 --- frontend:** HTML/CSS, form, result card, history,
    mobile responsiveness.
-   **Person 3 --- AI and domain:** Gemini prompt, language quality
    review, safe demo scenarios, no unsupported agronomy claims.
-   **Person 4 (if available) --- cloud and pitch:** project setup,
    Cloud Run, Secret Manager, slides, rehearsal, screenshots.

If only three people, the backend owner can pair with cloud deployment
after the API is stable. Agree on API field names at the beginning; do
not wait for frontend/backend integration until H5.

## 14. Common errors and fixes

  -----------------------------------------------------------------------------------------------------------------------------
  Error                             Likely reason           Fix
  --------------------------------- ----------------------- -------------------------------------------------------------------
  `py` is not recognized            Python launcher not     Reinstall Python with PATH option; open a new terminal; try
                                    installed or PATH not   `python --version`.
                                    refreshed               

  `Activate.ps1 cannot be loaded`   PowerShell execution    Use `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`,
                                    policy                  then activate again.

  `ModuleNotFoundError: flask`      Wrong Python            Activate `.venv`; run `python -m pip install -r requirements.txt`.
                                    environment or          
                                    dependencies not        
                                    installed               

  Port 8080 is already in use       Another server is       Stop the old process or set `$env:PORT="8081"` and open port 8081.
                                    running                 

  `GEMINI_API_KEY` missing          `.env` absent or        Copy `.env.example` to `.env`, set exact variable name, restart
                                    variable name wrong     app.

  Gemini error / quota / model      Key, project, quota, or Check key and API access; set `GEMINI_MODEL` to a model available
  unavailable                       model name issue        to your project. Fallback should keep the demo working.

  Firestore permission denied       Cloud Run service       Grant `roles/datastore.user` to the actual runtime service account;
                                    account lacks Firestore redeploy if needed.
                                    role                    

  `DefaultCredentialsError` locally Firestore local mode    Set `USE_FIRESTORE=false` for local development, or configure ADC
                                    enabled without         with `gcloud auth application-default login`.
                                    credentials             

  Cloud Run deploy fails to build   Wrong directory or      Run from the folder containing `Dockerfile`; check build logs;
                                    dependency/build issue  confirm `requirements.txt` exists.

  Cloud Run returns 500             Runtime exception or    Inspect
                                    missing                 `gcloud run services logs read krishimitra --region asia-south1`;
                                    secret/permissions      verify env vars and IAM.

  Health says SQLite after deploy   `USE_FIRESTORE` was not Re-run deployment with `USE_FIRESTORE=true` and correct project ID.
                                    set correctly           

  Recent history disappears after   SQLite was used on      Use Firestore mode in Cloud Run; SQLite is for local development
  deploy                            ephemeral container     only.
                                    storage                 

  History loads but result fails    API response shape or   Open browser developer tools → Console and Network; verify POST
                                    JS error                `/api/advisory` returns 201 JSON.

  Hindi/Marathi phrasing is awkward Model variation or      Keep the demo script fixed; have a fluent speaker review the exact
                                    transliteration         output; do not claim expert-reviewed translations unless true.

  App works locally but not         Missing environment     Check health JSON, Cloud Run logs, Firestore region, and service
  deployed                          variable, IAM, or       identity.
                                    region mismatch         
  -----------------------------------------------------------------------------------------------------------------------------

## 15. GitHub README

The project ZIP includes `README.md` with: - project summary and feature
list - architecture - Windows setup - API endpoints - test command -
safety/data limitations - suggested team split

Before pushing:

``` powershell
git init
git add .
git status
```

Make sure `.env` and `krishimitra.db` are not staged. Then:

``` powershell
git commit -m "Build KrishiMitra MVP"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/krishimitra.git
git push -u origin main
```

Replace the remote with your repository URL. If a secret was committed,
revoke/rotate it; deleting the file in a later commit is not enough.

## 16. Demo script (2 minutes)

**0:00--0:15 --- Problem**\
"Farmers often see symptoms before they know what information matters.
KrishiMitra helps structure that observation and choose a sensible next
step."

**0:15--0:35 --- Input**\
Open the deployed app. Select Cotton, Demo district, Vegetative growth,
and Marathi or English. Enter: "A few leaves have yellow patches. I
noticed it three days ago. I have not checked the underside of the
leaves yet."

**0:35--1:05 --- Advisory**\
Submit. Point out the observation checklist, uncertainty, follow-up
plan, and referral to an agricultural expert. Explain that the app does
not claim a confirmed disease or prescribe chemicals.

**1:05--1:25 --- Persistence**\
Scroll to Recent crop plans, click the record, and show that the result
can be reopened. Submit a rating.

**1:25--1:45 --- Google Cloud**\
Show the Cloud Run URL and `/api/health` response. Explain that Cloud
Run hosts the app, Firestore saves records, and the Gemini key is stored
server-side in Secret Manager.

**1:45--2:00 --- Impact and next step**\
"Our MVP is a safe first step, not a replacement for extension services.
Next we would validate advice with agricultural experts, add
authenticated farmer profiles, and integrate verified local weather and
market data."

### Backup plan

-   Keep the app already open in a browser tab.
-   Save a short screen recording of a successful deployed run.
-   Keep one known-good sample scenario.
-   If Gemini is unavailable, show the labelled fallback rather than
    waiting on the network.
-   Do not change the deployed app after H10 unless a critical bug
    blocks the golden path.

## 17. Eight-slide pitch deck content

The event guidance calls for an eight-slide deck and emphasizes
innovation, implementation, impact, Google technology, and clear
communication. Use the exact rubric in the event brief as the source of
truth; the weighting noted there is approximately Innovation 25%,
Implementation 30%, Impact 25%, and Google technology usage 20%.

### Slide 1 --- Title

**KrishiMitra: A clearer next step for every crop concern**\
Multilingual crop observation and follow-up assistant\
Team name · members · hackathon name

### Slide 2 --- Problem

-   A farmer notices leaf spots, yellowing, wilting, or insects.
-   The farmer may not know what observations to record or when to seek
    expert help.
-   Overconfident, generic advice can lead to poor decisions.
-   The gap we target: understandable first-step guidance, not a
    replacement for agronomists.

Use a simple farmer → observation → uncertainty illustration. Avoid
unsupported market-size statistics.

### Slide 3 --- Why now

-   Generative AI can translate a plain-language description into
    structured steps.
-   A mobile web app avoids installing a separate app.
-   A cloud-backed prototype can save and revisit observations.
-   The challenge is trust: uncertainty and safe boundaries must be
    designed in.

### Slide 4 --- Solution

-   Enter crop, location, stage, and symptoms.
-   Receive possible explanations with explicit uncertainty.
-   Get safe observation steps, follow-up, and expert referral.
-   Use English, Hindi, or Marathi.
-   Reopen history and give feedback.

### Slide 5 --- How it works

Diagram: Browser → Flask/Cloud Run → Gemini → advisory response;
Flask/Cloud Run → Firestore → saved history.\
Mention Secret Manager for the Gemini API key. State that local
development uses SQLite.

### Slide 6 --- Live demo

Show the real deployed golden path: 1. Enter a crop concern. 2. Generate
advisory. 3. Reopen it from history. 4. Submit feedback. Keep this slide
mostly visual; use a real screenshot, not a mockup represented as a
completed feature.

### Slide 7 --- Impact and trust

-   Reduces friction in recording a crop concern.
-   Gives a structured checklist in a familiar language.
-   Makes uncertainty and expert referral visible.
-   Future evaluation: expert-reviewed sample set, translation review,
    usefulness ratings, and safe-referral rate. Do not claim yield gains
    or diagnostic accuracy without evidence.

### Slide 8 --- What's next

1.  Validate prompt and advice quality with agricultural experts / KVK.
2.  Add authenticated farmer accounts and private records.
3.  Add verified weather and market feeds with source timestamps.
4.  Add opt-in photo support and carefully evaluated image analysis.
5.  Pilot with a small, consented group and measure usability. End with:
    "KrishiMitra helps farmers ask better questions and take safer next
    steps."

## 18. Scope cuts if time runs short

Cut in this order: 1. Polish animations and decorative effects. 2. Extra
crop options. 3. Extra languages beyond one well-reviewed demo language.
4. Optional cloud history if Firestore setup blocks the demo; keep local
SQLite and be honest about it. 5. Feedback comments (keep rating only).

Never cut: - The full golden path. - A working deployed URL or backup
recording. - Server-side secret handling. - Input validation. - Clear
distinction between general guidance and verified diagnosis. - The final
demo rehearsal.

## 19. Reference links

-   Gemini API overview and generation:
    https://ai.google.dev/api/generate-content
-   Firestore server quickstart:
    https://firebase.google.com/docs/firestore/quickstart-server
-   Firestore Python client reference:
    https://docs.cloud.google.com/python/docs/reference/firestore/latest
-   Cloud Run deployment docs:
    https://cloud.google.com/run/docs/deploying-source-code
-   Secret Manager docs: https://cloud.google.com/secret-manager/docs
-   Google Cloud CLI installation:
    https://cloud.google.com/sdk/docs/install

Cloud console labels and available Gemini models can change. If a model
is unavailable, update `GEMINI_MODEL` to a model enabled for your API
key/project and retest before the demo.
