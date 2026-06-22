# CargoPT Bot — Request FSM v1

## Purpose

This document defines the lifecycle of a customer transport request.

The request FSM drives customer UX, carrier UX, matching, reopen logic, admin actions, analytics and future calendar features.

## Main happy path

new → offered → accepted → in_contact → completed

## Full status list

- new
- offered
- accepted
- in_contact
- completed
- cancelled_by_customer
- failed_by_carrier
- reopened
- expired
- admin_closed

## Status semantics

### new

Request has been created but not yet offered to carriers.

Allowed transitions:

- new → offered
- new → cancelled_by_customer
- new → admin_closed

### offered

Request has been sent to matching carriers.

Allowed transitions:

- offered → accepted
- offered → expired
- offered → cancelled_by_customer
- offered → admin_closed

Rules:

- at least one request_offer must exist
- all open offers must have expiration time

### accepted

A carrier accepted the request first.

Allowed transitions:

- accepted → in_contact
- accepted → failed_by_carrier
- accepted → cancelled_by_customer
- accepted → admin_closed

Rules:

- one request_assignment must exist
- losing offers must be cancelled

### in_contact

Contacts were transferred. Parties are negotiating details.

Allowed transitions:

- in_contact → completed
- in_contact → failed_by_carrier
- in_contact → reopened
- in_contact → cancelled_by_customer
- in_contact → admin_closed

Rules:

- this does not mean the job is completed
- this means human negotiation is ongoing

### completed

The request ended successfully.

Rules:

- final state
- request_assignment.status must be completed

### cancelled_by_customer

Customer cancelled request.

Rules:

- final state
- open offers must be cancelled
- active assignment must be cancelled

### failed_by_carrier

Carrier failed after accepting request.

Allowed transitions:

- failed_by_carrier → reopened
- failed_by_carrier → admin_closed

Rules:

- assignment must be marked failed
- carrier should be added to request_excluded_carrier

### reopened

Request is available for another matching round.

Allowed transitions:

- reopened → offered
- reopened → cancelled_by_customer
- reopened → admin_closed
- reopened → expired

Rules:

- offer_round increments
- excluded carriers must not receive this request again

### expired

Request was not accepted or became stale.

Allowed transitions:

- expired → reopened
- expired → admin_closed

### admin_closed

Admin closed request manually.

Rules:

- final administrative state

## First-accept-wins rule

1. Carrier presses Accept.
2. System opens transaction.
3. System checks request status.
4. System checks offer status.
5. System creates assignment.
6. System marks winning offer as accepted.
7. System cancels other open offers.
8. System changes request status to accepted.
9. System writes event log.
10. System notifies all parties.

Late accept attempts receive "request already taken".

## Reopen flow

Trigger reasons:

- carrier_declined
- no_agreement
- no_response
- admin_reopen

Steps:

1. Mark active assignment as failed or cancelled.
2. Create request_excluded_carrier row.
3. Set request status to reopened.
4. Increment offer_round.
5. Run matching engine.
6. Create new request_offer rows.
7. Set status to offered.
8. Notify customer.

## Event log requirements

Every state transition must write one row to request_event_log.

Minimum event types:

- request_created
- request_confirmed
- request_offered
- offer_accepted
- offer_cancelled
- assignment_created
- contacts_sent
- contact_result_recorded
- request_completed
- request_cancelled_by_customer
- request_failed_by_carrier
- request_reopened
- request_expired
- request_admin_closed
