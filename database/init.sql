-- AI Calligraphy Grading System Database Schema
-- MySQL 9.1

CREATE DATABASE IF NOT EXISTS calligraphy_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE calligraphy_ai;

-- Table: grading_records - stores grading results
CREATE TABLE IF NOT EXISTS grading_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Grading results
    overall_score DECIMAL(5,2),
    grade VARCHAR(20),
    char_count INT DEFAULT 0,
    
    -- AI feedback
    ai_comment TEXT,
    strengths TEXT,
    suggestions TEXT,
    
    -- Detailed scores JSON
    char_details JSON,
    
    -- Status
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    error_message TEXT,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_filename (filename),
    INDEX idx_upload_time (upload_time),
    INDEX idx_score (overall_score),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: character_scores - detailed per-character scores
CREATE TABLE IF NOT EXISTS character_scores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    record_id INT NOT NULL,
    char_text VARCHAR(10) NOT NULL,
    score DECIMAL(5,2),
    grade VARCHAR(20),
    
    -- Dimension scores
    center_of_mass_score DECIMAL(5,2),
    stroke_accuracy_score DECIMAL(5,2),
    structure_score DECIMAL(5,2),
    
    -- Position in image
    bbox_x INT,
    bbox_y INT,
    bbox_width INT,
    bbox_height INT,
    
    -- Feedback
    feedback TEXT,
    
    FOREIGN KEY (record_id) REFERENCES grading_records(id) ON DELETE CASCADE,
    INDEX idx_record (record_id),
    INDEX idx_char (char_text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
