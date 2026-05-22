"""
Regenerates all CSV/JSON seed data centered on 2 hero claims.
Hero claims are pre-defined with deliberate discrepancies baked in.
Supporting rows (other members, history) fill out the tables realistically.

Run from the generate/ directory: python3 generate_seed_data.py
"""

import csv, json, os, random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUT = Path(__file__).parent.parent / "seed_data"

def fmt(d): return d.isoformat()
def rd(start, end):
    s = date.fromisoformat(start); e = date.fromisoformat(end)
    return s + timedelta(days=random.randint(0, (e - s).days))

def write_csv(rel, rows, drop_private=True):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows: return
    fields = [k for k in rows[0] if not (drop_private and k.startswith("_"))]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(f"  {len(rows):>3} rows → {path.relative_to(Path(__file__).parent.parent)}")

def write_json(rel, data):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = [{k: v for k, v in r.items() if not k.startswith("_")} for r in data]
    with open(path, "w") as f: json.dump(clean, f, indent=2, default=str)
    print(f"  {len(clean):>3} records → {path.relative_to(Path(__file__).parent.parent)}")

# ── Hero claims (pre-defined, internally consistent) ──────────────────────────

HERO_CLAIMS = [
    {
        "claim_id":            "CLM2024-H001",
        "member_id":           "MBR001",
        "subscriber_id":       "SUB001",
        "provider_id":         "1234567890",
        "provider_name":       "Strong Memorial Hospital",
        "claim_type":          "UB04",
        "total_billed_amount": 87500.00,
        "total_allowed_amount":52200.00,
        "drg_code":            "470",
        "drg_days":            4,
        "service_from_date":   "2024-03-15",
        "service_to_date":     "2024-03-19",
        "discharge_status":    "01",
        "primary_diagnosis":   "M17.11",
        "secondary_diagnoses": "E11.9|I10|Z96.641",
        "micro_image_id":      "IMG00001",
        "processed_date":      "2024-04-02",
        "claim_status":        "paid",
    },
    {
        "claim_id":            "CLM2024-H002",
        "member_id":           "MBR002",
        "subscriber_id":       "SUB002",
        "provider_id":         "2345678901",
        "provider_name":       "Rochester General Hospital",
        "claim_type":          "UB04",
        "total_billed_amount": 74200.00,
        "total_allowed_amount":44800.00,
        "drg_code":            "291",
        "drg_days":            7,
        "service_from_date":   "2024-06-10",
        "service_to_date":     "2024-06-17",
        "discharge_status":    "01",
        "primary_diagnosis":   "I50.9",
        "secondary_diagnoses": "I10|E11.65|N18.5|I50.43",
        "micro_image_id":      "IMG00002",
        "processed_date":      "2024-07-01",
        "claim_status":        "paid",
    },
]

# Hero auth records — H001 has a deliberate discrepancy (authorized_days=3, actual LOS=4)
HERO_AUTHS = [
    {
        "claim_id":                "CLM2024-H001",
        "auth_ref_number":         "AUTH00001",
        "member_id":               "MBR001",
        "auth_status":             "approved",
        "auth_from_date":          "2024-03-15",
        "auth_to_date":            "2024-03-17",   # ← 3 days authorized, claim shows 4-day LOS
        "authorized_days":         3,
        "authorized_amount":       36500.00,       # ← ~30% under actual allowed ($52,200)
        "requesting_provider_npi": "1234567890",
        "decision_support_reviewed": True,
        "_note": "DISCREPANCY: auth covers 3 days, actual LOS 4 days; auth amount < allowed",
    },
    {
        "claim_id":                "CLM2024-H002",
        "auth_ref_number":         "AUTH00002",
        "member_id":               "MBR002",
        "auth_status":             "approved",
        "auth_from_date":          "2024-06-10",
        "auth_to_date":            "2024-06-17",   # matches exactly
        "authorized_days":         7,
        "authorized_amount":       44800.00,       # matches allowed
        "requesting_provider_npi": "2345678901",
        "decision_support_reviewed": True,
        "_note": "clean — no discrepancy",
    },
]

