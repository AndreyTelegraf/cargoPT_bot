# CargoPT Bot — Project Structure v1

## Purpose

This document defines the implementation structure for CargoPT Bot.

The goal is to keep the MVP simple, but not chaotic.

The codebase must support:

- Telegram customer flow
- Telegram carrier flow
- Telegram admin flow
- database models
- domain services
- matching engine
- scheduler
- schedule-layer
- tests
- future web admin panel

## Architectural principle

CargoPT should be built as a modular monolith.

Do not split into microservices.

Do not put business logic directly inside Telegram handlers.

Handlers should:

- parse user input
- call services
- render response
- route next state

Services should contain business logic.

Repositories should contain DB access.

Flow:

handler -> service -> repository -> database

## Recommended repository layout

cargoPT_bot/
  app/
    main.py
    config.py
    bot/
    handlers/
    keyboards/
    states/
    services/
    repositories/
    models/
    db/
    scheduler/
    notifications/
    admin/
    utils/
  migrations/
  tests/
  scripts/
  docs/
  .env.example
  requirements.txt
  alembic.ini
  README.md

## app/main.py

Application entrypoint.

Responsibilities:

- load config
- initialize bot
- initialize dispatcher
- initialize database
- register routers
- start scheduler if enabled
- start polling

Must not contain business logic.

## app/config.py

Configuration layer.

Reads environment variables:

- BOT_TOKEN
- ADMIN_IDS
- DATABASE_URL
- ENVIRONMENT
- LOG_LEVEL

Future variables:

- REDIS_URL
- SENTRY_DSN
- GOOGLE_MAPS_API_KEY

Rules:

- no hardcoded secrets
- no production token in repository
- .env.example contains only placeholders

## app/bot/

Telegram bot setup.

Suggested files:

- app/bot/factory.py
- app/bot/routers.py

Responsibilities:

- create Bot instance
- create Dispatcher
- register routers
- configure middleware

## app/handlers/

Telegram handlers.

Suggested layout:

- app/handlers/customer/
- app/handlers/carrier/
- app/handlers/admin/
- app/handlers/common/

Handler rules:

- no complex SQL
- no matching logic
- no direct lifecycle mutations without service call
- no long business workflows

Handlers should call services.

Canonical flow:

handler -> service -> repository -> database

## app/states/

FSM state declarations.

Suggested files:

- customer_request.py
- carrier_onboarding.py
- admin.py

Rules:

- FSM describes UI process only
- FSM is not source of truth for business lifecycle
- database statuses remain source of truth

## app/keyboards/

Telegram keyboards.

Suggested files:

- customer.py
- carrier.py
- admin.py
- common.py

Responsibilities:

- inline keyboards
- reply keyboards
- callback helpers

No business logic.

## app/services/

Business logic layer.

Suggested services:

- request_service.py
- carrier_service.py
- assignment_service.py
- matching_service.py
- onboarding_service.py
- subscription_service.py
- notification_service.py
- schedule_service.py
- admin_service.py

Rules:

- lifecycle logic belongs here
- matching belongs here
- scheduler actions call services
- handlers never bypass services

## app/repositories/

Database access layer.

Suggested repositories:

- request_repository.py
- carrier_repository.py
- assignment_repository.py
- subscription_repository.py
- event_log_repository.py

Responsibilities:

- SQLAlchemy queries
- persistence
- transaction helpers

## app/models/

SQLAlchemy ORM models.

Suggested files:

- carrier.py
- request.py
- offer.py
- assignment.py
- schedule.py
- subscription.py
- event_log.py

Rules:

- models reflect DB schema
- no business workflows in models
- enum values should be centralized later

## app/db/

Database infrastructure.

Suggested files:

- base.py
- session.py
- engine.py
- migrations helpers if needed

Responsibilities:

- engine creation
- session factory
- transaction scope helpers

## app/scheduler/

Background job layer.

Suggested files:

- runner.py
- jobs.py
- offer_expiry.py
- subscription_expiry.py
- reminders.py

Rules:

- scheduler calls services
- scheduler does not contain business decisions directly
- every job must be idempotent

## app/notifications/

Notification rendering and sending.

Suggested files:

- templates.py
- sender.py
- customer.py
- carrier.py
- admin.py

Responsibilities:

- build messages
- send Telegram messages
- keep notification text out of business services where possible

## app/admin/

Admin-specific orchestration.

Suggested files:

- dashboard.py
- carrier_admin.py
- request_admin.py
- subscription_admin.py

Rule:

- admin layer may orchestrate services
- admin layer must not bypass permission checks

## app/utils/

Small shared helpers only.

Allowed:

- datetime helpers
- formatting helpers
- validation helpers

Avoid:

- business logic dumping ground
- hidden dependencies
- large unrelated helpers

## tests/

Test layout:

- tests/unit/
- tests/integration/
- tests/smoke/

Priority tests:

- request FSM transitions
- carrier onboarding
- matching filters
- first-accept-wins
- reopen flow
- scheduler idempotency
- permission checks

## scripts/

Operational scripts.

Examples:

- create_admin.py
- create_invite.py
- seed_service_areas.py
- backup_db.py
- smoke_local.py

Rules:

- scripts must be safe to run intentionally
- destructive scripts require explicit confirmation flag

## Implementation order

Recommended order:

1. project skeleton
2. config layer
3. database base/session
4. SQLAlchemy models
5. Alembic migration
6. repositories
7. request service
8. carrier service
9. matching service
10. Telegram customer FSM
11. Telegram carrier FSM
12. scheduler jobs
13. admin layer
14. smoke tests
15. staging deploy

## Non-goals

Do not add before MVP:

- microservices
- web dashboard
- Redis dependency
- Celery dependency
- payment provider
- map tracking
- rating system

## Core rule

Keep Telegram as an adapter.

Keep business logic in services.

Keep DB access in repositories.

Keep lifecycle state in the database.

