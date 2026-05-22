"""
Generates mock PDFs for the Claims Audit Hackathon:
  - 2 UB-04 paper claim forms  (one per hero claim)
  - 3 SharePoint policy documents

Output → seed_data/quick_claim/images/  and  seed_data/sharepoint/docs/
"""

from pathlib import Path
from pdf_writer import PDF

OUT_CLAIMS   = Path(__file__).parent.parent / "seed_data/quick_claim/images"
OUT_POLICIES = Path(__file__).parent.parent / "seed_data/sharepoint/docs"
OUT_CLAIMS.mkdir(parents=True, exist_ok=True)
OUT_POLICIES.mkdir(parents=True, exist_ok=True)


# ── UB-04 helper ─────────────────────────────────────────────────────────────

def ub04_field(pdf, label, value, lx, ly, vx, size=9):
    pdf.text(lx, ly, label, size=8, bold=False)
    pdf.text(vx, ly, value, size=size, bold=False)


def make_ub04(path, claim: dict):
    pdf = PDF()

    # Title bar
    pdf.rect(40, 40, 532, 22, fill=False)
    pdf.text(200, 55, "UB-04 CLAIM FORM", size=12, bold=True)
    pdf.text(400, 55, "(MOCK — NOT FOR SUBMISSION)", size=8)

    # Box outline
    pdf.rect(40, 62, 532, 700, fill=False)

    # ── Section 1: Patient / Insured ─────────────────────────────────────────
    y = 80
    pdf.hline(40, y, 572)
    pdf.text(42, y + 12, "PATIENT INFORMATION", size=9, bold=True)

    y += 24
    ub04_field(pdf, "FL 1  PROVIDER NAME:", claim["provider_name"],        42, y, 180)
    ub04_field(pdf, "FL 3a PATIENT CTRL NO:", claim["claim_id"],           42, y+14, 180)
    ub04_field(pdf, "FL 3b MED REC NO:",      claim.get("member_id",""),   42, y+28, 180)
    ub04_field(pdf, "FL 4  TYPE OF BILL:",    "111 - Inpatient",          310, y,    430)
    ub04_field(pdf, "FL 5  FED TAX NO:",      "16-1234567",               310, y+14, 430)

    y += 48
    pdf.hline(40, y, 572)

    # ── Section 2: Admission / Discharge ─────────────────────────────────────
    pdf.text(42, y + 12, "ADMISSION / DISCHARGE", size=9, bold=True)
    y += 24
    ub04_field(pdf, "FL 12 ADMIT DATE:", claim["service_from_date"], 42, y, 160)
    ub04_field(pdf, "FL 13 ADMIT HR:",   "08",                       42, y+14, 160)
    ub04_field(pdf, "FL 14 ADMIT TYPE:", "1 - Emergency",            42, y+28, 160)
    ub04_field(pdf, "FL 16 DHR:",        "14",                       310, y,    430)
    ub04_field(pdf, "FL 17 STAT:",       claim.get("discharge_status","01") + " - " + claim.get("discharge_status_desc","Discharged home"), 310, y+14, 430)
    ub04_field(pdf, "FL 6  STMT FROM:",  claim["service_from_date"], 310, y+28, 430)
    ub04_field(pdf, "FL 6  STMT THRU:",  claim["service_to_date"],   310, y+42, 430)

    y += 62
    pdf.hline(40, y, 572)

    # ── Section 3: Patient demographics ─────────────────────────────────────
    pdf.text(42, y + 12, "PATIENT DEMOGRAPHICS", size=9, bold=True)
    y += 24
    ub04_field(pdf, "FL 8  PATIENT NAME:",    claim["patient_name"],   42, y,    180)
    ub04_field(pdf, "FL 10 BIRTHDATE:",       claim["dob"],            42, y+14, 180)
    ub04_field(pdf, "FL 11 SEX:",             claim["sex"],            42, y+28, 180)
    ub04_field(pdf, "FL 8a PATIENT ID:",      claim["member_id"],     310, y,    430)
    ub04_field(pdf, "FL 60 CERT NO (HIC):",   claim["subscriber_id"], 310, y+14, 430)

    y += 48
    pdf.hline(40, y, 572)

    # ── Section 4: Diagnosis codes ────────────────────────────────────────────
    pdf.text(42, y + 12, "DIAGNOSIS / PROCEDURE CODES", size=9, bold=True)
    y += 24
    dx_codes = claim.get("diagnosis_codes", [])
    for i, dx in enumerate(dx_codes[:6]):
        col = 42 if i < 3 else 310
        row_y = y + (i % 3) * 14
        ub04_field(pdf, f"FL 67{'abcdef'[i].upper()} DX:", dx, col, row_y, col + 80)

    proc_codes = claim.get("procedure_codes", [])
    for i, pc in enumerate(proc_codes[:2]):
        ub04_field(pdf, f"FL 74{'ab'[i]}  PROC:", pc, 42, y + 48 + i*14, 160)

    y += 80
    pdf.hline(40, y, 572)

    # ── Section 5: Revenue codes / charges ───────────────────────────────────
    pdf.text(42, y + 12, "REVENUE CODES / CHARGES", size=9, bold=True)
    y += 24
    pdf.text(42,  y, "REV CD", size=8, bold=True)
    pdf.text(120, y, "DESCRIPTION",          size=8, bold=True)
    pdf.text(320, y, "HCPCS",                size=8, bold=True)
    pdf.text(390, y, "SERV DATE",            size=8, bold=True)
    pdf.text(470, y, "CHARGES",              size=8, bold=True)
    y += 12

    for rev in claim.get("revenue_lines", []):
        pdf.text(42,  y, rev["code"],    size=9)
        pdf.text(120, y, rev["desc"],    size=9)
        pdf.text(320, y, rev.get("hcpcs",""),  size=9)
        pdf.text(390, y, claim["service_from_date"], size=9)
        pdf.text(470, y, f"${rev['charge']:,.2f}", size=9)
        y += 13

    pdf.hline(40, y, 572)
    y += 5
    pdf.text(390, y+10, "TOTAL CHARGES:", size=9, bold=True)
    pdf.text(470, y+10, f"${claim['total_billed_amount']:,.2f}", size=9, bold=True)

    y += 28
    pdf.hline(40, y, 572)

    # ── Section 6: Payer / DRG ────────────────────────────────────────────────
    pdf.text(42, y + 12, "PAYER / DRG INFORMATION", size=9, bold=True)
    y += 24
    ub04_field(pdf, "FL 50  PAYER NAME:", "PAYER CO",            42, y,    160)
    ub04_field(pdf, "FL 71  PPS CODE:",   claim.get("drg_code",""),   42, y+14, 160)
    ub04_field(pdf, "FL 71  DRG DESC:",   claim.get("drg_desc",""),   42, y+28, 300)
    ub04_field(pdf, "FL 58  INSURED ID:", claim["subscriber_id"],    310, y,    430)
    ub04_field(pdf, "FL 80  REMARKS:",    claim.get("remarks",""),   310, y+14, 430)

    y += 50
    pdf.hline(40, y, 572)

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.text(42, y+18, "PROVIDER SIGNATURE ON FILE", size=8)
    pdf.text(300, y+18, f"NPI: {claim['provider_npi']}", size=8)
    pdf.text(42, y+30, "THIS IS A MOCK DOCUMENT GENERATED FOR HACKATHON TESTING PURPOSES", size=7)

    pdf.write(str(path))
    print(f"  wrote {path.name}")


