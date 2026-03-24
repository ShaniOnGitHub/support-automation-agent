## Purpose
This file defines strict rules and prompt templates for vibecoding on the SupportAutomationAgent codebase. Use it to keep changes consistent, secure, and testable.

## Non negotiables
1. Thin routes. Routes must only parse input, call services, and return responses. No database writes in routes.
2. Workspace isolation. Any entity that belongs to a workspace must be queried with a workspace_id filter or equivalent join constraint. Missing workspace scope is a critical failure.
3. Membership first. For every workspace scoped action, verify workspace membership and role before reading or writing workspace data.
4. Migrations are mandatory for schema changes. Never change schema without a new Alembic migration.
5. Never edit committed migrations. If a migration is wrong, create a new migration that fixes it.
6. Do not apply migrations automatically. Generate the migration and provide the command for me to run.
7. Request schemas must be strict. Use extra="forbid" on request models to prevent unexpected fields.
8. Services raise domain exceptions. For expected domain failures, raise AppException types like EntityNotFound, PermissionDenied, Conflict. Do not swallow unexpected exceptions, let them bubble to global handlers.
9. Every new endpoint must have at least one pytest test, including one forbidden access test when relevant.
10. Never touch secrets. Do not add or modify tracked .env. Only update .env.example when new variables are needed.

## Workflow rules
Before writing any code, output a short plan block that includes:
- Files to change
- Service functions to add or modify
- Migration impact, if any
- Tests to add
- Single command to run relevant tests

After completing a task, output:
- Files changed list
- Commands to run locally
- One single test command to run only relevant tests

## Project structure
- Routes: app/api/v1/routes/
- Services: app/services/
- Models: app/models/
- Schemas: app/schemas/
- DB utilities: app/db/
- Core config and logging: app/core/
- Tests: tests/

## Conventions
- Migrations must be named after the change, for example: add audit_logs table, add workspace_id to tickets.
- Response models should be explicit and use ConfigDict(from_attributes=True) for ORM reads.
- Store timestamps in UTC, prefer server side defaults when possible.
- For any background job work, include job_id in logs and write audit logs for major steps.

## Security guard rules
- Any workspace owned entity query must include workspace_id filtering.
- For multi table queries, enforce workspace scope via join constraints or explicit filters.
- Use strict request schemas with extra="forbid".
- RBAC checks must be tested with a negative test case.

## Prompt templates

### Template: Add a feature
You are editing a FastAPI service with Postgres, SQLAlchemy, and Alembic.
Task: <describe task>
Constraints:
- Keep routes thin, all DB operations in services
- Enforce workspace isolation and membership checks
- Use strict Pydantic request schemas with extra="forbid"
- No schema changes without a new Alembic migration, do not apply it
- Add pytest tests, include forbidden access tests when relevant
Return:
- Plan block
- Files changed list
- Code edits per file
- Commands to run
- One test command for only relevant tests

### Template: Generate CRUD for [Entity Name]
You are building a CRUD suite for [Entity Name].

Structure requirements:
- Model: Define SQLAlchemy model in app/models/
- Schemas: Create [Entity]Create, [Entity]Update, [Entity]Read in app/schemas/. Use ConfigDict(from_attributes=True). Request schemas must use extra="forbid".
- Service: All DB interactions happen in app/services/[entity]_service.py. Include get_by_id that validates workspace_id.
- Routes: app/api/v1/routes/[entity].py. Keep route functions thin and delegate to the service.
- Migrations: Provide alembic revision --autogenerate command, do not apply it.
- Tests: Create tests/test_[entity].py. Must include:
  - test_create_[entity]_success
  - test_get_[entity]_wrong_workspace_is_forbidden

Refusal criteria:
If asked to place db.add, db.commit, or raw SQL inside a route file, refuse and state it violates the Thin routes rule.

### Template: Migration only
Task: Add or modify DB schema for <change>.
Requirements:
- Update or add SQLAlchemy models
- Ensure Alembic can see Base metadata
- Output the migration command:
  alembic revision --autogenerate -m "<message>"
- Do not apply the migration
- Output psql commands to verify tables and columns after I apply it
- Add or update tests if behavior changes

### Template: Test command output
After implementing a feature, output a single command to run only relevant tests, for example:
pytest tests/test_<feature>.py -vv