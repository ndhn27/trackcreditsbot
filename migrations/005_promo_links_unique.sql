-- Migration 005: Add unique constraint on promo_links(track_key, promo_type)
-- Required for ON CONFLICT upsert in promo_links_insert().
-- Removes existing duplicate rows (keeps the last inserted per pair) before
-- adding the constraint so the migration is safe on existing data.

DELETE FROM promo_links
WHERE id NOT IN (
    SELECT MAX(id)
    FROM promo_links
    GROUP BY track_key, promo_type
);

ALTER TABLE promo_links
    ADD CONSTRAINT uq_promo_links_track_type UNIQUE (track_key, promo_type);
