from pathlib import Path

import pandas as pd

print("=" * 70)
print("DAY 31 - NLP QUALITY VALIDATION")
print("=" * 70)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "output" / "pros_cons_generated.csv"
OUTPUT_FILE = BASE_DIR / "output" / "nlp_quality_report.csv"


# ============================================================
# LOAD DATA
# ============================================================

df = pd.read_csv(INPUT_FILE)

print("\nInput File:")
print(INPUT_FILE)

print("\nRows:", len(df))
print("Companies:", df["company_id"].nunique())


# ============================================================
# VALIDATION CHECKS
# ============================================================

total_companies = df["company_id"].nunique()

missing_company = df["company_id"].isna().sum()

missing_type = df["type"].isna().sum()

missing_rule = df["rule_id"].isna().sum()

missing_text = df["text"].isna().sum()

blank_text = (
    df["text"]
    .astype(str)
    .str.strip()
    .eq("")
    .sum()
)

missing_confidence = df["confidence_pct"].isna().sum()

invalid_confidence = (
    (~df["confidence_pct"].between(0, 100))
    .sum()
)

invalid_type = (
    (~df["type"].isin(["pro", "con"]))
    .sum()
)


# ============================================================
# COMPANY COVERAGE
# ============================================================

companies = set(
    df["company_id"]
    .dropna()
    .astype(str)
    .str.strip()
)

pro_companies = set(
    df.loc[
        df["type"] == "pro",
        "company_id"
    ]
    .dropna()
    .astype(str)
    .str.strip()
)

con_companies = set(
    df.loc[
        df["type"] == "con",
        "company_id"
    ]
    .dropna()
    .astype(str)
    .str.strip()
)

companies_without_pro = sorted(
    companies - pro_companies
)

companies_without_con = sorted(
    companies - con_companies
)


# ============================================================
# DUPLICATE RULE CHECK
# ============================================================

duplicate_rules = (
    df
    .groupby(
        ["company_id", "type", "rule_id"]
    )
    .size()
)

duplicate_rule_count = (
    duplicate_rules > 1
).sum()


# ============================================================
# RULE DISTRIBUTION
# ============================================================

pro_count = (
    df[df["type"] == "pro"]
    .shape[0]
)

con_count = (
    df[df["type"] == "con"]
    .shape[0]
)


# ============================================================
# QUALITY SCORE
# ============================================================

checks = {
    "total_companies_92": total_companies == 92,
    "missing_company": missing_company == 0,
    "missing_type": missing_type == 0,
    "missing_rule": missing_rule == 0,
    "missing_text": missing_text == 0,
    "blank_text": blank_text == 0,
    "missing_confidence": missing_confidence == 0,
    "invalid_confidence": invalid_confidence == 0,
    "invalid_type": invalid_type == 0,
    "all_companies_have_pro": len(companies_without_pro) == 0,
    "all_companies_have_con": len(companies_without_con) == 0,
}


passed_checks = sum(checks.values())

total_checks = len(checks)

quality_score = (
    passed_checks / total_checks
) * 100


# ============================================================
# REPORT DATAFRAME
# ============================================================

report = pd.DataFrame(
    [
        {
            "check": "Total Records",
            "value": len(df),
            "status": "INFO"
        },
        {
            "check": "Total Companies",
            "value": total_companies,
            "status": "PASS"
            if total_companies == 92
            else "FAIL"
        },
        {
            "check": "Pros",
            "value": pro_count,
            "status": "INFO"
        },
        {
            "check": "Cons",
            "value": con_count,
            "status": "INFO"
        },
        {
            "check": "Missing Company IDs",
            "value": missing_company,
            "status": "PASS"
            if missing_company == 0
            else "FAIL"
        },
        {
            "check": "Missing Types",
            "value": missing_type,
            "status": "PASS"
            if missing_type == 0
            else "FAIL"
        },
        {
            "check": "Missing Rule IDs",
            "value": missing_rule,
            "status": "PASS"
            if missing_rule == 0
            else "FAIL"
        },
        {
            "check": "Missing Text",
            "value": missing_text,
            "status": "PASS"
            if missing_text == 0
            else "FAIL"
        },
        {
            "check": "Blank Text",
            "value": blank_text,
            "status": "PASS"
            if blank_text == 0
            else "FAIL"
        },
        {
            "check": "Missing Confidence",
            "value": missing_confidence,
            "status": "PASS"
            if missing_confidence == 0
            else "FAIL"
        },
        {
            "check": "Invalid Confidence",
            "value": invalid_confidence,
            "status": "PASS"
            if invalid_confidence == 0
            else "FAIL"
        },
        {
            "check": "Invalid Type",
            "value": invalid_type,
            "status": "PASS"
            if invalid_type == 0
            else "FAIL"
        },
        {
            "check": "Companies Without Pro",
            "value": len(companies_without_pro),
            "status": "PASS"
            if len(companies_without_pro) == 0
            else "FAIL"
        },
        {
            "check": "Companies Without Con",
            "value": len(companies_without_con),
            "status": "PASS"
            if len(companies_without_con) == 0
            else "FAIL"
        },
        {
            "check": "Duplicate Company/Type/Rule",
            "value": duplicate_rule_count,
            "status": "PASS"
            if duplicate_rule_count == 0
            else "WARNING"
        },
        {
            "check": "Quality Score",
            "value": round(quality_score, 2),
            "status": "PASS"
            if quality_score == 100
            else "WARNING"
        },
    ]
)


# ============================================================
# SAVE REPORT
# ============================================================

report.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# DISPLAY
# ============================================================

print("\n" + "=" * 70)
print("NLP QUALITY REPORT")
print("=" * 70)

print(report.to_string(index=False))

print("\nCompanies Without Pro:")
print(companies_without_pro)

print("\nCompanies Without Con:")
print(companies_without_con)

print("\nDuplicate Rules:", duplicate_rule_count)

print("\nQuality Score:", round(quality_score, 2), "%")

print("\nOutput:")
print(OUTPUT_FILE)

print("\n" + "=" * 70)
print("DAY 31 VALIDATION COMPLETED")
print("=" * 70)