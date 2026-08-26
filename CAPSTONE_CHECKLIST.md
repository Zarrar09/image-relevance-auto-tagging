# CAPSTONE_CHECKLIST.md

This file tracks verification of every requirement in the FlyRank capstone brief (AI Image Understanding & Content Matching Engine). It is updated in place. Do not create a new file for future checks, edit this one.

Each item below must be marked `[x]` only if verified true against the actual repository contents, with a one line note underneath saying exactly what file, command, or evidence was checked. If an item cannot be verified or is missing, leave it as `[ ]` and explain why underneath. Do not mark anything done based on assumption.

Last checked: 2026-08-26

---

## 1. Definition of Done (brief section 6)

### AI Processing

- [x] Vision model produces structured output validated against a schema; invalid responses are never trusted
  Checked: src/vision.py:60-64 passes `ImageResult.model_json_schema()` as the Gemini `response_format.schema`, then src/vision.py:73 calls `ImageResult.model_validate_json(...)`. src/schemas.py:13-18 enforces `category: Literal[...5 values]` and `confidence: Field(ge=0, le=1)`. Confirmed all 6 tests in `tests/test_schemas.py` pass (bad category, out-of-range confidence, missing field, malformed JSON all raise `ValidationError`).
- [x] Low-confidence classifications are flagged instead of accepted
  Checked: scripts/find_pending_images.py:44 `final_status = "done" if result.confidence >= 0.75 else "flagged"`. Ran a direct read-only SQL query against the live DB (`SELECT status, COUNT(*) FROM Images GROUP BY status`): 49 done, 1 flagged. `SELECT ... WHERE status='flagged'` returned imageID 13, confidence 0.65, category wolf — below the 0.75 cutoff, correctly flagged.
- [x] Images are processed through a batch background job with retries
  Checked: scripts/find_pending_images.py:5-6,25-31 — `MAX_ATTEMPTS = 3`, `RETRY_DELAY_SECONDS = 4`, a `for attempt in range(1, MAX_ATTEMPTS+1)` loop around `tag_one_image` with try/except, only marking `failed` after all 3 attempts are exhausted (lines 33-42). This runs as a standalone script off the request path, not inside main.py.
- [ ] Vision and embedding costs are tracked per call
  Checked: scripts/find_pending_images.py:59-67 inserts into `api_calls` after every vision call. But scripts/embed_images.py and scripts/embed_posts.py (read in full) never insert into `api_calls` — no cost row is written for any embedding call. Confirmed live: `SELECT purpose, COUNT(*) FROM api_calls GROUP BY purpose` returns only `vision_tagging` (50 rows); there is no `embedding` purpose row at all. This is honestly disclosed as a known limitation in EVIDENCE.md §1.4 and BUILDLOG.md, but the requirement as stated ("vision AND embedding costs tracked") is not met by the code.

### Matching System

- [x] Image and post embeddings are stored; posts return ranked image suggestions
  Checked: live query confirms 50/50 images and 15/15 posts have non-null `embedding` columns. `GET /posts/{post_id}/images` (src/main.py:32-59) calls `rank_images_for_post` which orders by `embedding <=> $1` (cosine distance) ascending. Directly re-ran the ranking logic for post 1 and got 5 fox images in ascending distance order (0.239 → 0.270).
- [ ] Semantic matching works for equivalent concepts ("red fox" matches "Vulpes vulpes")
  Not independently verified. This requires calling the paid Gemini embedding API, and `scripts/semantic_test.py` is on the explicitly forbidden list, so it was not run. Cross-checking EVIDENCE.md §2.2 instead: it references running `python -m scripts.probe_semantic_match`, but no file of that name exists in `scripts/` — the actual file is `scripts/semantic_test.py` (confirmed via `ls scripts/`). The claimed result (all 5 closest images being fox images for a "Vulpes vulpes" query) is plausible given the embedding-distance-only ranking logic in guard.py, but the command in the evidence doc does not match any real script, so the pasted evidence cannot be reproduced as documented.
- [x] The mismatch guard rejects incorrect recommendations (the wolf-on-a-fox-post scenario provably fails)
  Checked: reproduced the forced-wolf scenario myself by calling `find_match_for_forced_image` directly (not running the forbidden `scripts/forced_wolf.py`, just invoking the same guard.py function from a throwaway script). Result: fox post 1, closest wolf image (imageID 19) at distance 0.359 (inside the 0.45 similarity threshold), guard result `rejected`, explanation `"category mismatch, expected fox but detected wolf"` — matches EVIDENCE.md §2.4 exactly.
