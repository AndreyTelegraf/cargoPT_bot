# CargoPT Bot — SQLAlchemy Models v1

## Purpose

This document defines the ORM model design for CargoPT Bot.

It translates the canonical database schema into SQLAlchemy model structure.

The goal is to make implementation mechanical:

- model classes
- relationships
- indexes
- unique constraints
- enum-like string values
- timestamp fields
- deletion/update policy

## ORM strategy

Recommended stack:

- SQLAlchemy 2.x
- typed declarative models
- Alembic migrations
- explicit relationships
- string status fields for MVP
- centralized constants/enums later

## General model rules

All models should use:

- explicit table names
- integer primary keys unless token-based
- UTC timestamps
- created_at where creation matters
- updated_at where mutation matters
- no business workflow methods inside ORM models

ORM models must not contain:

- matching logic
- FSM transition logic
- notification logic
- scheduler logic
- permission logic

Business logic belongs in services.

## Base model convention

Recommended base fields:

- id
- created_at
- updated_at where mutable

For append-only tables:

- created_at only
- no updated_at

## Timestamp policy

Use timezone-aware UTC timestamps where possible.

Application should set timestamps consistently.

Recommended helper later:

- utc_now()

Do not rely on local server timezone.

## Deletion policy

MVP should avoid hard deletes for business records.

Preferred approach:

- status fields
- is_active fields
- append-only event log

Hard delete may be allowed only for temporary technical state.

## Model files

Suggested files:

- app/models/carrier.py
- app/models/request.py
- app/models/offer.py
- app/models/assignment.py
- app/models/schedule.py
- app/models/subscription.py
- app/models/event_log.py
- app/models/location.py

## CarrierCompany

Table:

- carrier_company

Fields:

- id
- company_name
- contact_name
- phone
- telegram_user_id
- status
- paid_until
- internal_note
- created_at
- updated_at

Relationships:

- vehicles -> CarrierVehicle[]
- drivers -> CarrierDriver[]
- service_areas -> CarrierServiceArea[]
- subscriptions -> CarrierSubscription[]
- offers -> RequestOffer[]
- assignments -> RequestAssignment[]

Indexes:

- ix_carrier_company_telegram_user_id
- ix_carrier_company_status
- ix_carrier_company_paid_until

Unique constraints:

- telegram_user_id unique nullable

Status values:

- draft
- invited
- active
- inactive
- blocked
- expired

## CarrierVehicle

Table:

- carrier_vehicle

Fields:

- id
- carrier_id
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
- created_at
- updated_at

Relationships:

- carrier -> CarrierCompany
- offers -> RequestOffer[]
- assignments -> RequestAssignment[]

Indexes:

- ix_carrier_vehicle_carrier_id
- ix_carrier_vehicle_is_active
- ix_carrier_vehicle_vehicle_type

Vehicle type values:

- small_van
- medium_van
- large_van
- box_truck
- truck
- other

## CarrierDriver

Table:

- carrier_driver

Fields:

- id
- carrier_id
- name
- phone
- telegram_user_id
- is_active
- created_at
- updated_at

Relationships:

- carrier -> CarrierCompany
- assignments -> RequestAssignment[]

Indexes:

- ix_carrier_driver_carrier_id
- ix_carrier_driver_telegram_user_id
- ix_carrier_driver_is_active

MVP rule:

- driver is optional
- assignment may be carrier-level only

## ServiceArea

Table:

- service_area

Fields:

- id
- country
- district
- municipality
- normalized_name
- created_at

Relationships:

- carrier_links -> CarrierServiceArea[]

Unique constraints:

- uq_service_area_country_normalized_name

Indexes:

- ix_service_area_normalized_name
- ix_service_area_district
- ix_service_area_municipality

Rules:

- stores normalized Portuguese geography
- should be seeded, not created randomly during request flow

## CarrierServiceArea

Table:

- carrier_service_area

Fields:

- carrier_id
- area_id
- pickup_allowed
- dropoff_allowed
- max_distance_km
- urgent_allowed
- created_at

Relationships:

- carrier -> CarrierCompany
- area -> ServiceArea

Primary key:

- carrier_id + area_id

Indexes:

- ix_carrier_service_area_area_id
- ix_carrier_service_area_pickup_allowed
- ix_carrier_service_area_dropoff_allowed
- ix_carrier_service_area_urgent_allowed

Rules:

- matching engine reads this table
- pickup_allowed is stricter than dropoff_allowed in MVP

## Location

Table:

- location

Fields:

- id
- raw_input
- lat
- lon
- map_url
- formatted_address
- postal_code
- municipality
- district
- source
- confidence
- created_at

Relationships:

- pickup_requests -> TransportRequest[]
- dropoff_requests -> TransportRequest[]

Indexes:

- ix_location_municipality
- ix_location_district
- ix_location_postal_code
- ix_location_lat_lon

Source values:

- telegram_location
- manual_address
- google_maps_url
- admin_input
- unknown

Rules:

- raw_input is always preserved
- parsed address is helpful but not fully trusted
- map_url is stored when available

