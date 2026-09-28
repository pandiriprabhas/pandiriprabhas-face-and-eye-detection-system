from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

CODE_FILES = [
    "README.md",
    "requirements.txt",
    "run_mobile_server.sh",
    "esc_listener.py",
    "frontend/index.html",
    "backend/manage.py",
    "backend/project/__init__.py",
    "backend/project/settings.py",
    "backend/project/urls.py",
    "backend/project/asgi.py",
    "backend/project/wsgi.py",
    "backend/users/__init__.py",
    "backend/users/admin.py",
    "backend/users/apps.py",
    "backend/users/forms.py",
    "backend/users/models.py",
    "backend/users/serializers.py",
    "backend/users/urls.py",
    "backend/users/views.py",
    "backend/users/utils/__init__.py",
    "backend/users/utils/face_utils.py",
    "backend/users/utils/qr_utils.py",
    "backend/users/management/__init__.py",
    "backend/users/management/commands/__init__.py",
    "backend/users/management/commands/regenerate_qr_codes.py",
    "backend/users/migrations/__init__.py",
    "backend/users/migrations/0001_initial.py",
    "backend/users/migrations/0002_person_unique_number.py",
    "backend/users/templates/users/base.html",
    "backend/users/templates/users/dashboard.html",
    "backend/users/templates/users/history_list.html",
    "backend/users/templates/users/person_activate.html",
    "backend/users/templates/users/person_detail.html",
    "backend/users/templates/users/person_scan.html",
    "src/app.py",
    "src/detector.py",
    "src/gui.py",
    "src/utils.py",
    "src/video.py",
    "tests/test_cascade_load.py",
]


def file_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def project_tree() -> str:
    allowed_prefixes = ("backend", "frontend", "src", "tests", "android", "docs", "scripts")
    visible = [
        ".gitignore",
        "README.md",
        "README_OLD.md",
        "requirements.txt",
        "run_mobile_server.sh",
        "esc_listener.py",
    ]
    lines = ["Face and eye detection/"]
    all_paths = []
    for path in ROOT.rglob("*"):
        rel = path.relative_to(ROOT)
        parts = rel.parts
        if not parts:
            continue
        if parts[0] in {".git", ".venv", ".pytest_cache", "__pycache__"}:
            continue
        if parts[0] in {"media", "data", "logs"}:
            continue
        rel_s = rel.as_posix()
        if path.is_file() and (rel_s in visible or parts[0] in allowed_prefixes):
            all_paths.append(rel_s)
    for rel_s in sorted(all_paths):
        lines.append(f"  {rel_s}")
    lines.extend(
        [
            "  media/faces/ ... uploaded face images",
            "  media/qr_codes/ ... generated QR images",
            "  data/captures/ ... legacy OpenCV demo snapshots",
            "  backend/db.sqlite3 ... local SQLite database",
        ]
    )
    return "\n".join(lines)


