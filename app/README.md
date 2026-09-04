# SAFETrace AI — Investigator Dashboard (Frontend)

## 1. Purpose

This is the investigator-facing dashboard for **SAFETrace AI**, an
investigation-support system for missing-person cases. It lets an
investigator create cases, submit CCTV footage for AI analysis, review
AI-generated potential evidence, inspect prioritized leads, and verify or
reject each lead — all through a clean, professional web UI.

The frontend never runs AI models directly. All CCTV analysis, tracking,
and lead scoring happens in the backend (Member 2) and AI module
(Member 1); this app only calls the backend API and renders the results.

## 2. Technologies

- Python
- Streamlit
- Requests
- Pandas
- Pillow
- Plotly (for analytics charts)

## 3. Folder Structure

```
app/
├── streamlit_app.py      # Entry point, sidebar navigation, page routing
├── api_client.py         # All backend API calls (centralized)
├── components.py         # Reusable UI components (cards, banners, etc.)
├── styles.py              # Color palette + CSS
├── pages/
│   ├── dashboard.py       # Main dashboard / overview
│   ├── cases.py           # Case list + case details
│   ├── create_case.py     # Create new case form
│   ├── analysis.py        # CCTV upload + analysis
│   ├── evidence.py        # Evidence cards, filters, verify/reject
│   ├── leads.py           # Priority leads grouped by HIGH/MEDIUM/LOW
│   └── analytics_page.py  # Aggregate statistics + charts
└── README.md
```

## 4. Installation

```bash
cd app
pip install -r ../requirements.txt
# or, if requirements.txt is local to this folder:
pip install streamlit requests pandas pillow plotly
```

## 5. Running the Application

```bash
streamlit run app/streamlit_app.py
```

The dashboard will open at `http://localhost:8501` by default.

## 6. Backend URL Configuration

The backend URL is **not hard-coded**. Set it via environment variable:

```bash
export SAFETRACE_BACKEND_URL="http://localhost:8000"
streamlit run app/streamlit_app.py
```

If unset, it defaults to `http://localhost:8000`. This lets Member 4
change the URL at deployment time without touching frontend code.

## 7. Available Dashboard Pages

| Page | Purpose |
|---|---|
| 🏠 Dashboard | Overview stats, recent cases, high-priority leads |
| 📁 Cases | List all cases, view case details |
| ➕ Create Case | Register a new missing-person case |
| 🎥 CCTV Analysis | Upload CCTV video, trigger AI analysis, view results |
| 🔎 Evidence | Browse evidence cards/table, filter, verify/reject |
| 🚨 Priority Leads | Leads grouped by HIGH/MEDIUM/LOW with score & reason |
| 📊 Analytics | Aggregate stats and priority/status charts |

## 8. API Integration

All API calls live in `api_client.py`. Endpoints consumed:

```
POST   /cases
GET    /cases
GET    /cases/{case_id}
POST   /videos
POST   /ai-results
GET    /cases/{case_id}/evidence
GET    /cases/{case_id}/leads
PATCH  /evidence/{evidence_id}/status
```

No other file makes raw `requests` calls — every page imports
`api_client` functions only.

## 9. Demo Workflow

1. Open the dashboard → **🏠 Dashboard**
2. **➕ Create Case** → e.g. `Demo Person`, last seen at `Demo Railway Station`
3. **🎥 CCTV Analysis** → select case, enter `CAM-03` / location, upload
   `station_cam03.mp4`, click **ANALYZE VIDEO**
4. View the **Annotated CCTV Video** and analysis summary
5. **🔎 Evidence** → view evidence card `EV-00027`
6. **🚨 Priority Leads** → see `Lead Score: 88.5`, `Priority: HIGH`
7. Note the **"Requires Investigator Verification"** disclaimer
8. Click **VERIFY** → status updates to **Verified**

## 10. Troubleshooting

**"⚠️ Backend unavailable"**
Confirm the FastAPI backend is running and `SAFETRACE_BACKEND_URL` points
to it. Check the sidebar connectivity indicator (🟢/🔴).

**Case creation fails**
Check that `name` and `last_seen_location` are filled in. Look at the
error caption shown under the message for backend details.

**Video/image not displaying**
The backend must return an accessible URL or path for
`annotated_video_url` / `crop_image_url` / `reference_image_url`. Local
Windows paths will not resolve after deployment — coordinate with
Member 4 on file storage.

**Analysis hangs**
If the backend performs synchronous analysis, this is expected — the UI
shows a spinner until the response returns. For long-running jobs,
consider an async/polling backend design.

## Important Note on Terminology

This dashboard **never** claims AI results are a confirmed identity. All
detections are shown as **"Potential Lead"** / **"Potential Candidate"**
requiring **investigator verification**, even after a lead is marked
"Verified" (labeled "Investigator Verified Evidence", not "AI Confirmed
Identity").