# Hero Care Advance records — H001 has provider NPI mismatch + date shift
HERO_CARE_ADVANCE = [
    {
        "auth_ref_number":           "AUTH00001",
        "member_id":                 "MBR001",
        "requesting_provider_npi":   "1234567890",
        "rendering_provider_npi":    "9876543210",   # ← different from requesting NPI on claim
        "provider_name":             "Strong Memorial Hospital",
        "diagnosis_codes":           ["M17.11", "E11.9"],
        "procedure_codes":           ["27447"],
        "service_codes":             ["inpatient_stay"],
        "auth_from_date":            "2024-03-15",
        "auth_to_date":              "2024-03-17",
        "authorized_days":           3,
        "services_rendered":         "total knee arthroplasty right",
        "approval_status":           "approved",
        "decision_support_reviewed": True,
        "decision_date":             "2024-03-10",
        "_note": "DISCREPANCY: rendering NPI differs from Facets; only 3 days authorized vs 4-day stay",
    },
    {
        "auth_ref_number":           "AUTH00002",
        "member_id":                 "MBR002",
        "requesting_provider_npi":   "2345678901",
        "rendering_provider_npi":    "2345678901",
        "provider_name":             "Rochester General Hospital",
        "diagnosis_codes":           ["I50.9", "I10", "E11.65", "N18.5"],
        "procedure_codes":           ["93306"],
        "service_codes":             ["inpatient_stay"],
        "auth_from_date":            "2024-06-10",
        "auth_to_date":              "2024-06-17",
        "authorized_days":           7,
        "services_rendered":         "inpatient hospitalization for decompensated CHF",
        "approval_status":           "approved",
        "decision_support_reviewed": True,
        "decision_date":             "2024-06-09",
        "_note": "clean",
    },
]

# Hero benefit summaries
HERO_BENEFITS = [
    {
        "member_id": "MBR001", "plan_id": "PPO-GOLD", "plan_year": 2024,
        "copay_amount": 30, "coinsurance_pct": 0.20,
        "oop_max_individual": 5000.00, "oop_max_family": 10000.00,
        "deductible_individual": 1000.00, "deductible_family": 2000.00,
        "benefit_effective_date": "2024-01-01",
    },
    {
        "member_id": "MBR002", "plan_id": "HMO-SILVER", "plan_year": 2024,
        "copay_amount": 40, "coinsurance_pct": 0.30,
        "oop_max_individual": 5000.00, "oop_max_family": 10000.00,
        "deductible_individual": 2000.00, "deductible_family": 4000.00,
        "benefit_effective_date": "2024-01-01",
    },
]

# Hero accumulators — MBR001 near OOP max; MBR002 over OOP max
HERO_ACCUMULATORS = [
    {
        "member_id": "MBR001", "subscriber_id": "SUB001",
        "plan_id": "PPO-GOLD", "plan_year": 2024,
        "accumulator_type": "OOP",
        "service_effective_date": "2024-03-19",
        "accumulated_amount": 4850.00,           # $150 under $5,000 max
        "family_accumulated_amount": 6200.00,
        "last_updated_ts": "2024-04-02T18:00:00Z",
    },
    {
        "member_id": "MBR001", "subscriber_id": "SUB001",
        "plan_id": "PPO-GOLD", "plan_year": 2024,
        "accumulator_type": "deductible",
        "service_effective_date": "2024-01-15",
        "accumulated_amount": 1000.00,           # fully met
        "family_accumulated_amount": 2000.00,
        "last_updated_ts": "2024-04-02T18:00:00Z",
    },
    {
        "member_id": "MBR002", "subscriber_id": "SUB002",
        "plan_id": "HMO-SILVER", "plan_year": 2024,
        "accumulator_type": "OOP",
        "service_effective_date": "2024-06-17",
        "accumulated_amount": 5420.00,           # $420 OVER $5,000 max → overpayment
        "family_accumulated_amount": 8900.00,
        "last_updated_ts": "2024-07-01T18:00:00Z",
    },
    {
        "member_id": "MBR002", "subscriber_id": "SUB002",
        "plan_id": "HMO-SILVER", "plan_year": 2024,
        "accumulator_type": "deductible",
        "service_effective_date": "2024-02-20",
        "accumulated_amount": 2000.00,           # fully met
        "family_accumulated_amount": 4000.00,
        "last_updated_ts": "2024-07-01T18:00:00Z",
    },
]

