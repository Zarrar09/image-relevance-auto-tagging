# BUILDLOG.md

This is an honest log of where AI helped while building this project, where it got things wrong, and what I actually decided or changed myself. I used Claude a lot while building this, but the schema design, the eval set, the data checks, and the calls on what was actually good enough were mine, not something I just accepted because it was suggested.

## Where AI helped

- Helped me write docker-compose.yml, since I did not know the exact format and style to write it in.
- Helped troubleshoot Docker Desktop failing to start. Turned out to be a virtualization setting issue at first, then WSL2 was not even installed on my machine.
- Helped me write the FastAPI endpoints and the Pydantic models once I had already decided what the six endpoints needed to do.
- Explained why asyncpg has no native pgvector support and helped me get the vector cast workaround working, since I had never used pgvector before.
- Helped write the pytest files once I decided what actually needed testing, the three gates in the guard, the schema validation, and the API endpoints.
- Helped me fix a pytest import error where the tests could not find the src folder, which just needed a pytest.ini file added.
- Helped write the retry logic in find_pending_images.py and explained why max_tokens needs to be set high even for a short answer, since reasoning models spend tokens thinking before they respond.
- Helped draft the confidence rubric in the vision prompt after my first version kept returning 1.0 for basically every image, which was useless.

## Where AI was wrong

- Early on when I was designing the database schema, I used the word "Animal" to describe the category field. This confused me later because it did not line up with what the brief actually calls it, and it was not even consistent with itself. Once I actually started building the schema I noticed this and fixed it.
- At one point it suggested I could improve my precision score by rewriting my blog posts so they matched the photos I had already picked as correct answers. I caught that this would basically mean changing the test until it agreed with itself, which is not a real measurement. We did not do this.
- It suggested embedding the image attributes together with the caption to try fix the low exact photo precision score. I tested it myself and the number did not improve at all, and it actually caused one post to flip from a correct rejection into a wrong acceptance. I reverted it back to caption only after seeing the real numbers.
- It assumed the Gemini embedding API would return token usage the same way the vision API does. I wrote a small script to check this directly and it turned out to be false, the embedding response has no usage data in the version I am using. This is why embedding calls are not cost tracked in this project, it is a real gap, not something hidden.
- The ON CONFLICT logic in save_match only updates a row when both the post ID and image ID match exactly. After I reran run_guard.py a few times while testing different prompt versions, this left old rows sitting in the matches table instead of getting replaced, since the guard's top pick for some posts had changed. I noticed this myself when the matches table had 30 rows instead of 15, and we fixed it once we understood why.

## What I decided

- I built the matches table as a third table, this was not something AI suggested. I remembered from my database course that when you have a many to many relationship you need a separate table for it, and I decided that table should use a composite key of imageID and postID.
- I originally had fields planned that would have stored more than one value in a single column, which is not how a relational database is supposed to work. I decided these belonged as their own proper columns instead, tied to the specific match, not crammed into one field.
- I added a status column to both the Images table and the Posts table, since both of them go through stages, not yet processed, done, or something that failed and needs a retry. It made sense for both tables to be able to represent that.
- I picked all 15 answers in the eval set by actually looking at the image filenames and photo content myself, not by trusting the captions or just copying whatever the guard already picked. If I had copied the guard's own picks the accuracy number would not have meant anything.
- I decided to keep the more descriptive vision prompt even though it made the exact photo precision score go down, because the captions themselves got genuinely better and the category level accuracy stayed at 100 percent either way.
- I noticed early on that images 1, 2, and 3 were stuck on a pending status left over from an old test I ran in a previous session, and flagged that before it messed up the eval set results.
- I manually tested every API endpoint through the Swagger docs before we wrote any automated tests for them, including the approve and reject flow and what happens when you send an invalid status.
- I decided not to keep chasing the exact photo precision number higher once it was clear the real reason for the gap was that my blog posts are written about topics while my photo captions describe specific scenes. That is just how the data is, not something worth breaking the actual system to fix.
- I chose to document the embedding cost tracking gap honestly instead of faking a number to make a checklist item look done.