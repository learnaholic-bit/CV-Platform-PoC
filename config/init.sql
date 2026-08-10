CREATE TABLE IF NOT EXISTS facility_events (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    image_path VARCHAR(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);