# Cognos — MBR002 shows $4,750 (vs Facets $5,420 → $670 discrepancy)
HERO_COGNOS = [
    {
        "subscriber_id": "SUB001", "member_id": "MBR001",
        "member_name": "SULLIVAN, MARGARET A",
        "plan_id": "PPO-GOLD", "plan_year": 2024, "benefit_type": "OOP",
        "service_effective_date": "2024-03-19",
        "accumulated_amount": 4850.00,           # matches Facets (clean)
        "family_accumulated_amount": 6200.00,
        "claim_count": 4, "last_claim_date": "2024-04-02",
    },
    {
        "subscriber_id": "SUB002", "member_id": "MBR002",
        "member_name": "CHEN, ROBERT J",
        "plan_id": "HMO-SILVER", "plan_year": 2024, "benefit_type": "OOP",
        "service_effective_date": "2024-06-17",
        "accumulated_amount": 4750.00,           # ← DISCREPANCY: Facets=$5,420, Cognos=$4,750
        "family_accumulated_amount": 8100.00,
        "claim_count": 6, "last_claim_date": "2024-07-01",
        "_discrepancy": "Cognos missing $670 vs Facets — likely reversed claim not reflected",
    },
]

# Hero claim history (90-day lookback context)
HERO_HISTORY = [
    # MBR001 prior claims feeding into OOP accumulation
    {"member_id":"MBR001","subscriber_id":"SUB001","claim_id":"HIST001A",
     "service_from_date":"2024-01-08","service_to_date":"2024-01-08",
     "claim_type":"CMS1500","allowed_amount":280.00,"paid_amount":250.00,"provider_id":"5678901234"},
    {"member_id":"MBR001","subscriber_id":"SUB001","claim_id":"HIST001B",
     "service_from_date":"2024-02-14","service_to_date":"2024-02-14",
     "claim_type":"CMS1500","allowed_amount":420.00,"paid_amount":336.00,"provider_id":"5678901234"},
    {"member_id":"MBR001","subscriber_id":"SUB001","claim_id":"HIST001C",
     "service_from_date":"2024-03-01","service_to_date":"2024-03-01",
     "claim_type":"CMS1500","allowed_amount":310.00,"paid_amount":248.00,"provider_id":"5678901234"},
    # MBR002 prior claims
    {"member_id":"MBR002","subscriber_id":"SUB002","claim_id":"HIST002A",
     "service_from_date":"2024-03-22","service_to_date":"2024-03-22",
     "claim_type":"CMS1500","allowed_amount":890.00,"paid_amount":623.00,"provider_id":"3456789012"},
    {"member_id":"MBR002","subscriber_id":"SUB002","claim_id":"HIST002B",
     "service_from_date":"2024-04-15","service_to_date":"2024-04-15",
     "claim_type":"CMS1500","allowed_amount":1240.00,"paid_amount":868.00,"provider_id":"3456789012"},
    {"member_id":"MBR002","subscriber_id":"SUB002","claim_id":"HIST002C",
     "service_from_date":"2024-05-30","service_to_date":"2024-05-31",
     "claim_type":"UB04","allowed_amount":8400.00,"paid_amount":5880.00,"provider_id":"2345678901"},
]

# ── Supporting members (background noise) ─────────────────────────────────────

PROVIDERS = [
    {"npi":"1234567890","name":"Strong Memorial Hospital"},
    {"npi":"2345678901","name":"Rochester General Hospital"},
    {"npi":"3456789012","name":"Unity Hospital"},
    {"npi":"4567890123","name":"Thompson Health"},
    {"npi":"5678901234","name":"Highland Hospital"},
]

