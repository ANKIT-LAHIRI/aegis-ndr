"""
baseline.py — a rule-based detector, evaluated before any ML is introduced.

The point of a baseline is discipline: before trusting any machine
learning model's accuracy number, you need to know what a simple,
hand-written rule already achieves. If a model can't beat this, the
model isn't earning its complexity.

Two thresholds, both derived directly from patterns observed by eye
in Current data (see README):
  - very few packets, near-zero duration  -> looks like a port scan
  - moderate packets, short duration,
    small total bytes                     -> looks like a brute-force attempt
Anything else is treated as normal.

This is deliberately simple. It is expected to have blind spots, and
finding those blind spots — not just the headline accuracy — is the
actual goal of this script.
"""

import csv


def classify(row):
    packets = int(row["packets"])
    duration = float(row["duration"])
    bytes_ = int(row["bytes"])

    if packets <= 3 and duration < 1.0:
        return "suspicious_scan"
    if packets < 60 and duration < 10.0 and bytes_ < 10000:
        return "suspicious_bruteforce"
    return "normal"


with open("balanced_flows.csv", newline="") as f:
    rows = list(csv.DictReader(f))

correct = 0
total = len(rows)

print(f"{'TRUE LABEL':<18}{'PREDICTED':<22}{'MATCH?':<8}")
print("-" * 48)

for row in rows:
    prediction = classify(row)
    true_label = row["label"]

    # ground truth: is this flow actually attack-like?
    is_attack_like = true_label in ("attack", "portscan", "attack_blocked")
    # rule's opinion: did it flag anything at all?
    predicted_attack_like = prediction != "normal"

    match = is_attack_like == predicted_attack_like
    correct += match

    print(f"{true_label:<18}{prediction:<22}{'YES' if match else 'NO':<8}")

print(f"\nBaseline accuracy (attack-like vs normal-like): "
      f"{correct}/{total} = {correct/total:.1%}")

# --- per-class breakdown: the number that actually matters ---
print("\nPer-class breakdown:")
by_label = {}
for row in rows:
    label = row["label"]
    prediction = classify(row)
    is_attack_like = label in ("attack", "portscan", "attack_blocked")
    predicted_attack_like = prediction != "normal"
    match = is_attack_like == predicted_attack_like
    by_label.setdefault(label, [0, 0])
    by_label[label][0] += match
    by_label[label][1] += 1

for label, (hits, n) in by_label.items():
    print(f"  {label:<18}{hits}/{n} = {hits/n:.0%}")
