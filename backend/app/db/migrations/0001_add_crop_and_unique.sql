-- Migration: add crop and production_mt columns and ensure unique constraint/index
-- Run this in Supabase SQL editor or include in your migration flow.

ALTER TABLE IF EXISTS agri_metrics
  ADD COLUMN IF NOT EXISTS crop text NOT NULL DEFAULT 'All crops';

ALTER TABLE IF EXISTS agri_metrics
  ADD COLUMN IF NOT EXISTS production_mt double precision;

ALTER TABLE IF EXISTS predictions
  ADD COLUMN IF NOT EXISTS crop text NOT NULL DEFAULT 'All crops';

-- Use a DO block to add the unique constraint only if missing
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint c
    JOIN pg_class t ON c.conrelid = t.oid
    WHERE c.conname = 'agri_metrics_zone_season_crop_key'
      AND t.relname = 'agri_metrics'
  ) THEN
    ALTER TABLE agri_metrics
      ADD CONSTRAINT agri_metrics_zone_season_crop_key UNIQUE (zone_id, season, crop);
  END IF;
END
$$;

-- As a fallback, ensure a unique index exists (safe to run even if constraint added above)
CREATE UNIQUE INDEX IF NOT EXISTS agri_metrics_zone_season_crop_idx
  ON agri_metrics(zone_id, season, crop);
