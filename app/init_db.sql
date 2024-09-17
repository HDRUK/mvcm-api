-- Disable foreign key checks
SET FOREIGN_KEY_CHECKS = 0;

-- Drop all tables dynamically
DROP TABLE IF EXISTS CONCEPT;
DROP TABLE IF EXISTS STANDARD_CONCEPTS;
DROP TABLE IF EXISTS CONCEPT_SYNONYM;
DROP TABLE IF EXISTS CONCEPT_RELATIONSHIP;
DROP TABLE IF EXISTS CONCEPT_ANCESTOR;

-- Enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Create CONCEPT TABLE
CREATE TABLE IF NOT EXISTS CONCEPT (
    concept_id INT PRIMARY KEY,
    concept_name VARCHAR(500),
    domain_id VARCHAR(20),
    vocabulary_id VARCHAR(20),
    concept_class_id VARCHAR(20),
    standard_concept VARCHAR(1),
    concept_code VARCHAR(50),
    valid_start_date DATE,
    valid_end_date DATE,
    invalid_reason VARCHAR(1)
);

CREATE FULLTEXT INDEX idx_concept_name ON CONCEPT(concept_name);
CREATE INDEX idx_concept_id ON CONCEPT(concept_id);
CREATE INDEX idx_standard_concept_vocabulary_id_concept_id ON CONCEPT(standard_concept, vocabulary_id, concept_id);

SELECT 'Table CONCEPT created' AS message;

-- Create STANDARD_CONCEPTS TABLE
CREATE TABLE IF NOT EXISTS STANDARD_CONCEPTS LIKE CONCEPT;

CREATE FULLTEXT INDEX idx_sc_concept_name ON STANDARD_CONCEPTS(concept_name);
CREATE INDEX idx_sc_concept_id ON STANDARD_CONCEPTS(concept_id);
CREATE INDEX idx_sc_standard_concept_vocabulary_id_concept_id ON STANDARD_CONCEPTS(standard_concept, vocabulary_id, concept_id);

SELECT 'Table STANDARD_CONCEPTS created' AS message;

-- Create CONCEPT_SYNONYM TABLE
CREATE TABLE IF NOT EXISTS CONCEPT_SYNONYM (
    concept_id INT,
    concept_synonym_name VARCHAR(1000) COLLATE utf8_bin,
    language_concept_id INT,
    PRIMARY KEY (concept_id, concept_synonym_name, language_concept_id),
    FOREIGN KEY (concept_id) REFERENCES CONCEPT(concept_id),
    FOREIGN KEY (language_concept_id) REFERENCES CONCEPT(concept_id)
);

CREATE FULLTEXT INDEX idx_concept_synonym_name ON CONCEPT_SYNONYM(concept_synonym_name);
CREATE INDEX idx_concept_synonym_id ON CONCEPT_SYNONYM(concept_id);
SELECT 'Table CONCEPT_SYNONYM created' AS message;

-- Create CONCEPT_RELATIONSHIP TABLE
CREATE TABLE IF NOT EXISTS CONCEPT_RELATIONSHIP (
    concept_id_1 INT,
    concept_id_2 INT,
    relationship_id VARCHAR(20),
    valid_start_date DATE,
    valid_end_date DATE,
    invalid_reason VARCHAR(1),
    PRIMARY KEY (concept_id_1, concept_id_2, relationship_id),
    FOREIGN KEY (concept_id_1) REFERENCES CONCEPT(concept_id),
    FOREIGN KEY (concept_id_2) REFERENCES CONCEPT(concept_id)
);

CREATE INDEX idx_concept_relationship_on_id1_enddate ON CONCEPT_RELATIONSHIP(concept_id_1, valid_end_date);
CREATE INDEX idx_concept_relationship_on_id2 ON CONCEPT_RELATIONSHIP(concept_id_2);
SELECT 'Table CONCEPT_RELATIONSHIP created' AS message;

-- Create CONCEPT_ANCESTOR TABLE
CREATE TABLE IF NOT EXISTS CONCEPT_ANCESTOR (
    ancestor_concept_id INT,
    descendant_concept_id INT,
    min_levels_of_separation INT,
    max_levels_of_separation INT,
    PRIMARY KEY (ancestor_concept_id, descendant_concept_id),
    FOREIGN KEY (ancestor_concept_id) REFERENCES CONCEPT(concept_id),
    FOREIGN KEY (descendant_concept_id) REFERENCES CONCEPT(concept_id)
);

CREATE INDEX idx_concept_ancestor_on_descendant_id ON CONCEPT_ANCESTOR(descendant_concept_id);
CREATE INDEX idx_concept_ancestor_on_ancestor_id ON CONCEPT_ANCESTOR(ancestor_concept_id);
SELECT 'Table CONCEPT_ANCESTOR created' AS message;
