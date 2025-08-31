CREATE TABLE IF NOT EXISTS ads_spend_db (
    date DATE,
    platform VARCHAR,
    account VARCHAR,
    campaign VARCHAR,
    country VARCHAR,
    device VARCHAR,
    spend DECIMAL(12,2),
    clicks INTEGER,
    impressions INTEGER,
    conversions INTEGER,
    -- Metadata challenge required
    load_date TIMESTAMP,
    source_file_name VARCHAR
);