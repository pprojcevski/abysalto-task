-- Ensure pgvector extension is available and installed
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_available_extensions WHERE name = 'vector'
    ) THEN
        RAISE EXCEPTION 'pgvector extension is not available in this PostgreSQL installation';
    END IF;
END
$$;

CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        RAISE EXCEPTION 'pgvector extension failed to install';
    END IF;

    RAISE NOTICE 'pgvector extension installed successfully (version: %)',
        (SELECT extversion FROM pg_extension WHERE extname = 'vector');
END
$$;
