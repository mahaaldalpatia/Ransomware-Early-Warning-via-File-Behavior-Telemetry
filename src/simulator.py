import os
import time
import random
import csv
import json
import zipfile
from pathlib import Path

# Optional libraries for authentic enterprise file generation
try:
    from reportlab.pdfgen import canvas as pdf_canvas
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from PIL import Image as PILImage
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TARGET_DIR = BASE_DIR / "real_world_data"


# --------------------------------------------------
# REAL-WORLD FILE GENERATORS
# --------------------------------------------------

def create_real_docx(file_path, title, body_text):
    """
    Creates an authentic Microsoft Word (.docx) package containing
    standard OpenXML document structures.
    """
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '<Default Extension="xml" ContentType="application/xml"/>\n'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>\n'
        '</Relationships>'
    )
    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        f'<w:body><w:p><w:r><w:t>{title}</w:t></w:r></w:p>'
        f'<w:p><w:r><w:t>{body_text}</w:t></w:r></w:p></w:body>\n'
        '</w:document>'
    )

    with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", rels)
        z.writestr("word/document.xml", doc_xml)


def create_real_pdf(file_path, title, lines):
    """
    Generates an authentic Adobe PDF document with real stream objects.
    """
    if HAS_REPORTLAB:
        c = pdf_canvas.Canvas(str(file_path))
        c.setFont("Helvetica-Bold", 14)
        c.drawString(72, 750, title)
        c.setFont("Helvetica", 10)
        y = 720
        for line in lines:
            c.drawString(72, y, line)
            y -= 18
        c.save()
    else:
        # Fallback minimal valid PDF structure
        pdf_content = (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000053 00000 n\n0000000102 00000 n\n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n182\n%%EOF"
        )
        file_path.write_bytes(pdf_content)


def create_real_csv(file_path, title, row_count=25):
    """
    Generates a structured financial/customer CSV ledger.
    """
    departments = ["Finance", "Engineering", "Legal", "Operations", "Marketing"]
    vendors = ["Amazon Web Services", "Microsoft Azure", "Salesforce", "Cisco Systems", "Dell Technologies"]

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Transaction_ID", "Date", "Department", "Vendor", "Amount_USD", "Status"])
        for i in range(1, row_count + 1):
            date_str = f"2026-10-{random.randint(1, 28):02d}"
            amount = round(random.uniform(500.0, 45000.0), 2)
            writer.writerow([
                f"TXN-{2026000 + i}",
                date_str,
                random.choice(departments),
                random.choice(vendors),
                f"${amount:,.2f}",
                "APPROVED"
            ])


