# Contribution Guide — tablio-api

This document defines the mandatory conventions for contributing to the Tablio backend. Read completely before writing the first line of code.

---

## Branches

| Type | Pattern | Example |
|---|---|---|
| New feature | `feature/<name>` | `feature/auth-jwt` |
| Bug fix | `fix/<name>` | `fix/order-total-calc` |
| Maintenance | `chore/<name>` | `chore/update-deps` |
| CI/CD | `ci/<name>` | `ci/add-mypy-step` |

**Mandatory flow:** `feature/*` → `develop` → `main`

- No direct push to `main` or `develop`.
- Every change enters via a Pull Request.
- The PR to `main` requires the status checks to pass: **quality**, **test**, **commit-lint**.
- The PR to `develop` requires the same checks (without forced linear history).

---

## Commit Messages — Conventional Commits

Format: `<type>: <description in present imperative>`

| Type | When to use it |
|---|---|
| `feat` | New visible feature |
| `fix` | Bug fix |
| `refactor` | Change with no functional impact |
| `test` | Add or fix tests |
| `docs` | Documentation |
| `chore` | Dependencies, config, maintenance |
| `ci` | Changes in GitHub Actions |
| `perf` | Performance improvement |

**Valid examples:**

```
feat: add jwt authentication with refresh tokens
fix: recalculate total_amount server-side on order creation
test: add integration tests for public menu endpoint
chore: update uv lockfile after adding slowapi
ci: add mypy check to quality job
```

Breaking changes: use `feat!:` or include `BREAKING CHANGE:` in the footer.

---

## Python Code Conventions

- **Package manager:** `uv` — never use `pip` directly.
- **Linter and formatter:** Ruff (`uv run ruff check .` and `uv run ruff format .`).
- **Types:** MyPy in `strict` mode. Type hints are mandatory in all functions. `Any` is not accepted without a justifying comment.
- **Naming:** `snake_case` for variables/functions/files, `PascalCase` for classes and exceptions, `UPPER_SNAKE_CASE` for constants.
- **Async:** All database access is asynchronous. Use `async def` + `await` in repositories and services.
- **Line length:** 88 characters (Ruff).
- **Imports:** Ordered by Ruff (stdlib → third-party → local).

---

## Layered Architecture — Fundamental Rule

```
Routes → Services → Repositories → SQLAlchemy Models → PostgreSQL
```

- **Routes:** Only validate input (Pydantic) and delegate to the service. No business logic.
- **Services:** All business logic. Orchestrate repositories. Validate ownership.
- **Repositories:** Single point of access to the DB. No business logic. No knowledge of HTTP.

**Never skip this separation.**

---

## Critical Business Rules

1. **Mandatory soft delete.** Never physically `DELETE` products, categories, or restaurants. Use `is_active = false` or `is_available = false`.
2. **Total calculated on the server.** The `total_amount` of an order is calculated in the backend by checking the prices in the DB. The client only sends `product_id` and `quantity`.
3. **Snapshot in order_items.** When creating an order, save `product_name` and `unit_price` as an immutable copy. Future changes to the product do not affect historical orders.
4. **Ownership validation.** Every operation on private resources verifies that the resource's `restaurant_id` belongs to the authenticated user. This validation happens in the service layer.
5. **Timestamps in UTC.** All date/time fields are `TIMESTAMPTZ`. JSON responses use ISO 8601 with UTC offset: `2026-04-27T15:30:00Z`.
6. **Schema changes only via Alembic.** Never modify the DB manually. Never use `Base.metadata.create_all()` in production.

---

## Testing

- Tests are written in the **same phase** as the production code. No testing debt is accumulated.
- **Minimum coverage:** 70% at all times.
- **Types of tests:**
  - `tests/unit/` — Isolated services with mocked repositories. No DB.
  - `tests/integration/` — HTTP endpoints against real PostgreSQL (Docker). DB cleanup between tests.
  - `tests/e2e/` — Full end-to-end flow.
- Run before each PR: `uv run pytest --cov=app --cov-report=term-missing`.

---

## Checklist Before Opening a PR

- [ ] `uv run ruff check .` passes without errors
- [ ] `uv run ruff format .` produces no changes
- [ ] `uv run mypy app/` passes without errors
- [ ] `uv run pytest` passes with coverage ≥ 70%
- [ ] The commit message follows Conventional Commits
- [ ] The branch comes from `develop`, not `main`
- [ ] There are no credentials or real `.env` committed
