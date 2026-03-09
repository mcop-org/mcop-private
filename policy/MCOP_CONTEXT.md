# MCOP Data Context

## Purpose

This document describes the structure and meaning of the **MCOP activity dataset**.

It exists to provide **context to automated agents (such as Codex)** so they can correctly interpret business events and build deterministic analytics.

If a metric definition is unclear or ambiguous, **agents must request clarification before implementing logic**.

---

# Activity Dataset

The **activity dataset** records events related to client interactions with coffee inventory.

Each row represents a **client request or operational event** associated with coffee inventory.

Requests may relate to:

- samples
- reservations
- releases

These requests move through defined **statuses and lifecycle stages**.

---

# Column Definitions

## Identifiers

**id_request**  
Unique event identifier for each activity record.

**client_id**  
Unique identifier assigned to each client.

**company_name**  
Name of the client company.

**contact_first_name**  
First name of the primary contact at the client company.

**contact_last_name**  
Last name of the primary contact at the client company.

**id_booking**  
Identifier linking a **release request** to the **reservation it belongs to**.

---

## Request Type

**request_type**

Possible values:

sample  
reservation  
release  

Meaning:

- **sample** → request for a product sample
- **reservation** → client reserves coffee inventory
- **release** → client requests coffee to be released from the warehouse

---

## Request Status

**request_status**

Possible values:

created  
approved  
rejected  
completed  

Meaning:

**created**  
Request created by the client.

**approved**  
Request approved by Mercanta operations.

**rejected**  
Request declined by Mercanta.

**completed**  
Process fully completed.

---

## Request Dates

**request_date**  
Date when the client created the request.

**approval_date**  
Date when Mercanta approved the request.

**amendment_date**  
Date when an existing reservation is amended to add or remove products.

---

## Delivery Information

**delivery_tracking_number**  
Tracking number associated with a dispatched order.

**delivery_cost**  
Cost of delivery associated with a release.

**dispatch_date**  
Date when coffee leaves the warehouse for the client.

**invoice_number**  
Invoice generated when coffee is released.

---

## Product Information

**product_id**  
Unique identifier for each coffee product.

**product_reference**  
Commercial reference used to identify the coffee.

**bag_size_kg**  
Weight of a single bag in kilograms.

**bags**  
Number of bags involved in the request.

**bags_remaining**  
Remaining number of bags in the reservation after releases.

**price_per_kg**  
Commercial price per kilogram.

**harvest_date**  
Harvest date of the coffee.

---

## Product Status

**status**

Possible values:

available  
sold out  
incoming  

Meaning:

- **available** → coffee is in warehouse and available
- **sold out** → no remaining inventory
- **incoming** → coffee not yet landed

---

## Commercial Relationship

**pathway**

Clients are assigned a commercial relationship pathway.

Possible values:

A  
B  

These pathways represent different commercial frameworks used by Mercanta.

---

## Contract Terms

**reservation_days**

Number of days a client is contractually allowed to hold a reservation before all coffee must be released.

Counting starts **from the reservation approval date**.

**payment_days**

Number of days the client has to settle payment after release.

---

## Logistics

**landing_status**

Possible values:

incoming  
landed  

Meaning:

- **incoming** → coffee still in transit
- **landed** → coffee arrived at warehouse

**landing_date**

Expected date coffee arrives from origin to warehouse.

**warehouse**

Location where coffee is stored.

Possible values include:

United Kingdom  
Europe  

---

# Lifecycle Definitions

## Created

created → request created by client

---

## Approved

approved → a reservation is approved when coffee has landed and is ready at the warehouse to be released

---

## Rejected

rejected → sample, reservation or release request declined

---

## Completed

completed → coffee fully released

---

# Release Definition

Release means:

Coffee leaves the warehouse and ownership transfers to the client.

---

# Request Status Rules

## Sample

sample request status:

approve  
rejected  

---

## Reservation

reservation status:

created  
rejected  
completed  

---

## Release

release status:

created  
approved  
rejected  
completed  

---

# Important Rule for Agents

If a requested metric depends on business definitions **not explicitly defined in this document**, the agent **must request clarification before implementing logic**.

Examples include:

- revenue definitions  
- reservation balance calculations  
- lifecycle interpretations  

Agents must **never guess business logic**.

---

# Deterministic Analytics Requirement

All analytics produced from this dataset must:

- be deterministic  
- use explicit sorting  
- avoid randomness  
- avoid system time unless explicitly passed as `as_of`

---

# Data Evolution

New columns may be added to the dataset in the future.

Agents must:

- ignore unknown columns  
- avoid failing on schema extensions  
- prefer **best-effort interpretation with explicit clarification when required**

---

# Reservation and Release Relationship Model

Reservations and releases are related operational events.

A **reservation** allocates coffee inventory to a client.

A **release** removes coffee from that reservation and transfers ownership to the client.

Multiple releases may occur from a single reservation.

