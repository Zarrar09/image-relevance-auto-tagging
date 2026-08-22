## Images

This is the design of the database before implementing it, to reduce the number of issues and have it properly planned out.

Schema for images:

- imageID: INT, primary key
- filePath: VARCHAR
- subject: VARCHAR
- category: VARCHAR
- attributes: TEXT[] (or JSON)
- caption: VARCHAR
- confidence: DECIMAL
- embedding: VECTOR(N)
- status: VARCHAR (pending/processing/done/failed)
- createdAt: TIMESTAMP
- index: status

## Posts

Schema for posts:

- postID: integer, and is going to be the primary key for the posts
- postContent: VARCHAR, the actual information regarding the post
- expectedSubject: VARCHAR, What the model expects to see in the images subject
- expectedCategory: VARCHAR, What the model expects to see in the images category
- embedding: VECTOR(N)
- status: VARCHAR, pending, processing, done, failed
- createdAt: TIMESTAMP

## Mathces

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
- index: postID, imageID