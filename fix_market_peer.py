from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent

DB = BASE_DIR / "data" / "database" / "nifty100.db"
RAW = BASE_DIR / "data" / "raw"

print("=" * 70)
print("MARKET CAP + PEER GROUPS DATABASE REPAIR")
print("=" * 70)

print(f"\nDatabase: {DB}")

# ============================================================
# MARKET CAP
# ============================================================

market_file = RAW / "market_cap.xlsx"

print(f"\nReading RAW Excel: {market_file}")

market_df = pd.read_excel(market_file, header=0)

print("Original columns:")
print(market_df.columns.tolist())

# Clean column names
market_df.columns = [str(c).strip() for c in market_df.columns]

expected_market_columns = [
    "id",
    "company_id",
    "year",
    "market_cap_crore",
    "enterprise_value_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
]

if list(market_df.columns) != expected_market_columns:
    raise ValueError(
        f"\nUnexpected market_cap columns:\n{market_df.columns.tolist()}"
    )

market_df["id"] = pd.to_numeric(market_df["id"], errors="coerce").astype("Int64")
market_df["company_id"] = market_df["company_id"].astype(str).str.strip()
market_df["year"] = pd.to_numeric(
    market_df["year"], errors="coerce"
).astype("Int64")

numeric_market_columns = [
    "market_cap_crore",
    "enterprise_value_crore",
    "pe_ratio",
    "pb_ratio",
    "ev_ebitda",
    "dividend_yield_pct",
]

for col in numeric_market_columns:
    market_df[col] = pd.to_numeric(market_df[col], errors="coerce")

print("\nMarket cap shape:", market_df.shape)
print(market_df.head(3).to_string(index=False))

# ============================================================
# PEER GROUPS
# ============================================================

peer_file = RAW / "peer_groups.xlsx"

print(f"\nReading RAW Excel: {peer_file}")

peer_df = pd.read_excel(peer_file, header=0)

print("Original columns:")
print(peer_df.columns.tolist())

peer_df.columns = [str(c).strip() for c in peer_df.columns]

expected_peer_columns = [
    "id",
    "peer_group_name",
    "company_id",
    "is_benchmark",
]

if list(peer_df.columns) != expected_peer_columns:
    raise ValueError(
        f"\nUnexpected peer_groups columns:\n{peer_df.columns.tolist()}"
    )

peer_df["id"] = pd.to_numeric(peer_df["id"], errors="coerce").astype("Int64")
peer_df["peer_group_name"] = (
    peer_df["peer_group_name"].astype(str).str.strip()
)
peer_df["company_id"] = peer_df["company_id"].astype(str).str.strip()

# Convert benchmark to 0/1
peer_df["is_benchmark"] = (
    peer_df["is_benchmark"]
    .astype(str)
    .str.strip()
    .str.lower()
    .map({
        "true": 1,
        "false": 0,
        "1": 1,
        "0": 0,
    })
)

print("\nPeer groups shape:", peer_df.shape)
print(peer_df.head(5).to_string(index=False))

# ============================================================
# DATABASE
# ============================================================

print("\nConnecting to database...")

conn = sqlite3.connect(DB)

try:

    # --------------------------------------------------------
    # MARKET CAP
    # --------------------------------------------------------

    print("\nReplacing market_cap table...")

    market_df.to_sql(
        "market_cap",
        conn,
        if_exists="replace",
        index=False,
    )

    # --------------------------------------------------------
    # PEER GROUPS
    # --------------------------------------------------------

    print("Replacing peer_groups table...")

    peer_df.to_sql(
        "peer_groups",
        conn,
        if_exists="replace",
        index=False,
    )

    conn.commit()

    # ========================================================
    # VERIFY MARKET CAP
    # ========================================================

    print("\n" + "=" * 70)
    print("VERIFYING MARKET CAP")
    print("=" * 70)

    print(
        conn.execute(
            "PRAGMA table_info(market_cap)"
        ).fetchall()
    )

    print("\nRows:")
    print(
        conn.execute(
            "SELECT COUNT(*) FROM market_cap"
        ).fetchone()[0]
    )

    print("\n2024 test:")
    print(
        conn.execute(
            """
            SELECT *
            FROM market_cap
            WHERE year = ?
            LIMIT 3
            """,
            (2024,),
        ).fetchall()
    )

    # ========================================================
    # VERIFY PEER GROUPS
    # ========================================================

    print("\n" + "=" * 70)
    print("VERIFYING PEER GROUPS")
    print("=" * 70)

    print(
        conn.execute(
            "PRAGMA table_info(peer_groups)"
        ).fetchall()
    )

    print("\nRows:")
    print(
        conn.execute(
            "SELECT COUNT(*) FROM peer_groups"
        ).fetchone()[0]
    )

    print("\nDistinct peer groups:")
    print(
        conn.execute(
            """
            SELECT DISTINCT peer_group_name
            FROM peer_groups
            ORDER BY peer_group_name
            """
        ).fetchall()
    )

    print("\nHDFCBANK test:")
    print(
        conn.execute(
            """
            SELECT *
            FROM peer_groups
            WHERE company_id = ?
            """,
            ("HDFCBANK",),
        ).fetchall()
    )

finally:
    conn.close()

print("\n" + "=" * 70)
print("SUCCESS: market_cap and peer_groups repaired from RAW Excel.")
print("=" * 70)