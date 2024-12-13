CREATE TABLE vessel_positions (
    vessel_id TEXT NOT NULL,
    vessel_name TEXT,
    latitude FLOAT NOT NULL,
    longitude FLOAT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    PRIMARY KEY (vessel_id, timestamp)
);
