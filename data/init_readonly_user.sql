-- PostgreSQL Read-Only User Setup Script for Query Sandboxing
-- This script creates a SELECT-only database user to serve as a second layer of defense.

-- 1. Create Read-Only Database User
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonly_user') THEN
        CREATE USER readonly_user WITH PASSWORD 'readonly_password';
    END IF;
END
$$;

-- 2. Revoke Create & Write Privileges
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM readonly_user;

-- 3. Grant Database & Schema Access
GRANT CONNECT ON DATABASE text_to_sql_db TO readonly_user;
GRANT USAGE ON SCHEMA public TO readonly_user;

-- 4. Grant SELECT-Only Privileges on All Current and Future Tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;
