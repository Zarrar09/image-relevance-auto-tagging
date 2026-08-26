This is the design of the database before implementing it, to reduce the number of issues and have it properly planned out.

## Images

Schema for images:

- imageID: INT, primary key
- filePath: VARCHAR
- subject: VARCHAR
- category: VARCHAR
- attributes: TEXT[] (or JSON)
- caption: VARCHAR
- confidence: DECIMAL
- embedding: VECTOR(N)
- status: VARCHAR (pending/processing/done/failed/flagged)
- createdAt: TIMESTAMP
- index: status, category

## Posts

Schema for posts:

- postID: integer, and is going to be the primary key for the posts
- postContent: VARCHAR, the actual information regarding the post
- expectedCategory: VARCHAR, what the model expects to see in the image's category
- embedding: VECTOR(N)
- status: VARCHAR, pending, processing, done, failed
- createdAt: TIMESTAMP
- index: expectedCategory

## Matches

Since both have a relationship of M:N therefore, we have to create a schema for matches.

Schema for matches:

- postID: INT, FK -> posts
- imageID: INT, FK -> images
- (postID, imageID) -> composite primary key
- calculatedSimilarity: DECIMAL
- result: VARCHAR (accepted/rejected)
- explanation: TEXT
- reviewStatus: VARCHAR (pending/approved/rejected)
- createdAt: TIMESTAMP
- index: postID, reviewStatus

## API Calls

Added during Phase 2 to track cost per AI call, one row per vision or embedding call made.

Schema for api_calls:

- callID: INT, primary key
- imageID: INT, FK -> images (nullable, since post embedding calls have no image)
- postID: INT, FK -> posts (nullable, since image calls have no post)
- purpose: VARCHAR (vision_tagging/embedding)
- inputTokens: INT
- outputTokens: INT
- totalTokens: INT
- createdAt: TIMESTAMP
- index: purpose

## Changes from the original design

- expectedSubject on Posts was removed. expectedCategory was enough for the guard category check.
- flagged was added to the status values of pending/processing/done/failed. 
- api_calls was added as a fourth table, not in the original three-table plan. Cost tracking per call was a requirement from the start, but it needed its own table rather than every image having its own section of billing, as an image can create a bill more than once.