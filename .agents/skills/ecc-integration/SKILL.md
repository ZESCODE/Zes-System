---
category: Core

name: ecc-integration
description: Unified ECC development workflow integrating Core Workflow, Testing & QA, Frontend, and Backend skills. One skill to rule the dev cycle — plan, code, test, review, deploy.
metadata:
  origin: ECC
  version: 1.0.0
  categories:
    - core-workflow
    - testing-qa
    - frontend
    - backend
---


# ECC Unified Integration

This skill orchestrates the **four essential development pillars** — Core Workflow, Testing & QA, Frontend, and Backend — into a single, opinionated pipeline. Use it as your primary workflow driver; fall through to individual skills when you need deep-domain detail.

---

## 1. Core Workflow (Plan → Code → Review → Ship)

| Phase | Skill | Trigger |
|-------|-------|---------|
| **Plan** | `search-first` | Before writing any code, search for existing solutions |
| **Design** | `tdd-workflow` | Define tests before implementation |
| **Implement** | `coding-standards` + `error-handling` | During implementation |
| **Review** | `verification-loop` | After implementation |
| **Ship** | `strategic-compact` | Before committing to manage context |

### Quick Reference

```bash
# 1. Search before building — use search-first skill
# 2. Implement with discipline:
#    - Immutability: always create new objects, never mutate
#    - Typed returns: every function has a defined return type
#    - No bare excepts: catch specific exceptions
#    - Validate early, fail fast
# 3. Verify — use verification-loop skill
# 4. Compact context before next task — use strategic-compact skill
```

### Git Workflow (via `git-workflow`)

```
main ── feature/xxx ── PR ── merge
  └── fix/xxx (hotfix branch)
```

- Branch naming: `feature/<issue>-<slug>`, `fix/<issue>-<slug>`
- Commit style: `type(scope): message` (e.g. `feat(api): add user CRUD`)
- Always rebase before PR, never merge-commit from feature branches

---

## 2. Testing & QA (Test-First Quality)

| Layer | Skill | Coverage Target |
|-------|-------|-----------------|
| **Unit** | `python-testing` or `tdd-workflow` | 80%+ unit tests |
| **Integration** | `tdd-workflow` | 70%+ integration tests |
| **E2E / UI** | `e2e-testing`, `browser-qa` | Critical paths |
| **Performance** | `benchmark` | Baseline + regression gates |

### Quick Commands

```bash
pytest -v                                              # all tests
pytest -v -k "test_feature"                            # filtered
pytest --cov=src --cov-report=term-missing             # coverage
npx playwright test                                    # E2E
npx playwright test --ui                                # interactive
pytest tests/benchmark/ --benchmark-only               # benchmarks
```

### Quality Gates

Before marking complete:
1. ✅ All new code has unit tests (80%+ line coverage for changed files)
2. ✅ Integration tests pass for changed APIs/data layers
3. ✅ No regressions in existing benchmark suite
4. ✅ E2E critical paths verified (if UI changed)

---

## 3. Frontend (React + Vite + Modern Stack)

| Concern | Skill | Notes |
|---------|-------|-------|
| **Framework** | `react-patterns` | Hooks, server/client components, Suspense, error boundaries |
| **Performance** | `react-performance` | Waterfalls, bundle, re-renders, memoization |
| **Build** | `vite-patterns` | Config, HMR, proxy, env, SSR |
| **Accessibility** | `frontend-a11y` | Semantic HTML, ARIA, keyboard nav, screen readers |
| **Design** | `designmd` | DESIGN.md theme application |

### React Checklist

- [ ] Functional components + hooks (no classes)
- [ ] Custom hooks extract reusable state logic
- [ ] Memoize expensive computations (useMemo, useCallback)
- [ ] React.lazy + Suspense for code-splitting
- [ ] Error boundaries at route/section level
- [ ] No prop drilling — use composition or context
- [ ] Form actions for data mutations or react-hook-form

### Vite Quick Start

```bash
npm create vite@latest my-app -- --template react
npm install
npm run dev           # → http://localhost:5173
npm run build         # → dist/
npm run preview       # preview production build
```

### Accessibility Baseline

- Every interactive element is keyboard-focusable
- Images have meaningful `alt` text
- Color contrast ratio ≥ 4.5:1 (normal) / 3:1 (large)
- Form inputs have associated `<label>`
- Live regions for dynamic content updates
- Visible focus indicator on all interactive elements

---

## 4. Backend (API + Data + Services)

| Concern | Skill | Notes |
|---------|-------|-------|
| **API Design** | `api-design` | RESTful naming, status codes, pagination, errors |
| **Framework** | `fastapi-patterns` (Python) or `backend-patterns` (Node) | Project structure, DI, async |
| **Database** | `postgres-patterns`, `database-migrations` | Schema, indexing, migrations |
| **Cache** | `redis-patterns` | Caching strategies, rate limiting |
| **DevOps** | `docker-patterns` | Dockerfile, compose, networking |

### REST API Standards

```
GET    /resources          → 200 + list (paginated)
POST   /resources          → 201 + created resource
GET    /resources/:id      → 200 / 404
PUT    /resources/:id      → 200 / 404
DELETE /resources/:id      → 204 / 404

Error response:
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "User-friendly description",
    "details": [...]      // optional field-level errors
  }
}
```

### Database Migration Flow

```bash
migrate create -ext sql -dir migrations -seq add_users_table
migrate -database "$DATABASE_URL" -path migrations up
migrate -database "$DATABASE_URL" -path migrations down 1
```

### Security Must-Haves

- [ ] Parameterized queries (no string interpolation in SQL)
- [ ] Input validation on all endpoints (Pydantic / Zod schemas)
- [ ] Rate limiting on auth and mutation endpoints
- [ ] CORS whitelist — never `Access-Control-Allow-Origin: *`
- [ ] Secrets via environment variables, never hardcoded
- [ ] Error responses never leak stack traces or internal paths

---

## Decision Tree — Which Skill to Use When

```
Starting a new feature?
  ├─ Simple UI component?              → frontend-patterns + designmd
  ├─ New API endpoint?                  → api-design + fastapi-patterns
  ├─ Complex multi-step flow?           → tdd-workflow + search-first
  └─ Bug fix?                           → systematic-debugging + verification-loop

Need to verify quality?
  ├─ Unit/integration tests needed?     → python-testing / tdd-workflow
  ├─ E2E / visual tests needed?         → e2e-testing / browser-qa
  ├─ Performance regression check?      → benchmark
  └─ Security audit?                     → security-review + security-scan

Choosing a stack?
  ├─ Frontend: React + Vite + shadcn/ui → react-patterns + vite-patterns
  ├─ Backend: Python (FastAPI)          → fastapi-patterns + postgres-patterns
  ├─ Backend: Node.js (Express/Next)    → backend-patterns + database-migrations
  └─ Mobile-friendly?                    → frontend-a11y + responsive patterns
```

## Environment & Configuration

```bash
# Common environment variables
DATABASE_URL=postgres://user:pass@localhost:5432/db
REDIS_URL=redis://localhost:6379
API_PORT=8000
NODE_ENV=development|production|test
LOG_LEVEL=debug|info|warn|error
```

## Quick Command Reference

```bash
npm run dev              # Vite dev server
uvicorn app.main:app --reload   # FastAPI dev
pytest -v --cov          # Run tests + coverage
migrate up               # Apply migrations
migrate down 1           # Rollback one migration
docker compose up -d     # Start all services
docker compose logs -f   # Follow logs
docker compose down      # Stop everything
npx playwright test      # E2E tests
pytest --benchmark-only  # Benchmarks
```