SUPPORT_MEMBERS = [
    {"member_id":f"MBR{i:03d}","subscriber_id":f"SUB{i:03d}",
     "plan_id":random.choice(["PPO-GOLD","HMO-SILVER","HMO-BRONZE"]),
     "plan_year":2024}
    for i in range(3, 11)
]

def make_support_data():
    claims, auths, benefits, accumulators, history, cognos = [], [], [], [], [], []
    for i, m in enumerate(SUPPORT_MEMBERS, 3):
        cid = f"CLM2024-S{i:03d}"
        prov = random.choice(PROVIDERS)
        svc = rd("2024-01-01","2024-10-31")
        los = random.randint(2, 8)
        billed = round(random.uniform(15000, 120000), 2)
        allowed = round(billed * random.uniform(0.45, 0.65), 2)
        drg = random.choice(["470","291","871","392","603","190"])

        claims.append({
            "claim_id": cid, "member_id": m["member_id"],
            "subscriber_id": m["subscriber_id"], "provider_id": prov["npi"],
            "provider_name": prov["name"], "claim_type": "UB04",
            "total_billed_amount": billed, "total_allowed_amount": allowed,
            "drg_code": drg, "drg_days": los,
            "service_from_date": fmt(svc), "service_to_date": fmt(svc + timedelta(days=los)),
            "discharge_status": "01", "primary_diagnosis": random.choice(["M17.11","I50.9","A41.9","J44.1"]),
            "secondary_diagnoses": "E11.9|I10",
            "micro_image_id": f"IMG{i:05d}" if random.random() < 0.5 else "",
            "processed_date": fmt(svc + timedelta(days=random.randint(5,25))),
            "claim_status": "paid",
        })

        if billed > 30000:
            auths.append({
                "claim_id": cid, "auth_ref_number": f"AUTH{i:05d}",
                "member_id": m["member_id"], "auth_status": "approved",
                "auth_from_date": fmt(svc), "auth_to_date": fmt(svc + timedelta(days=los)),
                "authorized_days": los,
                "authorized_amount": round(allowed * 1.02, 2),
                "requesting_provider_npi": prov["npi"],
                "decision_support_reviewed": False,
            })

        oop_max = random.choice([3000, 5000, 7500])
        accumulated = round(oop_max * random.uniform(0.3, 0.95), 2)
        benefits.append({
            "member_id": m["member_id"], "plan_id": m["plan_id"], "plan_year": 2024,
            "copay_amount": 30, "coinsurance_pct": 0.20,
            "oop_max_individual": oop_max, "oop_max_family": oop_max * 2,
            "deductible_individual": 1500, "deductible_family": 3000,
            "benefit_effective_date": "2024-01-01",
        })
        accumulators.append({
            "member_id": m["member_id"], "subscriber_id": m["subscriber_id"],
            "plan_id": m["plan_id"], "plan_year": 2024, "accumulator_type": "OOP",
            "service_effective_date": fmt(svc),
            "accumulated_amount": accumulated,
            "family_accumulated_amount": round(accumulated * 1.6, 2),
            "last_updated_ts": fmt(svc + timedelta(days=5)) + "T00:00:00Z",
        })
        cognos.append({
            "subscriber_id": m["subscriber_id"], "member_id": m["member_id"],
            "member_name": f"PATIENT {m['member_id']}", "plan_id": m["plan_id"],
            "plan_year": 2024, "benefit_type": "OOP",
            "service_effective_date": fmt(svc),
            "accumulated_amount": accumulated,  # no discrepancy for support members
            "family_accumulated_amount": round(accumulated * 1.6, 2),
            "claim_count": random.randint(1, 5),
            "last_claim_date": fmt(svc + timedelta(days=5)),
        })
        for _ in range(random.randint(1, 3)):
            h_date = svc - timedelta(days=random.randint(1, 90))
            history.append({
                "member_id": m["member_id"], "subscriber_id": m["subscriber_id"],
                "claim_id": f"HIST{i:03d}{random.randint(10,99)}",
                "service_from_date": fmt(h_date),
                "service_to_date": fmt(h_date + timedelta(days=random.randint(0, 3))),
                "claim_type": random.choice(["UB04","CMS1500"]),
                "allowed_amount": round(random.uniform(300, 20000), 2),
                "paid_amount": round(random.uniform(200, 15000), 2),
                "provider_id": random.choice(PROVIDERS)["npi"],
            })

    return claims, auths, benefits, accumulators, history, cognos