- [x] Rejections include a human-readable explanation
  Checked: src/guard.py:11-27 `evaluate_gates` builds an f-string explanation for every branch (distance, category, confidence). src/api_schemas.py `MatchDecisionOut`/`MatchOut` both expose an `explanation: str` field, and `tests/test_guard.py` asserts on the exact explanation text for all 4 gate outcomes (all passing).
- [x] When no image clears the bar, the system answers "no confident match" with reasons
  Checked: reproduced live — post 9 (expected category "dog"), closest image distance 0.452, above the 0.45 `SIMILARITY_THRESHOLD` in src/guard.py:1, guard returns `rejected` / `"no confident match, closest image distance 0.452 is above threshold 0.45"`. Matches EVIDENCE.md §2.6 exactly.

### Backend

- [x] Database models for images, tags, embeddings, posts, suggestions, approvals/rejections, with the required indexes
  Checked: schema.sql defines `images` (subject/category/attributes/caption = tags, `embedding VECTOR(768)`), `posts` (with its own embedding), `matches` (suggestions, with `reviewStatus` pending/approved/rejected = approvals/rejections), and `api_calls`. Ran a live `SELECT indexname, tablename FROM pg_indexes WHERE schemaname='public'` — confirmed indexes on images(status), images(category), posts(expectedCategory), matches(postID), matches(reviewStatus), api_calls(purpose), plus the 4 primary keys. Matches EVIDENCE.md §3.1's table exactly.
- [x] API endpoints validated; the review workflow (approve / reject / inspect why) exists
  Checked: src/main.py has `POST /matches/{post_id}/{image_id}/review` (approve/reject via `ReviewUpdate` Pydantic Literal), `GET /matches/{post_id}/{image_id}` (inspect why — returns `explanation`), `GET /matches` with `review_status` filter. All backed by passing tests in tests/test_api.py.
- [x] Automated tests cover schema validation, mismatch rejection, and matching accuracy
  Checked: `tests/test_schemas.py` (schema validation, 6 tests), `tests/test_guard.py` (mismatch rejection + gate ordering, 6 tests), both passing. "Matching accuracy" is not asserted inside pytest but is measured by the separate automated eval script `scripts/run_eval.py` (see Probe 5) — this split (deterministic pytest + a distinct AI-behavior eval) is exactly what shared-requirement §5 asks for.
- [ ] A small labeled evaluation dataset measures top-1 precision; the number is in the README
  eval_set.json (15 labeled posts) + scripts/run_eval.py exist and were run directly: `TOP-1 PRECISION: 6.67%` (1/15), matching EVIDENCE.md §4.1. But README.md (read in full — it is 2 lines) contains no precision number, no mention of the eval, and no mention of run_eval.py at all. The number exists in EVIDENCE.md but was never copied into the README, so this item is not met as written.

### Quality & Documentation

- [ ] README with architecture explanation and diagram; submission-pack files from section 11 present
  Checked README.md in full — it is exactly 2 sentences (name + one-line description). No architecture explanation, no diagram (ASCII or image), no run/seed steps, no limitations note, and no precision number. The submission-pack files themselves (capstone.yaml, EVIDENCE.md, BUILDLOG.md, .env.example) do exist (see section 2), but the README itself fails every content requirement in this line item.

---

## 2. Required submission files (brief section 11)

- [ ] README.md exists: explains what the system does, has an architecture diagram (image or ASCII), exact run + seed steps, and an honest limitations note
  File exists at repo root but only contains a 2-line description. No diagram, no run/seed steps, no limitations note — confirmed by reading the full file.
- [x] capstone.yaml exists: has `run:`, `seed:`, `test:`, `base_url:`, and the endpoints to probe
  Checked: capstone.yaml has all five — `run:` (docker compose + uvicorn), `seed:` (chained scripts.* commands), `test:` (pytest), `base_url:`, and an `endpoints:` list of all 6 routes, matching src/main.py's actual route decorators one-for-one.
- [x] EVIDENCE.md exists: one pasted proof per Definition of Done checkbox above (test output, curl transcript, or log line, not just a claim)
  Checked: EVIDENCE.md has a numbered section per DoD item with a command and a result for each, plus 18 referenced screenshots. Cross-checked several of the pasted numbers directly against the live DB and code (see probes below) and they matched, with two exceptions noted in section 7 (a script name that doesn't exist, and a category-accuracy number the current run_eval.py doesn't actually print).
