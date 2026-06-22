# CargoPT Bot — Schedule Layer v1

## Purpose

Schedule-layer is a domain layer for calendar semantics.

It is not the same as scheduler.

Scheduler executes background jobs.

Schedule-layer stores and interprets real-world time commitments:

- requested moving date
- preferred time window
- carrier availability
- tentative booking
- confirmed booking
- future calendar UI

## Why this layer exists in MVP design

Even if MVP does not show a calendar, transport requests are time-sensitive.

Without schedule-layer, future calendar support would require rewriting:

- transport_request date fields
- matching logic
- carrier availability
- assignment logic
- admin request views

Therefore MVP keeps simple date fields but reserves a proper schedule domain.

## Core concepts

### Request time window

Customer's desired transport time.

Examples:

- urgent
- today
- tomorrow
- exact date
- flexible date range
- morning
- afternoon
- evening

### Carrier availability

Carrier's available capacity.

Examples:

- available tomorrow 09:00-13:00
- unavailable on Sunday
- limited capacity this week

### Carrier booking

A concrete reservation linked to request and carrier.

Can be:

- tentative
- confirmed
- cancelled
- completed

## MVP storage

### transport_request

Keeps simple fields:

- urgency
- preferred_date

### request_time_window

Optional but recommended early.

Fields:

- request_id
- date_from
- date_to
- time_from
- time_to
- flexibility
- source

### carrier_availability

May be implemented later.

### carrier_booking

May be implemented when calendar view appears.

## Design principle

Request lifecycle and schedule lifecycle are related but not identical.

Request status answers:

- what happened to the lead?

Schedule status answers:

- is time reserved?

Example:

- request.status = in_contact
- carrier_booking.status = tentative

Another example:

- request.status = completed
- carrier_booking.status = completed

## Future calendar states

Booking statuses:

- tentative
- confirmed
- cancelled
- completed

Availability statuses:

- available
- limited
- unavailable

## Matching integration

MVP:

- match by urgency and preferred_date only

Future:

- match by actual carrier availability
- avoid double-booking
- suggest alternative slots
- show admin calendar

## Admin calendar future

Admin should eventually see:

- requests by date
- assigned carrier
- tentative bookings
- confirmed jobs
- failed/reopened requests
- unassigned urgent requests

## Carrier calendar future

Carrier should eventually see:

- accepted jobs
- pending offers
- tentative bookings
- unavailable periods

## Customer calendar future

Customer does not need full calendar.

Customer only needs:

- date/time selected
- carrier confirmation
- ability to change requested date before assignment if allowed

## MVP rule

Do not overbuild calendar UI.

But do not hardcode schedule logic into transport_request only.

## Boundary with scheduler

Schedule-layer stores business time.

Scheduler runs technical jobs.

Examples:

- Schedule-layer stores "customer wants tomorrow afternoon"
- Scheduler expires an offer after 30 minutes
- Schedule-layer stores "carrier is booked at 10:00"
- Scheduler sends reminder before booking

These must remain separate layers.
