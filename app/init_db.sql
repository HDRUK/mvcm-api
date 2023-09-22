-- Create DATABASE
CREATE DATABASE IF NOT EXISTS mydb;
USE mydb;

-- Create TABLE
CREATE TABLE IF NOT EXISTS CONCEPT (
    concept_id INT PRIMARY KEY,
    concept_name VARCHAR(255),
    domain_id VARCHAR(20),
    vocabulary_id VARCHAR(20),
    concept_class_id VARCHAR(20),
    standard_concept VARCHAR(1),
    concept_code VARCHAR(50),
    valid_start_date DATE,
    valid_end_date DATE,
    invalid_reason VARCHAR(1)
);

SELECT 'Table CONCEPT created' AS message;
