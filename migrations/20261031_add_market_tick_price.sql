-- Required once for databases created before the price-only provider tick field.
ALTER TABLE market_ticks ADD COLUMN IF NOT EXISTS price NUMERIC(18, 8) NULL;