def code_appendix() -> str:
    sections = []
    for rel in CODE_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        language = path.suffix.lstrip(".") or "text"
        sections.append(
            f"""
            <section class="code-section">
              <h3>{escape(rel)}</h3>
              <pre><code class="language-{escape(language)}">{escape(file_text(rel))}</code></pre>
            </section>
            """
        )
    return "\n".join(sections)


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    today = date.today().strftime("%d %B %Y")
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Face and Eye Detection Project Report</title>
  <style>
    @page {{ margin: 20mm 16mm; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      color: #1f2933;
      line-height: 1.48;
      font-size: 12.5px;
    }}
    h1, h2, h3 {{ color: #0f172a; line-height: 1.2; }}
    h1 {{ font-size: 30px; margin: 0 0 8px; }}
    h2 {{ font-size: 20px; margin-top: 28px; border-bottom: 1px solid #d9e2ec; padding-bottom: 5px; }}
    h3 {{ font-size: 15px; margin-top: 18px; }}
    .subtitle {{ color: #52606d; font-size: 14px; margin-bottom: 26px; }}
    .box {{ border: 1px solid #d9e2ec; border-radius: 6px; padding: 12px 14px; background: #f8fafc; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 7px 8px; vertical-align: top; }}
    th {{ background: #eef2f7; text-align: left; }}
    code {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace; }}
    pre {{
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      border: 1px solid #d9e2ec;
      border-radius: 6px;
      padding: 10px;
      background: #0b1020;
      color: #e5e7eb;
      font-size: 8.4px;
      line-height: 1.28;
    }}
    .tree pre {{ background: #f8fafc; color: #1f2933; font-size: 10px; }}
    .page-break {{ page-break-before: always; }}
    .code-section {{ page-break-before: always; }}
    ul {{ margin-top: 6px; }}
    li {{ margin: 4px 0; }}
  </style>
</head>
<body>
  <h1>Face and Eye Detection Project Report</h1>
  <div class="subtitle">Generated on {escape(today)} from the local project files.</div>

  <div class="box">
    <strong>Project Summary:</strong>
    This project is a Django web application combined with OpenCV utilities. The main application registers a person,
    captures or uploads a face image, validates that a face and both eyes are visible, generates a QR identity code,
    and opens a profile/scan page when the QR code is scanned. The legacy tools under <code>src/</code> provide
    real-time webcam face and eye detection using Haar cascades.
  </div>

  <h2>Objectives</h2>
  <ul>
    <li>Detect a human face and eyes from an uploaded or captured image.</li>
    <li>Register a person with name, address, unique number, face image, and generated unique QR code.</li>
    <li>Provide mobile-friendly camera capture through HTTPS tunnel mode.</li>
    <li>Maintain scan and registration history for each person.</li>
    <li>Expose REST API endpoints for listing, creating, validating, and retrieving people.</li>
  </ul>

  <h2>Tools and Technologies Used</h2>
  <table>
    <tr><th>Tool / Technology</th><th>Use in Project</th></tr>
    <tr><td>Python</td><td>Main programming language for Django backend and OpenCV detection utilities.</td></tr>
    <tr><td>Django</td><td>Web framework for routing, templates, models, forms, sessions, and admin support.</td></tr>
    <tr><td>Django REST Framework</td><td>API layer for people listing, person creation, and profile retrieval.</td></tr>
    <tr><td>SQLite</td><td>Local database used by Django during development.</td></tr>
    <tr><td>OpenCV</td><td>Face and eye detection using Haar cascade classifiers.</td></tr>
    <tr><td>qrcode + Pillow</td><td>QR code generation and image handling.</td></tr>
    <tr><td>HTML, CSS, JavaScript</td><td>Dashboard, profile pages, camera preview, and browser image capture.</td></tr>
    <tr><td>Cloudflared</td><td>Creates a temporary HTTPS public URL so mobile browsers allow camera access.</td></tr>
    <tr><td>Typer and Rich</td><td>Command-line interface and formatted terminal output for the legacy OpenCV demo.</td></tr>
    <tr><td>Tkinter</td><td>Simple desktop GUI for live camera detection.</td></tr>
    <tr><td>pytest</td><td>Automated tests for cascade loading, capture behavior, and eye filtering logic.</td></tr>
  </table>

  <h2>Project Structure</h2>
  <div class="tree"><pre>{escape(project_tree())}</pre></div>

  <h2>Module Explanation</h2>
  <table>
    <tr><th>Part</th><th>Description</th></tr>
    <tr><td><code>backend/project/</code></td><td>Django settings, root URLs, WSGI, and ASGI configuration.</td></tr>
    <tr><td><code>backend/users/models.py</code></td><td>Defines <code>Person</code> and <code>PersonHistory</code> database tables.</td></tr>
    <tr><td><code>backend/users/views.py</code></td><td>Controls registration, detail pages, QR scan logging, deletion, and API responses.</td></tr>
    <tr><td><code>backend/users/utils/face_utils.py</code></td><td>Uses OpenCV to detect face and eye positions and optionally extracts face encodings.</td></tr>
    <tr><td><code>backend/users/utils/qr_utils.py</code></td><td>Builds QR code PNG bytes for each person profile URL.</td></tr>
    <tr><td><code>backend/users/templates/</code></td><td>HTML pages for dashboard, activation, scan result, profile, and history.</td></tr>
    <tr><td><code>src/</code></td><td>Legacy command-line and desktop GUI real-time detection tools.</td></tr>
    <tr><td><code>run_mobile_server.sh</code></td><td>Starts Django, applies migrations, regenerates QR codes, and optionally starts a Cloudflare tunnel.</td></tr>
    <tr><td><code>tests/</code></td><td>Basic automated tests for OpenCV cascade and capture logic.</td></tr>
  </table>

  <h2>Working Flow</h2>
  <ol>
    <li>User opens the Django dashboard.</li>
    <li>User enters name, address, and unique number.</li>
    <li>User activates the browser camera or uploads a face image.</li>
    <li>Server validates the image using OpenCV face and eye detection.</li>
    <li>If a face and both eyes are found, the person is saved to SQLite.</li>
    <li>A QR code is generated with a URL pointing to the person profile.</li>
    <li>When scanned, the QR page shows the person details and logs scan history.</li>
  </ol>

  <h2>Important Commands</h2>
  <pre><code>python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
AUTO_TUNNEL=1 FORCE_RESTART=1 APP_PORT=8001 bash run_mobile_server.sh
python -m src.app cameras
python -m src.app run --backend avfoundation
pytest</code></pre>

  <h2>Advantages</h2>
  <ul>
    <li>Simple and understandable implementation using widely available libraries.</li>
    <li>Works as both a web registration system and a real-time OpenCV demo.</li>
    <li>QR profile flow makes identity lookup fast from a mobile phone.</li>
    <li>OpenCV validation helps reject images where the face or eyes are not clear.</li>
    <li>Cloudflare tunnel mode solves the mobile browser HTTPS camera limitation during demos.</li>
    <li>Local SQLite setup is easy for student, internship, and prototype environments.</li>
    <li>Scan history gives a basic audit trail.</li>
  </ul>

  <h2>Disadvantages / Limitations</h2>
  <ul>
    <li>Haar cascade detection is lightweight but less accurate than modern deep-learning face detectors.</li>
    <li>Detection quality depends on lighting, camera quality, face angle, and eye visibility.</li>
    <li>The current app stores identity data and face images locally, so production use needs stronger privacy and security controls.</li>
    <li>SQLite is suitable for development but not ideal for many concurrent production users.</li>
    <li>Cloudflared trial URLs can change each run, so generated QR codes may need regeneration.</li>
    <li>The optional <code>face_recognition</code> package is not listed in requirements, so face encoding may return <code>None</code> unless installed separately.</li>
    <li>There is basic test coverage, but more tests are needed for Django views, APIs, templates, and QR regeneration.</li>
  </ul>

  <h2>Benefits / Applications</h2>
  <ul>
    <li>Can be used as a mini identity registration and QR verification prototype.</li>
    <li>Useful for learning computer vision, Django, REST APIs, image upload handling, and QR generation.</li>
    <li>Can support attendance, visitor registration, student identity demos, and access-log prototypes after security hardening.</li>
    <li>Good base project for extending into face recognition, liveness checking, or admin dashboards.</li>
  </ul>

  <h2>Recommended Improvements</h2>
  <ul>
    <li>Add authentication and role-based access for administrators.</li>
    <li>Use PostgreSQL/MySQL for production instead of SQLite.</li>
    <li>Replace or supplement Haar cascades with a modern detector such as MediaPipe, RetinaFace, YOLO, or DNN-based OpenCV models.</li>
    <li>Add image privacy controls, consent text, encryption strategy, and retention policy.</li>
    <li>Add API and Django view tests.</li>
    <li>Use a stable production domain so QR codes do not change between runs.</li>
  </ul>

  <h2>Conclusion</h2>
  <p>
    The project successfully demonstrates face and eye detection integrated with a practical Django QR identity workflow.
    It is best suited for learning, prototype demos, and small controlled environments. With stronger detection models,
    better security, authentication, and production database setup, it can be expanded into a more robust identity
    registration and verification system.
  </p>

  <h2 class="page-break">Complete Source Code Appendix</h2>
  <p>The following appendix includes the main text/code files from the project. Binary files, database files, virtual environment files, logs, and uploaded media are intentionally excluded.</p>
  {code_appendix()}
</body>
</html>
"""
    (DOCS / "face_eye_detection_project_report.html").write_text(html, encoding="utf-8")
    print(DOCS / "face_eye_detection_project_report.html")


if __name__ == "__main__":
    main()