## TransportRequest

Table:

- transport_request

Fields:

- id
- customer_telegram_id
- customer_name
- customer_phone
- customer_language
- lead_source
- pickup_location_id
- pickup_floor
- pickup_has_elevator
- dropoff_location_id
- dropoff_floor
- dropoff_has_elevator
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
- customer_comment
- status
- offer_round
- created_at
- updated_at

Relationships:

- pickup_location -> Location
- dropoff_location -> Location
- photos -> RequestPhoto[]
- route_snapshots -> RouteSnapshot[]
- offers -> RequestOffer[]
- assignments -> RequestAssignment[]
- excluded_carriers -> RequestExcludedCarrier[]
- event_logs -> RequestEventLog[]
- time_windows -> RequestTimeWindow[]
- bookings -> CarrierBooking[]

Indexes:

- ix_transport_request_customer_telegram_id
- ix_transport_request_status
- ix_transport_request_created_at
- ix_transport_request_preferred_date
- ix_transport_request_urgency
- ix_transport_request_lead_source
- ix_transport_request_pickup_location_id
- ix_transport_request_dropoff_location_id

Status values:

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

Lead source values:

- telegram_bot
- website
- whatsapp
- admin_created

Customer language values:

- ru
- en
- pt
- es

Rules:

- transport_request.status is source of truth for request lifecycle
- offer_round starts at 1
- offer_round increments on reopen
- customer phone is stored because Telegram identity is not enough for logistics

## RequestPhoto

Table:

- request_photo

Fields:

- id
- request_id
- telegram_file_id
- file_type
- created_at

Relationships:

- request -> TransportRequest

Indexes:

- ix_request_photo_request_id

Rules:

- stores Telegram file_id only
- file binary is not stored in database
- request may have zero or more photos

## RouteSnapshot

Table:

- route_snapshot

Fields:

- id
- request_id
- distance_km
- duration_minutes
- calculated_at
- source
- confidence

Relationships:

- request -> TransportRequest

Indexes:

- ix_route_snapshot_request_id
- ix_route_snapshot_distance_km

Rules:

- route data is a snapshot
- route may be missing in MVP
- matching must fallback to area logic if distance is unknown

## RequestOffer

Table:

- request_offer

Fields:

- id
- request_id
- carrier_id
- vehicle_id
- offer_round
- status
- offered_at
- expires_at
- accepted_at
- failure_reason

Relationships:

- request -> TransportRequest
- carrier -> CarrierCompany
- vehicle -> CarrierVehicle

Indexes:

- ix_request_offer_request_id
- ix_request_offer_carrier_id
- ix_request_offer_status
- ix_request_offer_expires_at
- ix_request_offer_offered_at

Unique constraints:

- uq_request_offer_request_carrier_round

Status values:

- offered
- accepted
- skipped
- expired
- failed
- cancelled

Rules:

- one carrier must not receive duplicate offer for same request and round
- accepted offer must create assignment
- losing offers must be cancelled after first accept wins

## RequestAssignment

Table:

- request_assignment

Fields:

- id
- request_id
- carrier_id
- vehicle_id
- driver_id
- status
- contact_result
- contact_result_comment
- created_at
- updated_at

Relationships:

- request -> TransportRequest
- carrier -> CarrierCompany
- vehicle -> CarrierVehicle
- driver -> CarrierDriver

Indexes:

- ix_request_assignment_request_id
- ix_request_assignment_carrier_id
- ix_request_assignment_status
- ix_request_assignment_contact_result

Status values:

- active
- completed
- failed
- cancelled

Contact result values:

- agreed
- no_answer_customer
- no_answer_carrier
- customer_refused
- carrier_refused
- price_disagreement
- duplicate_request
- other

Rules:

- only one active assignment per request
- completed request requires completed assignment
- failed assignment normally creates excluded carrier row

## RequestExcludedCarrier

Table:

- request_excluded_carrier

Fields:

- id
- request_id
- carrier_id
- reason
- created_at

Relationships:

- request -> TransportRequest
- carrier -> CarrierCompany

Unique constraints:

- uq_request_excluded_carrier_request_carrier

Indexes:

- ix_request_excluded_carrier_request_id
- ix_request_excluded_carrier_carrier_id

Reason values:

- carrier_declined
- no_agreement
- no_response
- admin_excluded

Rules:

- excluded carrier must not receive reopened request again
- created during failed/reopened flow

## RequestEventLog

Table:

- request_event_log

Fields:

- id
- request_id
- actor_type
- actor_id
- event_type
- old_status
- new_status
- payload_json
- created_at

Relationships:

- request -> TransportRequest

Indexes:

- ix_request_event_log_request_id
- ix_request_event_log_actor_type
- ix_request_event_log_event_type
- ix_request_event_log_created_at

Actor type values:

- customer
- carrier
- admin
- system

Rules:

- append-only
- no normal updates
- no normal deletes
- all lifecycle transitions write event log

## CarrierSubscription

Table:

- carrier_subscription

Fields:

