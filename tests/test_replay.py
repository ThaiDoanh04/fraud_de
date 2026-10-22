from datetime import datetime, timedelta

from source.replay import replay_offset

T0 = datetime(2020, 6, 21, 12, 0, 0)


def test_one_hour_at_speed_60_is_one_minute():
    assert replay_offset(T0, T0 + timedelta(hours=1), speed=60) == 60


def test_first_transaction_has_zero_offset():
    assert replay_offset(T0, T0, speed=60) == 0


def test_same_timestamp_transactions_have_same_offset():
    t = T0 + timedelta(minutes=5)
    assert replay_offset(T0, t, speed=10) == replay_offset(T0, t, speed=10) == 30
