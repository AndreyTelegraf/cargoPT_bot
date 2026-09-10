# CargoPT — Current Production Contract

Status: canonical Source of Truth for the running CargoPT service.

Verified: 2026-09-10 against branch `cargoPT_bot`, production services, the
application code and Alembic head `20260910_1930_offer_terms`.

If another document conflicts with this contract, `04_Request_FSM.md` or
`12_Deployment_Architecture.md`, the conflicting text is historical design
material and must not be used to change production behaviour.

## Product boundary

CargoPT is a request and matching service. A customer submits one transport
request. CargoPT may share it with suitable independent carriers. Carriers may
return offers, and the customer chooses one offer. CargoPT does not guarantee
that a carrier, offer, price, availability or completed transport will exist.

The public website supports Portuguese, English and Russian. Customer-facing
changes must preserve PT/EN/RU meaning and must not make stronger promises than
the product can fulfil.

## Intake channels

The website and Telegram bot are two interfaces to the same domain model.

- Website submissions use `source='web_form'`.
- The website creates and confirms a request through the API and exposes a
  token-protected tracking workspace where the customer can review, update,
  cancel and select an offer when the current status permits it.
- The Telegram bot handles customer and carrier conversations, moderation,
  offer responses and assignment confirmations.
- A normalized email address or Portuguese phone/WhatsApp number identifies a
  returning contact regardless of common spacing and prefix variants.

## Lead-time rule

Automatic carrier distribution is allowed only when the requested transport
time is at least 72 hours away.

If less than 72 hours remain, the request is stored as
`manual_review_required` and is not automatically sent to carriers. CargoPT may
review and handle it manually using the supplied contact details. Manual review
is not a promise of an offer or transport.

## Transaction and notification boundary

Creating a request, matching carriers, creating offers and enqueuing Telegram
notifications form one database transaction. External Telegram delivery starts
only after that transaction commits.

Telegram and email are durable outbox queues with deduplication, attempt state,
retry scheduling and terminal failures. A transport or provider error must not
roll back an already committed request. Replaying a submission or dispatcher
run must not create duplicate business records or duplicate accepted work.

## Offer and assignment rule

Carrier acceptance is not assignment and is not a first-accept-wins race.

1. Matching creates expiring pending offers for suitable carriers.
2. A carrier may decline, or accept by submitting structured commercial terms.
3. Accepted carrier offers remain available for comparison while the request is
   `offered`.
4. The customer explicitly selects one accepted, unexpired offer.
5. The selection is claimed atomically; all unselected open offers are closed.
6. The request moves to `assigned_pending_confirmation`.
7. Required party confirmations move it to `assigned`.
8. Work starts at `in_progress` and finishes at `completed`.
9. A failed or timed-out confirmation can return the request to
   `ready_for_matching` or `manual_review_required`, according to the guarded
   recovery flow.

Prices and terms are carrier-provided. The comparable offer record includes the
base price, what is included, possible extras and the proposed service date or
time window. Expired offers cannot be accepted or selected.

## Status contract

The only current job status values are those defined in
`app/domain/job_status.py`:

- `draft`
- `draft_expired`
- `ready_for_matching`
- `matching`
- `offered`
- `unmatched`
- `no_carriers_found`
- `offers_exhausted`
- `expired_without_response`
- `manual_review_required`
- `assigned_pending_confirmation`
- `assigned`
- `in_progress`
- `cancelled`
- `completed`

State transitions must use domain services and guarded repository operations.
API, bot handlers and maintenance scripts must not invent status strings or
update lifecycle state with unguarded SQL.

## Database boundary

Production uses SQLite through SQLAlchemy and Alembic. The ORM models and the
applied Alembic migration chain are the schema authority. Historical proposed
tables in older design documents are not production tables.

Production requirements:

- the service process `DATABASE_URL` is authoritative; repository `.env` files
  must not be assumed to point to production;
- `PRAGMA foreign_keys=ON` and zero foreign-key violations;
- `PRAGMA quick_check` must return `ok`;
- schema changes only through Alembic migrations;
- migration commands must receive the explicit production `DATABASE_URL`;
- an online SQLite backup is required before schema or risky data changes;
- a backup is trusted only after checksum, SQLite integrity and restore checks.

A future PostgreSQL migration is an option, not a current production
requirement.

## Runtime boundary

Production is one VPS with a Python 3.12 virtual environment and these systemd
units:

- `cargopt_api.service`
- `cargopt_bot.service`
- `cargopt_email_dispatch.timer`
- `cargopt_telegram_dispatch.timer`
- `cargopt_backup.timer`
- `cargopt_draft_archive.timer`
- `cargopt_regression.timer`
- `cargopt_business_health.timer`

The API trusts forwarded client addresses only from loopback and the configured
Cloudflare proxy networks. The bot uses Telegram polling. Background delivery,
backup, archive, regression and business-health work runs in separate systemd
jobs rather than an in-process scheduler.

The repository static source is `app/static`. The public webroot is
`/var/www/cargopt.pt`. Static deployment requires an explicit manifest, backup,
source-to-webroot parity checks and public PT/EN/RU smoke checks.

## Release boundary

The active production branch is `cargoPT_bot`. A release is complete only when
all applicable checks succeed:

1. record branch, working-tree state, production SHA and service state;
2. capture the exact failure and target code before changing one isolated layer;
3. create and validate a pre-change backup when database risk exists;
4. apply migrations with the explicit production database URL;
5. install exact dependency pins and pass `pip check` plus the vulnerability
   audit;
6. run targeted regression tests, then the full regression suite for a release;
7. restart only affected services and wait for their normal cold start;
8. verify API health, service state, recent logs and business-health output;
9. verify static manifest parity and public pages when frontend files changed;
10. commit and push only the verified release state, then require green CI.

Untracked production backups, databases and work directories are operational
assets and must not be committed, overwritten or treated as release source.

## Known operational limitations

- Local scheduled backups exist, but off-server backup and a loss-of-server
  restore drill remain a separate disaster-recovery requirement.
- Terminal notification failures and overdue manual-review requests are visible
  operational work; they must not be silently cleared or retried without an
  approved business action.
- Carrier identity, licence, insurance, vehicle and availability claims require
  verified operational data; the software must not fabricate them.