- id
- carrier_id
- plan
- paid_from
- paid_until
- status
- price
- created_at
- updated_at

Relationships:

- carrier -> CarrierCompany

Indexes:

- ix_carrier_subscription_carrier_id
- ix_carrier_subscription_status
- ix_carrier_subscription_paid_until

Status values:

- active
- expired
- cancelled
- pending

Rules:

- matching checks active subscription
- payment processing is manual in MVP

## AdminInviteToken

Table:

- admin_invite_token

Fields:

- token
- carrier_id
- created_by_admin_id
- expires_at
- used_at
- used_by_telegram_id
- status
- created_at

Relationships:

- carrier -> CarrierCompany

Primary key:

- token

Indexes:

- ix_admin_invite_token_carrier_id
- ix_admin_invite_token_status
- ix_admin_invite_token_expires_at
- ix_admin_invite_token_used_by_telegram_id

Status values:

- active
- used
- expired
- revoked

Rules:

- token is one-time use
- token binds Telegram account to carrier
- rebinding requires admin

## RequestTimeWindow

Table:

- request_time_window

Fields:

- id
- request_id
- date_from
- date_to
- time_from
- time_to
- flexibility
- source
- created_at

Relationships:

- request -> TransportRequest

Indexes:

- ix_request_time_window_request_id
- ix_request_time_window_date_from
- ix_request_time_window_date_to

Flexibility values:

- exact
- same_day
- flexible
- urgent

Rules:

- schedule-layer object
- not the same as scheduler job timing

## CarrierAvailability

Table:

- carrier_availability

Fields:

- id
- carrier_id
- date
- time_from
- time_to
- capacity_slots
- status
- created_at
- updated_at

Relationships:

- carrier -> CarrierCompany

Indexes:

- ix_carrier_availability_carrier_id
- ix_carrier_availability_date
- ix_carrier_availability_status

Status values:

- available
- limited
- unavailable

Rules:

- may be implemented after MVP
- reserved for future calendar support

## CarrierBooking

Table:

- carrier_booking

Fields:

- id
- carrier_id
- request_id
- date
- time_from
- time_to
- status
- created_at
- updated_at

Relationships:

- carrier -> CarrierCompany
- request -> TransportRequest

Indexes:

- ix_carrier_booking_carrier_id
- ix_carrier_booking_request_id
- ix_carrier_booking_date
- ix_carrier_booking_status

Status values:

- tentative
- confirmed
- cancelled
- completed

Rules:

- future calendar reservation object
- request status and booking status are related but separate

## Relationship loading policy

Default recommendation:

- use lazy relationships for normal operations
- use explicit selectinload/joinedload in repository methods where needed
- avoid accidental N+1 queries in admin dashboards

Repositories should control loading strategy.

## Constraint policy

Required unique constraints:

- carrier_company.telegram_user_id
- service_area.country + service_area.normalized_name
- carrier_service_area.carrier_id + carrier_service_area.area_id
- request_offer.request_id + request_offer.carrier_id + request_offer.offer_round
- request_excluded_carrier.request_id + request_excluded_carrier.carrier_id

Partial unique constraints may be useful later for:

- one active assignment per request
- one active invite per carrier
- one active subscription per carrier

SQLite may not support all partial constraints identically.

For MVP, enforce some of these in services if needed.

## Index policy

Indexes should support:

- request lookup by status
- carrier lookup by Telegram ID
- matching by carrier status/subscription
- offer expiration
- request event log inspection
- schedule/calendar lookup

Do not over-index before real usage data.

## Enum strategy

MVP uses string fields.

Recommended future implementation:

- constants.py or enums.py
- Python Enum if useful
- database check constraints later if stable

Do not scatter status strings across handlers.

## JSON payload policy

request_event_log.payload_json should store structured JSON as text for SQLite compatibility.

Future PostgreSQL may use JSONB.

Payload should include:

- relevant IDs
- reason
- admin_id where applicable
- previous values where useful
- operational context

Do not store large blobs.

## Migration readiness

ORM model definitions must map cleanly to Alembic migrations.

Rules:

- every table has explicit __tablename__
- every index has explicit name
- every unique constraint has explicit name
- foreign keys are explicit
- nullable policy is deliberate

## Implementation order

Recommended model implementation order:

1. Base and timestamp helpers
2. CarrierCompany
3. CarrierVehicle
4. CarrierDriver
5. ServiceArea
6. CarrierServiceArea
7. Location
8. TransportRequest
9. RequestPhoto
10. RouteSnapshot
11. RequestOffer
12. RequestAssignment
13. RequestExcludedCarrier
14. RequestEventLog
15. CarrierSubscription
16. AdminInviteToken
17. RequestTimeWindow
18. CarrierAvailability
19. CarrierBooking

## Smoke checks after model implementation

Minimum checks:

- import all models
- create metadata
- generate migration
- apply migration to empty DB
- inspect tables
- verify indexes
- insert minimal carrier
- insert minimal request
- insert offer
- create assignment
- write event log

## Core rule

ORM models describe persistence.

They do not decide business behavior.

Business behavior belongs in services.

