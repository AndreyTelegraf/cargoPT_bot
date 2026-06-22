# CargoPT Bot — DB Schema v1

## Purpose

This document defines the canonical MVP database schema for CargoPT Bot.

The database must support:

- customer transport requests
- carrier companies
- vehicles
- drivers
- service areas
- matching
- offers
- assignments
- reopen logic
- schedule-layer foundation
- audit/event logging
- future migration from SQLite to PostgreSQL

## Database strategy

MVP may start on SQLite for speed.

Schema must remain PostgreSQL-ready:

- use explicit IDs
- avoid SQLite-only logic
- keep timestamps in UTC
- keep enum values as strings
- keep event log append-only
- avoid storing business-critical state only in Telegram messages

## Core tables

### carrier_company

Represents a transport company or individual carrier.

Fields:

- id INTEGER PRIMARY KEY
- company_name TEXT NOT NULL
- contact_name TEXT
- phone TEXT
- telegram_user_id INTEGER UNIQUE
- status TEXT NOT NULL
- paid_until DATETIME
- internal_note TEXT
- created_at DATETIME NOT NULL
- updated_at DATETIME NOT NULL

Allowed status values:

- draft
- invited
- active
- inactive
- blocked
- expired

Indexes:

- telegram_user_id
- status
- paid_until

### carrier_vehicle

Represents a vehicle belonging to a carrier.

Fields:

- id INTEGER PRIMARY KEY
- carrier_id INTEGER NOT NULL REFERENCES carrier_company(id)
- vehicle_type TEXT NOT NULL
- payload_kg INTEGER
- volume_m3 REAL
- has_tail_lift BOOLEAN NOT NULL DEFAULT 0
- has_crane BOOLEAN NOT NULL DEFAULT 0
- has_mobile_lift BOOLEAN NOT NULL DEFAULT 0
- mobile_lift_max_floor INTEGER
- mobile_lift_max_weight_kg INTEGER
- crane_max_weight_kg INTEGER
- crane_reach_meters REAL
- is_active BOOLEAN NOT NULL DEFAULT 1
- created_at DATETIME NOT NULL
- updated_at DATETIME NOT NULL

Allowed vehicle_type values:

- small_van
- medium_van
- large_van
- box_truck
- truck
- other

Indexes:

- carrier_id
- is_active
- vehicle_type

### carrier_driver

Represents a driver connected to a carrier.

Fields:

- id INTEGER PRIMARY KEY
- carrier_id INTEGER NOT NULL REFERENCES carrier_company(id)
- name TEXT
- phone TEXT
- telegram_user_id INTEGER
- is_active BOOLEAN NOT NULL DEFAULT 1
- created_at DATETIME NOT NULL
- updated_at DATETIME NOT NULL

Indexes:

- carrier_id
- telegram_user_id
- is_active

### service_area

Normalized Portuguese geography unit.

Fields:

- id INTEGER PRIMARY KEY
- country TEXT NOT NULL DEFAULT 'PT'
- district TEXT
- municipality TEXT NOT NULL
- normalized_name TEXT NOT NULL
- created_at DATETIME NOT NULL

Unique constraint:

- country + normalized_name

Indexes:

- normalized_name
- district
- municipality

### carrier_service_area

Links carrier to operating areas.

Fields:

- carrier_id INTEGER NOT NULL REFERENCES carrier_company(id)
- area_id INTEGER NOT NULL REFERENCES service_area(id)
- pickup_allowed BOOLEAN NOT NULL DEFAULT 1
- dropoff_allowed BOOLEAN NOT NULL DEFAULT 1
- max_distance_km INTEGER
- urgent_allowed BOOLEAN NOT NULL DEFAULT 0
- created_at DATETIME NOT NULL

Primary key:

- carrier_id + area_id

Indexes:

- area_id
- pickup_allowed
- dropoff_allowed
- urgent_allowed

### location

Stores customer-provided pickup/dropoff points.

Fields:

- id INTEGER PRIMARY KEY
- raw_input TEXT
- lat REAL
- lon REAL
- map_url TEXT
- formatted_address TEXT
- postal_code TEXT
- municipality TEXT
- district TEXT
- source TEXT NOT NULL
- confidence REAL
- created_at DATETIME NOT NULL

Allowed source values:

- telegram_location
- manual_address
- google_maps_url
- admin_input
- unknown

Rule:

- raw input must always be preserved
- parsed address is helpful but not trusted as sole source
- map_url is stored when available

### transport_request

Main customer request.

Fields:

- id INTEGER PRIMARY KEY
- customer_telegram_id INTEGER NOT NULL
- customer_name TEXT
- customer_phone TEXT
- customer_language TEXT
- lead_source TEXT NOT NULL DEFAULT 'telegram_bot'

Pickup:

- pickup_location_id INTEGER REFERENCES location(id)
- pickup_floor INTEGER
- pickup_has_elevator BOOLEAN

Dropoff:

- dropoff_location_id INTEGER REFERENCES location(id)
- dropoff_floor INTEGER
- dropoff_has_elevator BOOLEAN

Request parameters:

- service_type TEXT
- cargo_size TEXT
- urgency TEXT
- preferred_date DATE
- loaders_needed INTEGER
- packing_required TEXT
- furniture_disassembly BOOLEAN
- furniture_assembly BOOLEAN
- disposal_required BOOLEAN
- heavy_items TEXT
- customer_comment TEXT

Operational fields:

- status TEXT NOT NULL
- offer_round INTEGER NOT NULL DEFAULT 1
- created_at DATETIME NOT NULL
- updated_at DATETIME NOT NULL

Allowed customer_language values:

- ru
- en
- pt
- es

Allowed lead_source values:

- telegram_bot
- website
- whatsapp
- admin_created

Allowed status values:

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

Indexes:

- customer_telegram_id
- status
- created_at
- preferred_date
- urgency
- lead_source

### request_photo

Photos attached to transport request.

Fields:

- id INTEGER PRIMARY KEY
- request_id INTEGER NOT NULL REFERENCES transport_request(id)
- telegram_file_id TEXT NOT NULL
- file_type TEXT
- created_at DATETIME NOT NULL

Indexes:

- request_id

### route_snapshot

Stores route data at request creation or recalculation.

Fields:

- id INTEGER PRIMARY KEY
- request_id INTEGER NOT NULL REFERENCES transport_request(id)
- distance_km REAL
- duration_minutes INTEGER
- calculated_at DATETIME NOT NULL
- source TEXT
- confidence REAL

Indexes:

- request_id
- distance_km

### request_offer

Offer sent to a carrier.

Fields:

- id INTEGER PRIMARY KEY
- request_id INTEGER NOT NULL REFERENCES transport_request(id)
- carrier_id INTEGER NOT NULL REFERENCES carrier_company(id)
- vehicle_id INTEGER REFERENCES carrier_vehicle(id)
- offer_round INTEGER NOT NULL
- status TEXT NOT NULL
- offered_at DATETIME NOT NULL
- expires_at DATETIME
- accepted_at DATETIME
- failure_reason TEXT

Allowed status values:

- offered
- accepted
- skipped
- expired
- failed
- cancelled

Unique constraint:

- request_id + carrier_id + offer_round

Indexes:

- request_id
- carrier_id
- status
- expires_at
- offered_at

### request_assignment

Winner carrier assignment.

Fields:

- id INTEGER PRIMARY KEY
- request_id INTEGER NOT NULL REFERENCES transport_request(id)
- carrier_id INTEGER NOT NULL REFERENCES carrier_company(id)
- vehicle_id INTEGER REFERENCES carrier_vehicle(id)
- driver_id INTEGER REFERENCES carrier_driver(id)
- status TEXT NOT NULL
- contact_result TEXT
- contact_result_comment TEXT
- created_at DATETIME NOT NULL
- updated_at DATETIME NOT NULL

