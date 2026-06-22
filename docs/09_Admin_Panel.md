# CargoPT Bot — Admin Panel v1

## Purpose

Admin Panel is the operational control layer for CargoPT MVP.

It allows admins to manage:

- carriers
- vehicles
- drivers
- subscriptions
- requests
- assignments
- failed/reopened requests
- invite tokens
- audit history

MVP admin panel may be implemented inside Telegram first.

A web admin panel can be added later without changing domain logic.

## MVP admin channels

Supported MVP options:

- Telegram admin commands
- Telegram admin menus
- simple internal CLI scripts
- later web dashboard

Recommended MVP:

- Telegram admin menus for daily operations
- CLI scripts for emergency maintenance
- no web dashboard until workflows stabilize

## Admin roles

MVP may start with one admin role:

- super_admin

Future roles:

- dispatcher
- finance_admin
- support_admin
- read_only_admin

## Admin permissions

super_admin can:

- create carriers
- edit carriers
- deactivate carriers
- block carriers
- create invite tokens
- extend subscriptions
- view all requests
- manually reopen requests
- manually close requests
- view event logs

dispatcher can later:

- view requests
- reopen requests
- close invalid requests
- contact carriers manually

finance_admin can later:

- extend subscriptions
- view payment/subscription status

support_admin can later:

- view request state
- help customers and carriers

read_only_admin can later:

- view data without mutations

## Carrier management

Admin must be able to:

- create carrier_company
- update company_name
- update contact_name
- update phone
- update internal_note
- set status
- view paid_until
- view Telegram binding
- reset Telegram binding if necessary

Carrier statuses:

- draft
- invited
- active
- inactive
- blocked
- expired

## Invite management

Admin must be able to:

- create invite token
- revoke invite token
- view invite status
- view used_by_telegram_id
- view used_at
- regenerate expired invite

Rules:

- one active invite per carrier by default
- used invite cannot be reused
- rebinding requires explicit admin action

## Vehicle management

Admin must be able to:

- add vehicle
- edit vehicle
- deactivate vehicle
- view vehicle capability summary

Vehicle fields:

- vehicle_type
- payload_kg
- volume_m3
- has_tail_lift
- has_crane
- has_mobile_lift
- mobile_lift_max_floor
- mobile_lift_max_weight_kg
- crane_max_weight_kg
- crane_reach_meters
- is_active

## Driver management

Admin must be able to:

- add driver
- edit driver
- deactivate driver
- view Telegram binding if used

MVP rule:

- driver assignment is optional
- carrier-level assignment is enough for first release

## Subscription management

Admin must be able to:

- create subscription
- extend subscription
- cancel subscription
- view current subscription status
- view paid_until

MVP does not process payments.

Payment confirmation is manual.

## Request management

Admin must be able to view:

- request ID
- customer name
- customer phone
- pickup location
- dropoff location
- floors/elevators
- cargo size
- photos count
- urgency
- preferred date
- additional services
- status
- offer_round
- matched carriers
- current assignment
- event log

Admin actions:

- reopen request
- close request
- mark request completed
- mark request failed
- cancel open offers
- exclude carrier manually

## Assignment management

Admin must be able to view:

- assigned carrier
- assigned vehicle
- assigned driver
- assignment status
- contact_result
- contact_result_comment

Admin actions:

- mark completed
- mark failed
- cancel assignment
- reopen request

## Reopen management

Manual reopen requires:

- reason
- optional comment
- optional carrier exclusion

System should:

- create event log row
- increment offer_round
- rerun matching engine
- notify customer if needed

## Audit log

Admin must be able to inspect request_event_log.

Minimum displayed fields:

- created_at
- actor_type
- actor_id
- event_type
- old_status
- new_status
- payload summary

MVP can show latest 20 events per request.

## Admin dashboard summary

MVP dashboard should show:

- new requests today
- offered requests
- in_contact requests
- reopened requests
- expired requests
- active carriers
- expired subscriptions
- requests needing admin attention

## Requests needing admin attention

A request needs admin attention if:

- no carriers matched
- all offers expired
- request reopened more than configured threshold
- customer cancelled after assignment
- carrier failed after accepting
- route data is missing and area matching failed

## Safety rules

Admin actions must:

- validate current state
- write event log
- avoid silent destructive updates
- never delete business records in MVP

Destructive actions should become status changes instead of hard deletes.

## Future web admin panel

Future web panel should reuse the same domain services.

The Telegram admin panel must not contain business logic that cannot be reused elsewhere.

