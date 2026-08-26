# Image Relevance Auto Tagging

This is my capstone project for the FlyRank Backend AI Engineering internship. The idea is simple to say and harder to build properly: given a folder of animal photos and a set of blog posts, the system should figure out which photo actually belongs with which post, based on what is really in the photo, not the filename or any keyword matching.

A post about red foxes should get a red fox photo. A wolf photo that looks kind of similar should get rejected, not picked because it was the closest thing available. And if nothing in the photo library is actually a good match, the system should say so honestly instead of guessing and hoping nobody notices.

That refusal part is really the whole point of this project. Anyone can build something that always returns an answer. Building something that knows when to say "I'm not confident enough to answer" is the harder and more useful skill, and that is what most of this project is actually about.

## What it does, in plain terms

1. It looks at every image with an AI vision model and writes down what it sees: the subject, the category (fox, wolf, dog, bear, or deer), some attributes, a caption, and how confident it is.
2. It turns the image captions and the blog post text into embeddings, which are just lists of numbers that represent meaning. Two pieces of text that mean similar things end up with numbers that are close together, even if they don't share any of the same words.
3. For each post, it finds the image whose numbers are closest to the post's numbers.
4. Before it ever suggests that image, it runs it through a mismatch guard. This is three checks in a row: is the image actually close enough in meaning, does its category match what the post expects, and was the model confident enough about that tag in the first place. If any of these fail, the match gets rejected with a plain English reason.
5. Everything the guard decides gets saved, and there is a small API where a human can look at a match, see why it was accepted or rejected, and approve or reject it themselves.

## Architecture

```
Images ---(vision model)---> tags, caption, confidence ---> stored in Images table
   |
   +---(embed the caption)---> image embedding

Posts ---(embed the post text)---> post embedding

GET /posts/{id}/images
   |
   +---> rank images by embedding distance to the post
   +---> run the mismatch guard (distance check, category check, confidence check)
         |
         +---> accepted, here is the image and why
         +---> rejected, here is why not

POST /matches/{post}/{image}/review
   +---> a human approves or rejects the guard's decision
```

## Stack

Python, FastAPI, asyncpg, Pydantic, PostgreSQL with the pgvector extension running in Docker, Gemini for both the vision tagging and the embeddings.

## How to run this

