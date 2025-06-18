import pandas as pd
import json
import os
from collections import defaultdict

# Role → School Type map
district_reps = {
    "Owen Bergan", "Peter Cahill", "Madyson Moy", "Katheryn Pearl",
    "Jack Carroll", "Kory Medici", "Jessica Mitchell", "J.P. Milbury",
    "Myles Stephenson", "Pat Chatfield"
}
charter_reps = {
    "Youssef Baba", "Nevin Ketchum", "Abby Mondello", "Michael Bollas",
    "Francis Rose", "Rhett Somers", "Ailish Maheras"
}

data_dir = "data"
calls_df = pd.read_csv(os.path.join(data_dir, "calls.csv"))
connects_df = pd.read_csv(os.path.join(data_dir, "connects.csv"))
customers_df = pd.read_csv(os.path.join(data_dir, "customers.csv"))
discos_df = pd.read_csv(os.path.join(data_dir, "discos.csv"))

def clean_state(state):
    return state.strip().upper()

# Initialize metrics dict
state_metrics = defaultdict(lambda: {
    "calls": 0, "connects": 0, "customers": 0, "discos": 0, "deals": 0, "score": 0,
    "district": {"calls": 0, "connects": 0, "customers": 0, "discos": 0, "deals": 0, "score": 0},
    "charter": {"calls": 0, "connects": 0, "customers": 0, "discos": 0, "deals": 0, "score": 0}
})

# ---- Helper to assign counts based on rep or type
def assign_school_type(role):
    if role in district_reps:
        return "district"
    elif role in charter_reps:
        return "charter"
    else:
        return None

# ---- Update from activity-based (calls + connects)
def update_activity(df, key):
    for _, row in df.iterrows():
        state = clean_state(row["State/Region"])
        count = int(row["Count of Calls"])  # or "Count of Deals" depending on file
        rep = row["Activity assigned to"].strip()
        school_type = assign_school_type(rep)

        state_metrics[state][key] += count
        if school_type:
            state_metrics[state][school_type][key] += count

# ---- Update from deal-based (discos + customers)
def update_deal_file(df, key):
    for _, row in df.iterrows():
        state = clean_state(row["State/Region"])
        count = int(row["Count of Deals"])  # explicit column name
        school_type = row["School Type"].strip().lower()
        school_type = school_type if school_type in {"charter", "district"} else None

        state_metrics[state][key] += count
        if school_type:
            state_metrics[state][school_type][key] += count

# Run all updates
update_activity(calls_df, "calls")
update_activity(connects_df, "connects")
update_deal_file(customers_df, "customers")
update_deal_file(discos_df, "discos")

# ---- Score calculation (weighted average) for both aggregate and subtypes
def compute_score(metrics):
    calls = metrics["calls"]
    connects = metrics["connects"]
    discos = metrics["discos"]
    deals = metrics.get("deals", 0)

    connect_rate = connects / calls if calls else 0
    book_rate = discos / connects if connects else 0
    deal_rate = deals / discos if discos else 0

    w_connect, w_book, w_deal = 0.5, 0.4, 0.1
    return round((connect_rate * w_connect) + (book_rate * w_book) + (deal_rate * w_deal), 3)

# Compute raw scores
max_score = 0
for s in state_metrics:
    state_metrics[s]["score_raw"] = compute_score(state_metrics[s])
    state_metrics[s]["district"]["score_raw"] = compute_score(state_metrics[s]["district"])
    state_metrics[s]["charter"]["score_raw"] = compute_score(state_metrics[s]["charter"])
    max_score = max(max_score, state_metrics[s]["score_raw"])

# Normalize scores to [0, 1]
for s in state_metrics:
    d = state_metrics[s]
    d["score"] = round(d["score_raw"] / max_score, 4) if max_score else 0
    d["district"]["score"] = round(d["district"]["score_raw"] / max_score, 4) if max_score else 0
    d["charter"]["score"] = round(d["charter"]["score_raw"] / max_score, 4) if max_score else 0
    del d["score_raw"]
    del d["district"]["score_raw"]
    del d["charter"]["score_raw"]

# ---- Write to JSON
with open("state_metrics.json", "w") as f:
    json.dump(state_metrics, f, indent=2)
