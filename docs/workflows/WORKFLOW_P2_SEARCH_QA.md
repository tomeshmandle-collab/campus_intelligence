# Team Workflow & AI Prompting Playbook — P2: Search & Question Answering

**Role:** P2 — Search & Question Answering  
**Primary Focus:** Search benchmark dataset, PostgreSQL full-text search backend, grounded Q&A orchestration with Gemini, and citation/uncertainty handling.  
**Boundaries:** Work within `backend/app/services/search/`, `backend/app/services/qa/`, and `tests/fixtures/qa/`. Do not modify database auth policies, storage buckets, or frontend UI layout.  
**Reference Document:** Refer to [docs/MASTER_PROJECT_ISSUES.md](file:///c:/Users/tomes/OneDrive/Desktop/campus_intelligence/docs/MASTER_PROJECT_ISSUES.md) for full issue specifications.

---

## 1. General Rules for Working with Git

Before you begin any task:
1. Make sure your local repository is on `main` and up to date:
   ```bash
   git switch main
   git pull origin main
   ```
2. Create your dedicated branch for the issue:
   ```bash
   git switch -c <branch-name>
   ```
3. Never work directly on `main`. Never commit API keys or passwords.
4. When finished, push your branch and open a Pull Request (PR) on GitHub tagging `@ProjectLead`.

---

## 2. Complete Issue Sequence & Step-by-Step AI Prompts for P2

---

### Issue P2-1 (Phase 1): Search Query Benchmark & Grounded Q&A Evaluation Dataset
- **Branch Name:** `feat/search-qa-dataset`
- **Working Directory:** `tests/fixtures/qa/`
- **Prerequisites:** Git setup, repository cloned.
- **Scope:** Build realistic benchmark of 25+ search queries and answerable/unanswerable questions.

#### 🔹 Prompt 1: Benchmark Dataset Creation
> "I am working as P2 (Search and Q&A) on CAI Campus Intelligence. Read `docs/MODULES.md` (M08 Search & Retrieval, M09 Question Answering) and `docs/PRD.md`.
> In `tests/fixtures/qa/search_qa_queries.json`, create a JSON evaluation dataset of 25 realistic college queries:
> - Category A (Keyword Search): Exact queries with expected notice IDs (e.g., 'library book return fine', 'hostel admission form last date').
> - Category B (Answerable Questions): Natural questions with expected factual answer, source notice filename, page number, and quote excerpt.
> - Category C (Unanswerable / Out of Scope): Questions college notices do not answer (e.g., 'What is today's lunch menu in canteen?'). Expected output: `not_found`.
> - Category D (Amended Notices): Questions where an earlier notice was changed by a later notice; answer must reflect the amended notice."

#### 🔹 Prompt 2: Dataset Verification Script
> "In `tests/scripts/verify_qa_dataset.py`, write a Python script to validate `tests/fixtures/qa/search_qa_queries.json`.
> Verify that every item has required fields (`id`, `query_type`, `query_text`, `expected_behavior`). Check that all query types match one of ['keyword_search', 'answerable_qa', 'unanswerable_qa', 'amended_qa']. Return exit code 0 if valid."

---

### Issue P2-2 (Phase 4): PostgreSQL Full-Text Keyword Search API & Chunk Indexing
- **Branch Name:** `feat/postgres-search-api`
- **Working Directory:** `backend/app/services/search/`, `backend/app/api/v1/`
- **Prerequisites:** Phase 2 notice ingestion complete and notice chunks populated.
- **Scope:** Build chunking generator and PostgreSQL `tsvector` keyword search endpoint.

#### 🔹 Prompt 1: Chunk Generator Service
> "Read `docs/DATABASE_SCHEMA.md` Section 3.4. In `backend/app/services/search/chunker.py`, implement a chunk generator:
> - Take notice page text and split into logical paragraph chunks (approx 200–400 words) while strictly retaining `page_number` and `notice_id`.
> - Save chunks into `notice_chunks` table, generating PostgreSQL full-text search vector `tsvector` on `chunk_text`."

#### 🔹 Prompt 2: Search API Endpoint
> "Read `docs/API_CONTRACTS.md` Section 7.6. In `backend/app/api/v1/search.py`, implement `GET /api/v1/search`:
> - Accept query parameters: `q` (search term), `audience`, `category`, `page`, `limit`.
> - Query `notices` and `notice_chunks` using PostgreSQL `websearch_to_tsquery` and ranking with `ts_rank`.
> - Filter: STRICTLY return only notices where `publication_status = 'published'`.
> - Response: Return matched notices with highlighted text snippet, relevance score, and source page number."

---

### Issue P2-3 (Phase 4): Backend Ask / Q&A Orchestration using Notice Evidence
- **Branch Name:** `feat/ask-orchestration-gemini`
- **Working Directory:** `backend/app/services/qa/`, `backend/app/api/v1/`
- **Prerequisites:** Issue P2-2 search service working.
- **Scope:** Grounded Q&A pipeline calling Gemini with retrieved notice chunks.

#### 🔹 Prompt 1: Grounded Q&A Orchestrator Service
> "Read `docs/MODULES.md` M09. In `backend/app/services/qa/ask_service.py`, implement `answer_question(question: str) -> AskResponse`:
> 1. Step 1: Use full-text search to retrieve top 3 most relevant chunks from published notices.
> 2. Step 2: If highest relevance score is below minimum threshold, immediately return `confidence_level: 'not_found'` with answer 'No published college notices contain information to answer this question.'
> 3. Step 3: If chunks exist, format prompt:
>    'You are CAI Campus Intelligence assistant. Answer the user question using ONLY the provided notice evidence below. Do not use external knowledge or fabricate facts. Quote the exact notice and page number for each fact.'
> 4. Call Gemini backend API and parse response into Pydantic model: `answer`, `confidence_level` ('high'|'medium'|'uncertain'), and `supporting_sources`."

#### 🔹 Prompt 2: Ask Endpoint Handler
> "In `backend/app/api/v1/ask.py`, implement `POST /api/v1/ask` per `docs/API_CONTRACTS.md` Section 7.7. Connect to `ask_service.py`, handle timeouts and rate-limit errors gracefully with HTTP 503 fallback."

---

### Issue P2-4 (Phase 4): Citation Verification & Uncertainty / Not-Found Fallbacks
- **Branch Name:** `feat/citations-uncertain-handling`
- **Working Directory:** `backend/app/services/qa/`, `tests/`
- **Prerequisites:** Issue P2-3 implemented.
- **Scope:** Post-generation citation verification preventing fabricated citations.

#### 🔹 Prompt 1: Citation Verifier & Grounding Validator
> "In `backend/app/services/qa/citation_verifier.py`, implement citation validation:
> - For every source in `supporting_sources`, check if the quoted excerpt actually occurs (via substring or fuzzy match >85%) in the corresponding retrieved chunk.
> - If an excerpt is fabricated/hallucinated by AI, remove that citation. If zero valid citations remain, downgrade `confidence_level` to `uncertain`.
> - Write Pytest tests in `tests/test_qa_grounding.py` verifying that hallucinations are caught and unanswerable queries return `not_found`."

---

## 3. Pre-PR Submission Checklist for P2
- [ ] Run search and Q&A tests:
  ```bash
  python tests/scripts/verify_qa_dataset.py
  pytest tests/test_qa_grounding.py
  ```
- [ ] Check Git status: verify zero secrets or `.env` files staged.
- [ ] Push branch: `git push -u origin <branch-name>`
- [ ] Open PR tagging `@ProjectLead`.
