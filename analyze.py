import csv
from collections import defaultdict

groups = defaultdict(list)

with open("combined_flows.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        groups[row["label"]].append(row)

print(f"{'LABEL':<10} {'COUNT':>6} {'AVG PKTS':>10} {'AVG BYTES':>11} {'AVG DUR(s)':>11} {'AVG SYN':>8}")
print("-" * 62)

for label, rows in groups.items():
    n = len(rows)
    avg_pkts = sum(int(r["packets"]) for r in rows) / n
    avg_bytes = sum(int(r["bytes"]) for r in rows) / n
    avg_dur = sum(float(r["duration"]) for r in rows) / n
    avg_syn = sum(int(r["syns"]) for r in rows) / n
    print(f"{label:<10} {n:>6} {avg_pkts:>10.1f} {avg_bytes:>11.1f} {avg_dur:>11.2f} {avg_syn:>8.1f}")
