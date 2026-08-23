CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE images (
    imageID SERIAL PRIMARY KEY,
    filePath VARCHAR(255) NOT NULL,
    subject VARCHAR(255),
    category VARCHAR(255),
    attributes TEXT[],
    caption VARCHAR(255),
    confidence DECIMAL(5, 2),
    embedding VECTOR(768),
    status VARCHAR(100) NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    postID SERIAL PRIMARY KEY,
    postContent TEXT NOT NULL,
    expectedSubject VARCHAR(255),
    expectedCategory VARCHAR(255),
    embedding VECTOR(768),
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