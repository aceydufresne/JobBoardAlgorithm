CREATE DATABASE embeddings;
USE embeddings;
CREATE TABLE term_vectors (
    term VARCHAR(255) PRIMARY KEY,
    vector BLOB NOT NULL
);
DESCRIBE term_vectors;