# ── Policy document helper ────────────────────────────────────────────────────

def make_policy(path, title: str, policy_id: str, effective: str, pages_content: list[list]):
    """
    pages_content: list of pages, each page is a list of (indent, text, bold, size) tuples.
    """
    pdf = PDF()

    def header(p: PDF):
        p.rect(40, 40, 532, 28, fill=False)
        p.text(42, 48, "PAYER CO", size=8, bold=True)
        p.text(42, 58, "CLINICAL POLICY & COVERAGE DOCUMENTATION", size=7)
        p.text(350, 48, f"Policy ID: {policy_id}", size=8)
        p.text(350, 58, f"Effective: {effective}", size=8)
        p.hline(40, 70, 572)

    def footer(p: PDF, page_num: int):
        p.hline(40, 752, 572)
        p.text(42,  760, "CONFIDENTIAL — INTERNAL USE ONLY", size=7)
        p.text(42,  770, "THIS IS A MOCK DOCUMENT GENERATED FOR HACKATHON TESTING PURPOSES", size=7)
        p.text(530, 770, f"Page {page_num}", size=7)

    for page_num, page_lines in enumerate(pages_content, 1):
        if page_num > 1:
            pdf.new_page()

        header(pdf)

        # Title on first page
        if page_num == 1:
            pdf.text(42, 90, title, size=14, bold=True)
            y = 115
        else:
            pdf.text(42, 90, f"{title} (continued)", size=11, bold=True)
            y = 110

        for (indent, text, bold, size) in page_lines:
            if text == "---":
                pdf.hline(42, y + 4, 570)
                y += 14
            elif text == "":
                y += 8
            else:
                pdf.text(42 + indent, y, text, size=size, bold=bold)
                y += size + 5

        footer(pdf, page_num)

    pdf.write(str(path))
    print(f"  wrote {path.name}")


