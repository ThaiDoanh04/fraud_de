"""Train LightGBM baseline (Task 1.3): lấy feature qua Feast (point-in-time), log + đăng ký model trên MLflow."""

from pathlib import Path

import lightgbm as lgb
import mlflow
import pandas as pd
from feast import FeatureStore
from mlflow import MlflowClient
from sklearn.metrics import average_precision_score, roc_auc_score

FEATURES = ["amount", "category", "hour", "card_txn_count_24h"]
MODEL_NAME = "fraud-detector"
SPLIT_SQL = """
SELECT trans_num, card_hash, txn_ts AS event_timestamp, amount, category, is_fraud
FROM iceberg.silver.transactions
WHERE txn_ts >= TIMESTAMP '{start}' AND txn_ts < TIMESTAMP '{end}'
"""

store = FeatureStore(repo_path=Path(__file__).resolve().parents[1] / "features")


def load(start: str, end: str) -> pd.DataFrame:
    """Lấy giao dịch trong khoảng thời gian, Feast gắn feature velocity đúng tại thời điểm từng giao dịch."""
    df = store.get_historical_features(
        entity_df=SPLIT_SQL.format(start=start, end=end),
        features=["card_velocity:card_txn_count_24h"],
    ).to_df()
    df["amount"] = df["amount"].astype(float)  # Trino trả decimal -> float cho LightGBM
    df["category"] = df["category"].astype("category")
    df["hour"] = pd.to_datetime(df["event_timestamp"]).dt.hour
    return df


def main() -> None:
    train = load("2019-01-01 00:00:00", "2020-05-01 00:00:00")
    valid = load("2020-05-01 00:00:00", "2020-06-21 00:00:00")
    # valid phải dùng đúng bộ mã category như train, nếu không LightGBM hiểu sai nhóm
    valid["category"] = pd.Categorical(valid["category"], categories=train["category"].cat.categories)

    params = {"n_estimators": 300, "learning_rate": 0.05, "num_leaves": 31, "scale_pos_weight": 10}

    mlflow.set_tracking_uri("http://localhost:5001")
    mlflow.set_experiment("fraud-baseline")
    with mlflow.start_run(run_name="lgbm-baseline"):
        model = lgb.LGBMClassifier(**params, verbose=-1)
        model.fit(train[FEATURES], train["is_fraud"])

        y, score = valid["is_fraud"], model.predict_proba(valid[FEATURES])[:, 1]
        metrics = {
            "valid_pr_auc": average_precision_score(y, score),
            "valid_roc_auc": roc_auc_score(y, score),
            # baseline ngây thơ: "giao dịch càng lớn càng đáng ngờ" -> model phải hơn mức này
            "rule_amount_pr_auc": average_precision_score(y, valid["amount"]),
            "train_rows": len(train),
            "valid_rows": len(valid),
            "valid_fraud_rate": y.mean(),
        }
        mlflow.log_params(params | {"features": ",".join(FEATURES)})
        mlflow.log_metrics(metrics)

        info = mlflow.lightgbm.log_model(model, name="model", registered_model_name=MODEL_NAME)
        MlflowClient().set_registered_model_alias(MODEL_NAME, "champion", info.registered_model_version)

    print({k: round(v, 4) for k, v in metrics.items()})
    assert metrics["valid_pr_auc"] > metrics["rule_amount_pr_auc"], "model không hơn rule đơn giản"


if __name__ == "__main__":
    main()
