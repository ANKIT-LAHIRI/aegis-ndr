"""
train.py — a first trained classifier, evaluated honestly against baseline.py.

Trains a shallow, readable DecisionTreeClassifier on balanced_flows.csv
and reports per-class precision/recall/F1 on a held-out test split —
never a single blended accuracy number, for the same reason baseline.py
avoids one: on imbalanced or tiny data, accuracy alone can look good
while hiding total failure on the classes that matter most.

Note: stratify=y was attempted first and fails here, because the
'background' class has exactly 1 example — you cannot split one row
into a non-empty train group and a non-empty test group. That failure
is itself a finding about dataset size, not a bug to silently work
around, so it's called out rather than hidden.
"""

import csv
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

rows = list(csv.DictReader(open("balanced_flows.csv")))

X = [[int(r["packets"]), int(r["bytes"]), float(r["duration"]), int(r["syns"])] for r in rows]
y = [r["label"] for r in rows]

# stratify=y is the responsible default, but fails on this dataset
# (see docstring) — dropped here, with the limitation stated above
# rather than silently worked around.
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=42)

model = DecisionTreeClassifier(max_depth=3, random_state=42)
model.fit(Xtr, ytr)

print("Evaluation on UNSEEN test data:\n")
print(classification_report(yte, model.predict(Xte), zero_division=0))

print("Learned decision rules:\n")
print(export_text(model, feature_names=["packets", "bytes", "duration", "syns"]))