# ── Hero claim data ────────────────────────────────────────────────────────────

HERO_1 = {
    "claim_id": "CLM2024-H001",
    "member_id": "MBR001",
    "subscriber_id": "SUB001",
    "patient_name": "SULLIVAN, MARGARET A",
    "dob": "1957-04-12",
    "sex": "F",
    "provider_npi": "1234567890",
    "provider_name": "STRONG MEMORIAL HOSPITAL",
    "claim_type": "UB04",
    "service_from_date": "2024-03-15",
    "service_to_date": "2024-03-19",
    "discharge_status": "01",
    "discharge_status_desc": "Discharged home",
    "drg_code": "470",
    "drg_desc": "Major Joint Replacement Lower Extremity w/o MCC",
    "total_billed_amount": 87500.00,
    "diagnosis_codes": ["M17.11", "E11.9", "I10", "Z96.641"],
    "procedure_codes": ["27447-RT"],
    "remarks": "RIGHT KNEE REPLACEMENT",
    "revenue_lines": [
        {"code": "0110", "desc": "Room & Board - Med/Surg",   "hcpcs": "",      "charge": 12800.00},
        {"code": "0360", "desc": "OR Services",                "hcpcs": "27447", "charge": 38200.00},
        {"code": "0370", "desc": "Anesthesia",                 "hcpcs": "00400", "charge": 4200.00},
        {"code": "0272", "desc": "Medical/Surgical Supplies",  "hcpcs": "",      "charge": 18900.00},
        {"code": "0730", "desc": "EKG / ECG",                  "hcpcs": "93005", "charge": 480.00},
        {"code": "0300", "desc": "Laboratory",                 "hcpcs": "",      "charge": 1820.00},
        {"code": "0320", "desc": "Radiology - Diagnostic",     "hcpcs": "",      "charge": 2100.00},
        {"code": "0420", "desc": "Physical Therapy",           "hcpcs": "",      "charge": 9000.00},
    ],
}

HERO_2 = {
    "claim_id": "CLM2024-H002",
    "member_id": "MBR002",
    "subscriber_id": "SUB002",
    "patient_name": "CHEN, ROBERT J",
    "dob": "1952-09-30",
    "sex": "M",
    "provider_npi": "2345678901",
    "provider_name": "ROCHESTER GENERAL HOSPITAL",
    "claim_type": "UB04",
    "service_from_date": "2024-06-10",
    "service_to_date": "2024-06-17",
    "discharge_status": "01",
    "discharge_status_desc": "Discharged home",
    "drg_code": "291",
    "drg_desc": "Heart Failure & Shock with MCC",
    "total_billed_amount": 74200.00,
    "diagnosis_codes": ["I50.9", "I10", "E11.65", "N18.5", "I50.43"],
    "procedure_codes": ["93306"],
    "remarks": "DECOMPENSATED CHF W/ DM/CKD COMORBIDITIES",
    "revenue_lines": [
        {"code": "0110", "desc": "Room & Board - Med/Surg ICU", "hcpcs": "",      "charge": 28000.00},
        {"code": "0300", "desc": "Laboratory",                  "hcpcs": "",      "charge": 4800.00},
        {"code": "0320", "desc": "Radiology - Diagnostic",      "hcpcs": "",      "charge": 3200.00},
        {"code": "0258", "desc": "IV Solutions",                "hcpcs": "",      "charge": 2400.00},
        {"code": "0260", "desc": "IV Therapy - Pharmacy",       "hcpcs": "",      "charge": 11600.00},
        {"code": "0730", "desc": "EKG / ECG",                   "hcpcs": "93010", "charge": 620.00},
        {"code": "0480", "desc": "Cardiology",                  "hcpcs": "93306", "charge": 8400.00},
        {"code": "0730", "desc": "Telemetry Monitoring",        "hcpcs": "",      "charge": 7200.00},
        {"code": "0636", "desc": "Drugs Detailed Coding",       "hcpcs": "",      "charge": 7980.00},
    ],
}


