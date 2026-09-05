# SAFETrace AI

## AI-Assisted Missing Person Investigation and Evidence Prioritization

SAFETrace AI is an AI-assisted investigation platform designed to help investigators analyze authorized CCTV or sample video footage and prioritize potential leads during missing-person investigations.

The system combines computer vision, person detection, multi-object tracking, candidate analysis, evidence generation, lead scoring, and an investigator-facing dashboard into a single workflow.

---

# 1. Problem Statement

Missing-person investigations may involve reviewing large amounts of CCTV footage manually.

Searching through long video recordings can be time-consuming and may make it difficult for investigators to quickly identify useful evidence.

SAFETrace AI aims to assist investigators by automatically detecting and tracking people in authorized video footage and generating prioritized potential leads for human review.

The system is designed as an investigation-support tool and does not replace human investigators.

---

# 2. Proposed Solution

SAFETrace AI provides an end-to-end workflow that processes authorized CCTV or sample video and generates potential investigative leads.

The overall workflow is:

Reference Evidence
        ↓
Authorized CCTV / Sample Video
        ↓
Frame Extraction & Preprocessing
        ↓
Person Detection
        ↓
Multi-Object Tracking
        ↓
Candidate / Appearance Analysis
        ↓
Timestamp & Camera/Location Correlation
        ↓
AI Results
        ↓
Evidence Generation
        ↓
Lead Scoring
        ↓
Priority Leads
        ↓
Investigator Verification

---

# 3. Key Features

- Case creation and management
- Reference evidence management
- Authorized CCTV / sample video analysis
- Person detection
- Multi-object tracking
- Track ID generation
- Timestamp-based evidence handling
- Candidate / appearance analysis
- Potential evidence generation
- Lead scoring
- Priority-based lead ranking
- Evidence review
- Investigator verification
- Verify / Reject workflow
- Investigator dashboard

---

# 4. System Architecture

