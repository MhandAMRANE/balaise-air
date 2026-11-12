CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS mesures (
    id          SERIAL,
    date_heure  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    temperature REAL,
    humidite    REAL,
    air         INTEGER,
    etat        VARCHAR(10),
    cause       VARCHAR(50),
    PRIMARY KEY (id, date_heure)   -- TimescaleDB impose la colonne de temps dans la clé primaire
);

-- create_hypertable crée aussi automatiquement l'index sur date_heure.
SELECT create_hypertable('mesures', by_range('date_heure', INTERVAL '1 day'), if_not_exists => TRUE);
