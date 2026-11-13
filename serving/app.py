"""Scoring service tối thiểu (Task 1.4): feature online từ Feast + model @champion từ MLflow."""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import mlflow
import pandas as pd
from fastapi import FastAPI
from feast import FeatureStore
from mlflow import MlflowClient
from pydantic import BaseModel, Field

MODEL_NAME = "fraud-detector"
FEATURES = ["amount", "category", "hour", "card_txn_count_24h"]  # phải giống hệt ml/train_baseline.py
state: dict = {}


class Transaction(BaseModel):
    trans_num: str = Field(min_length=1)
    card_hash: str = Field(min_length=1)
    amount: float = Field(gt=0)
    category: str = Field(min_length=1)
    txn_ts: datetime


class Score(BaseModel):
    trans_num: str
    score: float
    model_version: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    # tải model và mở feature store MỘT LẦN lúc khởi động, không tải lại mỗi request
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"))
    state["version"] = MlflowClient().get_model_version_by_alias(MODEL_NAME, "champion").version
    state["model"] = mlflow.lightgbm.load_model(f"models:/{MODEL_NAME}@champion")
    feast_repo = os.environ.get("FEAST_REPO", str(Path(__file__).resolve().parents[1] / "features"))
    state["store"] = FeatureStore(repo_path=feast_repo)
    yield
    state.clear()


app = FastAPI(title="Fraud scoring", version="1.0.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_version": state.get("version")}


@app.post("/score", response_model=Score)
def score(txn: Transaction) -> Score:
    online = state["store"].get_online_features(
        features=["card_velocity:card_txn_count_24h"],
        entity_rows=[{"card_hash": txn.card_hash}],
    ).to_dict()
    # thẻ chưa từng thấy -> online store chưa có giá trị -> coi như chưa có giao dịch nào trước đó
    velocity = online["card_txn_count_24h"][0] or 0

    row = pd.DataFrame(
        [{"amount": txn.amount, "category": txn.category, "hour": txn.txn_ts.hour, "card_txn_count_24h": velocity}]
    )[FEATURES].astype({"category": "category"})
    proba = float(state["model"].predict_proba(row)[:, 1][0])
    return Score(trans_num=txn.trans_num, score=proba, model_version=state["version"])
