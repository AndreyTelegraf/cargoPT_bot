# CargoPT Bot — Notification Matrix v1

## Purpose

This document defines MVP notifications for customers, carriers and admins.

Notifications must support:

- request lifecycle
- offer lifecycle
- assignment lifecycle
- reopen flow
- subscription operations
- admin attention cases

## Principles

Notifications must be:

- short
- action-oriented
- state-aware
- safe to repeat when idempotent
- logged when they correspond to business events

Do not put critical business state only inside notification text.

Database state is source of truth.

## Customer notifications

### Request created

Trigger:

- customer confirms request

Condition:

- transport_request.status = new

Message purpose:

- confirm that the request was received
- explain that carriers are being searched

Action:

- allow customer to cancel request

### Request offered to carriers

Trigger:

- matching engine creates offers

Condition:

- transport_request.status = offered

Message purpose:

- tell customer that the request is being shown to carriers

Action:

- no action required
- cancel request optional

### Carrier accepted

Trigger:

- request_assignment created

Condition:

- transport_request.status = accepted

Message purpose:

- tell customer that a carrier accepted
- provide carrier contact if policy allows immediate contact transfer

Action:

- contact carrier
- wait for carrier contact
- cancel if no longer needed

### Contacts transferred

Trigger:

- system sends contact details to both sides

Condition:

- transport_request.status = in_contact

Message purpose:

- tell customer to discuss price/time/details directly

Action:

- confirm success later
- report no agreement later

### Request completed

Trigger:

- customer/carrier/admin marks success

Condition:

- transport_request.status = completed

Message purpose:

- final confirmation

Action:

- none in MVP

### Request reopened

Trigger:

- assignment failed or no agreement

Condition:

- transport_request.status = reopened or offered after reopen

Message purpose:

- explain that previous carrier did not work out
- tell customer that search continues

Action:

- wait
- cancel request if no longer needed

### Request expired

Trigger:

- all offers expired or schedule window passed

Condition:

- transport_request.status = expired

Message purpose:

- explain that no carrier was found in time

Action:

- request admin help
- reopen if allowed
- create new request if needed

### Request cancelled

Trigger:

- customer cancels request

Condition:

- transport_request.status = cancelled_by_customer

Message purpose:

- confirm cancellation

Action:

- none

## Carrier notifications

### New offer received

Trigger:

- request_offer.status = offered

Message purpose:

- show request summary
- show pickup/dropoff area
- show urgency/date
- show cargo/services
- show heavy items
- show photos if available

Actions:

- accept
- skip

### Offer already taken

Trigger:

- carrier accepts after another carrier already won

Condition:

- request already has active assignment

Message purpose:

- explain that the request is no longer available

Action:

- none

### Offer expired

Trigger:

- scheduler expires offer

Condition:

- request_offer.status = expired

Message purpose:

- tell carrier that the offer is no longer active

Action:

- none

### Carrier won assignment

Trigger:

- carrier is first to accept

Condition:

- request_assignment.status = active

Message purpose:

- confirm that carrier got the request
- provide customer contact
- explain next step

Actions:

- contact customer
- mark agreed
- mark no agreement
- mark cannot perform

### Carrier skipped offer

Trigger:

- carrier presses skip

Condition:

- request_offer.status = skipped

Message purpose:

- confirm skip

Action:

- none

### Carrier failed assignment

Trigger:

- carrier reports cannot perform after accepting

Condition:

- request_assignment.status = failed

Message purpose:

- confirm failure was recorded

Action:

- none

### Subscription expired

Trigger:

- subscription_expiry_job

Condition:

- carrier_subscription.status = expired

Message purpose:

- tell carrier they will no longer receive requests

Action:

- contact admin / pay renewal

## Admin notifications

### No carriers matched

Trigger:

- matching engine returns zero carriers

Message purpose:

- alert admin that request needs attention

Action:

- inspect request
- edit data
- manually assign
- close
- contact customer

### All offers expired

Trigger:

- scheduler expires all offers for current round

Message purpose:

- alert admin if policy requires manual review

Action:

- reopen
- close
- contact carriers manually

### Request reopened

Trigger:

- request enters reopened status

Message purpose:

- keep admin aware of failed flow

Action:

- monitor if repeated

### Reopen threshold exceeded

Trigger:

- offer_round exceeds configured threshold

Message purpose:

- alert admin that request is problematic

Action:

- manual intervention

### Carrier subscription expired

Trigger:

- subscription expiry

Message purpose:

- admin renewal follow-up

Action:

- contact carrier
- extend subscription
- deactivate carrier

### Carrier failed after accepting

Trigger:

- request_assignment.status = failed

Message purpose:

- identify unreliable carrier or operational issue

Action:

- review carrier
- reopen request
- block/deactivate if repeated

## Notification logging

Recommended future table:

notification_log

Fields:

- id
- recipient_type
- recipient_id
- channel
- template_key
- related_request_id
- related_carrier_id
- status
- error_text
- sent_at
- created_at

MVP may skip this table if Telegram send failures are logged elsewhere.

## Template naming

Suggested template keys:

- customer_request_created
- customer_request_offered
- customer_carrier_accepted
- customer_contacts_sent
- customer_request_completed
- customer_request_reopened
- customer_request_expired
- customer_request_cancelled
- carrier_offer_received
- carrier_offer_taken
- carrier_offer_expired
- carrier_assignment_won
- carrier_offer_skipped
- carrier_assignment_failed
- carrier_subscription_expired
- admin_no_carriers_matched
- admin_all_offers_expired
- admin_request_reopened
- admin_reopen_threshold_exceeded
- admin_subscription_expired
- admin_carrier_failed_assignment

## Safety rules

Notifications must not:

- expose customer phone to carriers before assignment
- expose carrier phone to customer before assignment
- send offers to expired subscribers
- send reopened request to excluded carrier
- claim booking is confirmed if only in_contact exists