# ── CMS reference data ────────────────────────────────────────────────────────

ICD10_ROWS = [
    ("M17.11","Primary osteoarthritis, right knee","M17","Gonarthrosis","Musculoskeletal",True),
    ("M17.12","Primary osteoarthritis, left knee","M17","Gonarthrosis","Musculoskeletal",True),
    ("Z96.641","Presence of right artificial knee joint","Z96","Presence of functional implants","Factors influencing health",True),
    ("E11.9","Type 2 diabetes mellitus without complications","E11","Type 2 diabetes mellitus","Endocrine",True),
    ("E11.65","Type 2 diabetes mellitus with hyperglycemia","E11","Type 2 diabetes mellitus","Endocrine",True),
    ("I10","Essential (primary) hypertension","I10","Essential hypertension","Circulatory",True),
    ("I50.9","Heart failure, unspecified","I50","Heart failure","Circulatory",True),
    ("I50.32","Chronic diastolic heart failure","I50","Heart failure","Circulatory",True),
    ("I50.43","Acute on chronic combined systolic and diastolic HF","I50","Heart failure","Circulatory",True),
    ("N18.5","Chronic kidney disease, stage 5","N18","Chronic kidney disease","Genitourinary",True),
    ("A41.9","Sepsis, unspecified organism","A41","Other sepsis","Infectious",True),
    ("J44.1","COPD with (acute) exacerbation","J44","Chronic obstructive pulmonary disease","Respiratory",True),
    ("I21.09","ST elevation MI involving other coronary artery","I21","Acute myocardial infarction","Circulatory",True),
    ("L03.115","Cellulitis of right lower limb","L03","Cellulitis and acute lymphangitis","Skin",True),
    ("K92.1","Melena","K92","Other diseases of digestive system","Digestive",True),
]

HCC_ROWS = [
    ("M17.11",0,"No HCC mapping",0.0,2024),
    ("M17.12",0,"No HCC mapping",0.0,2024),
    ("E11.9",19,"Diabetes without Complications",0.104,2024),
    ("E11.65",18,"Diabetes with Chronic Complications",0.302,2024),
    ("I10",0,"No HCC mapping",0.0,2024),
    ("I50.9",85,"Congestive Heart Failure",0.331,2024),
    ("I50.32",85,"Congestive Heart Failure",0.331,2024),
    ("I50.43",85,"Congestive Heart Failure",0.331,2024),
    ("N18.5",136,"Chronic Kidney Disease Stage 5",0.289,2024),
    ("A41.9",2,"Septicemia/Sepsis/SIRS/Shock",0.514,2024),
    ("J44.1",111,"Chronic Obstructive Pulmonary Disease",0.335,2024),
    ("I21.09",86,"Acute Myocardial Infarction",0.248,2024),
]

