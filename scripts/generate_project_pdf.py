from __future__ import annotations

import textwrap
from datetime import date
from pathlib import Path

from generate_project_report import CODE_FILES, ROOT, DOCS, project_tree


PAGE_W = 595
PAGE_H = 842
LEFT = 45
RIGHT = 45
TOP = 52
BOTTOM = 48


def pdf_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", "")
    )


class SimplePdf:
    def __init__(self) -> None:
        self.pages: list[list[tuple[str, int, str]]] = []
        self.current: list[tuple[str, int, str]] = []
        self.y = PAGE_H - TOP

    def page_break(self) -> None:
        if self.current:
            self.pages.append(self.current)
        self.current = []
        self.y = PAGE_H - TOP

    def ensure_space(self, leading: int) -> None:
        if self.y - leading < BOTTOM:
            self.page_break()

    def line(self, text: str = "", font: str = "regular", size: int = 10, leading: int | None = None) -> None:
        leading = leading or int(size * 1.45)
        self.ensure_space(leading)
        self.current.append((font, size, text))
        self.y -= leading

    def paragraph(self, text: str, font: str = "regular", size: int = 10, width: int = 94) -> None:
        for raw in text.splitlines() or [""]:
            wrapped = textwrap.wrap(raw, width=width, replace_whitespace=False) or [""]
            for item in wrapped:
                self.line(item, font=font, size=size)
        self.line("", size=4, leading=6)

    def bullet(self, text: str) -> None:
        wrapped = textwrap.wrap(text, width=90)
        if not wrapped:
            self.line("•", size=10)
            return
        self.line(f"- {wrapped[0]}", size=10)
        for item in wrapped[1:]:
            self.line(f"  {item}", size=10)

    def heading(self, text: str) -> None:
        self.line("", size=6, leading=8)
        self.line(text, font="bold", size=15, leading=20)

    def subheading(self, text: str) -> None:
        self.line("", size=4, leading=6)
        self.line(text, font="bold", size=11, leading=15)

    def code(self, text: str) -> None:
        for raw in text.splitlines():
            expanded = raw.replace("\t", "    ")
            chunks = textwrap.wrap(expanded, width=106, replace_whitespace=False, drop_whitespace=False) or [""]
            for chunk in chunks:
                self.line(chunk, font="mono", size=7, leading=9)

    def finish(self, output: Path) -> None:
        if self.current:
            self.pages.append(self.current)

        objects: list[bytes] = []

        def add(obj: str | bytes) -> int:
            if isinstance(obj, str):
                obj = obj.encode("latin-1", errors="replace")
            objects.append(obj)
            return len(objects)

        catalog_id = add("PLACEHOLDER")
        pages_id = add("PLACEHOLDER")
        font_regular_id = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        font_bold_id = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
        font_mono_id = add("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

        page_ids: list[int] = []
        for page in self.pages:
            content_lines = []
            y = PAGE_H - TOP
            for font, size, text in page:
                font_name = {"regular": "F1", "bold": "F2", "mono": "F3"}[font]
                safe = pdf_escape(text)
                content_lines.append(f"BT /{font_name} {size} Tf {LEFT} {y} Td ({safe}) Tj ET")
                y -= int(size * 1.45) if font != "mono" else 9
            stream = "\n".join(content_lines).encode("latin-1", errors="replace")
            content_id = add(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")
            page_id = add(
                f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R /F3 {font_mono_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            )
            page_ids.append(page_id)

        objects[catalog_id - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode()
        kids = " ".join(f"{pid} 0 R" for pid in page_ids)
        objects[pages_id - 1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()

        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for idx, obj in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{idx} 0 obj\n".encode())
            pdf.extend(obj)
            pdf.extend(b"\nendobj\n")
        xref = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode())
        pdf.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
        )
        output.write_bytes(pdf)


def build_pdf() -> None:
    pdf = SimplePdf()
    pdf.line("Face and Eye Detection Project Report", font="bold", size=22, leading=28)
    pdf.line(f"Generated on {date.today().strftime('%d %B %Y')} from local project files.", size=10)
    pdf.line("", leading=10)
    pdf.paragraph(
        "This project is a Django web application combined with OpenCV utilities. The main app registers a person, "
        "captures or uploads a face image, validates face and eye visibility, generates a QR identity code, and opens "
        "a profile page when the QR code is scanned. The legacy tools under src/ provide webcam face and eye detection."
    )

    sections: list[tuple[str, list[str]]] = [
        (
            "Objectives",
            [
                "Detect a human face and eyes from an uploaded or captured image.",
                "Register a person with name, address, unique number, face image, and generated QR code.",
                "Provide mobile-friendly camera capture through HTTPS tunnel mode.",
                "Maintain scan and registration history for each person.",
                "Expose REST API endpoints for listing, creating, validating, and retrieving people.",
            ],
        ),
        (
            "Tools and Technologies Used",
            [
                "Python: main programming language.",
                "Django: backend web framework for routes, templates, models, forms, sessions, and admin support.",
                "Django REST Framework: API layer for people listing, person creation, and profile retrieval.",
                "SQLite: development database.",
                "OpenCV: Haar cascade face and eye detection.",
                "qrcode and Pillow: QR image generation.",
                "HTML, CSS, JavaScript: dashboard, profile screens, browser camera capture.",
                "Cloudflared: HTTPS tunnel for mobile camera access.",
                "Typer and Rich: command-line interface for legacy OpenCV demo.",
                "Tkinter: desktop GUI for live detection.",
                "pytest: automated tests.",
            ],
        ),
    ]
    for title, items in sections:
        pdf.heading(title)
        for item in items:
            pdf.bullet(item)

    pdf.heading("Project Structure")
    pdf.code(project_tree())

    pdf.heading("Module Explanation")
    module_items = [
        "backend/project/: Django settings, root URLs, WSGI, and ASGI configuration.",
        "backend/users/models.py: Person and PersonHistory database tables.",
        "backend/users/views.py: registration, detail pages, scan logging, deletion, and APIs.",
        "backend/users/utils/face_utils.py: OpenCV face and eye validation.",
        "backend/users/utils/qr_utils.py: QR code PNG generation.",
        "backend/users/templates/: dashboard, activation, scan result, profile, and history pages.",
        "src/: legacy command-line and desktop GUI real-time detection tools.",
        "run_mobile_server.sh: migrations, QR regeneration, Django startup, and optional Cloudflare tunnel.",
    ]
    for item in module_items:
        pdf.bullet(item)

    pdf.heading("Working Flow")
    for item in [
        "User opens the Django dashboard.",
        "User enters name, address, and unique number.",
        "User activates the browser camera or uploads a face image.",
        "Server validates the image using OpenCV.",
        "If a face and both eyes are found, the person is saved to SQLite.",
        "A QR code is generated with a URL pointing to the person profile.",
        "When scanned, the QR page shows person details and logs scan history.",
    ]:
        pdf.bullet(item)

    pdf.heading("Important Commands")
    pdf.code(
        "python3 -m venv .venv\n"
        "source .venv/bin/activate\n"
        "pip install -r requirements.txt\n"
        "AUTO_TUNNEL=1 FORCE_RESTART=1 APP_PORT=8001 bash run_mobile_server.sh\n"
        "python -m src.app cameras\n"
        "python -m src.app run --backend avfoundation\n"
        "pytest"
    )

    pdf.heading("Advantages")
    for item in [
        "Simple implementation using widely available libraries.",
        "Works as both a web registration system and a real-time OpenCV demo.",
        "QR profile flow makes identity lookup fast from a mobile phone.",
        "OpenCV validation helps reject unclear images.",
        "Cloudflare tunnel mode solves mobile browser HTTPS camera limitations during demos.",
        "Local SQLite setup is easy for student, internship, and prototype environments.",
        "Scan history gives a basic audit trail.",
    ]:
        pdf.bullet(item)

    pdf.heading("Disadvantages / Limitations")
    for item in [
        "Haar cascade detection is lightweight but less accurate than modern deep-learning face detectors.",
        "Detection quality depends on lighting, camera quality, face angle, and eye visibility.",
        "The app stores identity data and face images locally, so production use needs stronger privacy and security controls.",
        "SQLite is suitable for development but not ideal for many concurrent production users.",
        "Cloudflared trial URLs can change each run, so generated QR codes may need regeneration.",
        "The optional face_recognition package is not listed in requirements, so face encoding may return None unless installed separately.",
        "More tests are needed for Django views, APIs, templates, and QR regeneration.",
    ]:
        pdf.bullet(item)

    pdf.heading("Benefits / Applications")
    for item in [
        "Mini identity registration and QR verification prototype.",
        "Useful for learning computer vision, Django, REST APIs, image upload handling, and QR generation.",
        "Can support attendance, visitor registration, student identity demos, and access-log prototypes after hardening.",
        "Good base for face recognition, liveness checking, or admin dashboard extensions.",
    ]:
        pdf.bullet(item)

    pdf.heading("Recommended Improvements")
    for item in [
        "Add authentication and role-based access for administrators.",
        "Use PostgreSQL or MySQL for production instead of SQLite.",
        "Replace or supplement Haar cascades with MediaPipe, RetinaFace, YOLO, or DNN-based OpenCV models.",
        "Add image privacy controls, consent text, encryption strategy, and retention policy.",
        "Add API and Django view tests.",
        "Use a stable production domain so QR codes do not change between runs.",
    ]:
        pdf.bullet(item)

    pdf.heading("Conclusion")
    pdf.paragraph(
        "The project successfully demonstrates face and eye detection integrated with a practical Django QR identity "
        "workflow. It is best suited for learning, prototype demos, and small controlled environments. With stronger "
        "detection models, better security, authentication, and production database setup, it can be expanded into a "
        "more robust identity registration and verification system."
    )

    pdf.page_break()
    pdf.line("Complete Source Code Appendix", font="bold", size=18, leading=24)
    pdf.paragraph(
        "The appendix includes the main text/code files from the project. Binary files, database files, virtual "
        "environment files, logs, and uploaded media are intentionally excluded."
    )
    for rel in CODE_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        pdf.page_break()
        pdf.line(rel, font="bold", size=13, leading=18)
        pdf.code(path.read_text(encoding="utf-8", errors="replace"))

    output = DOCS / "face_eye_detection_project_report.pdf"
    pdf.finish(output)
    print(output)


if __name__ == "__main__":
    build_pdf()
