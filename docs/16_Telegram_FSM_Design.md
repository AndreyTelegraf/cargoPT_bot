# CargoPT Bot — Telegram FSM Design v1

## Purpose

This document defines Telegram FSM architecture for CargoPT Bot.

FSM is responsible only for user interaction flow.

FSM is not responsible for:

- request lifecycle
- matching decisions
- assignments
- subscriptions
- permissions
- scheduling

Those belong to domain services.

## Core principle

FSM stores conversation progress.

Database stores business state.

If FSM state and database state disagree:

- database is the source of truth

## User roles

CargoPT has three Telegram roles:

- customer
- carrier
- admin

Each role has an independent FSM.

## FSM design goals

The FSM should be:

- restart-safe
- interruption-safe
- simple to audit
- easy to extend
- independent from business logic

## Recommended structure

app/states/

- customer_request.py
- carrier_onboarding.py
- carrier_actions.py
- admin_actions.py

Handlers should interact with FSM only through state transitions.

Business services must not depend on FSM state names.

## Global recovery rule

Every flow should support:

- /start
- cancel
- timeout recovery

Users must never become trapped inside a state.

## Customer FSM overview

Customer request creation is the largest FSM in the system.

High-level flow:

start
 ->
cargo_type
 ->
photos
 ->
pickup_location
 ->
pickup_details
 ->
dropoff_location
 ->
dropoff_details
 ->
schedule
 ->
services
 ->
comment
 ->
phone
 ->
confirmation
 ->
submitted

## Customer FSM states

Suggested class:

CustomerRequestStates

States:

- cargo_type
- photos
- pickup_location
- pickup_details
- dropoff_location
- dropoff_details
- schedule
- services
- comment
- phone
- confirmation

## cargo_type

Question:

What needs to be transported?

Options:

- few_boxes
- furniture_items
- studio_t0
- t1
- t2
- t3_plus
- office
- other

FSM stores:

- cargo_size
- service_type if clear

Transition:

- cargo_type -> photos

## photos

Question:

Add cargo photos?

Options:

- add_photo
- skip_photos
- done_photos

Behavior:

- customer may send multiple photos
- bot stores Telegram file_id
- photos are attached to draft request
- skip is allowed

Transition:

- photos -> pickup_location

## pickup_location

Question:

Pickup address?

Options:

- send Telegram location
- enter address manually
- send map link if supported later

FSM stores:

- pickup raw input
- pickup source
- pickup lat/lon if Telegram location

Transition:

- pickup_location -> pickup_details

## pickup_details

Question:

Pickup floor and elevator?

Fields:

- pickup_floor
- pickup_has_elevator

Rules:

- floor may be 0
- elevator answer is required
- unknown elevator may be allowed later

Transition:

- pickup_details -> dropoff_location

## dropoff_location

Question:

Dropoff address?

Options:

- send Telegram location
- enter address manually
- send map link if supported later

FSM stores:

- dropoff raw input
- dropoff source
- dropoff lat/lon if Telegram location

Transition:

- dropoff_location -> dropoff_details

## dropoff_details

Question:

Dropoff floor and elevator?

Fields:

- dropoff_floor
- dropoff_has_elevator

Transition:

- dropoff_details -> schedule

## schedule

Question:

When is transport needed?

Options:

- urgent
- today
- tomorrow
- choose_date

FSM stores:

- urgency
- preferred_date
- request_time_window data if available

Transition:

- schedule -> services

## services

Question:

Additional services?

Fields:

- packing_required
- furniture_disassembly
- furniture_assembly
- loaders_needed
- disposal_required
- heavy_items

Packing options:

- none
- partial
- full

Loaders options:

- 0
- 1
- 2
- 3+

Heavy item options:

- none
- safe
- piano
- gym_machine
- side_by_side_fridge
- other

Transition:

- services -> comment

## comment

Question:

Comment for carrier?

Rules:

- optional
- should have maximum length
- can be skipped

Transition:

- comment -> phone

## phone

Question:

Customer phone?

Rules:

- required
- validate basic phone format
- accept Portuguese and international format
- store exactly enough for carrier contact

Transition:

- phone -> confirmation

## confirmation

Bot shows full request summary.

Customer actions:

- confirm
- edit
- cancel

On confirm:

- create transport_request
- create locations
- attach photos
- create route_snapshot if possible
- write event log
- run matching engine
- clear FSM state