CCS_ROWS = [
    ("M17.11",203,"Osteoarthritis",True),
    ("M17.12",203,"Osteoarthritis",True),
    ("E11.9",49,"Diabetes mellitus without complication",False),
    ("E11.65",49,"Diabetes mellitus without complication",False),
    ("I10",98,"Essential hypertension",True),
    ("I50.9",108,"Congestive heart failure; nonhypertensive",True),
    ("I50.32",108,"Congestive heart failure; nonhypertensive",True),
    ("N18.5",158,"Chronic kidney disease",True),
    ("A41.9",2,"Septicemia (except in labor)",False),
    ("J44.1",127,"COPD and bronchiectasis",True),
    ("I21.09",100,"Acute myocardial infarction",False),
]

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Building hero-claim-centered seed data…\n")

    s_claims, s_auths, s_benefits, s_accumulators, s_history, s_cognos = make_support_data()

    # Facets
    write_csv("facets/claim_header.csv",    HERO_CLAIMS + s_claims)
    write_csv("facets/auth_summary.csv",    HERO_AUTHS + s_auths)
    write_csv("facets/benefit_summary.csv", HERO_BENEFITS + s_benefits)
    write_csv("facets/accumulators.csv",    HERO_ACCUMULATORS + s_accumulators)
    write_csv("facets/claim_history.csv",   HERO_HISTORY + s_history)

    # Care Advance
    s_ca = [
        {
            "auth_ref_number": a["auth_ref_number"], "member_id": a["member_id"],
            "requesting_provider_npi": a["requesting_provider_npi"],
            "rendering_provider_npi":  a["requesting_provider_npi"],
            "provider_name": next(p["name"] for p in PROVIDERS if p["npi"]==a["requesting_provider_npi"]),
            "diagnosis_codes": ["I50.9"], "procedure_codes": ["99233"],
            "service_codes": ["inpatient_stay"],
            "auth_from_date": a["auth_from_date"], "auth_to_date": a["auth_to_date"],
            "authorized_days": a["authorized_days"],
            "services_rendered": "inpatient hospitalization",
            "approval_status": a["auth_status"],
            "decision_support_reviewed": a["decision_support_reviewed"],
            "decision_date": a["auth_from_date"],
        }
        for a in s_auths
    ]
    write_json("care_advance/authorizations.json", HERO_CARE_ADVANCE + s_ca)

    # Cognos
    write_csv("cognos/accumulator_report.csv", HERO_COGNOS + s_cognos)

    # CMS public data
    icd10 = [{"icd10_code":r[0],"code_description":r[1],"category_code":r[2],
               "category_description":r[3],"chapter":r[4],"is_billable":r[5],
               "effective_date":"2024-10-01","expiration_date":""} for r in ICD10_ROWS]
    write_csv("cms_public/icd10_hierarchy.csv", icd10)

    hcc = [{"icd10_code":r[0],"hcc_category":r[1],"hcc_description":r[2],
             "raf_weight":r[3],"model_year":r[4]} for r in HCC_ROWS]
    write_csv("cms_public/hcc_mappings.csv", hcc)

    ccs = [{"icd10_code":r[0],"ccs_category":r[1],"ccs_label":r[2],"is_chronic":r[3]} for r in CCS_ROWS]
    write_csv("cms_public/ccs_categories.csv", ccs)

    # Quick Claim manifest (heroes + any support with image IDs)
    manifest = [
        {"image_id":"IMG00001","claim_id":"CLM2024-H001","member_id":"MBR001",
         "form_type":"UB04","file_path":"seed_data/quick_claim/images/IMG00001.pdf",
         "file_format":"PDF","received_date":"2024-03-22"},
        {"image_id":"IMG00002","claim_id":"CLM2024-H002","member_id":"MBR002",
         "form_type":"UB04","file_path":"seed_data/quick_claim/images/IMG00002.pdf",
         "file_format":"PDF","received_date":"2024-06-19"},
    ] + [
        {"image_id":c["micro_image_id"],"claim_id":c["claim_id"],"member_id":c["member_id"],
         "form_type":c["claim_type"],"file_path":f"seed_data/quick_claim/images/{c['micro_image_id']}.pdf",
         "file_format":"PDF","received_date":c["service_to_date"]}
        for c in s_claims if c["micro_image_id"]
    ]
    write_csv("quick_claim/paper_claim_manifest.csv", manifest)

    print(f"\nHero discrepancies:")
    print("  CLM2024-H001: auth covers 3 days (actual LOS=4), auth_amount=$36,500 (allowed=$52,200), Care Advance NPI mismatch")
    print("  CLM2024-H002: Facets OOP=$5,420 vs Cognos OOP=$4,750 ($670 gap, member over OOP max)")

if __name__ == "__main__":
    main()
