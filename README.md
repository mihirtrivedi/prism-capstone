# Prism: Production-Grade LLM Gateway and Semantic Cache

**Prism** is an AI-first, production-grade LLM Gateway and Semantic Cache built for the Airtribe AI-first Software Engineering Program Capstone.

The gateway sits in the hot path between applications and upstream model providers, making real-time AI decisions:
1. **Smart Difficulty Routing (`model: "auto"`):** Classifies prompt complexity to dispatch queries to `fast` or `smart` model tiers (100% accuracy on the trapped eval benchmark).
2. **Per-Tenant Semantic Caching:** Matches semantic meaning (paraphrases) rather than exact strings, with strict tenant isolation to prevent data leaks.
3. **Resilience & Failover:** Upstream timeouts, exponential backoff retries, and automated fallback chains across multiple providers (Alpha $\rightarrow$ Beta).
4. **Zero-Buffer Streaming:** Passes SSE token chunks progressively to clients while metering token consumption upon stream completion.
5. **Multi-Tenancy & Governance:** Enforces virtual keys, model allowlists, atomic sliding-window rate limits (zero over-admission), and monthly cost budgets.
6. **Ops Console:** Embedded real-time dashboard displaying tenant spend, cache hit rates, and granular request logs.

---

## Documentation & Specifications

* 📋 **[problem-statement.md](problem-statement.md)**: Capstone requirements, 9 Must-Have features, grading criteria, and deliverables.
* 🔌 **[docs/api-contract.md](docs/api-contract.md)**: API schema, OpenAI payload structure, header contracts, and error responses.
* 🗄️ **[docs/data-model.md](docs/data-model.md)**: Schemas, persistence entities, usage records, and cache models.
* 📊 **[docs/evaluation-guide.md](docs/evaluation-guide.md)**: Smoke test, concurrency load test, and routing evaluation guidelines.
* 🛠️ **[docs/implementation-guide.md](docs/implementation-guide.md)**: Staged build roadmap, failure injection scenarios, and FAQ.

---

## Architecture Overview

```
                                      +--------------------------+
                                      |     Client Application    |
                                      +--------------------------+
                                                   |
                                     (Virtual Key Bearer Token)
                                                   v
                          +------------------------------------------------+
                          |              Prism LLM Gateway                 |
                          |                 (FastAPI)                      |
                          +------------------------------------------------+
                                 |                 |                 |
                   +-------------+                 |                 +-------------+
                   v                               v                               v
         [ Sliding Window ]             [ Semantic Cache ]               [ Smart Router ]
         Zero Over-Admission             Per-Tenant Isolated            'auto' 100% Eval
                   |                               |                               |
                   +-------------------------------+-------------------------------+
                                                   |
                                          (Provider Adapter)
                                                   |
                         +-------------------------+-------------------------+
                         v                                                   v
             +-----------------------+                           +-----------------------+
             | Mock Provider Alpha   |  ---(Live Failover)--->   | Mock Provider Beta    |
             | (:9001, alpha-small)  |                           | (:9002, beta-small)   |
             +-----------------------+                           +-----------------------+
```

---

## Quickstart Guide

### 1. Requirements
* Python 3.9+ (Python 3.12 recommended)
* Installed dependencies:
  ```bash
  pip install fastapi uvicorn httpx pydantic
  ```

### 2. Start Upstream Providers & Gateway

You can launch all services manually or with the automated runner.

#### Manual Startup:
* **Terminal 1 (Provider Alpha):**
  ```powershell
  python scripts/mock_provider.py --port 9001 --name alpha
  ```
* **Terminal 2 (Provider Beta):**
  ```powershell
  python scripts/mock_provider.py --port 9002 --name beta
  ```
* **Terminal 3 (Prism Gateway):**
  ```powershell
  python main.py --port 8080
  ```

---

## Running Verification & Tests

### Automated All-In-One Verification
Run the end-to-end verification suite (spins up providers, runs smoke test, runs load test, and terminates cleanly):

```powershell
python scripts/run_full_verification.py
```

### 1. Smoke Test (Contract Compliance)
```powershell
python scripts/smoke_test.py --url http://localhost:8080 --key prism-sk-search-1a2b3c --model fast
```
* **Result:** **18 passed, 0 warnings, 0 failed** (Validates 200 responses, streaming, SSE chunks, [DONE], headers, auth, unknown models, exact repeat cache hits, paraphrase cache hits, and unrelated prompt misses).

### 2. Concurrency Load Test (Zero Over-Admission)
```powershell
python scripts/load_test.py --url http://localhost:8080 --key prism-sk-free-7g8h9i --model fast --requests 30 --concurrency 10 --rpm-limit 10
```
* **Result:** **Accepted (200): 10, Rate Limited (429): 20**.
* **Zero Over-Admission:** Target achieved. Client accounting totals match gateway usage logs exactly.

### 3. Smart Routing Evaluation (`model: "auto"`)
```powershell
python eval_router.py
```
* **Result:** **20/20 passed (100.0% accuracy)** against `data/routing_eval.jsonl`, overcoming all short-but-hard proof traps and long-but-trivial roster extraction traps.

### 4. Unit Test Suite (Critical Logic Verification)
```powershell
python -m unittest discover tests
```
* **Result:** **12/12 passed (0.003s)** covering token pricing math, sliding-window rate limit isolation, semantic cache paraphrases, near-miss rejection, salt stripping, and alias chain resolution.

---

## Ops Console Dashboard

Open your browser to:
👉 **[http://localhost:8080](http://localhost:8080)** (or `http://localhost:8080/admin/dashboard`)

The dashboard displays:
- Total requests and spend across all tenants
- Real-time cache hit rate percentage
- Virtual keys table with monthly budgets, current spend, and RPM limits
- Live stream of recent request logs (latency, status, tokens, cost, cache results, fallback events)

---

## API & Header Contract

### `POST /v1/chat/completions`
OpenAI-compatible payload.

#### Response Headers:
* `x-prism-provider`: Upstream provider and model that served the request (e.g. `alpha/alpha-small`).
* `x-prism-cache`: `hit` or `miss`.
* `x-prism-fallback`: `true` if served by a fallback provider after primary failure; otherwise `false`.
* `x-prism-cost-usd`: Precise request cost in USD calculated from `model_pricing.json` (omitted on streaming response headers, metered in logs).

#### Standardized Rejections:
* `401 Unauthorized`: Invalid/missing virtual key (`authentication_error`)
* `403 Forbidden`: Model not in tenant's allowlist (`model_not_allowed`)
* `429 Too Many Requests`: RPM exceeded (`rate_limit_exceeded`)
* `429 / 402`: Monthly budget exhausted (`budget_exceeded`)
* `404 Not Found`: Unknown model/alias (`model_not_found`)
* `502 Bad Gateway`: Upstream provider failure (`upstream_error`)
