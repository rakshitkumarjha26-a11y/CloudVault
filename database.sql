-- ═══════════════════════════════════════════════════════════
--  CloudVault Database Schema
--  Cloud Computing Project — MySQL Database
-- ═══════════════════════════════════════════════════════════
--
--  CLOUD MAPPING:
--  This MySQL database → AWS RDS / Azure SQL / GCP Cloud SQL
--  In production, connection string would use the RDS endpoint.
--
--  Run this file with:
--    mysql -u root -p < database.sql
-- ═══════════════════════════════════════════════════════════

-- Create and select the database
CREATE DATABASE IF NOT EXISTS cloudvault
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE cloudvault;

-- ──────────────────────────────────────────────
--  Table: users
--  Stores registered user accounts
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)     NOT NULL,
    email       VARCHAR(150)     NOT NULL UNIQUE,
    password    VARCHAR(255)     NOT NULL,       -- bcrypt hashed
    created_at  DATETIME         DEFAULT CURRENT_TIMESTAMP
);

-- ──────────────────────────────────────────────
--  Table: files
--  Stores metadata for each uploaded file
--  (Actual file bytes live in /uploads/ folder,
--   or in S3 bucket in real cloud deployment)
-- ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS files (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    user_id       INT            NOT NULL,
    original_name VARCHAR(255)   NOT NULL,   -- name user sees
    stored_name   VARCHAR(255)   NOT NULL,   -- UUID-based name on disk/S3
    file_size     BIGINT         NOT NULL,   -- in bytes
    file_type     VARCHAR(20)    NOT NULL,   -- extension (PDF, PNG, etc.)
    uploaded_at   DATETIME       DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_files (user_id),
    INDEX idx_uploaded_at (uploaded_at)
);

-- ──────────────────────────────────────────────
--  Sample Data (optional, for testing)
-- ──────────────────────────────────────────────
-- Password for demo@cloudvault.com is: demo123
-- INSERT INTO users (name, email, password) VALUES
-- ('Demo User', 'demo@cloudvault.com',
--  'pbkdf2:sha256:600000$...');  -- generate with werkzeug

-- ──────────────────────────────────────────────
--  View: user_storage_summary (bonus analytics)
-- ──────────────────────────────────────────────
CREATE OR REPLACE VIEW user_storage_summary AS
SELECT
    u.id,
    u.name,
    u.email,
    COUNT(f.id)       AS total_files,
    COALESCE(SUM(f.file_size), 0) AS total_bytes,
    u.created_at
FROM users u
LEFT JOIN files f ON u.id = f.user_id
GROUP BY u.id, u.name, u.email, u.created_at;
