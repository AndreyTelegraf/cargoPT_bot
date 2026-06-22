# CargoPT Bot — Scheduler v1

## Purpose

Scheduler executes background jobs.

It is operational infrastructure, not business schedule-layer.

Scheduler is responsible for:

- offer expiration
- reopen processing
- subscription expiration
- reminders
- cleanup of temporary states
- future operational jobs

## Boundary

Scheduler answers:

- what technical job should run now?

Schedule-layer answers:

- what real-world time commitment exists?

These layers must remain separate.

## MVP jobs

### offer_expiry_job

Runs periodically.

Finds request_offer rows where:

- status = offered
- expires_at < now

Actions:

- set request_offer.status = expired
- write request_event_log

If all offers for request/round are expired and no assignment exists:

- set transport_request.status = expired
or
- trigger reopen/admin attention depending on policy

### reopen_processing_job

Handles requests marked reopened but not yet re-offered.

Actions:

- run matching engine
- create new offers
- update request status to offered

If no carriers are found:

- notify admin
- keep request as reopened or mark as expired depending on policy

### subscription_expiry_job

Finds carrier_subscription rows where:

- status = active
- paid_until < now

Actions:

- set subscription.status = expired
- prevent matching
- optionally notify carrier
- notify admin

### reminder_job

Possible reminders:

- carrier has active assignment but no contact result
- customer has request in contact stage
- admin has stale reopened request
- future booking reminder when calendar is implemented

### invite_expiry_job

Finds admin_invite_token rows where:

- status = active
- expires_at < now

Actions:

- set status = expired

### cleanup_job

Non-destructive cleanup only.

May clean:

- stale FSM sessions
- expired temporary states
- old cache values

Must not delete business data.

## Recommended implementation

MVP options:

- aiogram background task
- APScheduler
- cron invoking Python command
- systemd timer

Recommended MVP:

- simple async scheduler inside bot process if single instance
- move to separate worker before scaling

## Idempotency rules

All jobs must be idempotent.

A job may run twice without corrupting state.

Rules:

- always filter by current status
- always check state before update
- never assume previous job completed
- write event log only for real transition
- avoid long transactions

## Failure behavior

If a job fails:

- log exception
- do not partially update unrelated requests
- next run should retry safely

## Job run logging

Future table:

scheduler_run_log

Fields:

- id
- job_name
- started_at
- finished_at
- processed_count
- error_count
- status
- error_text

MVP may log to stdout/file.

## Frequencies

Suggested MVP frequencies:

- offer_expiry_job: every 1 minute
- reopen_processing_job: every 1 minute
- subscription_expiry_job: every 1 hour
- invite_expiry_job: every 10 minutes
- reminder_job: every 15 minutes
- cleanup_job: daily

## Scaling rule

If bot runs as a single process, in-process scheduler is acceptable.

If bot runs multiple replicas, scheduler must move to:

- single worker process
or
- distributed lock
or
- external job runner

Do not run the same non-idempotent job from multiple bot replicas.