- [x] BUILDLOG.md exists: documents where AI helped, where it was wrong, what was changed
  Checked: BUILDLOG.md has three clearly separated sections ("Where AI helped", "Where AI was wrong", "What I decided") with specific, concrete examples (e.g. the embedding-cost-tracking gap, the ON CONFLICT duplicate-rows bug, the "Animal" category naming mistake).
- [x] .env.example exists: lists every environment variable the app needs, with safe placeholder values, and the real .env is not committed
  Checked: .env.example lists POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, DATABASE_URL, PORT, GEMINI_API_KEY, all with placeholder values. Confirmed via `git ls-files` that `.env` itself is not tracked, and `git log --all -p -- .env` returned nothing (never committed at any point in history).

---

## 3. GitHub repo rules (brief section 11)

- [x] Repo is public and separate from any track-assignments repo
  Checked: `git remote -v` shows origin `https://github.com/Zarrar09/image-relevance-auto-tagging`. `curl -s -o /dev/null -w "%{http_code}" https://github.com/Zarrar09/image-relevance-auto-tagging` returned `200` (a private repo returns 404 to an unauthenticated request), and the repo root contains only this project's files, no other assignment content.
- [x] .gitignore excludes venv/virtualenv, `__pycache__`, `.pytest_cache`, and `.env`
  Checked .gitignore lines: `__pycache__/` (line 2), `.pytest_cache/` (line 51), `.env` (line 151), `venv/` (line 155). Confirmed via `git ls-files` that none of `venv/`, `__pycache__/`, `.pytest_cache/`, `.env` appear in the tracked file list, even though all four exist untracked in the working directory.
- [x] A LICENSE file is present
  Checked: LICENSE exists at repo root, full MIT license text, copyright 2026.
- [x] No API keys, tokens, or secrets appear anywhere in the committed history
  Checked: `git log --all -p -- .env` returned nothing. `git log --all -p | grep "GEMINI_API_KEY=AQ"` (the real key value currently sitting in the untracked local .env) returned nothing anywhere in history. `git grep GEMINI_API_KEY` in the working tree only finds `os.getenv("GEMINI_API_KEY")` references in src/vision.py and src/embeddings.py, never a literal value.
- [x] Commit history shows real incremental progress (multiple meaningful commits, not one single final dump)
  Checked: `git log --oneline` shows 20 commits, tracking a real progression (repo setup → schema design → docker → image collection → tagging bug fixes → phase-2 cost logging → embeddings → guard → eval iterations → tests → API → evidence → docs).
- [x] The image corpus (or a way to reproduce it) and blog_posts.json are committed so a stranger can actually run `seed`
  Checked: `git ls-files` lists all 50 images under `images/{bear,deer,dog,fox,wolf}/` (10 per category) and `blog_posts.json` at the root.

---

## 4. Acceptance probes (brief section 12, Layer 2)

- [x] **Probe 1** — Run the batch job on the corpus: every image gains schema-valid tags, and at least one low-confidence image is flagged, not guessed
  Verified against the live DB directly (not by re-running the batch job, per instructions): 50 images total (matches the 50 files in `images/`), 49 `done` + 1 `flagged` (imageID 13, confidence 0.65, below the 0.75 threshold in scripts/find_pending_images.py). Matches EVIDENCE.md §1.2 exactly.
- [x] **Probe 2** — Query images for the "red fox" article: the fox image ranks first, wolf and dog rank clearly lower
  Verified by calling `rank_images_for_post(conn, 1, 5)` directly: post 1's expected category is "fox"; top 5 results are all category=fox, distances 0.239, 0.244, 0.246, 0.262, 0.270, strictly ascending. Matches EVIDENCE.md §2.1 exactly.
- [x] **Probe 3** — Force the wolf as a candidate for the fox post: the guard rejects it with a category-mismatch explanation
  Verified by calling `find_match_for_forced_image` directly with fox post 1 and the closest wolf image (imageID 19, distance 0.359, inside the 0.45 threshold): result `rejected`, explanation `"category mismatch, expected fox but detected wolf"`. Matches EVIDENCE.md §2.4 exactly.
- [x] **Probe 4** — Query a post with no suitable image: the system returns "no confident match" with reasons
  Verified: post 9 (expected "dog") — closest image distance 0.452, above the 0.45 threshold, result `rejected`, explanation `"no confident match, closest image distance 0.452 is above threshold 0.45"`. Matches EVIDENCE.md §2.6 exactly.
