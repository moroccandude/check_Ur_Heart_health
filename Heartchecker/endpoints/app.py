from fastapi import FastAPI
import json

app = FastAPI()

with open("./data/coronary_artery_disease.json") as f:
    records = json.load(f)

current_index = {"idx": 0}

@app.get("/api_v1")
def get_message() -> dict:
    idx = current_index["idx"]
    record = records[idx]
    current_index["idx"] = idx + 1
    return record
