"""
Company ID normalization.

Only known source-level spelling/identifier corrections belong here.
Do NOT add missing companies to the master dataset.
"""

COMPANY_ID_MAP = {
    "AGTL": "ATGL",
}


def normalize_company_id(company_id):
    """
    Normalize a company ID to the project's master identifier.

    Examples:
        AGTL -> ATGL
        ATGL -> ATGL
        WIPRO -> WIPRO
    """
    if company_id is None:
        return None

    company_id = str(company_id).strip().upper()

    if not company_id:
        return None

    return COMPANY_ID_MAP.get(company_id, company_id)


if __name__ == "__main__":
    print("COMPANY ID NORMALIZATION TEST")
    print("-" * 40)

    test_ids = [
        "AGTL",
        "ATGL",
        "wipro",
        "  relIance  ",
        None,
    ]

    for company_id in test_ids:
        print(
            f"{str(company_id):<12} -> "
            f"{normalize_company_id(company_id)}"
        )