- [ ] **Probe 5** — Run the eval script: top-1 precision is reported, and it matches the number written in the README
  Ran `python -m scripts.run_eval` directly (allowed command). Output: `TOP-1 PRECISION: 6.67%` (1/15 correct), `PRECISION ON ACCEPTED MATCHES: 7.14%` — this matches EVIDENCE.md §4.1's "6.67%" claim exactly. However README.md contains no precision number anywhere (it's a 2-line file), so there is nothing in the README for this number to "match" — the probe fails on the README half of the requirement.
- [ ] **Probe 6** — Check the cost log: every vision and embedding call is attributed with a cost entry
  Verified live: `SELECT purpose, COUNT(*), SUM(totalTokens) FROM api_calls GROUP BY purpose` returns only `vision_tagging` → 50 rows, 84,179 total tokens (matches EVIDENCE.md §1.4). There is no `embedding` row at all. Confirmed in code that scripts/embed_images.py and scripts/embed_posts.py never write to `api_calls`. Embedding calls are not attributed with a cost entry.

---

## 5. Shared requirements (brief section 12, every capstone must show these)

- [x] Layered architecture: data, logic, and HTTP are separated into different files/modules
  Checked: src/database.py (connection only), src/guard.py (matching/gate business logic), src/main.py (FastAPI routes) are separate modules, and main.py imports guard.py functions rather than reimplementing gate logic. Caveat: the `/matches` CRUD endpoints (`list_matches`, `get_match`, `review_match` in src/main.py:88-161) run raw SQL directly against the connection rather than delegating to guard.py or database.py, so the HTTP layer isn't fully insulated from SQL for those three routes — the core AI-matching logic is properly layered, the CRUD/review routes are not.
- [x] Validation at the boundary: bad input returns a clean 4xx, never a 500
  Checked src/main.py: `limit` out of [1,50] → explicit 400 (line 34-35); unknown post/match → explicit 404; bad `review_status` value → Pydantic `Literal` on `ReviewUpdate` → automatic 422; non-integer path param → automatic 422. Confirmed via passing tests: `test_invalid_limit_returns_400`, `test_get_images_for_missing_post_returns_404`, `test_non_integer_post_id_returns_422`, `test_review_rejects_invalid_status_value`, `test_list_matches_rejects_bad_review_status`.
- [x] At least one background job: slow/bulk work runs off the request path, with retries
  Checked: scripts/find_pending_images.py runs as a standalone script (not a request handler) with a 3-attempt retry loop and a 4s delay between attempts.
- [x] Real persistence: schema exists as a file (schema.sql or migrations), with the right indexes
  Checked schema.sql directly, and confirmed the indexes it defines actually exist in the live database via `pg_indexes`.
- [x] Idempotency where it matters: a retried action happens once, not twice (check the match-creation endpoint specifically)
  Checked src/guard.py:86-97 `save_match` uses `INSERT ... ON CONFLICT (postID, imageID) DO UPDATE`. `POST /posts/{post_id}/match` (src/main.py:62-85) calls this. Confirmed via `tests/test_api.py::test_creating_the_same_match_twice_is_idempotent` passing (posts the same match twice, row count unchanged).
- [x] Secrets are clean: only in .env, never logged, never committed
  Checked: `Grep` across the repo for any print/log statement referencing an API key or secret value found nothing (only `os.getenv("GEMINI_API_KEY")` reads in src/vision.py and src/embeddings.py). `.env` is gitignored and was never committed (see section 3). The real key only lives in the local, untracked `.env`.
- [ ] Cost is tracked per AI call, attributed
  Same finding as Probe 6 / DoD 1: only vision-tagging calls are logged to `api_calls` (50 rows, confirmed live). Embedding calls (scripts/embed_images.py, scripts/embed_posts.py) never write a cost row. Not met for the "per AI call" part of this requirement.
- [x] Tests cover the scary cases, deterministically, and AI-behavior features have an eval
  Checked: `pytest tests/ -v` run directly → 24/24 passed (gate-order edge cases, 404/400/422 boundary cases, idempotency). `scripts/run_eval.py` + `eval_set.json` provide the deterministic AI-behavior eval (top-1 precision against 15 hand-labeled posts), run directly and reproduced 6.67%.

---

## 6. Missing or incomplete items

