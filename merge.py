import csv

sources = [
    ("attack_flows.csv", None),
    ("normal_flows.csv", None),
    ("normal2_flows.csv", None),
    ("portscan_flows.csv", None),
    ("blocked_flows.csv", None),
]

fieldnames = ["endpoints", "proto", "packets", "bytes", "duration", "syns", "label"]
all_rows = []

for filename, _ in sources:
    try:
        with open(filename, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                clean_row = {k: v.strip() for k, v in row.items()}
                all_rows.append(clean_row)
        print(f"Read {filename}: OK")
    except FileNotFoundError:
        print(f"Skipped {filename}: not found")

with open("combined_flows.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in all_rows:
        writer.writerow(row)

print(f"\nWrote {len(all_rows)} rows to combined_flows.csv")
