# CargoPT Bot — Permissions Model v1

## Purpose

This document defines access control for CargoPT MVP.

Permissions must protect:

- customer personal data
- carrier contact data
- request assignment flow
- admin-only operations
- subscription-controlled carrier access
- audit integrity

## MVP actor types

- customer
- carrier
- admin
- system

## Customer permissions

Customer can:

- create transport request
- upload request photos
- view own request status
- cancel own non-final request
- confirm successful agreement
- report no agreement
- provide contact phone
- provide pickup/dropoff data

Customer cannot:

- view carrier list
- choose carrier directly in MVP
- view offers sent to carriers
- access admin data
- reopen request manually after final close unless flow allows it
- see other customer requests

## Carrier permissions

Carrier can:

- receive matching offers if eligible
- accept offer
- skip offer
- view accepted assignment details
- contact customer after winning assignment
- report contact result
- report cannot perform
- view own company summary
- view own subscription status

Carrier cannot:

- view offers sent to other carriers
- accept expired offer
- accept request already assigned to another carrier
- receive offers with expired subscription
- receive same reopened request after being excluded
- view other carriers
- view admin notes
- edit paid_until
- self-activate
- self-register without invite

## Admin permissions

MVP admin can:

- create carrier
- edit carrier
- deactivate carrier
- block carrier
- create invite token
- revoke invite token
- extend subscription
- cancel subscription
- view all requests
- view all offers
- view all assignments
- reopen request manually
- close request manually
- exclude carrier from request
- view event log
- inspect operational state

## System permissions

System can:

- create request_offer rows
- expire offers
- change request status based on scheduler rules
- create assignment after carrier acceptance
- cancel losing offers
- create request_event_log entries
- expire subscriptions
- expire invite tokens
- send notifications

System must not:

- delete business records silently
- complete request without assignment
- assign expired carrier
- send customer phone to non-winning carrier
- send carrier contact before assignment policy allows it

## Role expansion

Future roles:

- super_admin
- dispatcher
- finance_admin
- support_admin
- read_only_admin

### super_admin

Can perform all admin actions.

### dispatcher

Can:

- view requests
- view carriers
- reopen requests
- close invalid requests
- contact users manually
- inspect assignments

Cannot:

- change subscription payment state unless allowed
- block carrier unless allowed

### finance_admin

Can:

- view carrier subscriptions
- extend paid_until
- mark subscription cancelled
- view payment notes

Cannot:

- view full customer details unless necessary
- alter request lifecycle

### support_admin

Can:

- view request state
- view limited contact details
- help customer/carrier understand status
- escalate to dispatcher

Cannot:

- edit subscription
- block carrier
- force assignment

### read_only_admin

Can:

- view dashboards
- view request summaries
- view carrier summaries

Cannot mutate data.

## Data visibility rules

### Customer data visible to carrier

Before carrier wins:

- pickup/dropoff general area
- cargo description
- floors/elevators
- photos if allowed
- urgency/date
- additional services

After carrier wins:

- customer phone
- precise pickup/dropoff data
- customer name if provided

### Carrier data visible to customer

Before carrier wins:

- none or generic "carrier is reviewing"

After carrier wins:

- carrier company/contact name
- carrier phone or Telegram contact
- operational instructions

### Admin data

Admin can view:

- all operational data
- internal notes
- event logs
- subscription data

Admin actions must be logged.

## Telegram identity binding

Carrier access is based on:

- carrier_company.telegram_user_id

Rules:

- invite token binds first successful Telegram account
- rebinding requires admin
- one Telegram account per carrier company in MVP

Customer identity is based on:

- customer_telegram_id

Customer phone is still collected because Telegram identity is not enough for real-world transport coordination.

## Subscription gate

Carrier can receive offers only if:

- carrier_company.status = active
- carrier_subscription.status = active
- paid_until >= now

This check belongs to matching engine and must not rely only on UI hiding.

## State-based permissions

Carrier can accept offer only if:

- request_offer.status = offered
- transport_request.status is offered or reopened
- carrier subscription is active
- carrier is not excluded from request

Customer can cancel request only if:

- request status is not final

Admin can reopen request only if:

- request is not completed
- request is not cancelled_by_customer unless explicit override is later added

## Audit requirements

All sensitive operations must write audit/event log.

Sensitive operations:

- carrier created
- invite created
- invite used
- Telegram binding changed
- subscription extended
- carrier deactivated
- carrier blocked
- request manually reopened
- request manually closed
- assignment manually changed
- carrier excluded

## MVP implementation

MVP may implement permissions as service-level checks.

Do not rely only on Telegram button visibility.

Every callback handler must re-check permissions before mutation.