# ── Policy documents ──────────────────────────────────────────────────────────

L = 0    # no indent
I1 = 12  # indent level 1
I2 = 24  # indent level 2

def B(text, size=10): return (L, text, True, size)
def N(text, indent=L, size=10): return (indent, text, False, size)
def H(text): return B(text, 12)
def SUB(text): return B(text, 10)
def blank(): return N("")
def rule(): return (L, "---", False, 0)

POLICY_1_PAGES = [
    # Page 1
    [
        N("Policy Number: POL-ORTHO-2024-001 | Category: Prior Authorization | Department: Medical Management", size=8),
        blank(),
        H("1. PURPOSE"),
        rule(),
        N("This policy establishes the prior authorization requirements and medical necessity criteria"),
        N("for elective total and partial knee replacement procedures (arthroplasty) billed under"),
        N("DRG 470 (Major Joint Replacement Lower Extremity without MCC) and DRG 469 (with MCC)."),
        blank(),
        H("2. SCOPE"),
        rule(),
        N("Applies to all Payer Co commercial, Medicare Advantage, and Exchange plan members"),
        N("requiring elective orthopedic surgical intervention for osteoarthritis of the knee."),
        blank(),
        H("3. DEFINITIONS"),
        rule(),
        N("Total Knee Arthroplasty (TKA):", indent=I1),
        N("Surgical replacement of the knee joint with a prosthetic implant. CPT 27447 (total),", indent=I2, size=9),
        N("CPT 27446 (partial/unicompartmental).", indent=I2, size=9),
        blank(),
        N("DRG 470:", indent=I1),
        N("MS-DRG grouping for Major Joint Replacement Lower Extremity without Major Complication", indent=I2, size=9),
        N("or Comorbidity (MCC). Expected length of stay: 2-4 days.", indent=I2, size=9),
        blank(),
        N("Primary ICD-10 Indicators:", indent=I1),
        N("M17.11 - Primary osteoarthritis, right knee", indent=I2, size=9),
        N("M17.12 - Primary osteoarthritis, left knee", indent=I2, size=9),
        N("M17.31 - Secondary osteoarthritis, right knee", indent=I2, size=9),
        blank(),
        H("4. PRIOR AUTHORIZATION REQUIREMENTS"),
        rule(),
        SUB("4.1 Authorization is REQUIRED for:"),
        N("All elective TKA procedures regardless of facility type", indent=I1),
        N("Admission must be authorized prior to scheduled date of service", indent=I1),
        N("Authorization period: up to 4 days inpatient (standard TKA without complications)", indent=I1),
        N("Authorization number must appear in FL 63 of UB-04 claim form", indent=I1),
        blank(),
        SUB("4.2 Medical Necessity Criteria (ALL must be met):"),
        N("Documented moderate-to-severe knee OA (Kellgren-Lawrence Grade III or IV)", indent=I1),
        N("Functional limitation documented in medical record (pain at rest, limited ROM)", indent=I1),
        N("Failure of conservative therapy (minimum 3 months PT, NSAIDs, or injections)", indent=I1),
        N("BMI < 40 or documented weight management program if BMI 40-50", indent=I1),
        N("Medically stable for general or spinal anesthesia", indent=I1),
    ],
    # Page 2
    [
        H("5. AUTHORIZATION DURATION AND EXTENSION"),
        rule(),
        N("Standard authorization covers 3 days inpatient post-procedure."),
        N("Day 1 authorization covers day of surgery through expected Day 3 discharge."),
        blank(),
        N("Extension criteria — clinical review required for stays beyond 4 days:", indent=I1),
        N("Unexpected surgical complication (infection, DVT, PE)", indent=I2, size=9),
        N("Hemodynamic instability requiring monitoring", indent=I2, size=9),
        N("Inability to participate in PT (pain >7/10 uncontrolled)", indent=I2, size=9),
        N("New cardiac event post-operatively", indent=I2, size=9),
        blank(),
        N("NOTE: Unauthorized days beyond the approved authorization will be subject to", size=9),
        N("retrospective review and may result in denial. Providers must call 1-800-XXX-XXXX", size=9),
        N("for same-day extension requests.", size=9),
        blank(),
        H("6. AUDIT TRIGGERS"),
        rule(),
        N("The following patterns trigger automatic claims audit routing:"),
        N("Actual LOS exceeds authorized days by 1+ day without extension", indent=I1),
        N("Authorization dates do not overlap with claim statement dates (FL 6)", indent=I1),
        N("Rendering provider NPI on claim differs from requesting provider NPI on auth", indent=I1),
        N("Total charges exceed $100,000 for DRG 470 without MCC", indent=I1),
        blank(),
        H("7. CODING GUIDANCE"),
        rule(),
        N("Principal diagnosis must be the condition that required the admission after study."),
        N("Secondary diagnoses (E11.9, I10) should be coded when documented and treated."),
        N("Z96.641/Z96.642 (presence of joint implant) should be coded as secondary if applicable."),
        N("Discharge status must accurately reflect disposition (FL 17)."),
        blank(),
        H("8. REFERENCES"),
        rule(),
        N("CMS ICD-10-CM Official Guidelines for Coding and Reporting FY2024"),
        N("InterQual Criteria: Acute Care, Musculoskeletal — Knee Replacement"),
        N("Milliman Care Guidelines: Orthopedic Surgery"),
        N("CMS MS-DRG Grouper and Definitions Manual Version 41"),
    ],
]