Transition:

- confirmation -> submitted
## Carrier onboarding FSM

Suggested class:

CarrierOnboardingStates

States:

- invite_validation
- company
- geography
- services
- capabilities
- urgency
- distance
- vehicles
- confirmation

## invite_validation

Entry point:

- carrier opens invite link

Validation:

- token exists
- token status is active
- token is not expired
- token is not used
- carrier exists

On success:

- continue to company

On failure:

- show error
- stop flow

## company

Collects:

- company_name
- contact_name
- phone

Rules:

- values may prefill from admin-created carrier
- carrier may confirm or edit

Transition:

- company -> geography

## geography

Collects:

- districts
- municipalities
- pickup_allowed
- dropoff_allowed
- max_distance_km if needed

Rules:

- MVP may use predefined buttons
- free text should be normalized later
- unsupported geography requires admin review

Transition:

- geography -> services

## services

Collects carrier service types:

- moving
- furniture
- appliances
- office
- international
- other

Transition:

- services -> capabilities

## capabilities

Collects:

- loaders
- packing
- furniture assembly
- furniture disassembly
- tail lift
- crane
- mobile lift

If crane or mobile lift is selected:

- ask for max weight
- ask for max floor/reach where relevant

Transition:

- capabilities -> urgency

## urgency

Collects:

- accepts urgent requests
- does not accept urgent requests

Transition:

- urgency -> distance

## distance

Collects:

- city only
- up to 50 km
- up to 100 km
- all Portugal

Transition:

- distance -> vehicles

## vehicles

Carrier adds one or more vehicles.

Per vehicle collect:

- vehicle_type
- payload_kg
- volume_m3
- tail lift
- crane
- mobile lift
- active flag

Actions:

- add another vehicle
- finish vehicles

Transition:

- vehicles -> confirmation

## carrier onboarding confirmation

Bot shows onboarding summary.

Actions:

- confirm
- edit section
- cancel

On confirm:

- update carrier_company
- create/update carrier_service_area
- create carrier_vehicle rows
- bind telegram_user_id
- mark invite used
- activate carrier if subscription is valid
- write event log
- clear FSM state

## Carrier action FSM

Carrier offer and assignment actions do not need long FSM.

They are mostly callback-driven.

Main actions:

- accept offer
- skip offer
- mark agreed
- mark no agreement
- mark cannot perform
- view subscription

Rules:

- every callback re-checks permissions
- every callback re-checks current DB state
- button visibility is not security

## Offer accept callback

Callback data should contain:

- offer_id
- request_id
- action

On accept:

1. load offer
2. validate carrier identity
3. validate offer status
4. validate request status
5. validate subscription
6. call assignment service
7. return result message

Possible results:

- assignment won
- request already taken
- offer expired
- carrier not eligible
- error, contact admin

## Assignment result callback

Carrier may report:

- agreed
- no_answer_customer
- customer_refused
- price_disagreement
- cannot_perform
- other

Service maps result to:

- completed
- failed
- reopened
- admin attention

## Admin FSM overview

Admin actions should be menu-driven where possible.

Admin flows:

- dashboard
- carrier management
- invite management
- subscription management
- request management
- assignment management
- audit inspection

Admin FSM should stay shallow.

Long admin workflows should be avoided unless data entry is required.

## Admin states

Suggested class:

AdminActionStates

States:

- carrier_create
- carrier_edit
- invite_create
- subscription_extend
- request_search
- request_reopen
- request_close
- assignment_update

## carrier_create

Collects:

- company_name
- contact_name
- phone
- paid_until
- internal_note

On confirm:

- create carrier_company
- optionally create subscription
- optionally create invite token
- write event log

## invite_create

Input:

- carrier_id

Validates:

- carrier exists
- carrier is not blocked
- no active invite exists unless override

On confirm:

- create admin_invite_token
- send invite link to admin

## subscription_extend

Input:

- carrier_id
- paid_until
- plan
- price if needed

On confirm:

- create or update carrier_subscription
- update carrier_company.paid_until
- write event log

## request_search

Search options:

- request_id
- customer phone
- customer telegram id
- status
- date
- urgent requests
- reopened requests

Result actions:

- view
- reopen
- close
- mark completed
- inspect event log

## request_reopen

Required input:

