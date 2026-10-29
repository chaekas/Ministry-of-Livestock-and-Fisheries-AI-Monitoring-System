# Ministry of Livestock and Fisheries AI Monitoring System

A Streamlit prototype for a future AI-assisted ministry monitoring application.

## Phase 1 scope

- Initial administrator setup and login with salted PBKDF2 password hashes
- Basic role labels: administrator, officer, supervisor
- SQLite persistence for users, inspections, and audit events
- Dashboard, manual inspection records, and CSV reporting
- Navigation placeholders for five future computer-vision modules

## Planned AI modules

1. Livestock counting
2. Fish counting
3. Animal health screening for veterinary review
4. Fish species identification
5. Livestock movement monitoring

These modules are not yet connected to YOLO models in Phase 1. No disease diagnosis or automatic species claim should be relied on until a suitable model is trained and validated.

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
