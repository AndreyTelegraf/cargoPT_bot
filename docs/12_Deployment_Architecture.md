# CargoPT Bot — Historical Deployment Architecture v1

> This file preserves an early design proposal. It is not a production runbook.
> Current runtime, database, backup and release boundaries are defined by
> `00_Current_Production_Contract.md`.

## Purpose

This document defines MVP deployment architecture for CargoPT Bot.

The deployment must support:

- Telegram bot runtime
- database persistence
- background scheduler
- logs
- backups
- safe migration path
- future scaling

## MVP deployment target

Recommended MVP target:

- single VPS
- systemd service
- Python virtualenv
- SQLite in current production
- git-based deploy
- file/stdout logs
- scheduled online SQLite backups plus pre-change backups

This is enough for MVP because:

- traffic is expected to be low at launch
- business logic is more important than infrastructure
- operational simplicity matters more than scaling

## Runtime components

MVP components:

- bot process
- database
- separate systemd jobs for scheduled work
- docs in repository

Future components:

- worker process
- Redis
- PostgreSQL
- web admin panel
- monitoring stack

## Recommended MVP stack

- Python 3.12
- aiogram 3
- SQLAlchemy
- Alembic
- SQLite for current production
- PostgreSQL only as an optional future migration
- systemd
- GitHub repository
- dotenv-based config

## Repository layout preview

Future code layout:

- app/
- app/bot/
- app/handlers/
- app/services/
- app/models/
- app/db/
- app/scheduler/
- app/admin/
- app/config/
- migrations/
- tests/
- docs/

## Environment configuration

Required environment variables:

- BOT_TOKEN
- ADMIN_IDS
- DATABASE_URL
- ENVIRONMENT
- LOG_LEVEL

Future variables:

- REDIS_URL
- SENTRY_DSN
- GOOGLE_MAPS_API_KEY
- BACKUP_PATH
- WEBHOOK_URL

## Polling vs webhook

MVP should use Telegram polling.

Reason:

- simpler deployment
- no HTTPS/webhook setup
- easier debugging
- enough for single-bot MVP

Webhook can be added later if needed.

## Database choice

### Current production

SQLite is the current production database.

Pros:

- fast setup
- no external service
- easy local testing

Cons:

- weaker concurrency
- limited operational tooling
- less suitable for production growth

### Optional future migration

PostgreSQL may be evaluated separately; it is not a public-launch prerequisite.

Pros:

- better concurrency
- stronger constraints
- easier backups
- better observability
- future web/admin scaling

## Scheduler deployment

MVP:

- scheduler may run inside bot process

Rule:

- only one bot process must run if scheduler is embedded

Future:

- scheduler moves to separate worker process
- bot handles Telegram updates only
- worker handles background jobs

## systemd services

Production uses separate API and bot services plus systemd timers for email and
Telegram dispatch, backup, draft archive, regression and business-health work.
The exact unit list is maintained in `00_Current_Production_Contract.md`.

## Logging

MVP logs:

- stdout through systemd journal
- structured enough messages
- error tracebacks preserved

Log levels:

- DEBUG for local
- INFO for staging/prod
- ERROR for exceptions

Must log:

- bot startup
- DB connection
- scheduler job runs
- request status transitions
- matching results
- failed Telegram sends
- unexpected exceptions

## Backups

SQLite MVP:

- daily DB copy
- backup before migrations
- backup before risky patches

PostgreSQL MVP:

- pg_dump daily
- backup before migrations
- backup retention policy

Minimum retention:

- 7 daily backups
- 4 weekly backups after public launch

## Deployment flow

Recommended deployment flow:

1. git pull
2. create backup
3. install dependencies
4. run migrations
5. run tests
6. restart service
7. check service status
8. inspect recent logs
9. run manual smoke

## Rollback

Rollback must be possible.

Minimum rollback assets:

- previous git commit
- database backup before migration
- service restart command

Rollback flow:

1. stop service
2. checkout previous commit
3. restore DB backup if schema changed
4. install previous dependencies if needed
5. restart service
6. run smoke

## Staging

Recommended environments:

- local
- staging
- production

Staging should use:

- separate bot token
- separate database
- separate systemd service
- same code branch or staging branch

Do not test destructive flows on production data first.

## Security

Server access:

- SSH key only
- no password login
- limited sudo users
- secrets stored in .env outside git

Repository:

- never commit .env
- never commit bot token
- never commit production DB
- keep docs safe for public repo or move private data elsewhere

## Monitoring MVP

Minimum checks:

- systemd service active
- bot responds to /start
- DB accessible
- scheduler running
- recent logs clean

Future:

- Sentry
- uptime checks
- metrics dashboard
- alerting

## Scaling path

Phase 1:

- single process
- polling
- SQLite/PostgreSQL
- Telegram admin

Phase 2:

- PostgreSQL optional after a separately tested migration plan
- worker process
- Redis optional
- better logging
- notification log

Phase 3:

- web admin panel
- separate API layer
- calendar UI
- external monitoring
- horizontal bot/web scaling

## Deployment principle

Do not overbuild infrastructure before domain logic is stable.

CargoPT MVP should optimize for:

- operational clarity
- simple rollback
- clear logs
- reliable database state
- low maintenance cost