- request_id
- reason
- optional comment
- optional excluded carrier

On confirm:

- call request service
- increment offer_round
- create request_excluded_carrier if needed
- rerun matching
- write event log

## request_close

Required input:

- request_id
- reason

On confirm:

- set admin_closed
- cancel open offers
- cancel active assignment if needed
- write event log

## Callback naming

Callback data should be predictable and namespaced.

Suggested format:

domain:action:id

Examples:

- offer:accept:123
- offer:skip:123
- assignment:agreed:456
- request:cancel:789
- admin_request:reopen:789
- admin_carrier:view:55

For complex payloads, use callback factory classes.

## Callback safety

Every callback handler must:

1. parse callback data
2. load target object from DB
3. validate actor identity
4. validate permissions
5. validate current object state
6. call service
7. answer callback
8. update message if needed

Never trust callback data alone.

## Callback expiration

Buttons may outlive business state.

Examples:

- carrier clicks expired offer
- carrier clicks offer already taken
- customer clicks cancel after admin closed request

Handlers must return safe messages:

- offer expired
- request already taken
- request already closed
- action no longer available

## Message editing policy

Where possible:

- edit previous bot message after action
- remove obsolete buttons
- show current state

But do not rely on message UI as source of truth.

Database status always wins.

## FSM storage

MVP may use aiogram memory storage for early local development.

For production, prefer persistent FSM storage if operationally needed.

Options:

- MemoryStorage for local/dev
- RedisStorage later
- DB-backed draft persistence for critical flows

Important:

Customer request draft data should be recoverable enough.

If FSM is lost before confirmation:

- no business request should exist yet
- user can restart request flow

If request is confirmed:

- business state is stored in database
- FSM can be cleared safely

## Draft data policy

FSM may store draft data before confirmation.

Draft data examples:

- cargo_size
- photos file_ids
- pickup raw input
- dropoff raw input
- floor/elevator data
- schedule selection
- service options
- comment
- phone

Do not create final transport_request until confirmation.

Possible future improvement:

- request_draft table

Not needed for MVP unless request creation becomes too long or fragile.

## Timeouts

Recommended timeout behavior:

- if user is inactive during request creation, keep FSM state for reasonable time
- on return, show current step or restart option
- do not create partial request automatically

Admin and carrier flows can timeout more aggressively.

## Cancel behavior

Customer cancel inside FSM:

- clears FSM
- deletes draft data
- does not create transport_request

Customer cancel after confirmed request:

- calls request service
- sets business status to cancelled_by_customer if allowed

Carrier cancel onboarding:

- clears FSM
- does not bind Telegram account
- invite token remains active unless policy says otherwise

Admin cancel:

- clears current admin flow
- no mutation unless confirmation already happened

## Error handling

On unexpected error:

- log traceback
- show safe user message
- do not expose technical details
- keep or clear FSM depending on safety

If mutation may have partially happened:

- reload DB state
- show current real state
- do not infer from FSM

## Validation policy

Validate at each step.

Examples:

- phone format
- floor is integer
- date is valid
- photo file_id exists
- invite token is valid
- carrier is eligible
- admin is authorized

Validation failures should keep user in the same state.

## Smoke tests for FSM

Minimum customer smoke:

1. /start
2. create request
3. choose cargo type
4. skip photos
5. enter pickup
6. enter pickup floor/elevator
7. enter dropoff
8. enter dropoff floor/elevator
9. choose tomorrow
10. choose services
11. skip comment
12. enter phone
13. confirm
14. verify transport_request exists

Minimum carrier smoke:

1. open invite
2. complete onboarding
3. verify carrier Telegram binding
4. receive offer
5. accept offer
6. verify assignment created
7. mark agreed

Minimum admin smoke:

1. open admin dashboard
2. create carrier
3. create invite
4. extend subscription
5. view request
6. reopen request
7. inspect event log

## Implementation order

Recommended order:

1. common /start and cancel
2. CustomerRequestStates
3. customer request handlers
4. customer confirmation service call
5. CarrierOnboardingStates
6. carrier onboarding handlers
7. carrier offer callbacks
8. AdminActionStates
9. admin dashboard
10. admin request actions
11. smoke tests

## Core rule

FSM is an adapter-level conversation tool.

It must remain replaceable.

If Telegram FSM were replaced tomorrow, domain services and database lifecycle should still work.

