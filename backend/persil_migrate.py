import csv
import psycopg2
from psycopg2.extras import execute_batch

# =========================
# KONFIGURASI DB
# =========================
DB_CONFIG = {
    "host": "103.150.191.85",
    "port": 5432,
    "dbname": "valemis",
    "user": "valemis",
    "password": "Valemis@2025"
}

CSV_PATH = "data/persil_fix.csv"
SOURCE_SRID = 32751
TARGET_SRID = 4326
BATCH_SIZE = 106

# =========================
# SQL TEMPLATE
# =========================

# 1️⃣ pastikan asset ada, ambil id_parcel_asset
GET_OR_CREATE_ASSET = """
WITH ins AS (
    INSERT INTO tbl_acquisition_asset (id_asset)
    VALUES (%s)
    RETURNING id_parcel_asset
)
SELECT id_parcel_asset FROM ins
UNION
SELECT id_parcel_asset FROM tbl_acquisition_asset WHERE id_asset = %s;
"""

# 2️⃣ insert acquisition
INSERT_ACQUISITION = """
INSERT INTO tbl_acquisition (
    nama_pemilik,
    kode_parcel,
    id_project_id,
    status,
    desa,
    geom,
    id_asset_id
)
VALUES (
    %s,
    %s,
    %s,
    %s,
    %s,
    ST_Transform(
        ST_SetSRID(ST_GeomFromText(%s), %s),
        %s
    ),
    %s
);
"""

# =========================
# MAIN
# =========================
def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    total = 0
    batch = []

    with open(CSV_PATH, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for i,row in enumerate(reader):
            # =========================
            # FK: AcquisitionAsset
            # =========================
            cur.execute(
                GET_OR_CREATE_ASSET,
                (row["id_asset"].strip(), row["id_asset"].strip())
            )
            asset_id = cur.fetchone()[0]

            # =========================
            # BUILD BATCH
            # =========================
            # print(row)
            batch.append((
                row["nama_pemilik"].strip(),
                f"PARCEL-{i}",
                8,
                "Belum Diproses",
                row["desa"].strip(),
                row["geom"],      # WKT
                SOURCE_SRID,
                TARGET_SRID,
                asset_id
            ))

            # =========================
            # EXECUTE BATCH
            # =========================
        if len(batch) >= BATCH_SIZE:
                execute_batch(cur, INSERT_ACQUISITION, batch)
                conn.commit()
                total += len(batch)
                batch.clear()
                print(f"Inserted {total} rows")

        # sisa
        if batch:
            execute_batch(cur, INSERT_ACQUISITION, batch)
            conn.commit()
            total += len(batch)

    cur.close()
    conn.close()

    print(f"\n✅ SELESAI — TOTAL INSERT: {total}")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()
