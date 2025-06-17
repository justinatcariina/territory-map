# Python 3.12

import pandas as pd
import json
import os

# Input paths
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
            state_metrics[state] = {"calls": 0, "connects": 0, "customers": 0, "discos": 0}
        state_metrics[state][key] += count

update(calls, "calls")
update(connects, "connects")
update(customers, "customers")
update(discos, "discos")

for s, d in state_metrics.items():
    d["score"] = round(0.6 * d["discos"] + 0.3 * d["connects"] + 1.0 * d["customers"], 2)

with open("state_metrics.json", "w") as f:
    json.dump(state_metrics, f, indent=2)