Allowed status values:

- active
- completed
- failed
- cancelled

Allowed contact_result values:

- agreed
- no_answer_customer
- no_answer_carrier
- customer_refused
- carrier_refused
- price_disagreement
- duplicate_request
- other

Rule:

- only one active assignment per request

### request_excluded_carrier

Prevents a failed carrier from receiving the same reopened request again.

Fields:

- id INTEGER PRIMARY KEY
- request_id INTEGER NOT NULL REFERENCES transport_request(id)
- carrier_id INTEGER NOT NULL REFERENCES carrier_company(id)
- reason TEXT NOT NULL
- created_at DATETIME NOT NULL

Allowed reason values:

- carrier_declined
- no_agreement
- no_response
- admin_excluded

Unique constraint:

- request_id + carrier_id

### request_event_log

Append-only event history.

Fields:

- id INTEGER PRIMARY KEY
- request_id INTEGER REFERENCES transport_request(id)
- actor_type TEXT NOT NULL
- actor_id TEXT
- event_type TEXT NOT NULL
- old_status TEXT
- new_status TEXT
- payload_json TEXT
- created_at DATETIME NOT NULL

Allowed actor_type values:

- customer
- carrier
- admin
- system

Rule:

- never update or delete event log rows in normal operation

### carrier_subscription

Carrier payment/subscription record.

Fields:

- id INTEGER PRIMARY KEY
- carrier_id INTEGER NOT NULL REFERENCES carrier_company(id)
- plan TEXT NOT NULL
- paid_from DATETIME
- paid_until DATETIME
- status TEXT NOT NULL
- price REAL
- created_at DATETIME NOT NULL
- updated_at DATETIME NOT NULL

Allowed status values:

- active
- expired
- cancelled
- pending

### admin_invite_token

One-time invite for carrier onboarding.

Fields:

- token TEXT PRIMARY KEY
- carrier_id INTEGER NOT NULL REFERENCES carrier_company(id)
- created_by_admin_id INTEGER NOT NULL
- expires_at DATETIME NOT NULL
- used_at DATETIME
- used_by_telegram_id INTEGER
- status TEXT NOT NULL
- created_at DATETIME NOT NULL

Allowed status values:

- active
- used
- expired
- revoked

## Schedule-layer foundation tables

### request_time_window

Customer desired time window.

Fields:

- id INTEGER PRIMARY KEY
- request_id INTEGER NOT NULL REFERENCES transport_request(id)
- date_from DATE
- date_to DATE
- time_from TIME
- time_to TIME
- flexibility TEXT
- source TEXT
- created_at DATETIME NOT NULL

Allowed flexibility values:

- exact
- same_day
- flexible
- urgent

### carrier_availability

Carrier declared availability.

Fields:

- id INTEGER PRIMARY KEY
- carrier_id INTEGER NOT NULL REFERENCES carrier_company(id)
- date DATE NOT NULL
- time_from TIME
- time_to TIME
- capacity_slots INTEGER DEFAULT 1
- status TEXT NOT NULL
- created_at DATETIME NOT NULL
- updated_at DATETIME NOT NULL

Allowed status values:

- available
- limited
- unavailable

### carrier_booking

Calendar reservation for a request.

Fields:

- id INTEGER PRIMARY KEY
- carrier_id INTEGER NOT NULL REFERENCES carrier_company(id)
- request_id INTEGER NOT NULL REFERENCES transport_request(id)
- date DATE
- time_from TIME
- time_to TIME
- status TEXT NOT NULL
- created_at DATETIME NOT NULL
- updated_at DATETIME NOT NULL

Allowed status values:

- tentative
- confirmed
- cancelled
- completed

## Integrity rules

- request cannot be completed without completed assignment
- accepted offer must create assignment
- reopened request must increment offer_round
- failed assignment must create excluded carrier row unless admin overrides
- scheduler must expire old offers
- event log must record all status transitions