1. **Embedding calls are not cost-tracked.** scripts/embed_images.py and scripts/embed_posts.py never insert into `api_calls`; only vision-tagging calls do (confirmed live: 50 `vision_tagging` rows, 0 `embedding` rows). This is honestly disclosed in BUILDLOG.md/EVIDENCE.md as a known SDK limitation, but it means "vision and embedding costs are tracked per call" (DoD), Probe 6, and the shared "cost is tracked per AI call" requirement are all not actually met by the code as it stands. Fix: either log embedding calls with token counts of `0`/estimated values and a note, or switch to an SDK/endpoint that returns usage data for `embed_content`.
2. **README.md is not a real README.** It is 2 sentences. It is missing: an architecture explanation, an architecture diagram (ASCII or image), exact run + seed steps, an honest limitations note, and the top-1 precision number (6.67%, confirmed by directly running `scripts.run_eval`). Fix: expand README.md using the material that already exists in DESIGN.md, EVIDENCE.md, BUILDLOG.md, and capstone.yaml — none of that needs to be reinvented, it just needs to be pulled into the README.
3. **Probe 5 fails on the README half.** Even though `scripts.run_eval` correctly reports 6.67% and that matches EVIDENCE.md, there is no number in README.md at all for it to "match." Fixed by item 2 above.
4. **EVIDENCE.md §2.2 references a script that does not exist.** It says to run `python -m scripts.probe_semantic_match`; the actual file is `scripts/semantic_test.py`. Either rename the script to match the doc or fix the doc — as written, a stranger following EVIDENCE.md cannot reproduce this probe.
5. **EVIDENCE.md §4.1's "15/15 (100%) category accuracy" number cannot be reproduced.** scripts/run_eval.py, as it currently exists, only prints top-1 exact-match precision and precision-on-accepted-matches — it never computes or prints a category-level accuracy figure. Either add that computation to run_eval.py, or remove/caveat the claim in EVIDENCE.md.

If nothing else were wrong, that would be it — the AI-processing pipeline, matching guard, database layer, API, and tests themselves are all solid and directly verified. The gaps above are specific and fixable, not structural.

---

## 7. Notes / anything that looks inconsistent between files

- **README.md vs. everything else:** capstone.yaml, EVIDENCE.md, BUILDLOG.md, and DESIGN.md all assume a reader has run/seed instructions, an architecture explanation, and a precision number to reference — but none of that content actually lives in README.md, which is only a 2-line project description. The other docs are internally consistent with the code; README.md is just radically underfilled relative to what the brief and the other docs assume it contains.
- **EVIDENCE.md §2.2 command name mismatch:** the doc says `python -m scripts.probe_semantic_match`; the real file in `scripts/` is `semantic_test.py`. No file named `probe_semantic_match.py` exists anywhere in the repo (`git ls-files | grep scripts` confirmed).
- **EVIDENCE.md §4.1 category-accuracy figure is not something the current code produces.** `scripts/run_eval.py` only prints "TOP-1 PRECISION" and "PRECISION ON ACCEPTED MATCHES" — there is no category-accuracy calculation in the script at all, so the "15 out of 15 (100%)" figure in EVIDENCE.md isn't something a stranger can reproduce by running the documented command. It may be true (every "accepted" result implies a category match by construction of `evaluate_gates`, and only 1 of 15 posts was rejected), but the script doesn't say so explicitly, and the one rejected post's category-match status isn't shown by any current output.
- **schema.sql has leftover migration debris.** `idx_images_status` is created twice — once as a plain `CREATE INDEX` (line 39) and again as `CREATE INDEX IF NOT EXISTS` (line 53). Harmless (the second is a no-op) but not cleaned up. Similarly, `ALTER TABLE api_calls ADD COLUMN IF NOT EXISTS postID ...` (line 59) is a no-op because `postID` is already declared in the `CREATE TABLE api_calls` block above it (line 45). This matches DESIGN.md's own note that `api_calls` was added after the fact in "Phase 2," but the leftover ALTER statement in schema.sql itself wasn't cleaned up once the column was folded into the main CREATE TABLE.
- **docker-compose.yml defines a `web` service with `build: .`, but there is no Dockerfile anywhere in the repo** (`ls Dockerfile` / `git ls-files | grep -i dockerfile` both empty). This service would fail to build if started. It doesn't currently break anything because capstone.yaml's `run:` command only does `docker compose up -d db` (the `db` service) and then runs `uvicorn` directly on the host — the broken `web` service is simply never invoked by the documented run path. Still worth removing or fixing the `web` service definition so `docker compose up` (without specifying a service) doesn't fail.
- **test_evidence.txt** (repo root) is a leftover scratch/dev log from an earlier prompt-iteration test run (explicitly labeled "TEST RUN 1 - original prompt, caption only" and referencing numbers that no longer match the current database state, e.g. post 1 → distance 0.275 there vs. 0.239 now). It isn't one of the required submission files and isn't referenced by capstone.yaml, README.md, or EVIDENCE.md as authoritative, so it's not a contradiction, just uncommitted clutter worth removing before submission.
