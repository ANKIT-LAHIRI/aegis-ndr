"""
train.py — first ML model, evaluated honestly, including its own instability.

Two things happen here, and both are load-bearing for the README:

1. A single DecisionTreeClassifier is trained on balanced_flows.csv and
   evaluated with a full per-class report (precision/recall/F1), exactly
   like baseline.py, so it can be compared to the hand-written baseline
   on equal terms rather than a single blended accuracy number.

2. The same training/evaluation is then repeated across 10 different
   random_state seeds, reporting accuracy for each. At this dataset's
   current size (36 rows), a single seed's result swung from 64% to 82%
   in earlier manual testing — this loop makes that instability visible
   and reproducible rather than something discovered by accident.

Note: stratify=y was attempted first and fails, because 'background'
has exactly 1 example — you cannot split one row into a non-empty train
group and a non-empty test group. Stratification is dropped, and that
limitation is stated rather than silently worked around.
"""

import csv
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

rows = list(csv.DictReader(open("balanced_flows.csv")))
X = [[int(r["packets"]), int(r["bytes"]), float(r["duration"]), int(r["syns"])] for r in rows]
y = [r["label"] for r in rows]

# --- Part 1: one full, detailed run (random_state=42) ---
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42)
model = DecisionTreeClassifier(max_depth=3, random_state=42).fit(Xtr, ytr)

print("=== Single run (random_state=42) — full per-class report ===\n")
print(classification_report(yte, model.predict(Xte), zero_division=0))
print("Learned decision rules:\n")
print(export_text(model, feature_names=["packets", "bytes", "duration", "syns"]))

# --- Part 2: 10 different splits, to check how stable that single run's
#     number actually is. This is the real evaluation, not Part 1 alone. ---
print("\n=== Stability check: accuracy across 10 different train/test splits ===\n")
accuracies = []
for seed in range(10):
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=seed)
    m = DecisionTreeClassifier(max_depth=3, random_state=seed).fit(Xtr, ytr)
    acc = accuracy_score(yte, m.predict(Xte))
    accuracies.append(acc)
    print(f"seed={seed}  accuracy={acc:.1%}")

print(f"\nRange: {min(accuracies):.1%} - {max(accuracies):.1%}   "
      f"Mean: {sum(accuracies)/len(accuracies):.1%}")
print("A single seed's number is not trustworthy at this dataset size — "
      "the spread above is the honest result.")