POLICY_2_PAGES = [
    [
        N("Policy Number: POL-CARD-2024-008 | Category: Medical Necessity | Department: Medical Management", size=8),
        blank(),
        H("1. PURPOSE"),
        rule(),
        N("This policy defines medical necessity criteria for inpatient admission of members"),
        N("presenting with congestive heart failure (CHF) or acute decompensated heart failure"),
        N("(ADHF), billed under DRG 291 (Heart Failure & Shock with MCC) or DRG 292 (without MCC)."),
        blank(),
        H("2. MEDICAL NECESSITY CRITERIA FOR INPATIENT ADMISSION"),
        rule(),
        SUB("Any ONE of the following clinical indicators supports inpatient admission:"),
        N("O2 saturation < 90% on room air or requiring supplemental O2 > 2L/min", indent=I1),
        N("Heart rate > 120 bpm or < 50 bpm with hemodynamic compromise", indent=I1),
        N("Systolic BP < 90 mmHg (cardiogenic shock criteria)", indent=I1),
        N("BNP > 400 pg/mL or NT-proBNP > 1800 pg/mL on presentation", indent=I1),
        N("New or worsening renal failure (Cr increase > 0.5 mg/dL from baseline)", indent=I1),
        N("Requiring IV diuresis or vasoactive medications", indent=I1),
        blank(),
        H("3. EXPECTED LENGTH OF STAY"),
        rule(),
        N("Uncomplicated ADHF (DRG 292): 3-5 days"),
        N("ADHF with MCC (DRG 291): 5-8 days"),
        blank(),
        N("MCC for DRG 291 commonly includes:", indent=I1),
        N("Septicemia (A41.x) as secondary diagnosis", indent=I2, size=9),
        N("Acute respiratory failure (J96.0x)", indent=I2, size=9),
        N("Acute kidney failure (N17.x)", indent=I2, size=9),
        N("CKD Stage 4-5 (N18.4, N18.5) with acute decompensation", indent=I2, size=9),
        N("Diabetes with hyperglycemia (E11.65) requiring IV insulin", indent=I2, size=9),
        blank(),
        H("4. COMORBIDITY CODING — RISK ADJUSTMENT IMPLICATIONS"),
        rule(),
        N("The following secondary diagnoses affect HCC risk scores and must be coded"),
        N("accurately when present and treated during the admission:"),
        blank(),
        N("HCC 85 — Congestive Heart Failure (I50.x):", indent=I1),
        N("RAF weight: 0.331. Must document LVEF, ejection fraction type (systolic/diastolic).", indent=I2, size=9),
        blank(),
        N("HCC 136 — Chronic Kidney Disease Stage 5 (N18.5):", indent=I1),
        N("RAF weight: 0.289. Stage must be documented by treating physician.", indent=I2, size=9),
        blank(),
        N("HCC 18 — Diabetes with Chronic Complications (E11.65):", indent=I1),
        N("RAF weight: 0.302. Hyperglycemia treated with IV insulin qualifies.", indent=I2, size=9),
    ],
    [
        H("5. PRIOR AUTHORIZATION"),
        rule(),
        N("Emergency inpatient admissions for ADHF do not require prior authorization."),
        N("Planned admissions for elective catheterization or device implant during CHF workup"),
        N("require prior authorization under POL-CARD-2024-012."),
        blank(),
        N("Continued stay reviews are conducted at Day 3 for DRG 291 admissions."),
        N("Continued stay criteria must be documented in progress notes."),
        blank(),
        H("6. AUDIT TRIGGERS"),
        rule(),
        N("The following patterns trigger automatic claims audit routing:"),
        N("LOS > 10 days without documented complications or transfer note", indent=I1),
        N("DRG 291 billed without documented MCC in claim diagnosis field", indent=I1),
        N("HCC-qualifying diagnoses coded on claim but not documented in discharge summary", indent=I1),
        N("BNP / NT-proBNP not documented in chart for DRG 291 admission", indent=I1),
        N("Total charges > $90,000 for standard CHF admission", indent=I1),
        blank(),
        H("7. DISCHARGE PLANNING"),
        rule(),
        N("Discharge to home with HH services (FL 17 status 06): document HH order in chart."),
        N("Discharge to SNF (FL 17 status 03): 3-day qualifying inpatient stay required for Medicare."),
        N("Discharge to LTAC (FL 17 status 62): requires prior authorization."),
        blank(),
        H("8. REFERENCES"),
        rule(),
        N("ACC/AHA 2022 Guideline for Heart Failure Management"),
        N("InterQual Criteria: Acute Care, Cardiovascular — Heart Failure"),
        N("CMS ICD-10-CM Official Guidelines FY2024, Section I.C.9"),
        N("CMS-HCC Risk Adjustment Model V28 (2024)"),
    ],
]

