# CargoPT Bot — Matching Engine v1

## Purpose

The matching engine selects carriers eligible to receive a customer transport request.

MVP strategy:

- no auction
- no automatic price calculation
- no rating-based ranking
- no mandatory automatic vehicle assignment
- all eligible carriers receive the offer simultaneously
- first carrier to accept wins

## Input

Primary input:

- transport_request.id

Required related data:

- pickup location
- dropoff location
- route_snapshot if available
- service_type
- cargo_size
- urgency
- preferred_date
- loaders_needed
- packing_required
- furniture_disassembly
- furniture_assembly
- disposal_required
- heavy_items
- request_excluded_carrier
- carrier_subscription
- carrier_service_area
- carrier_vehicle

## Output

The engine creates request_offer rows.

Each offer contains:

- request_id
- carrier_id
- vehicle_id nullable
- offer_round
- status = offered
- offered_at
- expires_at

## Filter order

### 1. Carrier status

Carrier must have:

- carrier_company.status = active

### 2. Subscription status

Carrier must have:

- active subscription
- paid_until >= now

### 3. Exclusion filter

Carrier must not exist in request_excluded_carrier for the same request.

### 4. Pickup area

Carrier must support pickup area.

Matching priority:

- exact municipality
- district fallback
- all Portugal / broad area
- admin override

### 5. Dropoff area

Carrier should support dropoff area or route distance.

MVP rule:

- pickup area is strict
- dropoff area may be softer if distance limit allows the route

### 6. Distance

If route_snapshot.distance_km exists:

- carrier_service_area.max_distance_km must be null or >= distance_km

If distance is unknown:

- do not reject solely on distance
- mark offer payload with distance_unknown warning later if payload support exists

### 7. Urgency

If request is urgent or same-day:

- carrier must allow urgent requests

### 8. Service type

Request service type must match carrier supported services.

MVP service types:

- moving
- furniture
- appliances
- office
- international
- other

### 9. Capabilities

Request may require:

- loaders
- packing
- furniture disassembly
- furniture assembly
- disposal
- tail lift
- crane
- mobile lift

Carrier/vehicle must satisfy hard requirements where known.

## Heavy item logic

Heavy items should be used carefully.

Possible heavy item values:

- safe
- piano
- gym_machine
- side_by_side_fridge
- other

MVP rule:

- include heavy item data in offer text
- avoid over-filtering if capability data is uncertain
- filter only when requirement is structurally impossible

## Vehicle selection

MVP does not require fully automatic vehicle assignment.

Recommended behavior:

- if clear compatible vehicle exists, set vehicle_id
- if vehicle data is incomplete, allow carrier-level offer
- carrier decides operationally after accepting

## Offer expiration

Default TTL:

- urgent: 15 minutes
- today: 30 minutes
- future date: 60 minutes

TTL values should be configurable.

## First-accept-wins transaction

Accept action must be transactional.

Flow:

1. Load request.
2. Check request status is offered or reopened.
3. Load offer.
4. Check offer status is offered.
5. Create request_assignment.
6. Set winning offer to accepted.
7. Set other open offers to cancelled.
8. Set transport_request.status to accepted.
9. Write request_event_log.
10. Commit transaction.
11. Notify customer, winner carrier and losing carriers.

## Reopen matching

When request reopens:

1. Increment offer_round.
2. Exclude previous failed carrier.
3. Rerun matching filters.
4. Create new request_offer rows.
5. Notify matching carriers.

If no carriers match:

- request remains reopened or becomes expired depending on policy
- admin should be notified

## Analytics to preserve

Matching should allow later analysis of:

- matched carriers count
- sent offers count
- accept rate
- time to first accept
- reopen rate
- no-match reasons
- common failure reasons

## Anti-spam and safety rules

The engine must prevent:

- duplicate active offers for same request/carrier/round
- offers to inactive carriers
- offers to expired subscribers
- late acceptance of expired offers
- carrier receiving a request after being excluded
