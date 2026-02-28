# MCOP Data Contract (v1.0.0-stable)

## products.csv required headers
- product_id
- product_reference
- bag_size_kg
- bags
- bags_remaining
- price_per_kg
- landing_status
- landing_date

## activity.csv required headers
- product_id
- bag_size_kg
- bags
- price_per_kg
- reservation_days
- payment_days
- landing_date

## product_costs_protected.csv required headers
- product_id
- bag_size_kg
- bags
- cost_of_green_coffee_gbp_kg
- cost_farm_to_port_gbp_kg
- freight_cost_gbp_kg
- cost_uk_port_to_warehouse_gbp_kg
- initial_payment_pct
- remaining_payment_pct
- initial_payment_date
- remaining_payment_date
- harvest_date
- landing_date