POLICY_3_PAGES = [
    [
        N("Policy Number: POL-BEN-2024-015 | Category: Benefits Administration | Department: Claims", size=8),
        blank(),
        H("1. PURPOSE"),
        rule(),
        N("This policy defines how Payer Co calculates, tracks, and reconciles out-of-pocket"),
        N("(OOP) maximum accumulators across plan years, including the process for identifying"),
        N("and correcting discrepancies between the Facets claims system and Cognos reporting."),
        blank(),
        H("2. OOP MAXIMUM DEFINITION"),
        rule(),
        N("The annual OOP maximum is the most a member will pay for covered services in a plan year."),
        N("After reaching the OOP maximum, Payer Co pays 100% of covered in-network costs."),
        blank(),
        N("Amounts that count toward OOP maximum:", indent=I1),
        N("Deductible payments", indent=I2, size=9),
        N("Copayments for covered services", indent=I2, size=9),
        N("Coinsurance for covered services", indent=I2, size=9),
        blank(),
        N("Amounts that do NOT count toward OOP maximum:", indent=I1),
        N("Premiums", indent=I2, size=9),
        N("Out-of-network cost-sharing (for HMO plans)", indent=I2, size=9),
        N("Non-covered services", indent=I2, size=9),
        N("Balance billing from non-participating providers", indent=I2, size=9),
        blank(),
        H("3. ACCUMULATOR SOURCES OF TRUTH"),
        rule(),
        N("Primary system: Facets claims administration system"),
        N("  - Updated in real-time as claims are adjudicated", indent=I1, size=9),
        N("  - Member portal display is sourced from Facets", indent=I1, size=9),
        blank(),
        N("Secondary system: Cognos BI reporting (accumulator_report extract)"),
        N("  - Refreshed nightly via batch extract from Facets", indent=I1, size=9),
        N("  - Used for audit reporting and regulatory filings", indent=I1, size=9),
        N("  - Lag of up to 24 hours versus Facets real-time balance", indent=I1, size=9),
        blank(),
        H("4. KNOWN DISCREPANCY SCENARIOS"),
        rule(),
        N("The following scenarios can cause Cognos to differ from Facets:"),
        blank(),
        N("Scenario A — Adjusted Claims:", indent=I1),
        N("Claim adjusted after nightly Cognos extract runs. Facets is correct;", indent=I2, size=9),
        N("Cognos will reconcile on next nightly run.", indent=I2, size=9),
        blank(),
        N("Scenario B — Reversed Claims:", indent=I1),
        N("Claim reversal processed same day as Cognos extract. Accumulator may be", indent=I2, size=9),
        N("double-counted in Cognos until next reconciliation cycle.", indent=I2, size=9),
        blank(),
        N("Scenario C — Coordination of Benefits (COB):", indent=I1),
        N("COB adjustments may reduce accumulated amounts retroactively.", indent=I2, size=9),
        N("Facets applies COB in real time; Cognos may show pre-COB balance.", indent=I2, size=9),
    ],
    [
        H("5. ACCUMULATOR AUDIT PROCESS"),
        rule(),
        N("The high-dollar claims audit pipeline flags members where:"),
        N("abs(facets_accumulated - cognos_accumulated) / facets_accumulated > 0.05  (>5% variance)", indent=I1, size=9),
        N("OR facets_accumulated > oop_max_individual * 0.90  (within 10% of OOP cap)", indent=I1, size=9),
        blank(),
        N("Auditor workflow for each flagged member:"),
        N("Step 1: Review claim_history for 90-day window (use service_from_date)", indent=I1),
        N("Step 2: Confirm claim_type filter: professional + institutional (exclude pharmacy)", indent=I1),
        N("Step 3: Compare line-level allowed amounts to Cognos report rows", indent=I1),
        N("Step 4: If discrepancy > $100, escalate to Claims Adjustment team", indent=I1),
        N("Step 5: Document finding in audit_decisions table with evidence record", indent=I1),
        blank(),
        H("6. 90-DAY LOOKBACK WINDOW DEFINITION"),
        rule(),
        N("The 90-day lookback for accumulator validation uses SERVICE_FROM_DATE,"),
        N("not paid_date or processed_date. This is the regulatory requirement."),
        blank(),
        N("Date edge cases:", indent=I1),
        N("If service spans multiple calendar years, split accumulation by plan year", indent=I2, size=9),
        N("COB primary/secondary must be applied before accumulator comparison", indent=I2, size=9),
        N("Late charges (billed > 90 days post-service) count toward service year", indent=I2, size=9),
        blank(),
        H("7. WRITE-BACK AUTHORIZATION"),
        rule(),
        N("Accumulator corrections in Facets require:"),
        N("Supervisor approval for corrections > $500", indent=I1),
        N("Medical Director approval for corrections > $5,000", indent=I1),
        N("Regulatory filing for corrections affecting MLR calculation", indent=I1),
        blank(),
        N("Automated correction via the AI audit pipeline is NOT permitted."),
        N("The pipeline produces recommendations; human auditor executes correction in Facets."),
        blank(),
        H("8. REFERENCES"),
        rule(),
        N("ACA Section 1302(c) — Annual Limitation on Cost-Sharing"),
        N("CMS 2024 OOP Maximum Limits: Individual $9,450 / Family $18,900"),
        N("Payer Co Benefits Administration Manual, Chapter 7"),
        N("NAIC Model Accumulator Rule (adopted NY 2023)"),
    ],
]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Generating UB-04 paper claim PDFs…")
    make_ub04(OUT_CLAIMS / "IMG00001.pdf", HERO_1)
    make_ub04(OUT_CLAIMS / "IMG00002.pdf", HERO_2)

    print("\nGenerating SharePoint policy documents…")
    make_policy(
        OUT_POLICIES / "POL-ORTHO-2024-001_knee_replacement_prior_auth.pdf",
        "Prior Authorization Policy: Elective Knee Replacement (DRG 470/469)",
        "POL-ORTHO-2024-001", "2024-01-01",
        POLICY_1_PAGES,
    )
    make_policy(
        OUT_POLICIES / "POL-CARD-2024-008_heart_failure_admission_criteria.pdf",
        "Medical Necessity Criteria: Heart Failure Inpatient Admission (DRG 291/292)",
        "POL-CARD-2024-008", "2024-01-01",
        POLICY_2_PAGES,
    )
    make_policy(
        OUT_POLICIES / "POL-BEN-2024-015_oop_accumulator_policy.pdf",
        "Out-of-Pocket Maximum Accumulator Policy and Audit Process",
        "POL-BEN-2024-015", "2024-01-01",
        POLICY_3_PAGES,
    )

    print("\nDone.")

if __name__ == "__main__":
    main()
