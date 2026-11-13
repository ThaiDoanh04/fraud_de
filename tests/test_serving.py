from types import SimpleNamespace

import numpy as np
import pytest
from fastapi.testclient import TestClient

from serving import app as svc

VALID = {
    "trans_num": "t1",
    "card_hash": "abc",
    "amount": 50.0,
    "category": "grocery_pos",
    "txn_ts": "2020-06-21T22:15:31",
}


class FakeModel:
    def predict_proba(self, X):
        self.seen = X  # giữ lại input để kiểm tra
        return np.array([[0.2, 0.8]])


def fake_store(velocity):
    rows = {"card_txn_count_24h": [velocity]}
    return SimpleNamespace(get_online_features=lambda features, entity_rows: SimpleNamespace(to_dict=lambda: rows))


@pytest.fixture
def make_client():
    # không dùng "with TestClient(...)" -> lifespan không chạy -> không tải model thật
    def make(velocity=3):
        model = FakeModel()
        svc.state.update(model=model, version="7", store=fake_store(velocity))
        return TestClient(svc.app), model

    yield make
    svc.state.clear()


def test_score_uses_online_velocity_and_training_feature_order(make_client):
    client, model = make_client(velocity=3)
    resp = client.post("/score", json=VALID)
    assert resp.status_code == 200
    assert resp.json() == {"trans_num": "t1", "score": 0.8, "model_version": "7"}
    assert list(model.seen.columns) == svc.FEATURES
    assert model.seen.iloc[0]["card_txn_count_24h"] == 3
    assert model.seen.iloc[0]["hour"] == 22


def test_unknown_card_defaults_velocity_to_zero(make_client):
    client, model = make_client(velocity=None)
    client.post("/score", json=VALID)
    assert model.seen.iloc[0]["card_txn_count_24h"] == 0


@pytest.mark.parametrize(
    "field,value", [("amount", -5), ("amount", 0), ("card_hash", ""), ("txn_ts", "not-a-date")]
)
def test_invalid_input_is_rejected(make_client, field, value):
    client, _ = make_client()
    assert client.post("/score", json=VALID | {field: value}).status_code == 422
