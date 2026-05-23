-- Staging model: Clean sales data from raw zone
{{ config(materialized='view') }}

SELECT
    sale_id,
    product_id,
    sale_date::date AS sale_date,
    quantity,
    total_amount
FROM {{ source('raw', 'sales') }}
WHERE sale_id IS NOT NULL
  AND product_id IS NOT NULL
  AND quantity > 0
