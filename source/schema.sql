CREATE TABLE IF NOT EXISTS transactions_history (
    trans_num             TEXT PRIMARY KEY,
    row_id                INTEGER,
    trans_date_trans_time TIMESTAMP NOT NULL,
    cc_num                TEXT NOT NULL,
    merchant              TEXT,
    category              TEXT,
    amt                   NUMERIC(12, 2) NOT NULL,
    first                 TEXT,
    last                  TEXT,
    gender                TEXT,
    street                TEXT,
    city                  TEXT,
    state                 TEXT,
    zip                   TEXT,
    lat                   DOUBLE PRECISION,
    long                  DOUBLE PRECISION,
    city_pop              INTEGER,
    job                   TEXT,
    dob                   DATE,
    unix_time             BIGINT,
    merch_lat             DOUBLE PRECISION,
    merch_long            DOUBLE PRECISION,
    is_fraud              SMALLINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_txn_hist_time ON transactions_history (trans_date_trans_time);