```text
                         INVESTIGATOR
                              |
                              v
                    STREAMLIT DASHBOARD
                              |
                              v
                         FASTAPI API
                              |
                +-------------+-------------+
                |                           |
                v                           v
        AI / COMPUTER VISION            DATABASE
                |
                v
       FRAME EXTRACTION
                |
                v
       YOLO PERSON DETECTION
                |
                v
      BYTETrack / BoT-SORT
                |
                v
       CANDIDATE ANALYSIS
                |
                v
           AI RESULTS
                |
                v
       EVIDENCE GENERATION
                |
                v
          LEAD SCORING
                |
                v
         PRIORITY LEADS
                |
                v
     INVESTIGATOR VERIFICATION
                |
          +-----+-----+
          |           |
          v           v
        VERIFY      REJECT
        5. End-to-End Workflow
Create Case
     ↓
Add Reference Evidence
     ↓
Add CCTV / Sample Video
     ↓
Start Analysis
     ↓
Frame Extraction
     ↓
Person Detection
     ↓
Person Tracking
     ↓
Candidate Analysis
     ↓
Generate AI Results
     ↓
Create Potential Evidence
     ↓
Calculate Lead Score
     ↓
Prioritize Leads
     ↓
Investigator Review
     ↓
Verify / Reject
6. AI / Computer Vision Pipeline

SAFETrace AI uses a computer vision pipeline to process video footage.

Video
  ↓
Frame Extraction
  ↓
Person Detection
  ↓
Multi-Object Tracking
  ↓
Track IDs
  ↓
Person Crops
  ↓
Candidate Analysis
  ↓
AI Results
Person Detection

YOLO-based object detection is used to detect people in video frames.

The detector provides information such as:

Bounding boxes
Detection confidence
Frame information
Multi-Object Tracking

ByteTrack / BoT-SORT is used to maintain consistent track IDs across video frames.

Tracking provides information such as:

Track ID
Detection association across frames
Track duration
Frame/timestamp information
Candidate Analysis

Candidate analysis can use available visual and contextual information to identify potentially relevant tracks.

The system treats these results as potential candidates rather than confirmed identities.

7. AI Outputs

The AI pipeline can generate outputs such as:

outputs/
├── annotated_videos/
├── person_crops/
└── tracks/
    ├── tracks.json
    ├── tracks.csv
    └── track_summary.csv

Typical AI information includes:

Track ID
Detection confidence
Timestamp/frame information
Person crop information
Track duration
Video/camera metadata when available

Generated videos and large files are excluded from Git version control.

8. Backend

The backend provides REST APIs for communication between the investigator dashboard, AI pipeline, evidence management, and database.

The backend is implemented using FastAPI.

Main API Endpoints
POST /cases
GET /cases
GET /cases/{case_id}

POST /videos

POST /ai-results

GET /cases/{case_id}/evidence

GET /cases/{case_id}/leads

PATCH /evidence/{evidence_id}/status

The /ai-results endpoint is the primary integration point between AI processing and the backend.

9. Database

The backend stores investigation-related information including:

Cases
Videos
Tracks
Detections
Evidence
Leads

The database layer is implemented using the project's configured database and SQLAlchemy integration.

10. Lead Scoring

SAFETrace AI uses a prototype lead-scoring approach that combines multiple signals.

Lead Score =
0.40 × Detection
+ 0.20 × Duration
+ 0.30 × Visual Similarity
+ 0.10 × Time / Location
Priority Levels
80–100  → HIGH
60–79   → MEDIUM
0–59    → LOW

The scoring system is intended to help investigators prioritize potentially useful evidence.

Visual similarity is only used when the corresponding analysis is actually available.

The system should never generate or assume a similarity value simply to produce a higher score.

11. Investigator Dashboard

The Streamlit dashboard provides an investigator-facing interface.

Main sections include:

Dashboard
Cases
Create Case
CCTV Analysis
Evidence
Leads

The dashboard allows investigators to:

Create a case
Add reference information
Add CCTV/sample video
Start analysis
View AI analysis results
Review potential evidence
View prioritized leads
Open evidence
Verify or reject evidence
12. Evidence Workflow

Potential evidence generated by the AI pipeline can contain information such as:

Case ID
Video ID
Track ID
Timestamp
Camera/location information when available
Detection confidence
Candidate information
Lead score
Priority

Evidence is presented to investigators for review.

13. Human Verification

SAFETrace AI is an investigator-assistance system.

AI-generated results are treated as potential leads and require human review.

Preferred terminology
Potential Lead
Potential Candidate
Potential Evidence
Requires Investigator Verification
Investigator Verified Evidence
Avoid
AI Confirmed Identity
Confirmed Missing Person
100% Identity Match
Person Definitely Found

The system should not present an AI-generated candidate as a confirmed identity.

14. Technology Stack
Component	Technology
Programming Language	Python
Object Detection	YOLO
Object Tracking	ByteTrack / BoT-SORT
Video Processing	OpenCV
AI Runtime	PyTorch
Backend	FastAPI
Frontend	Streamlit
API Communication	Requests / REST
Data Processing	Pandas
Database Layer	SQLAlchemy
Database	PostgreSQL / Configured Database
15. Project Structure
SAFETrace-AI/
│
├── ai/
│   ├── __init__.py
│   ├── detector.py
│   ├── tracker.py
│   ├── video_processor.py
│   ├── candidate_analyzer.py
│   ├── config.py
│   └── README.md
│
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── scoring.py
│   ├── evidence_service.py
│   ├── case_service.py
│   ├── video_service.py
│   └── README.md
│
├── app/
│   ├── streamlit_app.py
│   ├── api_client.py
│   ├── components.py
│   ├── styles.py
│   ├── README.md
│   └── pages/
│       ├── dashboard.py
│       ├── cases.py
│       ├── create_case.py
│       ├── analysis.py
│       ├── evidence.py
│       └── leads.py
│
├── data/
│   └── sample_videos/
│
├── outputs/
│   └── tracks/
│
├── .gitignore
├── requirements.txt
└── README.md
16. Installation
Clone the Repository
git clone https://github.com/YOUR-USERNAME/SAFETrace-AI.git
cd SAFETrace-AI
Create Virtual Environment

Windows:

python -m venv venv

Activate:

venv\Scripts\activate

Linux/macOS:

python3 -m venv venv
source venv/bin/activate
Install Dependencies
pip install -r requirements.txt
17. Running the AI Pipeline

Place an authorized sample video in:

data/sample_videos/

Example:

data/sample_videos/test.mp4

Run:

python -m ai.video_processor --input data/sample_videos/test.mp4

The generated outputs are stored under:

outputs/
18. Running the Backend

From the project root:

uvicorn backend.app:app --reload --port 8000

FastAPI documentation:

http://127.0.0.1:8000/docs
19. Running the Dashboard

From the project root:

streamlit run app/streamlit_app.py

The dashboard will be available through the Streamlit local URL displayed in the terminal.

20. Complete Demo Workflow

The recommended demonstration flow is:

1. Open SAFETrace AI Dashboard
        ↓
2. Create Investigation Case
        ↓
3. Add Reference Evidence
        ↓
4. Add CCTV / Sample Video
        ↓
5. Start Analysis
        ↓
6. AI Detects People
        ↓
7. AI Tracks People
        ↓
8. Candidate Analysis
        ↓
9. AI Results Sent to Backend
        ↓
10. Potential Evidence Generated
        ↓
11. Lead Score Calculated
        ↓
12. Leads Prioritized
        ↓
13. Investigator Reviews Evidence
        ↓
14. Investigator Verifies / Rejects
21. Testing

The complete system should be tested using an end-to-end workflow.

AI Tests
Video can be loaded
Frames can be processed
People can be detected
Track IDs are generated
Detection confidence is recorded
Track information is generated
Backend Tests
Backend starts successfully
API documentation is available
Cases can be created
Cases can be retrieved
Videos can be registered
AI results can be submitted
Evidence can be retrieved
Leads can be retrieved
Evidence status can be updated
Frontend Tests
Dashboard loads
Case creation works
Case list works
CCTV analysis page works
Evidence page works
Leads page works
Verify/Reject workflow works
End-to-End Test
Create Case
     ↓
Upload/Add Video
     ↓
Start Analysis
     ↓
AI Processing
     ↓
Backend
     ↓
Database
     ↓
Evidence
     ↓
Lead Score
     ↓
Priority Lead
     ↓
Investigator Verification
22. Performance Measurement

Performance should be measured using actual test runs.

Recommended measurements include:

Video duration
Processing time
Frames processed
Total detections
Number of unique tracks
Average detection confidence
Processing FPS

Example prototype measurement:

Video Duration: 9.79 seconds
Processing Time: 121.29 seconds
Frames Processed: 290
Total Detections: 765
Unique Tracks: 7
Average Confidence: 0.7228

These measurements are dependent on the test video and hardware environment and should not be presented as universal real-world performance.

23. Privacy and Responsible AI

SAFETrace AI is intended to support authorized investigations.

The prototype:

Uses authorized or sample video footage.
Does not claim access to police or private CCTV databases.
Does not automatically confirm a person's identity.
Produces potential investigative leads.
Requires human investigator verification.
Should use appropriate access controls for sensitive evidence.
Should securely handle uploaded footage and generated evidence.
Should avoid unnecessary retention of sensitive data.
24. Deployment Considerations

The application can be deployed as a web-based system consisting of:

Internet
    ↓
Public Application URL
    ↓
Streamlit Dashboard
    ↓
FastAPI Backend
    ↓
AI Processing
    ↓
Database

For the prototype, controlled/sample footage can be used for demonstration.

Production deployment would require additional security, authentication, authorization, secure storage, monitoring, scalable processing, and approved integration with authorized CCTV/NVR infrastructure.

25. Current Prototype Scope

The prototype focuses on:

Case management
Video analysis
Person detection
Multi-object tracking
Candidate analysis
Evidence generation
Lead scoring
Priority ranking
Investigator dashboard
Human verification workflow
26. Future Scope

Future improvements may include:

Integration with authorized CCTV/NVR systems
Multi-camera person re-identification
Improved appearance-based candidate matching
Advanced temporal correlation
Advanced location correlation
Secure evidence storage
Role-based access control
Authentication and authorization
Scalable cloud deployment
GPU acceleration
Real-time processing
Improved model optimization
Audit logging
Advanced investigator analytics
27. Responsible Use

SAFETrace AI is designed as an investigation-support system.

AI-generated candidates should be treated as leads for further investigation and should not be considered definitive proof of identity.

Any real-world deployment should comply with applicable laws, organizational policies, privacy requirements, evidence-handling procedures, and authorized access controls.

28. Project Status

SAFETrace AI is being developed as a prototype for demonstration and evaluation.

The final integrated system combines:

AI / Computer Vision
        +
FastAPI Backend
        +
Database
        +
Streamlit Investigator Dashboard
        +
Evidence & Lead Scoring
        +
Human Verification

into one end-to-end investigation-support workflow.

29. Team

SAFETrace AI is developed as a collaborative project with separate responsibilities across:

AI / Computer Vision
Backend / Database
Frontend / Investigator Dashboard
Integration / Deployment / Documentation / Testing
30. License

This project is intended for educational, research, and prototype demonstration purposes.

Refer to the repository license for usage and distribution terms.
