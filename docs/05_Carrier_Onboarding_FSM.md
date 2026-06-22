# CargoPT Bot — Carrier Onboarding FSM v1

## Purpose

Carrier onboarding is admin-controlled.

Carriers cannot self-register because MVP monetization and quality control depend on manual approval.

## Main flow

admin_created → invite_created → invite_opened → questionnaire_started → questionnaire_completed → telegram_bound → active

## Carrier company statuses

- draft
- invited
- active
- inactive
- blocked
- expired

## Invite token statuses

- active
- used
- expired
- revoked

## Step 1 — Admin creates carrier

Admin enters:

- company_name
- contact_name
- phone
- paid_until
- internal_note

System creates:

- carrier_company.status = draft

## Step 2 — Admin creates invite

System creates:

- admin_invite_token
- status = active
- expires_at

Carrier status becomes:

- invited

Admin receives invite link.

## Step 3 — Carrier opens invite

Bot validates:

- token exists
- token.status = active
- token.expires_at > now
- token.used_at is null

If valid:

- onboarding session starts

If invalid:

- user receives error and admin contact instruction

## Step 4 — Questionnaire

Carrier answers:

Company:

- company name
- contact person
- phone

Geography:

- working districts/municipalities

Services:

- moving
- furniture
- appliances
- offices
- international

Capabilities:

- loaders
- packing
- furniture assembly
- furniture disassembly
- crane
- mobile lift
- tail lift

Urgency:

- accepts urgent requests
- does not accept urgent requests

Distance:

- city only
- up to 50 km
- up to 100 km
- all Portugal

Vehicles:

- one or more vehicles

## Step 5 — Telegram binding

After questionnaire completion:

- token.used_at is set
- token.used_by_telegram_id is set
- carrier_company.telegram_user_id is set
- carrier_company.status = active if subscription is valid

Rules:

- one Telegram account per carrier company in MVP
- rebinding requires admin

## Step 6 — Subscription validation

Carrier is active only if:

- carrier_company.status = active
- carrier_subscription.status = active
- paid_until >= now

If paid_until expires:

- carrier_company.status may remain active administratively
- matching engine must treat carrier as not eligible

## Carrier deactivation

Admin may deactivate carrier.

Effects:

- carrier_company.status = inactive
- carrier receives no new offers
- existing assignments remain visible

## Carrier blocking

Admin may block carrier.

Effects:

- carrier_company.status = blocked
- carrier cannot use bot
- carrier receives no offers
- admin note required

## Re-inviting carrier

Allowed if:

- old token expired
- old token revoked
- Telegram binding failed

Not allowed if:

- active token already exists
- carrier already bound unless admin explicitly resets binding

## Event logging

Carrier onboarding should write event logs.

Minimum events:

- carrier_created
- invite_created
- invite_opened
- questionnaire_started
- questionnaire_completed
- telegram_bound
- carrier_activated
- carrier_deactivated
- carrier_blocked
- subscription_extended
