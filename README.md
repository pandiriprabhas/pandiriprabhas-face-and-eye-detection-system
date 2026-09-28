# Face and Eye Detection

This project contains a Django face-to-QR workflow and OpenCV face/eye detection utilities.

## Features
- Register a person with name, address and unique number
- Capture and validate a face image
- Generate a QR code for the profile
- View registration and scan history
- OpenCV face and eye detection utilities
- Mobile HTTPS tunnel support

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python backend/manage.py migrate
python backend/manage.py runserver
```

For mobile camera access with an HTTPS tunnel:

```bash
AUTO_TUNNEL=1 FORCE_RESTART=1 APP_PORT=8001 bash run_mobile_server.sh
```

## Project Structure
- `backend/` — Django backend
- `frontend/` — frontend
- `src/` — OpenCV face/eye detection code
- `android/` — Android sample
- `tests/` — tests
- `scripts/` — helper/report scripts
- `docs/` — project documentation

## API
- `GET /api/people/`
- `POST /api/people/`
- `GET /api/people/<unique_code>/`
