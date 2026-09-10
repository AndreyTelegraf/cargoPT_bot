# CargoPT — Request FSM

Status: current production Source of Truth. Read together with
`00_Current_Production_Contract.md`.

## Principle

CargoPT is a request and matching service. A carrier accepting an invitation
creates a customer-visible offer; it does not assign the job. The customer
chooses one accepted offer explicitly.

## Statuses

### `draft`

The customer has started a request but has not completed confirmation.

Allowed outcomes:

- confirmation evaluates the request for matching;
- abandoned drafts become `draft_expired`.

### `draft_expired`

Terminal state for an unconfirmed draft that exceeded the retention window.

### `ready_for_matching`

The request is confirmed, has at least 72 hours of lead time and may enter
automatic matching.

Allowed transitions:

- `ready_for_matching` -> `matching`
- `ready_for_matching` -> `cancelled`

### `matching`

Suitable carriers and vehicles are being selected and offer records are being
created.

Allowed outcomes:

- `offered` when at least one carrier offer is open or accepted;
- `no_carriers_found` when no eligible carrier exists;
- `unmatched` for a matching result that needs later handling;
- `cancelled` on a guarded customer or operator cancellation.

### `offered`

The request has carrier offers. Carriers may accept by providing terms or
decline. Multiple accepted offers may coexist for customer comparison.

Allowed transitions:

- `offered` -> `assigned_pending_confirmation` only after an atomic customer
  selection;
- `offered` -> `offers_exhausted` when all candidates are resolved without a
  selectable offer;
- `offered` -> `expired_without_response` when the response window expires;
- `offered` -> `cancelled`.

An expired offer cannot be accepted or selected. Selection must verify that the
offer belongs to the request and is accepted, atomically claim the request, and
close the unselected offers.

### `unmatched`

No automatic match was completed. The request remains available for controlled
operational handling or cancellation.

### `no_carriers_found`

Matching found no eligible carriers. No automatic Telegram distribution was
created.

### `offers_exhausted`

All offer opportunities ended without a customer-selectable result.

### `expired_without_response`

The response window ended without a usable carrier response.

### `manual_review_required`

Automatic processing is deliberately stopped and an operator must review the
request. A request with less than 72 hours before the requested transport time
enters this status and is not automatically sent to carriers.

Other guarded recovery and exception paths may also enter manual review. The
status is not evidence that an offer or transport is guaranteed.

### `assigned_pending_confirmation`

The customer selected one carrier offer and the assignment is waiting for the
required confirmations.

Allowed transitions:

- `assigned_pending_confirmation` -> `assigned` after confirmation;
- `assigned_pending_confirmation` -> `ready_for_matching` through guarded
  reopen logic;
- recovery may route to `manual_review_required`;
- `assigned_pending_confirmation` -> `cancelled` where cancellation is allowed.

### `assigned`

The selected assignment is confirmed.

Allowed transitions:

- `assigned` -> `in_progress`
- `assigned` -> `cancelled`

### `in_progress`

The transport is being performed.

Allowed transitions:

- `in_progress` -> `completed`
- `in_progress` -> `cancelled`

### `completed`

Terminal successful lifecycle state. It records the system's confirmed
completion state; it must not be inferred from a sent notification.

### `cancelled`

Terminal cancellation state. Guarded cancellation closes open offers when the
current lifecycle state allows customer cancellation.

## Submission and outbox transaction

For an automatically distributed request, the database transaction contains:

1. the confirmed request;
2. matched carrier and vehicle decisions;
3. offer rows;
4. deduplicated Telegram outbox rows.

Only after commit may the Telegram dispatcher perform external sends. A failed
send changes outbox attempt state but must not remove the committed request or
offers. Submission idempotency prevents the same logical confirmation from
creating a second request and second distribution.

## Carrier response and customer selection

1. A carrier receives an expiring invitation.
2. The carrier declines, or accepts and submits structured price and service
   terms.
3. Acceptance changes the offer state and keeps the job `offered`.
4. The customer reviews all currently selectable offers in the tracking
   workspace or supported bot flow.
5. The customer selects one offer.
6. A guarded compare-and-set claims the job as
   `assigned_pending_confirmation`.
7. Other open offers are closed.
8. Required confirmations produce `assigned`.

Concurrent or repeated selection attempts must produce one winner and a clear
already-resolved response. They must not create duplicate assignments.

## Cancellation and recovery

Customer cancellation is allowed only from the explicit states enforced by the
domain service. The operation atomically claims the current state and closes
open offers. A concurrent state change causes a conflict rather than a blind
overwrite.

Assignment recovery clears confirmation state before returning to matching.
Automatic timeout processing is idempotent and must not replace a newer human or
customer decision.

## Authority

The status enum in `app/domain/job_status.py`, domain transition services and
guarded repository operations are executable authority. Documentation changes
must follow verified behaviour; changing this document alone never changes the
runtime FSM.
