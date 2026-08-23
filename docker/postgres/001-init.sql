-- ========================================================
-- MAIN APPLICATION DATABASE
-- ========================================================

CREATE EXTENSION IF NOT EXISTS vector;


-- ========================================================
-- TEST DATABASE
--
-- Allows Phase 10 pytest integration tests to continue
-- using the PostgreSQL container created by Compose.
-- ========================================================

CREATE DATABASE docintel_test;


-- ========================================================
-- ENABLE PGVECTOR IN TEST DATABASE
-- ========================================================

\connect docintel_test

CREATE EXTENSION IF NOT EXISTS vector;