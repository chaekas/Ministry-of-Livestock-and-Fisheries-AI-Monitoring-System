# Ministry of Livestock and Fisheries AI Monitoring System

A low-cost Streamlit prototype for fish and livestock market inspections.

## Prototype scope

1. **Fish counting:** Take a photo with the device camera or upload a fish photo. Upload a video for sampled-frame analysis.
2. **Livestock counting:** Take a photo with the device camera or upload a livestock photo. Upload a video for sampled-frame analysis.
3. **Market inspection records and reports:** Save the market/location, verified count, inspection notes, date, and officer; review records and export a CSV report.

The app includes local login, administrator-created user accounts, a SQLite database, an executive dashboard, and an inspection history.

## Run in GitHub Codespaces

Python 3.12 is recommended for the optional computer-vision dependencies.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Open port 8501 in the Codespaces Ports panel. On first launch, create the administrator account. No default password is provided.

## Enable AI counting

The core app can run without AI dependencies, but counting requires compatible model weights.

```bash
python -m pip install -r requirements-ai.txt
```

- Fish model path: `models/fish_counting.onnx`, configurable with `FISH_YOLO_MODEL`.
- Livestock model path: `models/livestock_counting.pt`, configurable with `LIVESTOCK_YOLO_MODEL`.

Place a model trained for the relevant detection task at the configured path. The application deliberately does not substitute generic model weights or report invented counts. Model files are excluded from Git commits and must be installed separately.

**Model limitations:** A model must be evaluated on representative local market photos and videos before operational use. Detections are estimates; an officer should verify counts before saving inspection records. Video analysis samples frames and reports the peak detections in one sampled frame. It does not count unique fish or animals across the entire video.

## Camera and video workflow

- The photo tabs use Streamlit's browser camera input when a supported camera is available and permitted by the browser.
- Existing videos can be uploaded for sampled-frame analysis.
- **Direct in-app video recording is not implemented yet**; this prototype currently supports direct photo capture and video upload.

## Data and security

- SQLite database: `data/ministry.db` by default.
- Local database files, uploads, environment files, and model weights are excluded from Git.
- Do not commit passwords, secrets, sensitive ministry footage, or identifiable animal-owner records.
- The authentication and authorization features are for prototyping and require a security review before ministry deployment.

## Tests

```bash
pytest -q
```

## Before ministry deployment

Validate model accuracy and licensing; add robust upload validation and size limits; review authentication, session protection, role-based access, and audit-log integrity; configure backups and retention; and deploy only on infrastructure approved by the Ministry.
