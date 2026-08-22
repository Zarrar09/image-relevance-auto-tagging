-- pgvector needs to be enabled once, before any table uses the VECTOR type
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE images (
    imageID SERIAL PRIMARY KEY,
    filePath VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL,
    attributes TEXT[] NOT NULL,
    caption VARCHAR(255) NOT NULL,
    confidence DECIMAL(5, 2) NOT NULL,
    embedding VECTOR(768) NOT NULL,
    status VARCHAR(100) NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    postID SERIAL PRIMARY KEY,
    postContent TEXT NOT NULL,
    expectedSubject VARCHAR(255) NOT NULL,
    expectedCategory VARCHAR(255) NOT NULL,
    embedding VECTOR(768) NOT NULL,
    status VARCHAR(100) NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE matches (
    imageID INT NOT NULL,
    postID INT NOT NULL,
    calculatedSimilarity DECIMAL(5, 2) NOT NULL,
    result VARCHAR(100) NOT NULL,
    explanation TEXT NOT NULL,
    reviewStatus VARCHAR(255) NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (imageID, postID),
    FOREIGN KEY (imageID) REFERENCES images(imageID),
    FOREIGN KEY (postID) REFERENCES posts(postID)
);

CREATE INDEX idx_images_status ON images (status);
CREATE INDEX idx_matches_postID ON matches (postID);