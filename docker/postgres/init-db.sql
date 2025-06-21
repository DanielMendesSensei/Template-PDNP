-- PostgreSQL initialization script
-- This script runs when the database is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set default encoding
SET client_encoding = 'UTF8';

-- Create custom functions if needed
-- Example: Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- You can add more initialization queries here
-- For example:
-- CREATE ROLE readonly WITH LOGIN PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE ${POSTGRES_DB} TO readonly;
-- GRANT USAGE ON SCHEMA public TO readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;