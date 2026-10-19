"""Download UCI Online Retail II and report aggregate discovery statistics.

Run from the repository root: python scripts/inspect_data.py
Raw files remain unchanged. No customer-level examples are exported.
"""

import hashlib
import json
import shutil
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"


def download_workbook():
    raw = ROOT / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    workbook = raw / "online_retail_II.xlsx"
    if workbook.exists():
        print("Using existing workbook (no download).", flush=True)
        return workbook
    archive = raw / "online_retail_ii.zip"
    if not archive.exists():
        temporary = archive.with_suffix(".download")
        print("Downloading original dataset from UCI...", flush=True)
        request = urllib.request.Request(URL, headers={"User-Agent": "RetailCast/0.1"})
        with urllib.request.urlopen(request, timeout=120) as response:
            with temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
        temporary.replace(archive)
    with zipfile.ZipFile(archive) as source:
        matches = [n for n in source.namelist() if Path(n).name == workbook.name]
        if len(matches) != 1:
            raise ValueError("Expected exactly one online_retail_II.xlsx in UCI archive")
        temporary = workbook.with_suffix(".download")
        with source.open(matches[0]) as incoming, temporary.open("wb") as output:
            shutil.copyfileobj(incoming, output)
        temporary.replace(workbook)
    return workbook


def summarize(frame):
    expected = {"Invoice", "StockCode", "Description", "Quantity", "InvoiceDate",
                "Price", "Customer ID", "Country"}
    if set(frame.columns) != expected:
        raise ValueError(f"Unexpected source columns: {frame.columns.tolist()}")
    dates = pd.to_datetime(frame["InvoiceDate"], errors="coerce")
    quantity = pd.to_numeric(frame["Quantity"], errors="coerce")
    price = pd.to_numeric(frame["Price"], errors="coerce")
    return {
        "rows": len(frame),
        "columns": frame.columns.tolist(),
        "inferred_dtypes": frame.dtypes.astype(str).to_dict(),
        "missing_values": {k: int(v) for k, v in frame.isna().sum().items()},
        "duplicate_rows_beyond_first": int(frame.duplicated().sum()),
        "cancellation_invoice_rows": int(frame["Invoice"].astype("string").str.upper()
                                         .str.startswith("C", na=False).sum()),
        "negative_quantity_rows": int((quantity < 0).sum()),
        "zero_quantity_rows": int((quantity == 0).sum()),
        "nonpositive_price_rows": int((price <= 0).sum()),
        "invalid_nonmissing_dates": int((dates.isna() & frame["InvoiceDate"].notna()).sum()),
        "invalid_nonmissing_quantities": int((quantity.isna() & frame["Quantity"].notna()).sum()),
        "invalid_nonmissing_prices": int((price.isna() & frame["Price"].notna()).sum()),
        "first_timestamp": str(dates.min()),
        "last_timestamp": str(dates.max()),
        "unique_product_codes": int(frame["StockCode"].nunique()),
        "unique_countries": int(frame["Country"].nunique()),
    }


def main():
    workbook = download_workbook()
    with workbook.open("rb") as source:
        checksum = hashlib.file_digest(source, "sha256").hexdigest()
    report = {
        "source_url": URL,
        "source_page": "https://archive.ics.uci.edu/dataset/502/online+retail+ii",
        "license": "CC BY 4.0 (as listed by UCI)",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "workbook_sha256": checksum,
        "sheets": {},
    }
    frames = []
    with pd.ExcelFile(workbook, engine="openpyxl") as excel:
        for name in excel.sheet_names:
            print(f"Reading sheet: {name} (may take a minute)...", flush=True)
            frame = pd.read_excel(excel, sheet_name=name)
            report["sheets"][name] = summarize(frame)
            frames.append(frame)
    combined = pd.concat(frames, ignore_index=True)
    report["combined"] = summarize(combined)
    destination = ROOT / "reports" / "data-discovery.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["combined"], indent=2))
    print(f"Aggregate report saved to {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
