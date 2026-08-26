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

CREATE TABLE api_calls (
    callID SERIAL PRIMARY KEY,
    imageID INT REFERENCES Images(imageID),
    postID INT REFERENCES Posts(postID),
    purpose VARCHAR(100) NOT NULL,
    inputTokens INT NOT NULL,
    outputTokens INT NOT NULL,
    totalTokens INT NOT NULL,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_images_status ON Images(status);
CREATE INDEX IF NOT EXISTS idx_images_category ON Images(category);
CREATE INDEX IF NOT EXISTS idx_posts_expectedcategory ON Posts(expectedCategory);
CREATE INDEX IF NOT EXISTS idx_matches_postid ON Matches(postID);
CREATE INDEX IF NOT EXISTS idx_matches_reviewstatus ON Matches(reviewStatus);
CREATE INDEX IF NOT EXISTS idx_api_calls_purpose ON api_calls(purpose);