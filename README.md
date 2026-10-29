# Ministry of Livestock and Fisheries AI Monitoring System

A Streamlit prototype for a future AI-assisted ministry monitoring application.

## Phase 1 scope

- Initial administrator setup and login with salted PBKDF2 password hashes
- Basic role labels: administrator, officer, supervisor
- SQLite persistence for users, inspections, and audit events
- Dashboard, manual inspection records, and CSV reporting
- Dashboard, manual inspection records, and CSV reporting
- Fish Counting image/video upload workflow using a configured custom YOLO model
- Navigation placeholders for the other four computer-vision modules

## Planned AI modules

1. Livestock counting
2. Fish counting
3. Animal health screening for veterinary review
4. Fish species identification
5. Livestock movement monitoring

Fish Counting now includes an image/video upload and inference workflow, but it requires a suitable trained fish-detection model file. The other four computer-vision modules remain placeholders. No disease diagnosis or automatic species claim should be relied on until a suitable model is trained and validated.

## Enable Fish Counting

The core application dependencies do not install the larger computer-vision stack. Use a Python version supported by PyTorch/Ultralytics; Python 3.12 is recommended. In a Python 3.12 environment, install the optional dependencies:

    python -m pip install -r requirements-ai.txt

Place your trained fish-detection YOLO weights at:

    models/fish_counting.pt

Alternatively, set the `FISH_YOLO_MODEL` environment variable to the full path of your weights file before starting Streamlit. Model weights are intentionally excluded from Git commits. Use a model whose labels and performance have been validated for the intended fish species, tank/channel conditions, camera angles, and image quality.

The image workflow reports detections in one image. The video workflow samples frames and reports the peak detections in one sampled frame; it does **not** claim to count unique fish across the whole video. Review detections and save only a verified count. If the model file or optional dependencies are missing, the page explains what is needed.

## Run in GitHub Codespaces

Python 3.12 is recommended for later YOLO/OpenCV integration. Phase 1 may run on other supported Python versions, depending on dependency availability.

    python -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    streamlit run app.py --server.address 0.0.0.0 --server.port 8501

Open port 8501 in the Codespaces Ports panel. On first launch, create the administrator account. No default password is provided.

## Local data and secrets

- SQLite data is stored under data/ministry.db by default.
- The .gitignore excludes local data, uploads, environment files, and model weights.
- Do not commit passwords, secrets, real sensitive ministry data, or identifiable animal-owner records.
- The Phase 1 login is a prototype, not a production identity and access management solution.

## Tests

    pytest -q

## Before ministry deployment

Conduct security review and testing; add rate limiting and secure session protections; restrict and validate uploads; configure backups and retention; establish audit-log protections; evaluate access control; and deploy only on infrastructure approved by the ministry.
