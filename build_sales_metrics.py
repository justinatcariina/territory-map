import pandas as pd
import json
import os

data_dir = "data"
calls = pd.read_csv(os.path.join(data_dir, "calls.csv"))
connects = pd.read_csv(os.path.join(data_dir, "connects.csv"))
customers = pd.read_csv(os.path.join(data_dir, "customers.csv"))
discos = pd.read_csv(os.path.join(data_dir, "discos.csv"))

state_metrics = {}

def update(df, key):
    for _, row in df.iterrows():
        state = row["State/Region"].strip().upper()
        count = int(row[1])
        if state not in state_metrics:
            state_metrics[state] = {"calls": 0, "connects": 0, "customers": 0, "discos": 0, "deals": 0}
        state_metrics[state][key] += count

update(calls, "calls")
update(connects, "connects")
update(customers, "customers")
update(discos, "discos")

# Suppose you have a deals.csv with deals count by state? If not, you can add deals to discos or hardcode 0
deals = pd.read_csv(os.path.join(data_dir, "deals.csv")) if os.path.exists(os.path.join(data_dir, "deals.csv")) else None
if deals is not None:
    update(deals, "deals")
else:
    # if no deals file, set deals = 0 to avoid KeyError
    for s in state_metrics:
        state_metrics[s]["deals"] = 0

# Calculate new score:
for s, d in state_metrics.items():
    calls = d["calls"]
    connects = d["connects"]
    discos = d["discos"]
    deals = d.get("deals", 0)

    connect_rate = connects / calls if calls else 0
    book_rate = discos / connects if connects else 0
    deal_rate = deals / discos if discos else 0

    # weights (adjust as you want)
    w_connect = 0.5
    w_book = 0.4
    w_deal = 0.1

    score = (connect_rate * w_connect) + (book_rate * w_book) + (deal_rate * w_deal)
    d["score_raw"] = round(score, 3)

# Normalize scores to range 0–1
max_score = max(d["score_raw"] for d in state_metrics.values())
for d in state_metrics.values():
    d["score"] = round(d["score_raw"] / max_score, 4)
    del d["score_raw"]

with open("state_metrics.json", "w") as f:
    json.dump(state_metrics, f, indent=2)
