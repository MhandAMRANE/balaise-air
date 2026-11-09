CREATE TABLE IF NOT EXISTS mesures (
    id          SERIAL PRIMARY KEY,
    date_heure  TIMESTAMP NOT NULL DEFAULT NOW(),
    temperature REAL,
    humidite    REAL,
    air         INTEGER,
    etat        VARCHAR(10),
    cause       VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_mesures_date ON mesures (date_heure);