def create_real_image(file_path, label):
    """
    Generates a valid corporate architecture/diagram image (PNG).
    """
    if HAS_PILLOW:
        img = PILImage.new("RGB", (320, 240), color=(random.randint(20, 70), random.randint(40, 100), random.randint(70, 150)))
        img.save(str(file_path), format="PNG")
    else:
        # 1x1 valid PNG bytes fallback
        png_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\r\xef\x80\xa7\x00\x00\x00\x00IEND\xaeB`\x82'
        file_path.write_bytes(png_bytes)


def create_real_json(file_path, config_name):
    """
    Generates an enterprise application configuration JSON file.
    """
    data = {
        "environment": "production",
        "cluster_name": config_name,
        "database": {
            "host": "db-cluster-primary.internal",
            "port": 5432,
            "max_connections": 150,
            "ssl_enabled": True
        },
        "endpoints": [
            {"service": "auth", "port": 8080, "status": "active"},
            {"service": "billing", "port": 8081, "status": "active"},
            {"service": "telemetry", "port": 9000, "status": "active"}
        ]
    }
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def create_real_text(file_path, title, notes):
    """
    Generates human-readable corporate memos and notes.
    """
    content = (
        f"CONFIDENTIAL MEMO: {title.upper()}\n"
        f"DATE: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"STATUS: INTERNAL REVIEW ONLY\n"
        f"{'-' * 60}\n"
        f"{notes}\n"
    )
    file_path.write_text(content, encoding="utf-8")


# --------------------------------------------------
# ENTERPRISE WORKLOAD SETUP
# --------------------------------------------------

def populate_real_world_files(target_dir):
    """
    Populates the target folder with authentic, diverse enterprise documents:
    PDFs, Word DOCX, CSV Ledgers, Images, JSON configs, and Text notes.
    """
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    print(f"\n[+] Populating authentic enterprise files in: {target_path.resolve()}")

    # 1. Real PDF Documents
    create_real_pdf(
        target_path / "Q3_Corporate_Financial_Statement.pdf",
        "Quarterly Financial and Performance Report",
        ["Total Revenue: $14,250,000", "Operating Expenses: $8,120,000", "Net Operating Margin: 43%", "Audit Status: COMPLIANT"]
    )
    create_real_pdf(
        target_path / "Annual_Cybersecurity_Compliance_Audit.pdf",
        "Cybersecurity Framework Assessment (NIST / ISO 27001)",
        ["Vulnerability Scans: COMPLETED", "Endpoint Protection: ACTIVE", "Firewall Rules: VERIFIED", "Access Review: PASSED"]
    )
    create_real_pdf(
        target_path / "Employee_Health_Benefits_Guide_2026.pdf",
        "Comprehensive Employee Benefits Program",
        ["Medical, Dental, Vision Coverage Summaries", "Retirement 401(k) Match Policies", "Wellness and Remote Work Allowances"]
    )

    # 2. Real Microsoft Word Documents (.docx)
    create_real_docx(
        target_path / "Confidential_Executive_Strategy_Brief.docx",
        "Enterprise Strategic Vision 2026-2028",
        "This confidential document outlines the planned infrastructure modernization, cloud migration roadmap, and security posture."
    )
    create_real_docx(
        target_path / "Contract_Agreement_Cloud_Vendor.docx",
        "Master Services Agreement - Vendor Partnership",
        "Terms and conditions for service level agreements (SLAs), data sovereignty compliance, and liability warranties."
    )
    create_real_docx(
        target_path / "Product_Architecture_Specification.docx",
        "Microservices Architecture Specifications",
        "API communication protocols, database schema migrations, and load balancing configurations for distributed services."
    )

    # 3. Real CSV Financial Ledgers
    create_real_csv(target_path / "Payroll_Ledger_Q3_2026.csv", "Payroll", row_count=30)
    create_real_csv(target_path / "Customer_Accounts_Payable.csv", "Accounts Payable", row_count=35)
    create_real_csv(target_path / "Quarterly_Tax_Filings_2026.csv", "Tax Filings", row_count=25)

    # 4. Real Images / Diagrams
    create_real_image(target_path / "Network_Topology_Map.png", "Network Map")
    create_real_image(target_path / "Corporate_Identity_Logo.png", "Company Logo")
    create_real_image(target_path / "System_Architecture_Diagram.png", "Architecture Diagram")

    # 5. Configuration & Structured Data
    create_real_json(target_path / "production_database_config.json", "primary-us-east")
    create_real_json(target_path / "api_gateway_routes.json", "gateway-cluster")

    # 6. Text Documents & Source Code
    create_real_text(
        target_path / "client_meeting_minutes.txt",
        "Executive Client Briefing",
        "Reviewed Q3 delivery timelines. Client requested enhanced endpoint security metrics and automated backup verification."
    )
    create_real_text(
        target_path / "database_maintenance_notes.txt",
        "Database Maintenance Schedule",
        "Scheduled index rebuilds and WAL checkpointing for Saturday midnight window. Backup verified intact."
    )
    (target_path / "backup_schema_dump.sql").write_text(
        "CREATE TABLE customers (id INT PRIMARY KEY, name VARCHAR(100), email VARCHAR(100));\n"
        "CREATE TABLE orders (order_id INT PRIMARY KEY, amount DECIMAL(10,2), created_at TIMESTAMP);\n",
        encoding="utf-8"
    )

    # Also generate a collection of numbered department files to ensure robust volume
    for i in range(1, 26):
        dept = random.choice(["legal", "finance", "operations", "engineering"])
        create_real_text(
            target_path / f"{dept}_record_{i:03d}.txt",
            f"Department Record {i}",
            f"Official departmental documentation for audit reference ID {dept.upper()}-{i:04d}."
        )

    file_count = len(list(target_path.iterdir()))
    print(f"[OK] Successfully populated {file_count} authentic multi-format files in {target_path.name}/")
    print("     Formats include: .pdf, .docx, .csv, .png, .json, .sql, .txt")


# --------------------------------------------------
# ENCRYPTION ENGINE (SIMULATED RANSOMWARE)
# --------------------------------------------------

def encrypt_file_simulated(file_path):
    """
    Simulates real ransomware cryptographic overwrite:
    Overwrites file with pseudo-random ciphertext bytes (mimicking AES-256 / ChaCha20).
    Drives Shannon entropy to ~7.8 - 7.95 across all document types.
    """
    try:
        original_size = file_path.stat().st_size
        cipher_bytes = os.urandom(max(original_size, 512))
        with open(file_path, "wb") as f:
            f.write(cipher_bytes)
        return True
    except (PermissionError, OSError):
        return False


# --------------------------------------------------
# NORMAL ACTIVITY SIMULATION
# --------------------------------------------------

def normal_activity(target_dir=None):
    """
    Simulates real-world everyday human office activity on real enterprise files:
    - Appends transaction rows to a CSV ledger
    - Updates a text document with human pauses
    - Renames an archived file
    - Creates a new draft
    """
    target_path = Path(target_dir) if target_dir else DEFAULT_TARGET_DIR
    target_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("     NORMAL USER WORKLOAD SIMULATION (BENIGN BASELINE)")
    print("=" * 70)
    print(f" Target Folder: {target_path.resolve()}")

    # Only populate if folder is empty
    if not any(target_path.iterdir()):
        populate_real_world_files(target_path)

    print("\n[+] Simulating normal human office workflow...")

    # Action 1: User updates a CSV ledger
    csv_file = target_path / "Customer_Accounts_Payable.csv"
    if csv_file.exists():
        with open(csv_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["TXN-2026999", "2026-10-23", "Finance", "Standard Office Supplies", "$420.50", "APPROVED"])
        print(f"  [User Action] Appended new transaction row to {csv_file.name}")
        time.sleep(0.8)

    # Action 2: User updates a text memo
    memo_file = target_path / "client_meeting_minutes.txt"
    if memo_file.exists():
        with open(memo_file, "a", encoding="utf-8") as f:
            f.write(f"\n[Updated {time.strftime('%H:%M:%S')}] Follow-up call completed with stakeholders.\n")
        print(f"  [User Action] Saved updates to {memo_file.name}")
        time.sleep(0.8)

    # Action 3: User creates a new meeting draft
    new_doc = target_path / "Weekly_Team_Sync_Draft.txt"
    new_doc.write_text("Agenda for Monday morning engineering sync.\n1. Telemetry metrics\n2. Release readiness\n", encoding="utf-8")
    print(f"  [User Action] Created draft: {new_doc.name}")
    time.sleep(0.8)

    # Action 4: User renames an archive file
    archive_file = target_path / "Payroll_Ledger_Q3_2026.csv"
    if archive_file.exists():
        new_name = target_path / "Payroll_Ledger_Q3_2026_ARCHIVED.csv"
        archive_file.rename(new_name)
        print(f"  [User Action] Archived file: {archive_file.name} -> {new_name.name}")
        time.sleep(0.8)

    print("\n[OK] Normal benign office activity simulation completed.")
    print("=" * 70)


# --------------------------------------------------
# RANSOMWARE ATTACK SIMULATION
# --------------------------------------------------

def suspicious_activity(target_dir=None, target_extension=".locked", delay=0.03):
    """
    Simulates a real-world ransomware attack across authentic enterprise files:
    - Target formats: .pdf, .docx, .csv, .png, .json, .sql, .txt
    - Stage 1: High-speed cryptographic payload overwrite (entropy spikes to ~7.9)
    - Stage 2: Mass extension alteration (appending .locked / .crypto)
    - Stage 3: Drops a ransom note demanding payment
    """
    target_path = Path(target_dir) if target_dir else DEFAULT_TARGET_DIR
    target_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 70)
    print("     CONTROLLED REAL-WORLD RANSOMWARE ATTACK SIMULATION")
    print("=" * 70)
    print(f" Target Folder: {target_path.resolve()}")
    print(" Multi-Format Target Spectrum: .pdf, .docx, .csv, .png, .json, .sql, .txt")
    print(f" Ransomware Extension Flag: {target_extension}")

    # Only populate if folder is empty
    if not any(target_path.iterdir()):
        populate_real_world_files(target_path)

    # Collect all legitimate user files
    target_files = [
        f for f in target_path.iterdir()
        if f.is_file() and not f.name.startswith("README_DECRYPT") and not f.name.endswith(target_extension)
    ]

    print(f"\n[!] STAGE 1: Launching high-speed cryptographic overwrite across {len(target_files)} real files...")
    print("    (Watch Shannon Entropy spike from normal ~4.5 to ~7.9 across all document formats)\n")

    encrypted_count = 0
    for file_path in target_files:
        if encrypt_file_simulated(file_path):
            encrypted_count += 1
            if encrypted_count % 8 == 0 or encrypted_count == len(target_files):
                print(f"  [*] Encrypted {encrypted_count}/{len(target_files)} files (including {file_path.suffix})...")
            if delay > 0:
                time.sleep(delay)

    print(f"[OK] Cryptographic overwrite complete on {encrypted_count} enterprise documents.")

    print(f"\n[!] STAGE 2: Mass extension alteration (appending {target_extension})...\n")

    renamed_count = 0
    for file_path in target_files:
        if file_path.exists():
            new_path = file_path.with_name(f"{file_path.name}{target_extension}")
            try:
                file_path.rename(new_path)
                renamed_count += 1
                if renamed_count % 8 == 0 or renamed_count == len(target_files):
                    print(f"  [*] Altered extension: {file_path.name} -> {new_path.name}")
                if delay > 0:
                    time.sleep(delay)
            except OSError:
                pass

    print(f"[OK] Altered extensions of {renamed_count} files.")

    # Stage 3: Drop Simulated Ransom Note
    ransom_note = target_path / "README_RESTORE_FILES.txt"
    ransom_note.write_text(
        "======================================================================\n"
        "           !!! YOUR ENTERPRISE FILES HAVE BEEN ENCRYPTED !!!          \n"
        "======================================================================\n"
        "All your PDF, DOCX, CSV, PNG, and database records have been locked\n"
        "using AES-256 and RSA-4096 encryption.\n\n"
        "This is an academic simulation demonstrating File Telemetry Early-Warning.\n"
        "No real systems were compromised.\n"
        "======================================================================\n",
        encoding="utf-8"
    )
    print(f"\n[!] STAGE 3: Dropped simulated ransom note ({ransom_note.name}).")

    print("\n[OK] Real-world ransomware attack simulation completed.")
    print("=" * 70)


# --------------------------------------------------
# CLEANUP
# --------------------------------------------------

def cleanup(target_dir=None):
    """
    Safely removes generated simulated files from the target directory.
    """
    target_path = Path(target_dir) if target_dir else DEFAULT_TARGET_DIR
    if not target_path.exists():
        print(f"[OK] Directory {target_path} does not exist. Nothing to clean.")
        return

    print(f"\n[+] Cleaning test files from: {target_path.resolve()}...")

    deleted = 0
    for file_path in list(target_path.iterdir()):
        if file_path.is_file():
            try:
                file_path.unlink()
                deleted += 1
            except OSError:
                pass

    print(f"[OK] Removed {deleted} test files. Folder clean.")


# --------------------------------------------------
# INTERACTIVE CLI MENU
# --------------------------------------------------

def main():
    while True:
        print("\n" + "=" * 65)
        print("    REAL-WORLD MULTI-FORMAT RANSOMWARE WORKLOAD SIMULATOR")
        print("=" * 65)
        print(" 1. Run Normal Office Activity (Benign Multi-Format Baseline)")
        print(" 2. Run Real Ransomware Attack (PDF, DOCX, CSV, PNG, JSON Overwrites)")
        print(" 3. Populate Directory with Fresh Enterprise Files")
        print(" 4. Clean Up Folder")
        print(" 5. Exit")

        choice = input("\nSelect an option [1-5]: ").strip()

        if choice == "1":
            normal_activity()
        elif choice == "2":
            suspicious_activity()
        elif choice == "3":
            populate_real_world_files(DEFAULT_TARGET_DIR)
        elif choice == "4":
            cleanup()
        elif choice == "5":
            print("Exiting simulator.")
            break
        else:
            print("[!] Invalid option. Please select 1-5.")


if __name__ == "__main__":
    main()
