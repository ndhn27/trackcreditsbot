-- Migration 003: Add check constraints to submissions table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'submissions_sub_type_check'
    ) THEN
        ALTER TABLE submissions
        ADD CONSTRAINT submissions_sub_type_check
        CHECK (sub_type IN ('credits', 'lyrics', 'report'));
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'submissions_status_check'
    ) THEN
        ALTER TABLE submissions
        ADD CONSTRAINT submissions_status_check
        CHECK (status IN ('pending', 'approved', 'rejected'));
    END IF;
END
$$;
