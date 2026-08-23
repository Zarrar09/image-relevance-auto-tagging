## AI HELP

- It helped me write docker-compose.yml, since I did not know the exact format and style to write it in.
- Helped troubleshoot Docker Desktop failing to start (virtualization issue in Docker Desktop, then WSL2 was not installed)

## AI was Wrong
 - Early on when designing the database schema, I got confused as used 'Animal' to explain category but it just confused me as
   it was not consistent as well with the brief. Then when I started building the schema, I realized this mistake and fixed it.

## What I decided
 - I chose to build a 3rd table of matches, which was not suggested by the AI. I recalled my database course fundamentals that when there
 is a M:N relationship, it forms a third table. This table I suggested to build a composite key of photoID and postID.
 - Furthermore, I removed receivedCategory and receivedSubject as in a relational databse we can only store one value per data, so storing multiple was wrong. So I made the decision they belong in the matches table instead.
 - Added a status attribute to both the Images and Post table, as both of them are organized and classfied so both can have a possibility where a row is not processed, is completed, not attempted, or needs a retry.