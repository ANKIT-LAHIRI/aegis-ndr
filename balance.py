"""
balance.py — fix class imbalance in the labelled flow dataset.

combined_flows.csv holds every flow ever extracted, honestly, including
1,002 portscan flows against single digits for every other category.
Training anything on that as-is would mean the model only ever really
learns "portscan" and treats everything else as noise.

This script caps every label at MAX_PER_LABEL rows: categories already
below the cap are kept in full (nothing is thrown away for the rare,
important classes), and any category above the cap is randomly
subsampled down to it. Only portscan is large enough to be affected.

combined_flows.csv is never modified — it stays as the full, honest
record. This script only ever reads it and writes a new file,
balanced_flows.csv, meant for evaluation and future model training.
"""

import csv
import random

MAX_PER_LABEL = 20

# --- Step 1: read every row and bucket it by its label ---
rows_by_label = {}
with open("combined_flows.csv", newline="") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        rows_by_label.setdefault(row["label"], []).append(row)

# --- Step 2: cap each bucket at MAX_PER_LABEL, sampling if needed ---
balanced_rows = []
for label, rows in rows_by_label.items():
    if len(rows) > MAX_PER_LABEL:
        sample = random.sample(rows, MAX_PER_LABEL)
        print(f"{label}: {len(rows)} rows -> sampled down to {MAX_PER_LABEL}")
    else:
        sample = rows
        print(f"{label}: {len(rows)} rows -> kept all")
    balanced_rows.extend(sample)

# --- Step 3: write the balanced dataset to its own file ---
with open("balanced_flows.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in balanced_rows:
        writer.writerow(row)

print(f"\nWrote {len(balanced_rows)} rows to balanced_flows.csv")
