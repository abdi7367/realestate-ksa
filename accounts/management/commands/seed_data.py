"""
Management command: seed_data
Buraidah / Al-Qassim region — realistic KSA real-estate demo data.

Usage:
    python manage.py seed_data
    python manage.py seed_data --clear

Install:
    mkdir -p accounts/management/commands
    touch accounts/management/__init__.py
    touch accounts/management/commands/__init__.py
    cp seed_data.py accounts/management/commands/seed_data.py
"""

from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

User = get_user_model()


def d(val: str) -> Decimal:
    return Decimal(val)


# ─────────────────────────────────────────────────────────────────────────────
# 6 USERS
# ─────────────────────────────────────────────────────────────────────────────
USERS = [
    {
        "username": "admin_qassim",
        "password": "Admin@1234",
        "first_name": "عبدالعزيز",
        "last_name": "البريدي",
        "email": "admin@qassim-realestate.sa",
        "role": "admin",
        "phone": "+966163000001",
        "national_id": "1060000001",
        "is_staff": True,
        "is_superuser": True,
    },
    {
        "username": "pm_qassim",
        "password": "Manager@1234",
        "first_name": "فهد",
        "last_name": "الرشيدي",
        "email": "pm@qassim-realestate.sa",
        "role": "property_manager",
        "phone": "+966163000002",
        "national_id": "1060000002",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "username": "accountant_qassim1",
        "password": "Account@1234",
        "first_name": "نورة",
        "last_name": "العنزي",
        "email": "accountant1@qassim-realestate.sa",
        "role": "accountant",
        "phone": "+966163000003",
        "national_id": "1060000003",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "username": "accountant_qassim2",
        "password": "Account@5678",
        "first_name": "سلطان",
        "last_name": "الشمري",
        "email": "accountant2@qassim-realestate.sa",
        "role": "accountant",
        "phone": "+966163000004",
        "national_id": "1060000004",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "username": "finance_qassim",
        "password": "Finance@1234",
        "first_name": "منيرة",
        "last_name": "الدوسري",
        "email": "finance@qassim-realestate.sa",
        "role": "finance_manager",
        "phone": "+966163000005",
        "national_id": "1060000005",
        "is_staff": False,
        "is_superuser": False,
    },
    {
        "username": "pm_qassim2",
        "password": "Manager@5678",
        "first_name": "ماجد",
        "last_name": "القحطاني",
        "email": "pm2@qassim-realestate.sa",
        "role": "property_manager",
        "phone": "+966163000006",
        "national_id": "1060000006",
        "is_staff": False,
        "is_superuser": False,
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 12 PROPERTIES  — Buraidah, Unaizah, Al-Qassim
# ─────────────────────────────────────────────────────────────────────────────
PROPERTIES = [
    {
        "property_code": "BRD-001",
        "name": "برج الملك فهد التجاري",
        "property_type": "commercial",
        "city": "Buraidah",
        "district": "Al Olaya",
        "location": "طريق الملك فهد، حي العليا، بريدة",
        "size_sqm": d("5200.00"),
        "num_units": 8,
        "ownership_status": "Owned",
        "owner_full_name": "Ibrahim Saleh Al-Rashidi",
        "owner_national_id": "1061000001",
        "owner_phone": "+966501100001",
        "owner_email": "ibrahim@alrashidi-qassim.sa",
        "owner_bank_iban": "SA0380000000608010200001",
        "owner_address": "فيلا 5، حي الروضة، بريدة، القصيم",
        "units": [
            {"unit_number": "101", "floor": 1, "size_sqm": d("210.00"), "unit_type": "office", "monthly_rent": d("9500.00")},
            {"unit_number": "102", "floor": 1, "size_sqm": d("190.00"), "unit_type": "office", "monthly_rent": d("8500.00")},
            {"unit_number": "201", "floor": 2, "size_sqm": d("230.00"), "unit_type": "office", "monthly_rent": d("10500.00")},
            {"unit_number": "202", "floor": 2, "size_sqm": d("200.00"), "unit_type": "office", "monthly_rent": d("9000.00")},
            {"unit_number": "301", "floor": 3, "size_sqm": d("250.00"), "unit_type": "office", "monthly_rent": d("11500.00")},
            {"unit_number": "G01", "floor": 0, "size_sqm": d("140.00"), "unit_type": "shop", "monthly_rent": d("14000.00")},
            {"unit_number": "G02", "floor": 0, "size_sqm": d("120.00"), "unit_type": "shop", "monthly_rent": d("12000.00")},
            {"unit_number": "G03", "floor": 0, "size_sqm": d("110.00"), "unit_type": "shop", "monthly_rent": d("11000.00")},
        ],
    },
    {
        "property_code": "BRD-002",
        "name": "مجمع الروضة السكني",
        "property_type": "residential",
        "city": "Buraidah",
        "district": "Al Rawdah",
        "location": "شارع الأمير سلطان، حي الروضة، بريدة",
        "size_sqm": d("3800.00"),
        "num_units": 6,
        "ownership_status": "Owned",
        "owner_full_name": "Saad Nasser Al-Anzi",
        "owner_national_id": "1061000002",
        "owner_phone": "+966501100002",
        "owner_email": "saad@alanzi-prop.sa",
        "owner_bank_iban": "SA4420000001234567200002",
        "owner_address": "بريدة، حي النخيل، شارع الملك عبدالله",
        "units": [
            {"unit_number": "A-01", "floor": 1, "size_sqm": d("160.00"), "unit_type": "apartment", "monthly_rent": d("5800.00")},
            {"unit_number": "A-02", "floor": 1, "size_sqm": d("160.00"), "unit_type": "apartment", "monthly_rent": d("5800.00")},
            {"unit_number": "B-01", "floor": 2, "size_sqm": d("180.00"), "unit_type": "apartment", "monthly_rent": d("6500.00")},
            {"unit_number": "B-02", "floor": 2, "size_sqm": d("180.00"), "unit_type": "apartment", "monthly_rent": d("6500.00")},
            {"unit_number": "V-01", "floor": 1, "size_sqm": d("380.00"), "unit_type": "villa", "monthly_rent": d("16000.00")},
            {"unit_number": "V-02", "floor": 1, "size_sqm": d("360.00"), "unit_type": "villa", "monthly_rent": d("15000.00")},
        ],
    },
    {
        "property_code": "BRD-003",
        "name": "مستودعات الصناعية الأولى",
        "property_type": "industrial",
        "city": "Buraidah",
        "district": "Al Sinaiyah",
        "location": "المنطقة الصناعية الأولى، طريق بريدة–عنيزة",
        "size_sqm": d("12000.00"),
        "num_units": 4,
        "ownership_status": "Owned",
        "owner_full_name": "Turki Fahad Al-Mutairi",
        "owner_national_id": "1061000003",
        "owner_phone": "+966501100003",
        "owner_email": "turki@almutairi-ind.sa",
        "owner_bank_iban": "SA7180000000608010200003",
        "owner_address": "ص.ب 4421، بريدة، القصيم 51411",
        "units": [
            {"unit_number": "WH-A", "floor": 1, "size_sqm": d("3000.00"), "unit_type": "office", "monthly_rent": d("22000.00")},
            {"unit_number": "WH-B", "floor": 1, "size_sqm": d("3500.00"), "unit_type": "office", "monthly_rent": d("26000.00")},
            {"unit_number": "WH-C", "floor": 1, "size_sqm": d("2500.00"), "unit_type": "office", "monthly_rent": d("18000.00")},
            {"unit_number": "WH-D", "floor": 1, "size_sqm": d("3000.00"), "unit_type": "office", "monthly_rent": d("22000.00")},
        ],
    },
    {
        "property_code": "BRD-004",
        "name": "مركز النخيل التجاري",
        "property_type": "commercial",
        "city": "Buraidah",
        "district": "Al Nakhil",
        "location": "طريق الملك عبدالله، حي النخيل، بريدة",
        "size_sqm": d("4100.00"),
        "num_units": 7,
        "ownership_status": "Owned",
        "owner_full_name": "Khalid Mohammed Al-Shammari",
        "owner_national_id": "1061000004",
        "owner_phone": "+966501100004",
        "owner_email": "khalid@alshammari-qassim.sa",
        "owner_bank_iban": "SA5440000001234567200004",
        "owner_address": "فيلا 12، حي الملك فهد، بريدة",
        "units": [
            {"unit_number": "G01", "floor": 0, "size_sqm": d("180.00"), "unit_type": "shop", "monthly_rent": d("16000.00")},
            {"unit_number": "G02", "floor": 0, "size_sqm": d("160.00"), "unit_type": "shop", "monthly_rent": d("14500.00")},
            {"unit_number": "G03", "floor": 0, "size_sqm": d("140.00"), "unit_type": "shop", "monthly_rent": d("13000.00")},
            {"unit_number": "101", "floor": 1, "size_sqm": d("200.00"), "unit_type": "office", "monthly_rent": d("9000.00")},
            {"unit_number": "102", "floor": 1, "size_sqm": d("200.00"), "unit_type": "office", "monthly_rent": d("9000.00")},
            {"unit_number": "201", "floor": 2, "size_sqm": d("220.00"), "unit_type": "office", "monthly_rent": d("10000.00")},
            {"unit_number": "202", "floor": 2, "size_sqm": d("210.00"), "unit_type": "office", "monthly_rent": d("9500.00")},
        ],
    },
    {
        "property_code": "BRD-005",
        "name": "أبراج المطار السكنية",
        "property_type": "residential",
        "city": "Buraidah",
        "district": "Al Matar",
        "location": "شارع المطار، حي المطار، بريدة",
        "size_sqm": d("2900.00"),
        "num_units": 7,
        "ownership_status": "Owned",
        "owner_full_name": "Hind Abdul-Rahman Al-Qahtani",
        "owner_national_id": "1061000005",
        "owner_phone": "+966501100005",
        "owner_email": "hind@alqahtani-brd.sa",
        "owner_bank_iban": "SA0380000000608010200005",
        "owner_address": "حي المطار، بريدة، القصيم",
        "units": [
            {"unit_number": "101", "floor": 1, "size_sqm": d("120.00"), "unit_type": "apartment", "monthly_rent": d("4200.00")},
            {"unit_number": "102", "floor": 1, "size_sqm": d("120.00"), "unit_type": "apartment", "monthly_rent": d("4200.00")},
            {"unit_number": "103", "floor": 1, "size_sqm": d("130.00"), "unit_type": "apartment", "monthly_rent": d("4500.00")},
            {"unit_number": "201", "floor": 2, "size_sqm": d("140.00"), "unit_type": "apartment", "monthly_rent": d("4800.00")},
            {"unit_number": "202", "floor": 2, "size_sqm": d("140.00"), "unit_type": "apartment", "monthly_rent": d("4800.00")},
            {"unit_number": "301", "floor": 3, "size_sqm": d("150.00"), "unit_type": "apartment", "monthly_rent": d("5200.00")},
            {"unit_number": "302", "floor": 3, "size_sqm": d("150.00"), "unit_type": "apartment", "monthly_rent": d("5200.00")},
        ],
    },
    {
        "property_code": "BRD-006",
        "name": "مستودعات الصناعية الثانية",
        "property_type": "industrial",
        "city": "Buraidah",
        "district": "Al Sinaiyah 2",
        "location": "المنطقة الصناعية الثانية، طريق القصيم الدولي",
        "size_sqm": d("18000.00"),
        "num_units": 3,
        "ownership_status": "Owned",
        "owner_full_name": "Walid Salman Al-Harbi",
        "owner_national_id": "1061000006",
        "owner_phone": "+966501100006",
        "owner_email": "walid@alharbi-ind.sa",
        "owner_bank_iban": "SA4420000001234567200006",
        "owner_address": "المنطقة الصناعية، بريدة، القصيم 51421",
        "units": [
            {"unit_number": "IND-01", "floor": 1, "size_sqm": d("6000.00"), "unit_type": "office", "monthly_rent": d("38000.00")},
            {"unit_number": "IND-02", "floor": 1, "size_sqm": d("7000.00"), "unit_type": "office", "monthly_rent": d("44000.00")},
            {"unit_number": "IND-03", "floor": 1, "size_sqm": d("5000.00"), "unit_type": "office", "monthly_rent": d("32000.00")},
        ],
    },
    {
        "property_code": "BRD-007",
        "name": "فلل حي الملك فهد",
        "property_type": "residential",
        "city": "Buraidah",
        "district": "King Fahd District",
        "location": "شارع الأمير محمد بن عبدالعزيز، حي الملك فهد، بريدة",
        "size_sqm": d("6000.00"),
        "num_units": 5,
        "ownership_status": "Owned",
        "owner_full_name": "Sultan Ibrahim Al-Dosari",
        "owner_national_id": "1061000007",
        "owner_phone": "+966501100007",
        "owner_email": "sultan@aldosari-realty.sa",
        "owner_bank_iban": "SA7180000000608010200007",
        "owner_address": "فيلا 8، حي الملك فهد، بريدة",
        "units": [
            {"unit_number": "V-01", "floor": 1, "size_sqm": d("480.00"), "unit_type": "villa", "monthly_rent": d("21000.00")},
            {"unit_number": "V-02", "floor": 1, "size_sqm": d("460.00"), "unit_type": "villa", "monthly_rent": d("20000.00")},
            {"unit_number": "V-03", "floor": 1, "size_sqm": d("500.00"), "unit_type": "villa", "monthly_rent": d("22000.00")},
            {"unit_number": "V-04", "floor": 1, "size_sqm": d("440.00"), "unit_type": "villa", "monthly_rent": d("19000.00")},
            {"unit_number": "V-05", "floor": 1, "size_sqm": d("420.00"), "unit_type": "villa", "monthly_rent": d("18000.00")},
        ],
    },
    {
        "property_code": "BRD-008",
        "name": "برج الخليج للأعمال",
        "property_type": "commercial",
        "city": "Buraidah",
        "district": "Al Khalidiyah",
        "location": "طريق الخالدية، حي الخالدية، بريدة",
        "size_sqm": d("6500.00"),
        "num_units": 6,
        "ownership_status": "Owned",
        "owner_full_name": "Faisal Hamad Al-Bishi",
        "owner_national_id": "1061000008",
        "owner_phone": "+966501100008",
        "owner_email": "faisal@albishi-comm.sa",
        "owner_bank_iban": "SA5440000001234567200008",
        "owner_address": "مكتب 3، برج الخليج، بريدة",
        "units": [
            {"unit_number": "101", "floor": 1, "size_sqm": d("320.00"), "unit_type": "office", "monthly_rent": d("14500.00")},
            {"unit_number": "102", "floor": 1, "size_sqm": d("300.00"), "unit_type": "office", "monthly_rent": d("13500.00")},
            {"unit_number": "201", "floor": 2, "size_sqm": d("350.00"), "unit_type": "office", "monthly_rent": d("16000.00")},
            {"unit_number": "202", "floor": 2, "size_sqm": d("330.00"), "unit_type": "office", "monthly_rent": d("15000.00")},
            {"unit_number": "301", "floor": 3, "size_sqm": d("400.00"), "unit_type": "office", "monthly_rent": d("18000.00")},
            {"unit_number": "G01", "floor": 0, "size_sqm": d("160.00"), "unit_type": "shop", "monthly_rent": d("15000.00")},
        ],
    },
    {
        "property_code": "ANZ-001",
        "name": "مجمع عنيزة التجاري",
        "property_type": "commercial",
        "city": "Unaizah",
        "district": "Al Markaz",
        "location": "شارع الملك سعود، المركز، عنيزة، القصيم",
        "size_sqm": d("3600.00"),
        "num_units": 5,
        "ownership_status": "Owned",
        "owner_full_name": "Nasser Khalid Al-Subaie",
        "owner_national_id": "1061000009",
        "owner_phone": "+966501100009",
        "owner_email": "nasser@alsubaie-unz.sa",
        "owner_bank_iban": "SA0380000000608010200009",
        "owner_address": "حي النزهة، عنيزة، القصيم",
        "units": [
            {"unit_number": "G01", "floor": 0, "size_sqm": d("200.00"), "unit_type": "shop", "monthly_rent": d("17000.00")},
            {"unit_number": "G02", "floor": 0, "size_sqm": d("180.00"), "unit_type": "shop", "monthly_rent": d("15500.00")},
            {"unit_number": "101", "floor": 1, "size_sqm": d("220.00"), "unit_type": "office", "monthly_rent": d("9500.00")},
            {"unit_number": "102", "floor": 1, "size_sqm": d("210.00"), "unit_type": "office", "monthly_rent": d("9000.00")},
            {"unit_number": "201", "floor": 2, "size_sqm": d("240.00"), "unit_type": "office", "monthly_rent": d("10500.00")},
        ],
    },
    {
        "property_code": "ANZ-002",
        "name": "شقق النزهة السكنية",
        "property_type": "residential",
        "city": "Unaizah",
        "district": "Al Nuzhah",
        "location": "حي النزهة، شارع الأمير عبدالله، عنيزة",
        "size_sqm": d("2400.00"),
        "num_units": 5,
        "ownership_status": "Owned",
        "owner_full_name": "Reem Fahad Al-Rashidi",
        "owner_national_id": "1061000010",
        "owner_phone": "+966501100010",
        "owner_email": "reem@alrashidi-res.sa",
        "owner_bank_iban": "SA4420000001234567200010",
        "owner_address": "فيلا 3، حي النزهة، عنيزة",
        "units": [
            {"unit_number": "101", "floor": 1, "size_sqm": d("130.00"), "unit_type": "apartment", "monthly_rent": d("4500.00")},
            {"unit_number": "102", "floor": 1, "size_sqm": d("130.00"), "unit_type": "apartment", "monthly_rent": d("4500.00")},
            {"unit_number": "201", "floor": 2, "size_sqm": d("150.00"), "unit_type": "apartment", "monthly_rent": d("5000.00")},
            {"unit_number": "202", "floor": 2, "size_sqm": d("150.00"), "unit_type": "apartment", "monthly_rent": d("5000.00")},
            {"unit_number": "301", "floor": 3, "size_sqm": d("170.00"), "unit_type": "apartment", "monthly_rent": d("5500.00")},
        ],
    },
    {
        "property_code": "BRD-009",
        "name": "مستودع الأغذية المركزي",
        "property_type": "industrial",
        "city": "Buraidah",
        "district": "Al Sinaiyah",
        "location": "المنطقة الصناعية، بجوار مصنع الألبان، بريدة",
        "size_sqm": d("9000.00"),
        "num_units": 3,
        "ownership_status": "Owned",
        "owner_full_name": "Ahmed Ali Al-Zahrany",
        "owner_national_id": "1061000011",
        "owner_phone": "+966501100011",
        "owner_email": "ahmed@alzahrany-ind.sa",
        "owner_bank_iban": "SA7180000000608010200011",
        "owner_address": "المنطقة الصناعية، بريدة 51411",
        "units": [
            {"unit_number": "COLD-A", "floor": 1, "size_sqm": d("2500.00"), "unit_type": "office", "monthly_rent": d("28000.00")},
            {"unit_number": "DRY-B", "floor": 1, "size_sqm": d("3500.00"), "unit_type": "office", "monthly_rent": d("32000.00")},
            {"unit_number": "DRY-C", "floor": 1, "size_sqm": d("3000.00"), "unit_type": "office", "monthly_rent": d("27000.00")},
        ],
    },
    {
        "property_code": "BRD-010",
        "name": "مجمع الياسمين السكني",
        "property_type": "residential",
        "city": "Buraidah",
        "district": "Al Yasmeen",
        "location": "حي الياسمين، طريق الأمير نايف، بريدة",
        "size_sqm": d("3100.00"),
        "num_units": 6,
        "ownership_status": "Owned",
        "owner_full_name": "Bandar Nasser Al-Otaibi",
        "owner_national_id": "1061000012",
        "owner_phone": "+966501100012",
        "owner_email": "bandar@alotaibi-yasmeen.sa",
        "owner_bank_iban": "SA5440000001234567200012",
        "owner_address": "حي الياسمين، شارع الورود، بريدة",
        "units": [
            {"unit_number": "101", "floor": 1, "size_sqm": d("145.00"), "unit_type": "apartment", "monthly_rent": d("5000.00")},
            {"unit_number": "102", "floor": 1, "size_sqm": d("145.00"), "unit_type": "apartment", "monthly_rent": d("5000.00")},
            {"unit_number": "201", "floor": 2, "size_sqm": d("165.00"), "unit_type": "apartment", "monthly_rent": d("5600.00")},
            {"unit_number": "202", "floor": 2, "size_sqm": d("165.00"), "unit_type": "apartment", "monthly_rent": d("5600.00")},
            {"unit_number": "V-01", "floor": 1, "size_sqm": d("400.00"), "unit_type": "villa", "monthly_rent": d("17500.00")},
            {"unit_number": "V-02", "floor": 1, "size_sqm": d("380.00"), "unit_type": "villa", "monthly_rent": d("16500.00")},
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 20 CONTRACTS
# ─────────────────────────────────────────────────────────────────────────────
TENANTS_CONTRACTS = [
    {
        "tenant": {"full_name": "محمد عبدالله الرشيدي", "national_id": "1062000001", "phone": "+966503100001", "email": "m.alrashidi@brd-tech.sa", "nationality": "Saudi", "date_of_birth": date(1982, 4, 10)},
        "property_code": "BRD-001", "unit_number": "101",
        "monthly_rent": d("9500.00"), "start_date": date(2025, 1, 1), "duration_months": 12,
        "payment_schedule": "monthly", "security_deposit": d("9500.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("10925.00"), "payment_date": date(2025, 1, 3), "due_date": date(2025, 1, 1), "method": "bank_transfer"},
            {"amount": d("10925.00"), "payment_date": date(2025, 2, 2), "due_date": date(2025, 2, 1), "method": "bank_transfer"},
            {"amount": d("10925.00"), "payment_date": date(2025, 3, 3), "due_date": date(2025, 3, 1), "method": "bank_transfer"},
            {"amount": d("10925.00"), "payment_date": date(2025, 4, 1), "due_date": date(2025, 4, 1), "method": "bank_transfer"},
        ],
    },
    {
        "tenant": {"full_name": "سارة خالد العنزي", "national_id": "1062000002", "phone": "+966503100002", "email": "sara.alanzi@consult.sa", "nationality": "Saudi", "date_of_birth": date(1990, 9, 22)},
        "property_code": "BRD-001", "unit_number": "102",
        "monthly_rent": d("8500.00"), "start_date": date(2024, 10, 1), "duration_months": 12,
        "payment_schedule": "monthly", "security_deposit": d("8500.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("9775.00"), "payment_date": date(2024, 10, 1), "due_date": date(2024, 10, 1), "method": "bank_transfer"},
            {"amount": d("9775.00"), "payment_date": date(2024, 11, 3), "due_date": date(2024, 11, 1), "method": "bank_transfer"},
            {"amount": d("9775.00"), "payment_date": date(2024, 12, 2), "due_date": date(2024, 12, 1), "method": "bank_transfer"},
            {"amount": d("9775.00"), "payment_date": date(2025, 1, 5), "due_date": date(2025, 1, 1), "method": "bank_transfer"},
            {"amount": d("9775.00"), "payment_date": date(2025, 2, 4), "due_date": date(2025, 2, 1), "method": "bank_transfer"},
        ],
    },
    {
        "tenant": {"full_name": "فهد ناصر الشمري", "national_id": "1062000003", "phone": "+966503100003", "email": "fahad.alshammari@trading.sa", "nationality": "Saudi", "date_of_birth": date(1978, 6, 15)},
        "property_code": "BRD-001", "unit_number": "201",
        "monthly_rent": d("10500.00"), "start_date": date(2025, 1, 1), "duration_months": 24,
        "payment_schedule": "quarterly", "security_deposit": d("21000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("36172.50"), "payment_date": date(2025, 1, 1), "due_date": date(2025, 1, 1), "method": "cheque"},
            {"amount": d("36172.50"), "payment_date": date(2025, 4, 2), "due_date": date(2025, 4, 1), "method": "cheque"},
        ],
    },
    {
        "tenant": {"full_name": "نورة سعد القحطاني", "national_id": "1062000004", "phone": "+966503100004", "email": "noura.qassim@gmail.com", "nationality": "Saudi", "date_of_birth": date(1993, 2, 28)},
        "property_code": "BRD-002", "unit_number": "A-01",
        "monthly_rent": d("5800.00"), "start_date": date(2025, 2, 1), "duration_months": 12,
        "payment_schedule": "monthly", "security_deposit": d("5800.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("6670.00"), "payment_date": date(2025, 2, 1), "due_date": date(2025, 2, 1), "method": "cash"},
            {"amount": d("6670.00"), "payment_date": date(2025, 3, 4), "due_date": date(2025, 3, 1), "method": "cash"},
            {"amount": d("6670.00"), "payment_date": date(2025, 4, 6), "due_date": date(2025, 4, 1), "method": "cash"},
        ],
    },
    {
        "tenant": {"full_name": "عبدالرحمن علي الدوسري", "national_id": "1062000005", "phone": "+966503100005", "email": "ar.aldosari@outlook.com", "nationality": "Saudi", "date_of_birth": date(1985, 11, 3)},
        "property_code": "BRD-002", "unit_number": "A-02",
        "monthly_rent": d("5800.00"), "start_date": date(2024, 8, 1), "duration_months": 12,
        "payment_schedule": "monthly", "security_deposit": d("5800.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("6670.00"), "payment_date": date(2024, 8, 1), "due_date": date(2024, 8, 1), "method": "bank_transfer"},
            {"amount": d("6670.00"), "payment_date": date(2024, 9, 2), "due_date": date(2024, 9, 1), "method": "bank_transfer"},
            {"amount": d("6670.00"), "payment_date": date(2024, 10, 3), "due_date": date(2024, 10, 1), "method": "bank_transfer"},
            {"amount": d("6670.00"), "payment_date": date(2024, 11, 1), "due_date": date(2024, 11, 1), "method": "bank_transfer"},
            {"amount": d("6670.00"), "payment_date": date(2024, 12, 5), "due_date": date(2024, 12, 1), "method": "bank_transfer"},
            {"amount": d("6670.00"), "payment_date": date(2025, 1, 7), "due_date": date(2025, 1, 1), "method": "bank_transfer"},
        ],
    },
    {
        "tenant": {"full_name": "بندر محمد المطيري", "national_id": "1062000006", "phone": "+966503100006", "email": "bandar.almutairi@logistics.sa", "nationality": "Saudi", "date_of_birth": date(1975, 7, 19)},
        "property_code": "BRD-003", "unit_number": "WH-A",
        "monthly_rent": d("22000.00"), "start_date": date(2024, 7, 1), "duration_months": 24,
        "payment_schedule": "annual", "security_deposit": d("44000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("304920.00"), "payment_date": date(2024, 7, 1), "due_date": date(2024, 7, 1), "method": "bank_transfer"},
        ],
    },
    {
        "tenant": {"full_name": "منى عبدالله البشي", "national_id": "1062000007", "phone": "+966503100007", "email": "mona.albishi@food.sa", "nationality": "Saudi", "date_of_birth": date(1988, 3, 14)},
        "property_code": "BRD-003", "unit_number": "WH-B",
        "monthly_rent": d("26000.00"), "start_date": date(2025, 1, 1), "duration_months": 12,
        "payment_schedule": "semi_annual", "security_deposit": d("52000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("179400.00"), "payment_date": date(2025, 1, 1), "due_date": date(2025, 1, 1), "method": "cheque"},
        ],
    },
    {
        "tenant": {"full_name": "وليد فهد الحربي", "national_id": "1062000008", "phone": "+966503100008", "email": "walid.alharbi@retail.sa", "nationality": "Saudi", "date_of_birth": date(1980, 12, 5)},
        "property_code": "BRD-004", "unit_number": "G01",
        "monthly_rent": d("16000.00"), "start_date": date(2024, 6, 1), "duration_months": 24,
        "payment_schedule": "quarterly", "security_deposit": d("32000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("55200.00"), "payment_date": date(2024, 6, 1), "due_date": date(2024, 6, 1), "method": "cheque"},
            {"amount": d("55200.00"), "payment_date": date(2024, 9, 1), "due_date": date(2024, 9, 1), "method": "cheque"},
            {"amount": d("55200.00"), "payment_date": date(2024, 12, 2), "due_date": date(2024, 12, 1), "method": "cheque"},
            {"amount": d("55200.00"), "payment_date": date(2025, 3, 3), "due_date": date(2025, 3, 1), "method": "cheque"},
        ],
    },
    {
        "tenant": {"full_name": "هند إبراهيم الزهراني", "national_id": "1062000009", "phone": "+966503100009", "email": "hind.alzahrany@pharmacy.sa", "nationality": "Saudi", "date_of_birth": date(1987, 8, 30)},
        "property_code": "BRD-004", "unit_number": "G02",
        "monthly_rent": d("14500.00"), "start_date": date(2025, 3, 1), "duration_months": 12,
        "payment_schedule": "monthly", "security_deposit": d("14500.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("16675.00"), "payment_date": date(2025, 3, 1), "due_date": date(2025, 3, 1), "method": "bank_transfer"},
            {"amount": d("16675.00"), "payment_date": date(2025, 4, 3), "due_date": date(2025, 4, 1), "method": "bank_transfer"},
        ],
    },
    {
        "tenant": {"full_name": "تركي سلمان العتيبي", "national_id": "1062000010", "phone": "+966503100010", "email": "turki.alotaibi@insurance.sa", "nationality": "Saudi", "date_of_birth": date(1983, 5, 17)},
        "property_code": "BRD-004", "unit_number": "G03",
        "monthly_rent": d("13000.00"), "start_date": date(2025, 1, 1), "duration_months": 12,
        "payment_schedule": "monthly", "security_deposit": d("13000.00"), "security_deposit_paid": False,
        "payments": [
            {"amount": d("14950.00"), "payment_date": date(2025, 1, 5), "due_date": date(2025, 1, 1), "method": "online"},
            {"amount": d("14950.00"), "payment_date": date(2025, 2, 8), "due_date": date(2025, 2, 1), "method": "online"},
        ],
    },
    {
        "tenant": {"full_name": "أحمد ناصر الشمري", "national_id": "1062000011", "phone": "+966503100011", "email": "ahmed.alsham@telecom.sa", "nationality": "Saudi", "date_of_birth": date(1979, 1, 25)},
        "property_code": "BRD-005", "unit_number": "101",
        "monthly_rent": d("4200.00"), "start_date": date(2025, 1, 1), "duration_months": 12,
        "payment_schedule": "monthly", "security_deposit": d("4200.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("4830.00"), "payment_date": date(2025, 1, 2), "due_date": date(2025, 1, 1), "method": "cash"},
            {"amount": d("4830.00"), "payment_date": date(2025, 2, 3), "due_date": date(2025, 2, 1), "method": "cash"},
            {"amount": d("4830.00"), "payment_date": date(2025, 3, 2), "due_date": date(2025, 3, 1), "method": "cash"},
        ],
    },
    {
        "tenant": {"full_name": "رانية فيصل القحطاني", "national_id": "1062000012", "phone": "+966503100012", "email": "rania.qht@education.sa", "nationality": "Saudi", "date_of_birth": date(1994, 6, 12)},
        "property_code": "BRD-005", "unit_number": "102",
        "monthly_rent": d("4200.00"), "start_date": date(2024, 9, 1), "duration_months": 12,
        "payment_schedule": "monthly", "security_deposit": d("4200.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("4830.00"), "payment_date": date(2024, 9, 1), "due_date": date(2024, 9, 1), "method": "bank_transfer"},
            {"amount": d("4830.00"), "payment_date": date(2024, 10, 1), "due_date": date(2024, 10, 1), "method": "bank_transfer"},
            {"amount": d("4830.00"), "payment_date": date(2024, 11, 3), "due_date": date(2024, 11, 1), "method": "bank_transfer"},
            {"amount": d("4830.00"), "payment_date": date(2024, 12, 2), "due_date": date(2024, 12, 1), "method": "bank_transfer"},
            {"amount": d("4830.00"), "payment_date": date(2025, 1, 4), "due_date": date(2025, 1, 1), "method": "bank_transfer"},
        ],
    },
    {
        "tenant": {"full_name": "سلطان حمد الدوسري", "national_id": "1062000013", "phone": "+966503100013", "email": "sultan.dosari@transport.sa", "nationality": "Saudi", "date_of_birth": date(1972, 3, 8)},
        "property_code": "BRD-006", "unit_number": "IND-01",
        "monthly_rent": d("38000.00"), "start_date": date(2024, 4, 1), "duration_months": 24,
        "payment_schedule": "annual", "security_deposit": d("76000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("526680.00"), "payment_date": date(2024, 4, 1), "due_date": date(2024, 4, 1), "method": "bank_transfer"},
        ],
    },
    {
        "tenant": {"full_name": "ماجد إبراهيم العنزي", "national_id": "1062000014", "phone": "+966503100014", "email": "majid.alanzi@steel.sa", "nationality": "Saudi", "date_of_birth": date(1976, 10, 20)},
        "property_code": "BRD-006", "unit_number": "IND-02",
        "monthly_rent": d("44000.00"), "start_date": date(2025, 2, 1), "duration_months": 12,
        "payment_schedule": "semi_annual", "security_deposit": d("88000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("303600.00"), "payment_date": date(2025, 2, 1), "due_date": date(2025, 2, 1), "method": "bank_transfer"},
        ],
    },
    {
        "tenant": {"full_name": "خالد عبدالعزيز البشي", "national_id": "1062000015", "phone": "+966503100015", "email": "khalid.bishi@consulting.sa", "nationality": "Saudi", "date_of_birth": date(1981, 7, 14)},
        "property_code": "BRD-007", "unit_number": "V-01",
        "monthly_rent": d("21000.00"), "start_date": date(2025, 1, 1), "duration_months": 12,
        "payment_schedule": "semi_annual", "security_deposit": d("42000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("144690.00"), "payment_date": date(2025, 1, 1), "due_date": date(2025, 1, 1), "method": "cheque"},
        ],
    },
    {
        "tenant": {"full_name": "فاطمة سعد الحربي", "national_id": "1062000016", "phone": "+966503100016", "email": "fatima.harbi@medical.sa", "nationality": "Saudi", "date_of_birth": date(1991, 4, 5)},
        "property_code": "BRD-007", "unit_number": "V-02",
        "monthly_rent": d("20000.00"), "start_date": date(2024, 11, 1), "duration_months": 12,
        "payment_schedule": "semi_annual", "security_deposit": d("40000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("137900.00"), "payment_date": date(2024, 11, 1), "due_date": date(2024, 11, 1), "method": "bank_transfer"},
        ],
    },
    {
        "tenant": {"full_name": "عمر وليد المطيري", "national_id": "1062000017", "phone": "+966503100017", "email": "omar.almutairi@finance.sa", "nationality": "Saudi", "date_of_birth": date(1984, 9, 9)},
        "property_code": "BRD-007", "unit_number": "V-03",
        "monthly_rent": d("22000.00"), "start_date": date(2025, 3, 1), "duration_months": 12,
        "payment_schedule": "monthly", "security_deposit": d("22000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("25300.00"), "payment_date": date(2025, 3, 1), "due_date": date(2025, 3, 1), "method": "bank_transfer"},
            {"amount": d("25300.00"), "payment_date": date(2025, 4, 2), "due_date": date(2025, 4, 1), "method": "bank_transfer"},
        ],
    },
    {
        "tenant": {"full_name": "ريم ناصر الشمري", "national_id": "1062000018", "phone": "+966503100018", "email": "reem.shammari@realestate.sa", "nationality": "Saudi", "date_of_birth": date(1986, 8, 18)},
        "property_code": "BRD-008", "unit_number": "101",
        "monthly_rent": d("14500.00"), "start_date": date(2025, 1, 1), "duration_months": 12,
        "payment_schedule": "quarterly", "security_deposit": d("29000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("49937.50"), "payment_date": date(2025, 1, 1), "due_date": date(2025, 1, 1), "method": "cheque"},
            {"amount": d("49937.50"), "payment_date": date(2025, 4, 3), "due_date": date(2025, 4, 1), "method": "cheque"},
        ],
    },
    {
        "tenant": {"full_name": "حمد فهد الرشيدي", "national_id": "1062000019", "phone": "+966503100019", "email": "hamad.alrashidi@aviation.sa", "nationality": "Saudi", "date_of_birth": date(1977, 2, 22)},
        "property_code": "ANZ-001", "unit_number": "G01",
        "monthly_rent": d("17000.00"), "start_date": date(2024, 8, 1), "duration_months": 24,
        "payment_schedule": "quarterly", "security_deposit": d("34000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("58650.00"), "payment_date": date(2024, 8, 1), "due_date": date(2024, 8, 1), "method": "bank_transfer"},
            {"amount": d("58650.00"), "payment_date": date(2024, 11, 1), "due_date": date(2024, 11, 1), "method": "bank_transfer"},
            {"amount": d("58650.00"), "payment_date": date(2025, 2, 3), "due_date": date(2025, 2, 1), "method": "bank_transfer"},
        ],
    },
    {
        "tenant": {"full_name": "لطيفة عبدالله الدوسري", "national_id": "1062000020", "phone": "+966503100020", "email": "latifa.dosari@hospital.sa", "nationality": "Saudi", "date_of_birth": date(1995, 12, 1)},
        "property_code": "BRD-009", "unit_number": "COLD-A",
        "monthly_rent": d("28000.00"), "start_date": date(2025, 1, 1), "duration_months": 12,
        "payment_schedule": "semi_annual", "security_deposit": d("56000.00"), "security_deposit_paid": True,
        "payments": [
            {"amount": d("193200.00"), "payment_date": date(2025, 1, 1), "due_date": date(2025, 1, 1), "method": "bank_transfer"},
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 15 DEBTS
# ─────────────────────────────────────────────────────────────────────────────
DEBTS = [
    {
        "property_code": "BRD-001", "debt_type": "bank_loan",
        "creditor_name": "بنك الراجحي - فرع بريدة",
        "total_amount": d("3500000.00"), "interest_rate": d("3.25"),
        "start_date": date(2022, 3, 1), "end_date": date(2029, 3, 1),
        "notes": "قرض عقاري لتمويل شراء برج الملك فهد التجاري.",
        "installments": [
            {"amount": d("41666.67"), "due_date": date(2025, 1, 1), "status": "paid", "paid_date": date(2025, 1, 5)},
            {"amount": d("41666.67"), "due_date": date(2025, 2, 1), "status": "paid", "paid_date": date(2025, 2, 3)},
            {"amount": d("41666.67"), "due_date": date(2025, 3, 1), "status": "paid", "paid_date": date(2025, 3, 2)},
            {"amount": d("41666.67"), "due_date": date(2025, 4, 1), "status": "pending"},
            {"amount": d("41666.67"), "due_date": date(2025, 5, 1), "status": "pending"},
            {"amount": d("41666.67"), "due_date": date(2025, 6, 1), "status": "pending"},
        ],
    },
    {
        "property_code": "BRD-003", "debt_type": "bank_loan",
        "creditor_name": "البنك الأهلي السعودي - بريدة",
        "total_amount": d("4800000.00"), "interest_rate": d("3.75"),
        "start_date": date(2021, 6, 1), "end_date": date(2031, 6, 1),
        "notes": "تمويل طويل الأجل لاقتناء مستودعات الصناعية الأولى.",
        "installments": [
            {"amount": d("48000.00"), "due_date": date(2025, 1, 1), "status": "paid", "paid_date": date(2025, 1, 4)},
            {"amount": d("48000.00"), "due_date": date(2025, 2, 1), "status": "paid", "paid_date": date(2025, 2, 2)},
            {"amount": d("48000.00"), "due_date": date(2025, 3, 1), "status": "paid", "paid_date": date(2025, 3, 1)},
            {"amount": d("48000.00"), "due_date": date(2025, 4, 1), "status": "pending"},
            {"amount": d("48000.00"), "due_date": date(2025, 5, 1), "status": "pending"},
        ],
    },
    {
        "property_code": "BRD-006", "debt_type": "bank_loan",
        "creditor_name": "بنك ساب - فرع القصيم",
        "total_amount": d("7200000.00"), "interest_rate": d("4.00"),
        "start_date": date(2020, 9, 1), "end_date": date(2035, 9, 1),
        "notes": "رهن عقاري — المستودعات الصناعية الثانية، المنطقة الصناعية الثانية.",
        "installments": [
            {"amount": d("72000.00"), "due_date": date(2025, 1, 1), "status": "paid", "paid_date": date(2025, 1, 3)},
            {"amount": d("72000.00"), "due_date": date(2025, 2, 1), "status": "paid", "paid_date": date(2025, 2, 1)},
            {"amount": d("72000.00"), "due_date": date(2025, 3, 1), "status": "overdue"},
            {"amount": d("72000.00"), "due_date": date(2025, 4, 1), "status": "pending"},
        ],
    },
    {
        "property_code": "BRD-008", "debt_type": "construction",
        "creditor_name": "شركة البنية التحتية السعودية",
        "total_amount": d("1200000.00"), "interest_rate": d("0.00"),
        "start_date": date(2023, 5, 1), "end_date": date(2026, 5, 1),
        "notes": "تمويل إنشاء وتشطيب برج الخليج للأعمال.",
        "installments": [
            {"amount": d("100000.00"), "due_date": date(2024, 5, 1), "status": "paid", "paid_date": date(2024, 5, 5)},
            {"amount": d("100000.00"), "due_date": date(2024, 8, 1), "status": "paid", "paid_date": date(2024, 8, 3)},
            {"amount": d("100000.00"), "due_date": date(2024, 11, 1), "status": "paid", "paid_date": date(2024, 11, 2)},
            {"amount": d("100000.00"), "due_date": date(2025, 2, 1), "status": "paid", "paid_date": date(2025, 2, 4)},
            {"amount": d("100000.00"), "due_date": date(2025, 5, 1), "status": "pending"},
        ],
    },
    {
        "property_code": "BRD-002", "debt_type": "contractor",
        "creditor_name": "شركة الفوزان للإنشاءات - بريدة",
        "total_amount": d("420000.00"), "interest_rate": d("0.00"),
        "start_date": date(2024, 10, 1), "end_date": date(2025, 10, 1),
        "notes": "أعمال تجديد مجمع الروضة السكني — تشطيبات داخلية وخارجية.",
        "installments": [
            {"amount": d("105000.00"), "due_date": date(2024, 10, 1), "status": "paid", "paid_date": date(2024, 10, 5)},
            {"amount": d("105000.00"), "due_date": date(2025, 1, 1), "status": "paid", "paid_date": date(2025, 1, 6)},
            {"amount": d("105000.00"), "due_date": date(2025, 4, 1), "status": "pending"},
            {"amount": d("105000.00"), "due_date": date(2025, 7, 1), "status": "pending"},
        ],
    },
    {
        "property_code": "BRD-004", "debt_type": "maintenance",
        "creditor_name": "شركة القصيم للصيانة المتكاملة",
        "total_amount": d("220000.00"), "interest_rate": d("0.00"),
        "start_date": date(2024, 7, 1), "end_date": date(2025, 7, 1),
        "notes": "عقد صيانة شاملة لمركز النخيل التجاري — تكييف وكهرباء وسباكة.",
        "installments": [
            {"amount": d("36666.67"), "due_date": date(2024, 7, 1), "status": "paid", "paid_date": date(2024, 7, 3)},
            {"amount": d("36666.67"), "due_date": date(2024, 9, 1), "status": "paid", "paid_date": date(2024, 9, 2)},
            {"amount": d("36666.67"), "due_date": date(2024, 11, 1), "status": "paid", "paid_date": date(2024, 11, 4)},
            {"amount": d("36666.67"), "due_date": date(2025, 1, 1), "status": "paid", "paid_date": date(2025, 1, 8)},
            {"amount": d("36666.67"), "due_date": date(2025, 3, 1), "status": "pending"},
            {"amount": d("36666.67"), "due_date": date(2025, 5, 1), "status": "pending"},
        ],
    },
    {
        "property_code": "BRD-005", "debt_type": "supplier",
        "creditor_name": "شركة المصعد العربي",
        "total_amount": d("145000.00"), "interest_rate": d("0.00"),
        "start_date": date(2024, 11, 1), "end_date": date(2025, 8, 1),
        "notes": "توريد وتركيب وصيانة مصعدين في أبراج المطار السكنية.",
        "installments": [
            {"amount": d("48333.33"), "due_date": date(2024, 11, 1), "status": "paid", "paid_date": date(2024, 11, 5)},
            {"amount": d("48333.33"), "due_date": date(2025, 2, 1), "status": "paid", "paid_date": date(2025, 2, 3)},
            {"amount": d("48333.34"), "due_date": date(2025, 5, 1), "status": "pending"},
        ],
    },
    {
        "property_code": "ANZ-001", "debt_type": "contractor",
        "creditor_name": "مقاولو عنيزة المتحدون",
        "total_amount": d("380000.00"), "interest_rate": d("0.00"),
        "start_date": date(2023, 8, 1), "end_date": date(2025, 2, 1),
        "notes": "إنشاء وتشطيب مجمع عنيزة التجاري — كامل المبنى.",
        "installments": [
            {"amount": d("95000.00"), "due_date": date(2023, 8, 1), "status": "paid", "paid_date": date(2023, 8, 5)},
            {"amount": d("95000.00"), "due_date": date(2023, 11, 1), "status": "paid", "paid_date": date(2023, 11, 3)},
            {"amount": d("95000.00"), "due_date": date(2024, 2, 1), "status": "paid", "paid_date": date(2024, 2, 4)},
            {"amount": d("95000.00"), "due_date": date(2024, 5, 1), "status": "paid", "paid_date": date(2024, 5, 2)},
        ],
    },
    {
        "property_code": "BRD-007", "debt_type": "maintenance",
        "creditor_name": "شركة تنسيق المناظر الطبيعية - القصيم",
        "total_amount": d("96000.00"), "interest_rate": d("0.00"),
        "start_date": date(2025, 1, 1), "end_date": date(2025, 12, 1),
        "notes": "عقد سنوي لصيانة الحدائق لفلل حي الملك فهد.",
        "installments": [
            {"amount": d("8000.00"), "due_date": date(2025, 1, 1), "status": "paid", "paid_date": date(2025, 1, 7)},
            {"amount": d("8000.00"), "due_date": date(2025, 2, 1), "status": "paid", "paid_date": date(2025, 2, 5)},
            {"amount": d("8000.00"), "due_date": date(2025, 3, 1), "status": "paid", "paid_date": date(2025, 3, 4)},
            {"amount": d("8000.00"), "due_date": date(2025, 4, 1), "status": "pending"},
            {"amount": d("8000.00"), "due_date": date(2025, 5, 1), "status": "pending"},
        ],
    },
    {
        "property_code": "BRD-009", "debt_type": "construction",
        "creditor_name": "شركة البناء المتقدم - بريدة",
        "total_amount": d("650000.00"), "interest_rate": d("0.00"),
        "start_date": date(2023, 2, 1), "end_date": date(2025, 2, 1),
        "notes": "إنشاء مستودع الأغذية المركزي — غرف التبريد والتخزين الجاف.",
        "installments": [
            {"amount": d("162500.00"), "due_date": date(2023, 2, 1), "status": "paid", "paid_date": date(2023, 2, 5)},
            {"amount": d("162500.00"), "due_date": date(2023, 8, 1), "status": "paid", "paid_date": date(2023, 8, 3)},
            {"amount": d("162500.00"), "due_date": date(2024, 2, 1), "status": "paid", "paid_date": date(2024, 2, 4)},
            {"amount": d("162500.00"), "due_date": date(2024, 8, 1), "status": "paid", "paid_date": date(2024, 8, 2)},
        ],
    },
    {
        "property_code": "BRD-010", "debt_type": "bank_loan",
        "creditor_name": "بنك الجزيرة - فرع بريدة",
        "total_amount": d("2100000.00"), "interest_rate": d("3.50"),
        "start_date": date(2023, 6, 1), "end_date": date(2030, 6, 1),
        "notes": "قرض عقاري لتطوير مجمع الياسمين السكني.",
        "installments": [
            {"amount": d("25000.00"), "due_date": date(2025, 1, 1), "status": "paid", "paid_date": date(2025, 1, 6)},
            {"amount": d("25000.00"), "due_date": date(2025, 2, 1), "status": "paid", "paid_date": date(2025, 2, 4)},
            {"amount": d("25000.00"), "due_date": date(2025, 3, 1), "status": "paid", "paid_date": date(2025, 3, 3)},
            {"amount": d("25000.00"), "due_date": date(2025, 4, 1), "status": "pending"},
            {"amount": d("25000.00"), "due_date": date(2025, 5, 1), "status": "pending"},
        ],
    },
    {
        "property_code": "ANZ-002", "debt_type": "maintenance",
        "creditor_name": "شركة العناية بالمباني - عنيزة",
        "total_amount": d("72000.00"), "interest_rate": d("0.00"),
        "start_date": date(2025, 1, 1), "end_date": date(2025, 12, 1),
        "notes": "عقد صيانة سنوي شامل لشقق النزهة السكنية، عنيزة.",
        "installments": [
            {"amount": d("6000.00"), "due_date": date(2025, 1, 1), "status": "paid", "paid_date": date(2025, 1, 8)},
            {"amount": d("6000.00"), "due_date": date(2025, 2, 1), "status": "paid", "paid_date": date(2025, 2, 6)},
            {"amount": d("6000.00"), "due_date": date(2025, 3, 1), "status": "paid", "paid_date": date(2025, 3, 5)},
            {"amount": d("6000.00"), "due_date": date(2025, 4, 1), "status": "pending"},
        ],
    },
    {
        "property_code": "BRD-001", "debt_type": "supplier",
        "creditor_name": "شركة برق للأنظمة الكهربائية",
        "total_amount": d("185000.00"), "interest_rate": d("0.00"),
        "start_date": date(2024, 9, 1), "end_date": date(2025, 6, 1),
        "notes": "تركيب وتحديث لوحة الكهرباء الرئيسية وأنظمة UPS — برج الملك فهد.",
        "installments": [
            {"amount": d("61666.67"), "due_date": date(2024, 9, 1), "status": "paid", "paid_date": date(2024, 9, 4)},
            {"amount": d("61666.67"), "due_date": date(2024, 12, 1), "status": "paid", "paid_date": date(2024, 12, 3)},
            {"amount": d("61666.66"), "due_date": date(2025, 3, 1), "status": "overdue"},
        ],
    },
    {
        "property_code": "BRD-004", "debt_type": "supplier",
        "creditor_name": "مصنع البلاط الوطني - القصيم",
        "total_amount": d("58000.00"), "interest_rate": d("0.00"),
        "start_date": date(2025, 2, 1), "end_date": date(2025, 8, 1),
        "notes": "توريد وتركيب بلاط وسيراميك — تجديد مركز النخيل.",
        "installments": [
            {"amount": d("19333.33"), "due_date": date(2025, 2, 1), "status": "paid", "paid_date": date(2025, 2, 5)},
            {"amount": d("19333.33"), "due_date": date(2025, 4, 1), "status": "pending"},
            {"amount": d("19333.34"), "due_date": date(2025, 6, 1), "status": "pending"},
        ],
    },
    {
        "property_code": "BRD-008", "debt_type": "other",
        "creditor_name": "أمانة منطقة القصيم",
        "total_amount": d("92000.00"), "interest_rate": d("0.00"),
        "start_date": date(2025, 1, 1), "end_date": date(2025, 12, 1),
        "notes": "رسوم البنية التحتية وتوصيل الخدمات البلدية — برج الخليج للأعمال.",
        "installments": [
            {"amount": d("46000.00"), "due_date": date(2025, 1, 1), "status": "paid", "paid_date": date(2025, 1, 10)},
            {"amount": d("46000.00"), "due_date": date(2025, 7, 1), "status": "pending"},
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 25 TRANSACTIONS
# ─────────────────────────────────────────────────────────────────────────────
TRANSACTIONS = [
    {"property_code": "BRD-001", "type": "income",  "category": "rental",          "amount": d("43700.00"),  "date": date(2025, 1, 5),  "description": "تحصيل إيجار يناير — مكاتب 101، 102، ومحل G01",              "ref": "TXN-BRD-001"},
    {"property_code": "BRD-001", "type": "expense", "category": "utilities",        "amount": d("11200.00"),  "date": date(2025, 1, 15), "description": "فاتورة الكهرباء والماء — يناير 2025",                         "ref": "TXN-BRD-002"},
    {"property_code": "BRD-001", "type": "expense", "category": "maintenance",      "amount": d("18500.00"),  "date": date(2025, 1, 20), "description": "صيانة لوحة الكهرباء الرئيسية وأعمال طارئة",                 "ref": "TXN-BRD-003"},
    {"property_code": "BRD-001", "type": "income",  "category": "service_charge",   "amount": d("6000.00"),   "date": date(2025, 2, 1),  "description": "رسوم الخدمات المشتركة — الربع الأول 2025",                   "ref": "TXN-BRD-004"},
    {"property_code": "BRD-001", "type": "expense", "category": "security",         "amount": d("9500.00"),   "date": date(2025, 2, 5),  "description": "خدمات الأمن والحراسة — فبراير 2025",                        "ref": "TXN-BRD-005"},
    {"property_code": "BRD-003", "type": "income",  "category": "rental",           "amount": d("304920.00"), "date": date(2024, 7, 2),  "description": "إيجار سنوي — مستودع WH-A (بندر المطيري)",                   "ref": "TXN-BRD-006"},
    {"property_code": "BRD-003", "type": "expense", "category": "maintenance",      "amount": d("42000.00"),  "date": date(2024, 8, 10), "description": "صيانة أنظمة التكييف المركزي والتهوية",                      "ref": "TXN-BRD-007"},
    {"property_code": "BRD-003", "type": "expense", "category": "government_fees",  "amount": d("8500.00"),   "date": date(2025, 1, 20), "description": "رسوم الرخصة الصناعية السنوية 2025",                         "ref": "TXN-BRD-008"},
    {"property_code": "BRD-004", "type": "income",  "category": "rental",           "amount": d("55200.00"),  "date": date(2024, 6, 1),  "description": "إيجار ربعي — محل G01 (وليد الحربي) الربع الثالث 2024",     "ref": "TXN-BRD-009"},
    {"property_code": "BRD-004", "type": "income",  "category": "rental",           "amount": d("16675.00"),  "date": date(2025, 3, 1),  "description": "إيجار مارس — محل G02 (هند الزهراني)",                       "ref": "TXN-BRD-010"},
    {"property_code": "BRD-004", "type": "expense", "category": "cleaning",         "amount": d("5500.00"),   "date": date(2025, 1, 8),  "description": "عقد نظافة شهري — يناير 2025",                               "ref": "TXN-BRD-011"},
    {"property_code": "BRD-004", "type": "expense", "category": "utilities",        "amount": d("9800.00"),   "date": date(2025, 2, 15), "description": "فواتير الكهرباء والماء — فبراير 2025",                      "ref": "TXN-BRD-012"},
    {"property_code": "BRD-006", "type": "income",  "category": "rental",           "amount": d("526680.00"), "date": date(2024, 4, 1),  "description": "إيجار سنوي — مستودع IND-01 (سلطان الدوسري)",               "ref": "TXN-BRD-013"},
    {"property_code": "BRD-006", "type": "expense", "category": "maintenance",      "amount": d("55000.00"),  "date": date(2024, 5, 12), "description": "صيانة شاملة للرافعات الصناعية والأرضيات",                  "ref": "TXN-BRD-014"},
    {"property_code": "BRD-006", "type": "expense", "category": "government_fees",  "amount": d("12000.00"),  "date": date(2025, 1, 10), "description": "رسوم هيئة المدن الصناعية (مدن) 2025",                       "ref": "TXN-BRD-015"},
    {"property_code": "BRD-007", "type": "income",  "category": "rental",           "amount": d("144690.00"), "date": date(2025, 1, 1),  "description": "إيجار نصف سنوي — فيلا V-01 (خالد البشي)",                   "ref": "TXN-BRD-016"},
    {"property_code": "BRD-007", "type": "income",  "category": "rental",           "amount": d("137900.00"), "date": date(2024, 11, 1), "description": "إيجار نصف سنوي — فيلا V-02 (فاطمة الحربي)",                 "ref": "TXN-BRD-017"},
    {"property_code": "BRD-007", "type": "expense", "category": "maintenance",      "amount": d("14000.00"),  "date": date(2025, 2, 10), "description": "أعمال صيانة السباكة والكهرباء — الفلل V-01 إلى V-03",     "ref": "TXN-BRD-018"},
    {"property_code": "BRD-008", "type": "income",  "category": "rental",           "amount": d("49937.50"),  "date": date(2025, 1, 1),  "description": "إيجار ربعي — مكتب 101 (ريم الشمري) الربع الأول 2025",      "ref": "TXN-BRD-019"},
    {"property_code": "BRD-008", "type": "expense", "category": "management",       "amount": d("18000.00"),  "date": date(2025, 1, 15), "description": "رسوم إدارة الممتلكات — الربع الأول 2025",                   "ref": "TXN-BRD-020"},
    {"property_code": "ANZ-001", "type": "income",  "category": "rental",           "amount": d("58650.00"),  "date": date(2025, 2, 3),  "description": "إيجار ربعي — محل G01 (حمد الرشيدي) الربع الأول 2025",      "ref": "TXN-BRD-021"},
    {"property_code": "ANZ-001", "type": "expense", "category": "cleaning",         "amount": d("4200.00"),   "date": date(2025, 2, 8),  "description": "خدمات النظافة الشهرية — فبراير 2025",                       "ref": "TXN-BRD-022"},
    {"property_code": "BRD-009", "type": "income",  "category": "rental",           "amount": d("193200.00"), "date": date(2025, 1, 1),  "description": "إيجار نصف سنوي — مستودع COLD-A (لطيفة الدوسري)",           "ref": "TXN-BRD-023"},
    {"property_code": "BRD-009", "type": "expense", "category": "utilities",        "amount": d("38000.00"),  "date": date(2025, 1, 20), "description": "فاتورة الكهرباء — تشغيل غرف التبريد يناير 2025",           "ref": "TXN-BRD-024"},
    {"property_code": "BRD-010", "type": "income",  "category": "rental",           "amount": d("34250.00"),  "date": date(2025, 1, 5),  "description": "تحصيل إيجار يناير — وحدات 101، 201، V-01",                 "ref": "TXN-BRD-025"},
]


# ─────────────────────────────────────────────────────────────────────────────
# 15 VOUCHERS  — all stages represented
# ─────────────────────────────────────────────────────────────────────────────
VOUCHERS = [
    {"property_code": "BRD-001", "voucher_number": "VCH-BRD-001", "date": date(2025, 1, 15), "amount": d("18500.00"),  "payee_name": "شركة برق للأنظمة الكهربائية",         "payment_method": "bank_transfer", "description": "صيانة طارئة للوحة الكهرباء الرئيسية — برج الملك فهد. فاتورة INV-2025-441.",        "approval_status": "approved"},
    {"property_code": "BRD-001", "voucher_number": "VCH-BRD-002", "date": date(2025, 2, 5),  "amount": d("9500.00"),   "payee_name": "شركة درع الخليج للأمن",               "payment_method": "bank_transfer", "description": "خدمات الأمن والحراسة — فبراير 2025، برج الملك فهد.",                                 "approval_status": "approved"},
    {"property_code": "BRD-003", "voucher_number": "VCH-BRD-003", "date": date(2024, 8, 12), "amount": d("42000.00"),  "payee_name": "شركة الهواء البارد للتكييف",          "payment_method": "cheque",        "description": "صيانة شاملة لأنظمة التكييف المركزي — المستودعات الصناعية الأولى.",                "approval_status": "approved"},
    {"property_code": "BRD-004", "voucher_number": "VCH-BRD-004", "date": date(2025, 1, 8),  "amount": d("5500.00"),   "payee_name": "مؤسسة النظافة الشاملة",               "payment_method": "cash",          "description": "عقد النظافة الشهري — يناير 2025، مركز النخيل التجاري.",                            "approval_status": "approved"},
    {"property_code": "BRD-006", "voucher_number": "VCH-BRD-005", "date": date(2024, 5, 14), "amount": d("55000.00"),  "payee_name": "شركة الرافعات الصناعية السعودية",    "payment_method": "bank_transfer", "description": "صيانة الرافعات وتجديد الأرضيات — المستودعات الصناعية الثانية.",                   "approval_status": "approved"},
    {"property_code": "BRD-007", "voucher_number": "VCH-BRD-006", "date": date(2025, 2, 12), "amount": d("14000.00"),  "payee_name": "مؤسسة المهندس للسباكة والكهرباء",    "payment_method": "bank_transfer", "description": "أعمال سباكة وكهرباء طارئة — فلل V-01 وV-02 وV-03، حي الملك فهد.",               "approval_status": "approved"},
    {"property_code": "BRD-008", "voucher_number": "VCH-BRD-007", "date": date(2025, 1, 16), "amount": d("18000.00"),  "payee_name": "شركة بريمير لإدارة الممتلكات",        "payment_method": "cheque",        "description": "رسوم إدارة الممتلكات — الربع الأول 2025، برج الخليج للأعمال.",                    "approval_status": "pending_admin"},
    {"property_code": "BRD-009", "voucher_number": "VCH-BRD-008", "date": date(2025, 1, 22), "amount": d("38000.00"),  "payee_name": "شركة السعودية للكهرباء - القصيم",    "payment_method": "online",        "description": "فاتورة الكهرباء — تشغيل غرف التبريد، يناير 2025، مستودع الأغذية.",               "approval_status": "approved"},
    {"property_code": "BRD-002", "voucher_number": "VCH-BRD-009", "date": date(2025, 3, 5),  "amount": d("105000.00"), "payee_name": "شركة الفوزان للإنشاءات",              "payment_method": "bank_transfer", "description": "الدفعة الثالثة — عقد تجديد مجمع الروضة السكني.",                                   "approval_status": "pending_finance"},
    {"property_code": "ANZ-001", "voucher_number": "VCH-BRD-010", "date": date(2025, 2, 10), "amount": d("4200.00"),   "payee_name": "مؤسسة عنيزة للنظافة",                "payment_method": "cash",          "description": "خدمات النظافة الشهرية — فبراير 2025، مجمع عنيزة التجاري.",                        "approval_status": "approved"},
    {"property_code": "BRD-005", "voucher_number": "VCH-BRD-011", "date": date(2025, 2, 3),  "amount": d("48333.33"),  "payee_name": "شركة المصعد العربي",                  "payment_method": "bank_transfer", "description": "الدفعة الثانية — عقد توريد وتركيب المصاعد، أبراج المطار السكنية.",              "approval_status": "pending_accountant"},
    {"property_code": "BRD-010", "voucher_number": "VCH-BRD-012", "date": date(2025, 3, 10), "amount": d("9800.00"),   "payee_name": "شركة المياه الوطنية - بريدة",        "payment_method": "online",        "description": "فاتورة الماء والصرف الصحي — مارس 2025، مجمع الياسمين السكني.",                    "approval_status": "draft"},
    {"property_code": "BRD-004", "voucher_number": "VCH-BRD-013", "date": date(2025, 2, 1),  "amount": d("19333.33"),  "payee_name": "مصنع البلاط الوطني - القصيم",        "payment_method": "cheque",        "description": "الدفعة الأولى — عقد توريد وتركيب البلاط، مركز النخيل التجاري.",                  "approval_status": "approved"},
    {"property_code": "BRD-001", "voucher_number": "VCH-BRD-014", "date": date(2025, 3, 15), "amount": d("7200.00"),   "payee_name": "أمانة منطقة القصيم",                 "payment_method": "online",        "description": "رسوم تجديد الرخصة التجارية السنوية — برج الملك فهد 2025.",                       "approval_status": "rejected"},
    {"property_code": "BRD-008", "voucher_number": "VCH-BRD-015", "date": date(2025, 3, 20), "amount": d("46000.00"),  "payee_name": "أمانة منطقة القصيم",                 "payment_method": "bank_transfer", "description": "رسوم البنية التحتية وتوصيل الخدمات البلدية — برج الخليج، الدفعة الأولى.",      "approval_status": "pending_finance"},
]


# ─────────────────────────────────────────────────────────────────────────────
# MANAGEMENT COMMAND
# ─────────────────────────────────────────────────────────────────────────────
class Command(BaseCommand):
    help = "Seed the database with Buraidah/Al-Qassim realistic demo data."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Wipe seed data first.")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self._clear()

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding Buraidah / Al-Qassim ===\n"))

        users = self._seed_users()
        properties, units_map = self._seed_properties(users["pm_qassim"])
        self._seed_contracts(units_map, users["admin_qassim"], users["accountant_qassim1"])
        self._seed_debts(properties)
        self._seed_transactions(properties, users["accountant_qassim1"])
        self._seed_vouchers(properties, users["accountant_qassim1"], users["finance_qassim"], users["admin_qassim"])

        self.stdout.write(self.style.SUCCESS("\n✓ Done!\n"))
        self.stdout.write(self.style.HTTP_INFO("  Credentials:"))
        for u in USERS:
            self.stdout.write(f"    {u['username']:<26} / {u['password']:<18}  ({u['role']})")
        self.stdout.write("")

    def _clear(self):
        self.stdout.write(self.style.WARNING("Clearing seed data..."))
        from vouchers.models import Voucher
        from finance.models import Transaction
        from debts.models import Debt
        from contracts.models import Contract, Tenant
        from properties.models import Property

        codes = [p["property_code"] for p in PROPERTIES]
        nids  = [t["tenant"]["national_id"] for t in TENANTS_CONTRACTS]
        Voucher.objects.filter(property__property_code__in=codes).delete()
        Transaction.objects.filter(property__property_code__in=codes).delete()
        Debt.objects.filter(property__property_code__in=codes).delete()
        Contract.objects.filter(unit__property__property_code__in=codes).delete()
        Tenant.objects.filter(national_id__in=nids).delete()
        Property.objects.filter(property_code__in=codes).delete()
        User.objects.filter(username__in=[u["username"] for u in USERS]).delete()
        self.stdout.write("  Done.\n")

    def _seed_users(self):
        self.stdout.write("→ Users...")
        out = {}
        for data in USERS:
            u, new = User.objects.get_or_create(
                username=data["username"],
                defaults={k: data[k] for k in ("first_name","last_name","email","role","phone","national_id","is_staff","is_superuser")},
            )
            if new:
                u.set_password(data["password"])
                u.save()
            out[data["username"]] = u
        self.stdout.write(f"   {len(out)} ready.")
        return out

    def _seed_properties(self, manager):
        from properties.models import Property, PropertyUnit
        self.stdout.write("→ Properties & units...")
        props, units_map = {}, {}
        for pdata in PROPERTIES:
            units_raw = pdata.pop("units")
            prop, _ = Property.objects.get_or_create(
                property_code=pdata["property_code"],
                defaults={**pdata, "property_manager": manager},
            )
            props[pdata["property_code"]] = prop
            for u in units_raw:
                unit, _ = PropertyUnit.objects.get_or_create(
                    property=prop, unit_number=u["unit_number"],
                    defaults={"floor": u["floor"], "size_sqm": u["size_sqm"],
                              "unit_type": u["unit_type"], "monthly_rent": u["monthly_rent"],
                              "rental_status": "vacant"},
                )
                units_map[(pdata["property_code"], u["unit_number"])] = unit
            pdata["units"] = units_raw
        self.stdout.write(f"   {len(props)} properties, {sum(len(p['units']) for p in PROPERTIES)} units ready.")
        return props, units_map

    def _seed_contracts(self, units_map, created_by, accountant):
        from contracts.models import Contract, Tenant, Payment
        self.stdout.write("→ Contracts & payments...")
        cc = pc = 0
        for cdata in TENANTS_CONTRACTS:
            td = cdata["tenant"]
            tenant, _ = Tenant.objects.get_or_create(
                national_id=td["national_id"],
                defaults={k: td[k] for k in ("full_name","phone","email","nationality","date_of_birth")},
            )
            unit = units_map.get((cdata["property_code"], cdata["unit_number"]))
            if not unit:
                continue
            if Contract.objects.filter(unit=unit, status="active").exists():
                cc += 1; continue
            total = cdata["monthly_rent"] * cdata["duration_months"]
            vat   = (total * Decimal("0.15")).quantize(Decimal("0.01"))
            contract = Contract.objects.create(
                unit=unit, tenant=tenant,
                monthly_rent=cdata["monthly_rent"], duration_months=cdata["duration_months"],
                security_deposit=cdata["security_deposit"], security_deposit_paid=cdata["security_deposit_paid"],
                payment_schedule=cdata["payment_schedule"],
                start_date=cdata["start_date"],
                end_date=cdata["start_date"] + relativedelta(months=cdata["duration_months"]),
                total_value=total, vat_amount=vat, total_value_with_vat=total + vat,
                status="active", created_by=created_by,
            )
            unit.rental_status = "occupied"
            unit.save(update_fields=["rental_status"])
            for p in cdata.get("payments", []):
                Payment.objects.get_or_create(
                    contract=contract, payment_date=p["payment_date"], amount=p["amount"],
                    defaults={"due_date": p.get("due_date"), "payment_method": p["method"],
                              "status": "confirmed", "recorded_by": accountant, "notes": ""},
                )
                pc += 1
            cc += 1
        self.stdout.write(f"   {cc} contracts, {pc} payments ready.")

    def _seed_debts(self, props):
        from debts.models import Debt, DebtInstallment
        self.stdout.write("→ Debts & installments...")
        dc = ic = 0
        for ddata in DEBTS:
            prop = props.get(ddata["property_code"])
            if not prop: continue
            insts = ddata.pop("installments")
            debt, created = Debt.objects.get_or_create(
                property=prop, creditor_name=ddata["creditor_name"], start_date=ddata["start_date"],
                defaults={k: ddata[k] for k in ("debt_type","total_amount","interest_rate","end_date","notes")},
            )
            if created:
                for i in insts:
                    DebtInstallment.objects.create(
                        debt=debt, amount=i["amount"], due_date=i["due_date"],
                        status=i["status"], paid_date=i.get("paid_date"), notes="",
                    )
                    ic += 1
            ddata["installments"] = insts
            dc += 1
        self.stdout.write(f"   {dc} debts, {ic} installments ready.")

    def _seed_transactions(self, props, created_by):
        from finance.models import Transaction
        self.stdout.write("→ Transactions...")
        count = 0
        for t in TRANSACTIONS:
            prop = props.get(t["property_code"])
            if not prop: continue
            _, created = Transaction.objects.get_or_create(
                reference=t["ref"],
                defaults={"property": prop, "transaction_type": t["type"], "category": t["category"],
                          "amount": t["amount"], "date": t["date"], "description": t["description"],
                          "created_by": created_by},
            )
            if created: count += 1
        self.stdout.write(f"   {count} transactions ready.")

    def _seed_vouchers(self, props, accountant, finance_mgr, admin_user):
        from vouchers.models import Voucher
        self.stdout.write("→ Vouchers...")
        count = 0
        for v in VOUCHERS:
            prop = props.get(v["property_code"])
            if not prop: continue
            status = v["approval_status"]
            approved_by = admin_user if status == "approved" else (accountant if status in ("pending_finance","pending_admin") else None)
            _, created = Voucher.objects.get_or_create(
                voucher_number=v["voucher_number"],
                defaults={"property": prop, "date": v["date"], "amount": v["amount"],
                          "payee_name": v["payee_name"], "payment_method": v["payment_method"],
                          "description": v["description"], "approval_status": status,
                          "created_by": accountant, "approved_by": approved_by},
            )
            if created: count += 1
        self.stdout.write(f"   {count} vouchers ready.")