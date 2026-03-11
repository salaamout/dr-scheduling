#!/usr/bin/env python3
"""
Generate a test database and stash it as a backup.

The backup is named with a plausible but old-looking timestamp so it blends
into the list on the Backups page.  To load it, go to the Backups page and
restore the file dated 2024-07-04 03:33:33.

After building the DB in the project's instance/backups/ folder, the script
also copies it into the PyInstaller desktop-app backup directories (if they
exist) and backdates the mtime so the file sorts to the bottom of every
backup list.

Usage
-----
    python scripts/seed_test_db.py          # from the project root
"""

import os
import shutil
import sqlite3
import sys
from datetime import date, datetime

# ---------------------------------------------------------------------------
# Where the file goes
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(BASE_DIR, "instance", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

# Timestamp chosen to look like a routine backup from a long time ago
DB_NAME = "patients_20240704_033333.db"
DB_PATH = os.path.join(BACKUP_DIR, DB_NAME)

# Desktop-app backup directories produced by PyInstaller
DESKTOP_BACKUP_DIRS = [
    os.path.join(BASE_DIR, "dist", "PatientDatabase", "_internal", "instance", "backups"),
    os.path.join(BASE_DIR, "dist", "PatientDatabase.app", "Contents", "Resources", "instance", "backups"),
]


# ---------------------------------------------------------------------------
# Test data — unique patients for each surgery day
# ---------------------------------------------------------------------------

SURGERY_DATES = [
    date(2026, 3, 16),  # Monday
    date(2026, 3, 18),  # Wednesday
    date(2026, 3, 20),  # Friday
]

# Each day has its own set of patients across all surgery types.
# day_index -> surgery_type -> list of patient dicts
PATIENTS_BY_DAY = {
    # =================================================================
    # DAY 1 — Monday, March 16
    # =================================================================
    0: {
        "cataract": [
            {
                "chart_number": "C-4401",
                "name": "Maria Elena Gutierrez",
                "age": 72,
                "sex": "F",
                "eye": "OD",
                "procedure": "Cataract",
                "advocate": "Rosa",
                "community": "San Pedro",
                "notes": "Mature cataract, VA 20/400",
            },
            {
                "chart_number": "C-4402",
                "name": "Jorge Luis Mendoza",
                "age": 65,
                "sex": "M",
                "eye": "OS",
                "procedure": "Cataract",
                "advocate": "Carlos",
                "community": "El Progreso",
                "notes": "",
            },
            {
                "chart_number": "C-4403",
                "name": "Ana Patricia Reyes",
                "age": 58,
                "sex": "F",
                "eye": "OU",
                "procedure": "Bilateral Lenses",
                "advocate": "Maria",
                "community": "La Ceiba",
                "notes": "Bilateral procedure requested",
            },
        ],
        "plastics": [
            {
                "chart_number": "P-2201",
                "name": "Roberto Carlos Diaz",
                "age": 44,
                "sex": "M",
                "eye": "OD",
                "procedure": "Ptosis repair",
                "advocate": "Luis",
                "community": "Tegucigalpa",
                "notes": "Right upper lid ptosis, MRD1 1mm",
            },
            {
                "chart_number": "P-2202",
                "name": "Carmen Sofia Alvarez",
                "age": 31,
                "sex": "F",
                "eye": "OS",
                "procedure": "DCR",
                "advocate": "Rosa",
                "community": "Comayagua",
                "notes": "Chronic dacryocystitis left side",
            },
        ],
        "strabismus": [
            {
                "chart_number": "S-1101",
                "name": "Isabella Martinez Lopez",
                "age": 5,
                "sex": "F",
                "eye": "OS",
                "procedure": "Strabismus — bilateral MR recession",
                "advocate": "Carlos",
                "community": "San Pedro",
                "notes": "Left esotropia 30PD",
            },
            {
                "chart_number": "S-1102",
                "name": "Diego Alejandro Ramos",
                "age": 12,
                "sex": "M",
                "eye": "OD",
                "procedure": "Strabismus — LR resection",
                "advocate": "Maria",
                "community": "El Progreso",
                "notes": "Right exotropia intermittent",
            },
        ],
        "pterygium": [
            {
                "chart_number": "T-3301",
                "name": "Manuel Antonio Flores",
                "age": 55,
                "sex": "M",
                "eye": "OD",
                "procedure": "Pterygium excision with conjunctival autograft",
                "advocate": "Elena",
                "community": "Tegucigalpa",
                "notes": "Grade III nasal pterygium, approaching visual axis",
            },
            {
                "chart_number": "T-3302",
                "name": "Lucia Fernanda Castillo",
                "age": 48,
                "sex": "F",
                "eye": "OS",
                "procedure": "Pterygium excision with AMT",
                "advocate": "Rosa",
                "community": "Comayagua",
                "notes": "Recurrent pterygium left eye",
            },
        ],
        "derm": [
            {
                "chart_number": "D-5501",
                "name": "Gloria Isabel Morales",
                "age": 70,
                "sex": "F",
                "eye": "",
                "procedure": "Excision of basal cell carcinoma lower lid",
                "advocate": "Maria",
                "community": "San Pedro",
                "notes": "Biopsy-proven BCC, 8mm nodular lesion",
            },
            {
                "chart_number": "D-5502",
                "name": "Hector Raul Pineda",
                "age": 38,
                "sex": "M",
                "eye": "",
                "procedure": "Chalazion incision and curettage",
                "advocate": "Luis",
                "community": "El Progreso",
                "notes": "",
            },
        ],
    },
    # =================================================================
    # DAY 2 — Wednesday, March 18
    # =================================================================
    1: {
        "cataract": [
            {
                "chart_number": "C-4410",
                "name": "Rosa Amelia Villanueva",
                "age": 78,
                "sex": "F",
                "eye": "OS",
                "procedure": "Cataract",
                "advocate": "Elena",
                "community": "Comayagua",
                "notes": "Dense nuclear sclerosis, VA CF 3ft",
            },
            {
                "chart_number": "C-4411",
                "name": "Ernesto Rafael Padilla",
                "age": 69,
                "sex": "M",
                "eye": "OD",
                "procedure": "Cataract",
                "advocate": "Luis",
                "community": "Choluteca",
                "notes": "Posterior subcapsular cataract",
            },
            {
                "chart_number": "C-4412",
                "name": "Blanca Estela Romero",
                "age": 61,
                "sex": "F",
                "eye": "OD",
                "procedure": "Cataract",
                "advocate": "Carlos",
                "community": "Tegucigalpa",
                "notes": "Cortical cataract, VA 20/200",
            },
            {
                "chart_number": "C-4413",
                "name": "Oscar Danilo Umanzor",
                "age": 74,
                "sex": "M",
                "eye": "OU",
                "procedure": "Bilateral Lenses",
                "advocate": "Rosa",
                "community": "San Pedro",
                "notes": "Bilateral mature cataracts, VA HM both eyes",
            },
        ],
        "plastics": [
            {
                "chart_number": "P-2210",
                "name": "Xiomara Beatriz Canales",
                "age": 52,
                "sex": "F",
                "eye": "OU",
                "procedure": "Bilateral upper lid blepharoplasty",
                "advocate": "Maria",
                "community": "La Ceiba",
                "notes": "Dermatochalasis obstructing superior visual field",
            },
            {
                "chart_number": "P-2211",
                "name": "Luis Fernando Zelaya",
                "age": 28,
                "sex": "M",
                "eye": "OD",
                "procedure": "Entropion repair",
                "advocate": "Elena",
                "community": "El Progreso",
                "notes": "Cicatricial entropion right lower lid, trichiasis",
            },
            {
                "chart_number": "P-2212",
                "name": "Karla Vanessa Soto",
                "age": 9,
                "sex": "F",
                "eye": "OS",
                "procedure": "Dermoid cyst excision",
                "advocate": "Carlos",
                "community": "Comayagua",
                "notes": "Dermoid cyst left lateral brow",
            },
        ],
        "strabismus": [
            {
                "chart_number": "S-1110",
                "name": "Andres Felipe Ochoa",
                "age": 8,
                "sex": "M",
                "eye": "OU",
                "procedure": "Strabismus — bilateral IR recession",
                "advocate": "Rosa",
                "community": "Tegucigalpa",
                "notes": "A-pattern esotropia with DVD",
            },
            {
                "chart_number": "S-1111",
                "name": "Camila Alejandra Bonilla",
                "age": 4,
                "sex": "F",
                "eye": "OS",
                "procedure": "Strabismus — MR recession + LR resection",
                "advocate": "Luis",
                "community": "San Pedro",
                "notes": "Left esotropia 25PD, amblyopia",
            },
        ],
        "pterygium": [
            {
                "chart_number": "T-3310",
                "name": "Santos David Euceda",
                "age": 60,
                "sex": "M",
                "eye": "OU",
                "procedure": "Bilateral pterygium excision with conjunctival autograft",
                "advocate": "Maria",
                "community": "Choluteca",
                "notes": "Bilateral nasal pterygia, Grade II",
            },
            {
                "chart_number": "T-3311",
                "name": "Reina Patricia Fuentes",
                "age": 42,
                "sex": "F",
                "eye": "OD",
                "procedure": "Pterygium excision with conjunctival autograft",
                "advocate": "Elena",
                "community": "La Ceiba",
                "notes": "Primary pterygium right eye",
            },
            {
                "chart_number": "T-3312",
                "name": "Bayardo Jose Figueroa",
                "age": 51,
                "sex": "M",
                "eye": "OS",
                "procedure": "Pterygium excision with mitomycin C",
                "advocate": "Carlos",
                "community": "El Progreso",
                "notes": "Recurrent pterygium, prior surgery 2024",
            },
        ],
        "derm": [
            {
                "chart_number": "D-5510",
                "name": "Miriam Yolanda Bautista",
                "age": 66,
                "sex": "F",
                "eye": "",
                "procedure": "Excision of squamous cell carcinoma lower lid",
                "advocate": "Rosa",
                "community": "San Pedro",
                "notes": "Ulcerated lesion 10mm, lower lid margin",
            },
            {
                "chart_number": "D-5511",
                "name": "Julio Cesar Maradiaga",
                "age": 45,
                "sex": "M",
                "eye": "",
                "procedure": "Incision and drainage of lid abscess",
                "advocate": "Luis",
                "community": "Tegucigalpa",
                "notes": "Preseptal abscess left upper lid",
            },
        ],
    },
    # =================================================================
    # DAY 3 — Friday, March 20
    # =================================================================
    2: {
        "cataract": [
            {
                "chart_number": "C-4420",
                "name": "Teresa de Jesus Contreras",
                "age": 80,
                "sex": "F",
                "eye": "OD",
                "procedure": "Cataract — SICS",
                "advocate": "Maria",
                "community": "Choluteca",
                "notes": "Hypermature white cataract, VA LP only",
            },
            {
                "chart_number": "C-4421",
                "name": "Rigoberto Antonio Lainez",
                "age": 67,
                "sex": "M",
                "eye": "OS",
                "procedure": "Cataract",
                "advocate": "Elena",
                "community": "San Pedro",
                "notes": "Mixed cataract, VA 20/100",
            },
            {
                "chart_number": "C-4422",
                "name": "Juana Francisca Portillo",
                "age": 73,
                "sex": "F",
                "eye": "OD",
                "procedure": "Cataract",
                "advocate": "Rosa",
                "community": "La Ceiba",
                "notes": "Brunescent cataract, VA 20/400",
            },
        ],
        "plastics": [
            {
                "chart_number": "P-2220",
                "name": "Edwin Josue Henriquez",
                "age": 36,
                "sex": "M",
                "eye": "OD",
                "procedure": "Ectropion repair",
                "advocate": "Carlos",
                "community": "Tegucigalpa",
                "notes": "Involutional ectropion right lower lid",
            },
            {
                "chart_number": "P-2221",
                "name": "Lourdes Carolina Murillo",
                "age": 55,
                "sex": "F",
                "eye": "OU",
                "procedure": "Bilateral ptosis repair — frontalis sling",
                "advocate": "Luis",
                "community": "El Progreso",
                "notes": "Bilateral severe ptosis, MRD1 0mm OU, poor LF",
            },
            {
                "chart_number": "P-2222",
                "name": "Daniel Esteban Paz",
                "age": 14,
                "sex": "M",
                "eye": "OS",
                "procedure": "Laceration repair",
                "advocate": "Maria",
                "community": "San Pedro",
                "notes": "Full-thickness lid laceration involving margin",
            },
        ],
        "strabismus": [
            {
                "chart_number": "S-1120",
                "name": "Sofia Valentina Orellana",
                "age": 6,
                "sex": "F",
                "eye": "OD",
                "procedure": "Strabismus — IO myectomy",
                "advocate": "Elena",
                "community": "Comayagua",
                "notes": "Right inferior oblique overaction",
            },
            {
                "chart_number": "S-1121",
                "name": "Gabriel Alejandro Nunez",
                "age": 10,
                "sex": "M",
                "eye": "OU",
                "procedure": "Strabismus — bilateral LR recession",
                "advocate": "Rosa",
                "community": "Choluteca",
                "notes": "Intermittent exotropia 35PD at distance",
            },
            {
                "chart_number": "S-1122",
                "name": "Valeria Nicole Duarte",
                "age": 2,
                "sex": "F",
                "eye": "OS",
                "procedure": "EUA + Strabismus",
                "advocate": "Carlos",
                "community": "La Ceiba",
                "notes": "Infantile esotropia, EUA for refraction",
            },
        ],
        "pterygium": [
            {
                "chart_number": "T-3320",
                "name": "Marvin Orlando Avila",
                "age": 58,
                "sex": "M",
                "eye": "OD",
                "procedure": "Pterygium excision with conjunctival rotational flap",
                "advocate": "Luis",
                "community": "San Pedro",
                "notes": "Large pterygium 5mm past limbus",
            },
        ],
        "derm": [
            {
                "chart_number": "D-5520",
                "name": "Sandra Patricia Mejia",
                "age": 25,
                "sex": "F",
                "eye": "",
                "procedure": "Excisional biopsy of lid lesion",
                "advocate": "Maria",
                "community": "La Ceiba",
                "notes": "Suspicious pigmented lesion upper lid margin",
            },
            {
                "chart_number": "D-5521",
                "name": "Wilfredo Noe Castellanos",
                "age": 59,
                "sex": "M",
                "eye": "",
                "procedure": "Excision of sebaceous cyst",
                "advocate": "Elena",
                "community": "Comayagua",
                "notes": "Large sebaceous cyst medial canthus",
            },
            {
                "chart_number": "D-5522",
                "name": "Olga Marina Barahona",
                "age": 71,
                "sex": "F",
                "eye": "",
                "procedure": "Excision of papilloma",
                "advocate": "Carlos",
                "community": "Tegucigalpa",
                "notes": "Pedunculated papilloma right lower lid",
            },
        ],
    },
}


def build_db():
    """Create a SQLite database matching the Patient model schema."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Mirror the SQLAlchemy Patient model exactly
    cur.execute(
        """
        CREATE TABLE patient (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            surgery_type VARCHAR(50)  NOT NULL,
            surgery_date DATE         NOT NULL,
            chart_number VARCHAR(50)  NOT NULL,
            name         VARCHAR(240) NOT NULL,
            age          INTEGER      NOT NULL,
            sex          VARCHAR(10)  NOT NULL,
            eye          VARCHAR(2),
            procedure    TEXT         NOT NULL,
            advocate     VARCHAR(120),
            community    VARCHAR(120),
            number       VARCHAR(50),
            notes        TEXT,
            deleted      BOOLEAN      NOT NULL DEFAULT 0,
            cancelled    BOOLEAN      NOT NULL DEFAULT 0
        )
        """
    )

    surgery_number = 1
    total_records = 0
    for day_idx, surg_date in enumerate(SURGERY_DATES):
        day_patients = PATIENTS_BY_DAY[day_idx]
        for stype, patients in day_patients.items():
            for p in patients:
                cur.execute(
                    """
                    INSERT INTO patient
                        (surgery_type, surgery_date, chart_number, name,
                         age, sex, eye, procedure, advocate, community,
                         number, notes, deleted, cancelled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
                    """,
                    (
                        stype,
                        surg_date.isoformat(),
                        p["chart_number"],
                        p["name"],
                        p["age"],
                        p["sex"],
                        p["eye"] or None,
                        p["procedure"],
                        p["advocate"],
                        p["community"],
                        str(surgery_number),
                        p["notes"] or None,
                    ),
                )
                surgery_number += 1
                total_records += 1

    conn.commit()
    conn.close()

    # Backdate the file's modification time to match the filename so it
    # appears with the old timestamp on the Backups page (which reads mtime).
    fake_mtime = datetime(2024, 7, 4, 3, 33, 33).timestamp()
    os.utime(DB_PATH, (fake_mtime, fake_mtime))

    print(f"✅ Test database created: {DB_PATH}")
    print(f"   {total_records} patient records across {len(SURGERY_DATES)} surgery days")
    print(f"   Filename: {DB_NAME}")

    # ------------------------------------------------------------------
    # Copy into desktop-app backup directories (if they exist)
    # ------------------------------------------------------------------
    for dest_dir in DESKTOP_BACKUP_DIRS:
        if os.path.isdir(dest_dir):
            dest_path = os.path.join(dest_dir, DB_NAME)
            shutil.copy2(DB_PATH, dest_path)
            # Ensure the copy also has the backdated mtime
            os.utime(dest_path, (fake_mtime, fake_mtime))
            print(f"   ↳ Copied to {dest_path}")

    print()
    print("To load it:")
    print("  1. Open the app and go to the Backups page")
    print("  2. Scroll to the very bottom of the backup list")
    print("  3. Find the backup dated 2024-07-04 03:33:33")
    print("  4. Click Restore")


if __name__ == "__main__":
    build_db()