The relationship is represented using:

id_booking

which links a release to the reservation it belongs to.

---

## Reservation Event

A reservation event is identified when:

request_type = reservation

The reservation represents an allocation of coffee to a client.

The reservation initially contains:

bags * bag_size_kg of coffee.

---

## Release Event

A release event is identified when:

request_type = release

A release reduces the quantity of coffee remaining in the reservation.

Multiple releases may occur for the same reservation.

Each release references the reservation using:

id_booking

---

## Reservation Balance

The reservation balance represents the coffee still held by the client but not yet released.

The remaining quantity may be tracked using:

bags_remaining

If bags_remaining is not present or unreliable, agents must request clarification before calculating balances.

---

## Event Model

The typical event sequence is:

reservation created  
reservation approved (coffee landed)  
release created  
release approved  
release completed

Multiple releases may occur until the reservation is fully completed.

---

## Reservation Completion

A reservation is considered **completed** when:

all reserved coffee has been released.

This may be represented by:

request_status = completed

or

bags_remaining = 0

If these rules conflict, agents must request clarification.

---

# Important Analytical Note

Reservations and releases must not be treated as independent sales events.

Releases are typically the event representing **inventory leaving the warehouse**.

Agents must request clarification before defining revenue, exposure, or sales metrics.

---

# Products Dataset

## Purpose

The **products dataset** describes the coffee products available, incoming, landed, or sold out in the MCOP system.

It provides the master product-level reference data used to understand:

- what coffee exists in the system
- origin and producer details
- physical stock characteristics
- offer availability
- commercial pricing
- warehouse references

This dataset is primarily used to provide **product context** for trading, reservation, release, warehouse, and dashboard analytics.

If a requested metric depends on product logic not explicitly defined here, the agent must request clarification before implementing logic.

---

## Product Dataset Column Definitions

### Core Product Identity

**product_id**  
Unique identifier for the product.

**product_reference**  
Commercial reference used internally to identify the coffee.

---

### Origin

**country_id**  
Unique identifier for the country of origin.

**country**  
Country name.

**region_id**  
Unique identifier for the region.

**region**  
Region name.

**farm**  
Name of the farm where the coffee is produced.

---

### Producer

**producer_id**  
Unique identifier for the producer.

**producer**  
Producer name.

---

### Coffee Characteristics

**variety_id**  
Unique identifier for the coffee variety.

**variety**  
Variety name.

**process_id**  
Unique identifier for the process.

**process**  
Processing method of the coffee.

Examples may include:

- washed
- natural
- thermal shock
- honey
- anaerobic

**cup_profile**  
Descriptive flavour notes, aromas, and sensory profile.

**cup_score**  
SCA cupping score.

---

### Physical Stock Information

**bag_size_kg**  
Weight of a single bag in kilograms.

**bags**  
Total number of bags of that reference in the shipment or lot.

**bags_available**  
Number of bags currently available in the offer list.

This is generally interpreted as:

bags available = total bags − reserved bags

If this interpretation changes, agents must request clarification.

---

### Commercial Fields

**price_per_kg**  
Commercial price per kilogram.

**harvest_date**  
Harvest date of the coffee.

---

### Product Status

**status**

Possible values may include:

- available
- sold out
- incoming

Meaning:

- **available** → coffee is available for reservation or release
- **sold out** → no bags remain commercially available
- **incoming** → coffee is not yet landed / not yet available

If status values differ in future exports, agents should inspect the live schema and request clarification if needed.

---

### Warehouse References

**rotation_number**  
Unique warehouse reference used by warehouse operatives.

**marks**  
Warehouse marks or reference labels associated with the product.

---

### Farm / Terroir Context

**elevation**  
Elevation of the farm above sea level.

---

# Products Dataset Analytical Notes

## Product-Level Value

The products dataset contains enough information to estimate product value using:

- bags
- bag_size_kg
- price_per_kg

However, if an agent needs to calculate product value for a specific business metric, it must ensure the intended formula and business meaning are appropriate for that metric.

If unclear, the agent must request clarification.

---

## Availability Logic

The products dataset may be used to understand:

- total bags in a lot
- currently available bags
- incoming coffee
- sold out coffee

Agents must not assume that `bags_available` alone fully explains reservation or release balances unless that behavior has been explicitly confirmed.

---

## Relationship to Activity Dataset

The products dataset provides **master product context**.

The activity dataset provides **event-level movement and client interactions**.

Typical relationship:

- `products.product_id` describes the coffee lot
- `activity.product_id` records client events against that lot

Agents should use the products dataset to enrich:

- dashboards
- top product analytics
- warehouse exposure analysis
- origin / producer / region breakdowns

---

## Deterministic Use Requirement

When products data is used in analytics, agents must:

- preserve deterministic ordering
- avoid guessing missing business definitions
- request clarification for ambiguous metrics
- ignore unknown future columns unless explicitly required