You will need Docker running, Python installed, and a Gemini API key from Google AI Studio (it's free, no card needed).

**1. Set up your environment**

Copy `.env.example` to `.env` and fill in your own `DATABASE_URL` and `GEMINI_API_KEY`. Never put real values in `.env.example`, that file is just a template that gets committed to git.

**2. Install everything**
```
pip install -r requirements.txt
```
This installs FastAPI, asyncpg, Pydantic, pytest, and the rest of what the project needs.

**3. Start the database**
```
docker compose up -d db
```
This spins up a Postgres container with pgvector already available, using the settings in `docker-compose.yml`. It runs in the background because of `-d`.

**4. Load the schema**

Run the contents of `schema.sql` against your database, either by pasting it into pgAdmin's query tool or piping it in through psql. This creates the four tables the project needs: `Images`, `Posts`, `Matches`, and `api_calls`, along with their indexes.

**5. Seed the data**

Run these one at a time, in this order:
```
python -m scripts.store_images_db
```
Reads every image file out of the `images/` folder and creates a row for each one in the `Images` table, marked as `pending`.

```
python -m scripts.store_posts
```
Reads `blog_posts.json` and creates a row for each blog post in the `Posts` table.

```
python -m scripts.find_pending_images
```
This is the batch job. It sends every pending image to the vision model, gets back a subject, category, attributes, caption, and confidence score, and saves all of that. If the model isn't confident enough, the image gets marked `flagged` instead of `done`. This step also writes a cost log entry for every call it makes.

```
python -m scripts.embed_images
```
Turns every image's caption into an embedding and saves it.

```
python -m scripts.embed_posts
```
Same thing, but for the blog post text.

```
python -m scripts.run_guard
```
Runs the actual matching logic across every post: finds the closest image, runs it through the three guard checks, and saves the decision.

**6. Start the API**
```
uvicorn src.main:app --reload
```
Then open `http://127.0.0.1:8000/docs` in a browser to see and try every endpoint.

**7. Run the tests**
```
pytest tests/ -v
```
All of this is also written down as one file in `capstone.yaml`, which lists the exact run, seed, and test commands together.

## What every file actually does

I wanted this section to actually be useful to someone opening the project for the first time, not just a list of filenames, so here is what each one is for.

### Root files

**schema.sql** is the database blueprint. It creates all four tables and their indexes. You run this once, before anything else.

**docker-compose.yml** describes the Postgres container with pgvector, so anyone can start the exact same database setup with one command.

**.env.example** shows which environment variables the project needs, with fake placeholder values. Your real `.env` file with your real API key never gets committed, it's in `.gitignore`.

**blog_posts.json** holds the 15 blog posts used in this project, three per animal category. Each post has its title, content, and which category it's expected to match.

**eval_set.json** is a small hand labeled answer key. For each of the 15 posts, I looked at the actual photos myself and picked which image I think is the genuinely correct match. This is used to measure how good the system's matching actually is, separate from what the system itself would pick.

**capstone.yaml** is a short file listing the exact commands to run, seed, and test the project, plus the list of API endpoints. This is meant to be the first thing an evaluator reads.

**requirements.txt** lists every Python package the project depends on.

**pytest.ini** is a tiny config file that tells pytest where to find the project's own code so the tests can import from `src/` correctly.

**DESIGN.md** is the plan I wrote before building anything, the database schema as I first imagined it. There's a short section at the bottom noting what actually changed once I started building, since a couple of things turned out to be unnecessary or missing once the real logic was written.

**EVIDENCE.md** has the actual proof, screenshots and command outputs, for every requirement in the project brief and every acceptance probe. If you want to see receipts instead of just claims, that file has them.

**BUILDLOG.md** is an honest log of where AI helped while I was building this, where it got something wrong or gave me a dead end, and what I actually changed because of that.

**test_evidence.txt** is my own working notes from testing different versions of the vision prompt and the embedding approach, kept as a personal record of what I tried and what the numbers looked like at each stage.

### src/ folder, the actual system

This is the real, permanent code. Everything in here gets imported and reused, nothing in here is a one-off script.

**database.py** just opens a connection to Postgres using the `DATABASE_URL` from `.env`. Every other file that needs the database goes through this.

**schemas.py** defines what a valid piece of vision output looks like using Pydantic. If the model returns something outside the expected shape, wrong category, confidence out of range, missing field, this is what catches it before it ever gets saved.

**vision.py** is the actual call to the Gemini vision model. It has the prompt that tells the model what to look for in each image and how to score its own confidence, and it sends the image and gets back a validated result.

**embeddings.py** turns a piece of text into a 768 number embedding using Gemini's embedding model, and also has a small helper that turns that list of numbers into the string format Postgres needs to store it as a vector.

**guard.py** is the decision core of the whole project. This is where the three gate checks live: is the image close enough in meaning, does the category match, was the model confident enough. It also has the logic for ranking images against a post and for saving a decision to the database.

**api_schemas.py** defines what the API sends back and receives, kept separate from `schemas.py` since those are about vision output, not the web layer.

**main.py** is the FastAPI app itself, the six endpoints that let you ask for ranked images, create a match, list matches, look at one match, and approve or reject one.

### scripts/ folder, the one time jobs

These are things you run once, or once per stage, to set things up or process data. None of them contain real logic themselves, they just call into `src/` and do a job.

**store_images_db.py** reads the image files off disk and creates the starting rows in the `Images` table.

**store_posts.py** reads `blog_posts.json` and creates the starting rows in the `Posts` table.

**resize_images.py** was used early on to shrink the original photos down to a reasonable size before uploading them, so the vision calls would be faster and cheaper.

**find_pending_images.py** is the batch tagging job described above.

**embed_images.py** and **embed_posts.py** generate and save the embeddings for images and posts.

**run_guard.py** runs the matching and guard logic across every post and saves the results.

**run_eval.py** compares the guard's actual picks against the hand labeled answers in `eval_set.json` and prints out how accurate the system is.

**forced_wolf.py** is one of the probes required by the brief. It deliberately hands the guard a wolf image on a fox post, one that is close enough in meaning to pass the first check, to prove the category check on its own actually catches it.

**semantic_test.py** is another proof script. It sends the guard a sentence that has nothing to do with any of the actual image captions in wording, "Vulpes vulpes, the scientific name for a wild canid," and checks that it still correctly finds fox images. This shows the matching works on meaning, not shared words.

**multi_image_test.py** was an early script I used just to poke at the vision model and see what kind of output it gave back, before `vision.py` and the batch job existed. It's not part of the real pipeline anymore, I kept it because it's an honest part of how this project actually got built.

### tests/ folder

**test_guard.py** tests the three gate checks directly, with made up input, no database needed. It checks each gate on its own, and also checks that they fire in the right order when more than one would technically apply.

**test_schemas.py** tests that the vision output validation actually catches bad data: wrong category, confidence out of range, a missing field, and broken JSON.

**test_api.py** tests the actual API endpoints, checking that ranking works, that missing posts return a proper not found error instead of crashing, that bad input gets rejected cleanly, and that the approve and reject workflow actually updates the right row without breaking anything else.

## The mismatch guard

This is genuinely the most important part of the project, so it's worth explaining on its own. The guard runs three checks, in this exact order, and stops at the first one that fails.

1. **Is the closest image actually close enough?** If the distance between the image and the post is too far, there's no point checking anything else, it's just not a match.
2. **Does the category match?** Even if two things are close in meaning, a wolf is not a fox. This check is what makes the fox versus wolf refusal actually work.
3. **Was the model confident about this tag in the first place?** Even a correct category tag isn't worth trusting if the model itself wasn't sure.

Only if all three pass does the guard accept the match. Every single decision, accepted or rejected, comes with a plain English explanation of why.

## How good is the matching, honestly

I measured this two different ways, and the two numbers tell different stories, so I'm reporting both instead of picking the one that looks better.

**Exact photo precision: 1 out of 15 posts (about 7 percent).** This measures whether the system's top pick was the exact same photo I personally would have picked for that post.

**Category precision: 15 out of 15 posts (100 percent).** This measures whether the system's top pick was at least the correct animal.

The reason these two numbers are so different comes down to how the posts and the photos are written. My blog posts are about topics, things like "wolf pack dynamics" or "the autumn rut." My photo captions describe specific scenes, things like "two wolves, one blurred in the background." A topic and a scene description just don't share much wording, even when the match is genuinely correct. So the system is very good at getting the right animal every time, which is what the mismatch guard actually promises, but picking the one exact photo I had in mind out of ten similar looking photos of the same animal is a much harder and honestly less meaningful task. I tried a couple of things to close that gap, changing the vision prompt to describe more unique detail per photo, and also trying to embed the attribute list alongside the caption, and neither one meaningfully improved the exact photo number. Both attempts and the reasoning are written up in BUILDLOG.md.

## Known limitations

I want to be upfront about the things I know aren't perfect, rather than let someone find them and wonder if I knew.

**Embedding calls are not cost tracked, only vision calls are.** I checked directly and the Gemini embedding API doesn't return any usage or token information in the version of the SDK I'm using, only the vision API does. The cost log table exists and is ready for it, there just isn't any real number to put in for embeddings right now.

**There's no vector index on the embedding columns.** At only 50 images, a plain search through every row is instant, and an approximate index like ivfflat can actually make results slightly worse at this small a scale. Adding one here would be adding complexity with no real benefit.

**The guard only ever looks at the single closest image per post.** This was a deliberate choice to keep the "safe rejection when uncertain" behavior simple. It means if the very best image for a post happens to rank second by a tiny margin, the guard never even considers it. A more advanced version could check the top handful of candidates instead of just one.

**Running the seed steps twice will create duplicate rows.** `store_images_db.py` and `store_posts.py` don't check if a row already exists before inserting, unlike the matches table which handles that properly. This is fine as long as seeding only happens once against a fresh database, which is the intended use.

**Tests run against the real local database, not a separate test database.** This was the simpler choice given the project's size and time, but it does mean the tests are changing real data temporarily while they run, even though they clean up after themselves.

## The six acceptance probes

All six are proven with real output and screenshots in EVIDENCE.md, but here's the short version:

1. Every image gets tagged, at least one gets flagged instead of guessed. Proven, 49 done, 1 flagged.
2. A fox post ranks fox images first, wolf and dog rank lower. Proven.
3. A wolf forced onto a fox post gets rejected specifically for category mismatch, even when it's close enough in meaning to pass the first check. Proven.
4. A post with no good match gets told so, with a reason. Proven.
5. The eval script reports a real, measured precision number. Proven and explained above.
6. Every AI call has a cost log entry. Proven for vision calls, documented as a known gap for embedding calls.